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

from . import cds_netapp_aiqum_constants as constants


def ingest_logs(instance_check, service, events, timestamp_field=None, fn_to_evaluate_event=None, force_ingest=False):
    """
    Used to ingest Logs
    """
    # check if log ingestion flag is set
    if not (force_ingest or instance_check.ingest_log):
        instance_check.log.info(
            "NETAPP AIQUM INFO: Skipping log ingestion of service: '%s'",
            service,
        )
        return

    ingested_logs_count = 0
    # add integration prefix to service name
    service = ".".join([constants.INTEGRATION_PREFIX, service])
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
                instance_check.log.error("NETAPP AIQUM ERROR: Could not submit logs")
                instance_check.log.exception(error)
    instance_check.log.info(
        "NETAPP AIQUM INFO: '%s/%s' Logs are ingested into Datadog platform with service: '%s'",
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
        instance_check.log.error("NETAPP AIQUM ERROR: Could not search log in Datadog")
        instance_check.log.exception(error)
        raise error


def create_chunks_for_events(events):
    """
    Used to create chunks of events
    """
    chunk = list()
    buffer_size = 0
    for event in events:
        size_of_event = sys.getsizeof(event)
        if (buffer_size + size_of_event) > constants.MAX_CHUNK_SIZE or len(chunk) >= constants.MAX_CHUNK_LENGTH:
            yield chunk
            chunk = list()
            buffer_size = 0
        chunk.append(event)
        buffer_size += size_of_event
    if len(chunk) > 0:
        yield chunk


def _prepare_body(instance_check, service, events, timestamp_field=None, fn_to_evaluate_event=None):
    """
    Used to prepare body of event
    """
    http_log_items = list()
    tags = ", ".join(instance_check.instance.get("tags", list()))

    for event in events:
        evaluated_tags = list()
        if timestamp_field:
            event["timestamp"] = event.get(timestamp_field)
        if fn_to_evaluate_event:
            event, evaluated_tags = fn_to_evaluate_event(event)

        # add host as a instance tag
        evaluated_tags.append(f"cds_netapp_aiqum_instance:{instance_check.host}")

        http_log_items.append(
            HTTPLogItemV1(
                ddsource="crest_data_systems_netapp_aiqum",
                ddtags=tags + ("," + ",".join(evaluated_tags) if evaluated_tags else ""),
                hostname=instance_check.host,
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
    instance_check.service_check(constants.AUTH_CHECK_NAME, msg[1], message=msg[0], hostname=instance_check.host)
    instance_check.event(
        {
            "source_type_name": constants.AUTH_EVENT_SOURCE_TYPE,
            "msg_title": "Authentication",
            "msg_text": msg[0],
        }
    )


def field_parser(event, fields):
    """
    Used to parse multi-level dict structure's fields to single level dictionary
    """
    result = dict()
    for field in fields:
        data = None
        field_keys = field.split(".")
        for index, key in enumerate(field_keys):
            index += 1
            data = data.get(key) if data else event.get(key)
            if isinstance(data, list) and index < len(field_keys):
                _data = []
                child_field = ".".join(field_keys[index:])
                for _event in data:
                    _result = field_parser(_event, [child_field])
                    if not (is_empty(_result.get(child_field)) or _result.get(child_field) == "-"):
                        _data.append(_result.get(child_field))
                data = _data
                break
            elif not data:
                break

        result[field] = "-" if is_empty(data) else data

    return result


def field_alias_generator(event, alias):
    """
    Used to generate event with provided alias fields
    """
    result = dict()
    for new_field in alias:
        if not is_empty(event.get(new_field)):
            result[new_field] = event[new_field]
            continue
        for old_field in alias[new_field]:
            if event.get(old_field):
                result[new_field] = event[old_field]
                break

        if is_empty(result.get(new_field)):
            result[new_field] = "-"

    return result


def tag_generator(event, fields):
    """
    Used to generate tag list from event with provided field name list
    """
    tags = list()
    for field in fields:
        tags.append(f"{field}:{event.get(field)}")
    return tags


def is_true(val: Union[str, int]) -> bool:
    """
    Used to check if value is true.
    """
    value = str(val).strip().upper()
    if value in ("1", "TRUE", "T", "Y", "YES"):
        return True
    return False


def is_float(val: Union[str, float, int]) -> bool:
    """
    Used to check if value is a float value.
    """
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def is_empty(val: any):
    """
    Used to check whether value is empty string, None value or empty object.
    """
    return not (val or is_float(val))


def generate_metrics(
    response_json, panel_name, event_fields, alias_fields, tag_fields, metric_fields, unique_field=None
):
    """
    Used to generate and return metrics list with tags.
    """
    metric_list = list()
    metric_dc = set()
    for record in response_json.get("records", []):
        raw_event = field_parser(record, event_fields)
        event = field_alias_generator(raw_event, alias_fields)
        tags = tag_generator(event, tag_fields)
        for metric_field in metric_fields:
            metric_prefix = ".".join([constants.INTEGRATION_PREFIX, panel_name, metric_field])
            metric_list.append(
                [
                    metric_prefix,
                    event.get(metric_field, 0),
                    tags,
                ]
            )

        if unique_field:
            metric_dc.add(event.get(unique_field))
    if unique_field:
        metric_list.append([".".join([constants.INTEGRATION_PREFIX, panel_name, "dc"]), len(metric_dc), []])
    return metric_list


def generate_logs(response_json, event_fields, alias_fields, conditions=None):
    """
    Used to generate logs with tags.
    """
    logs_list = list()
    for record in response_json.get("records", []):
        raw_event = field_parser(record, event_fields)
        event = field_alias_generator(raw_event, alias_fields)
        if not conditions or condition_check(event, conditions):
            logs_list.append(event)
    return logs_list


def condition_check(event, conditions):
    """
    Used to check whether given event passes the conditions.
    """
    for field in conditions:
        for condition in conditions[field]:
            value = event.get(field)
            if (condition == "not_empty" and is_empty(value)) or (
                condition == "not_zero" and is_float(value) and float(value) == 0
            ):
                return False

    return True
