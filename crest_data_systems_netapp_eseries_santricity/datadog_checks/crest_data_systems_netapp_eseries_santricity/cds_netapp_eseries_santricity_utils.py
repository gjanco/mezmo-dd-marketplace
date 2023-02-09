import json
import sys

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

from . import cds_netapp_eseries_santricity_consts as consts


def ingest_metric(instance_check, metric_name, metric_value, metrics_tag):
    """
    Used to ingest Metric
    """
    try:
        hostname = instance_check.instance.get("address", "NetApp_ESeries_SANtricity")
        metrics_tag.append(f'system_id:{instance_check.instance.get("system_id")}')
        tags = instance_check.instance.get("tags", []) + metrics_tag
        instance_check.gauge(metric_name, metric_value, tags=tags, hostname=hostname)
        instance_check.log.info(
            "NetApp ESeries SANtricity: Metric is ingested successfully."  # noqa: G00
            " metric_name={}".format(metric_name),
        )
    except Exception as ex:
        instance_check.log.error(
            "NetApp ESeries SANtricity: Exception occurred while"  # noqa: G00
            " metric ingestion: {} metric={}".format(str(ex), metric_name),
        )
        instance_check.log.exception(ex)


def ingest_logs(instance_check, service, events, timestamp_field=None, fn_to_evaluate_event=None):
    """
    Used to ingest Logs
    """
    # check if log ingestion flag is set
    if not instance_check.ingest_log:
        instance_check.log.info(
            "NetApp ESeries SANtricity: Skipping log ingestion of service: {}".format(service)  # noqa: G00
        )
        return
    try:
        ingested_logs_count = 0
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
                    instance_check.log.error("NetApp ESeries SANtricity: Could not submit logs")
                    instance_check.log.exception(error)
        instance_check.log.info(
            "NetApp ESeries SANtricity: {}/{} Logs are ingested into Datadog "  # noqa: G00
            "platform with service: {}".format(ingested_logs_count, len(events), service),
        )
    except Exception as ex:
        instance_check.log.error(
            "NetApp ESeries SANtricity: Exception occurred "  # noqa: G00
            "while log ingestion: {} service={}".format(str(ex), service),
        )
        instance_check.log.exception(ex)


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
        instance_check.log.error("NetApp ESeries SANtricity: Could not search log in Datadog")
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
        if (buffer_size + size_of_event) > consts.MAX_CHUNK_SIZE or len(chunk) >= consts.MAX_CHUNK_LENGTH:
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
    hostname = instance_check.instance.get("address", "NetApp_ESeries_SANtricity")
    tags = instance_check.instance.get("tags", [])

    for event in events:
        evaluted_tags = []
        if timestamp_field:
            event["timestamp"] = event.get(timestamp_field)
        if fn_to_evaluate_event:
            event, evaluted_tags = fn_to_evaluate_event(event)
        evaluted_tags.append(f"arrayName:{instance_check.arrayName}")
        http_log_items.append(
            HTTPLogItemV1(
                ddsource="crest_data_systems_netapp_eseries_santricity",
                ddtags=",".join(tags + evaluted_tags),
                hostname=hostname,
                message=json.dumps(event),
                service=service,
            )
        )
    return http_log_items
