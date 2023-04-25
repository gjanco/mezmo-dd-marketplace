import json
import sys
from typing import Union

from datadog_api_client.v1 import ApiClient as ApiClientV1
from datadog_api_client.v1 import ApiException as ApiExceptionV1
from datadog_api_client.v1 import Configuration as ConfigurationV1
from datadog_api_client.v1.api import logs_api as logs_api_v1
from datadog_api_client.v1.models import HTTPLog as HTTPLogV1
from datadog_api_client.v1.models import HTTPLogItem as HTTPLogItemV1
from datadog_api_client.v2 import ApiClient as ApiClientV2
from datadog_api_client.v2 import ApiException as ApiExceptionV2
from datadog_api_client.v2 import Configuration as ConfigurationV2
from datadog_api_client.v2.api import logs_api as logs_api_v2
from datadog_api_client.v2.models import LogsSort as LogsSortV2
from dateutil.parser import parse as dateutil_parser

from .cds_netapp_ontap_constants import (
    AUTH_CHECK_NAME,
    AUTH_EVENT_SOURCE_TYPE,
    INTEGRATION_PREFIX,
    MAX_CHUNK_LENGTH,
    MAX_CHUNK_SIZE,
)


def ingest_metric(instance_check, metric_name, metric_value, metrics_tag=None):
    """
    Used to ingest Metric
    """
    try:
        metrics_tag = [] if not metrics_tag else metrics_tag
        modified_metric_tags = []
        # add instance host to tag
        modified_metric_tags.append(f"cds_netapp_ontap_instance:{instance_check.host}")
        # add server type (cluster or 7-mode) to tag
        modified_metric_tags.append(f'server-type:{"cluster" if instance_check.client.isClustered() else "7-mode"}')
        # add integration prefix to metrics name
        metric_name = ".".join([INTEGRATION_PREFIX, metric_name])

        for tag in metrics_tag:
            modified_metric_tags.append(tag)
        tags = instance_check.instance.get("tags", []) + modified_metric_tags
        instance_check.gauge(metric_name, metric_value, tags=tags, hostname=instance_check.host)
    except Exception as err:
        instance_check.log.error(
            "NETAPP ONTAP ERROR: Error occurred while ingesting metric. "  # noqa: G001
            "MetricName: '{metric_name}'".format(metric_name=metric_name),
        )
        instance_check.log.exception(err)


def ingest_logs(instance_check, service, events, timestamp_field=None, fn_to_evaluate_event=None, force_ingest=False):
    """
    Used to ingest Logs
    """
    # check if log ingestion flag is set
    if not (force_ingest or instance_check.ingest_log):
        instance_check.log.info(
            "NETAPP ONTAP INFO: Skipping log ingestion of service: '%s'",
            service,
        )
        return

    ingested_logs_count = 0
    # add integration prefix to service name
    service = ".".join([INTEGRATION_PREFIX, service])
    with ApiClientV1(ConfigurationV1(api_key=instance_check.configuration)) as api_client:
        api_instance = logs_api_v1.LogsApi(api_client)
        chunks = list(create_chunks_for_events(events))
        for chunk in chunks:
            body_items = _prepare_body(instance_check, service, chunk, timestamp_field, fn_to_evaluate_event)
            body = HTTPLogV1(body_items)
            try:
                # Send logs
                _ = api_instance.submit_log(body)
                ingested_logs_count += len(chunk)
            except ApiExceptionV1 as error:
                instance_check.log.error("NETAPP ONTAP ERROR: Could not submit logs")
                instance_check.log.exception(error)
    instance_check.log.info(
        "NETAPP ONTAP INFO: '%s/%s' Logs are ingested into Datadog platform with service: '%s'",
        ingested_logs_count,
        len(events),
        service,
    )


def search_log_in_datadog(instance_check, index, query="", **kwargs):
    """
    Used to search log
    """
    with ApiClientV2(ConfigurationV2(api_key=instance_check.configuration)) as api_client:
        api_instance = logs_api_v2.LogsApi(api_client)
        filter_query = query
        filter_from = dateutil_parser(kwargs.get("from"))
        filter_to = dateutil_parser(kwargs.get("to"))
        filter_index = index
        sort = LogsSortV2("-timestamp")
    try:
        # Get a list of logs
        api_response = api_instance.list_logs_get(
            filter_query=filter_query,
            filter_index=filter_index,
            sort=sort,
            filter_from=filter_from,
            filter_to=filter_to,
            page_limit=1,
        )
        return api_response
    except ApiExceptionV2 as error:
        instance_check.log.error("NETAPP ONTAP ERROR: Could not search log in Datadog")
        instance_check.log.exception(error)
        raise error


def create_chunks_for_events(events):
    """
    Used to create chunks of events
    """
    chunk = []
    buffer_size = 0
    for event in events:
        size_of_event = sys.getsizeof(event)
        if (buffer_size + size_of_event) > MAX_CHUNK_SIZE or len(chunk) >= MAX_CHUNK_LENGTH:
            yield chunk
            chunk = []
            buffer_size = 0
        chunk.append(event)
        buffer_size += size_of_event
    if len(chunk) > 0:
        yield chunk


def _prepare_body(instance_check, service, events, timestamp_field=None, fn_to_evaluate_event=None):
    """
    Used to prepare body of event
    """
    http_log_items = []
    hostname = instance_check.instance.get("hostname", instance_check.host)
    tags = ", ".join(instance_check.instance.get("tags", []))

    for event in events:
        evaluated_tags = []
        if timestamp_field:
            event["timestamp"] = event.get(timestamp_field)
        if fn_to_evaluate_event:
            event, evaluated_tags = fn_to_evaluate_event(event)

        # add instance host to tag
        evaluated_tags.append(f"cds_netapp_ontap_instance:{instance_check.host}")
        # add server type (cluster or 7-mode) to tag
        evaluated_tags.append(f'server-type:{"cluster" if instance_check.client.isClustered() else "7-mode"}')

        http_log_items.append(
            HTTPLogItemV1(
                ddsource="crest_data_systems_netapp_ontap",
                ddtags=tags + ("," + ",".join(evaluated_tags) if evaluated_tags else ""),
                hostname=hostname,
                message=json.dumps(event),
                service=service,
            )
        )
    return http_log_items


def ingest_service_check_and_event_for_auth(instance_check, is_authenticated=True, reason=""):
    """
    Ingest Service Check and Event for authentication
    """
    msg = ["Authentication successful", 0] if is_authenticated else [f"Authentication failed. Reason: {reason}", 2]
    instance_check.service_check(AUTH_CHECK_NAME, msg[1], message=msg[0], hostname=instance_check.host)
    instance_check.event(
        {
            "source_type_name": AUTH_EVENT_SOURCE_TYPE,
            "msg_title": "Authentication",
            "msg_text": msg[0],
        }
    )


def combine_dict(dict_list):
    """
    Used to combine list of dictionaries into one
    """
    result = {}
    for dict in dict_list:
        result = {**result, **dict}
    return result


def perf_response_parser(raw):
    """
    Used to create key-value pair dict from name-value pairs list of dictionary
    """
    result = {}
    for ele in raw:
        if ele.get("name") and ele.get("value"):
            result[ele["name"]] = ele["value"]

    return result


def field_parser(event, fields):
    """
    Used to parse multi-level dict structure's fields to single level dictionary
    """
    result = {}
    for field in fields:
        data = None
        for key in field.split("."):
            data = data.get(key, {}) if data else event.get(key, {})

        result[field.split(".")[-1]] = data or "-"

    return result


def field_alias_generator(event, alias):
    """
    Used to generate event with provided alias fields
    """
    result = {}
    for new_field in alias:
        if event.get(new_field):
            result[new_field] = event[new_field]
            continue
        for old_field in alias[new_field]:
            if event.get(old_field):
                result[new_field] = event[old_field]
                break

        if not result.get(new_field):
            result[new_field] = "-"

    return result


def is_true(val: Union[str, int]) -> bool:
    """
    Used to check if val is true.
    """

    value = str(val).strip().upper()
    if value in ("1", "TRUE", "T", "Y", "YES"):
        return True
    return False
