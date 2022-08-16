import json
import sys
import time
from datetime import datetime, timedelta
from enum import Enum

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

from . import cds_ms_defender_consts as consts


class RateLimitExceedException(Exception):
    pass


class VulnerabilitySeverity(Enum):
    Critical = "Critical"
    High = "High"
    Medium = "Medium"
    Low = "Low"


def ingest_metric(instance_check, metric_name, metric_value, metrics_tag):
    """
    Used to ingest Metric
    """
    modified_metric_tags = []
    for tag in metrics_tag:
        modified_tag = tag.split(":")
        tag_key = "%s_%s" % (consts.INTEGRATION_PREFIX.replace(".", "_"), modified_tag[0])
        modified_metric_tags.append("%s:%s" % (tag_key, modified_tag[1]))
    tags = instance_check.instance.get("tags", []) + modified_metric_tags
    instance_check.gauge(metric_name, metric_value, tags=tags)


def ingest_logs(instance_check, service, events, timestamp_field=None, fn_to_evaluate_event=None):
    """
    Used to ingest Logs
    """
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
                instance_check.log.error("Could not submit logs")
                instance_check.log.exception(error)
    instance_check.log.info(
        "'%s/%s' Logs are ingested into Datadog platform with service: '%s'", ingested_logs_count, len(events), service
    )


def search_log(instance_check, index, query, **kwargs):
    """
    Used to search log
    """
    with ApiClientV2(ConfigurationV2(api_key=instance_check.configuration)) as api_client:
        api_instance = logs_api_v2.LogsApi(api_client)

        filter_query = query
        filter_from = dateutil_parser(kwargs.get('from'))
        filter_to = dateutil_parser(kwargs.get('to'))
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
        instance_check.log.error("Could not search log in Datadog")
        instance_check.log.exception(error)
        raise error


def search_checkpoint_log(instance_check, from_last_seconds=7200):
    """
    Used to search Checkpoint Log
    """

    now_time = datetime.utcnow()
    from_time = now_time - timedelta(seconds=from_last_seconds)
    now_time_str = now_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    from_time_str = from_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    param = {'from': from_time_str, 'to': now_time_str}
    filter_query = "source:{}".format(consts.CHECKPOINT_SOURCE_TYPE)
    try:
        response = search_log(instance_check, index=instance_check.log_index, query=filter_query, **param)

        # if data parse the result
        if len(response['data']) > 0:
            checkpoint_data = response['data'][0]['attributes']['attributes']
            data = {}
            for key, value in checkpoint_data.items():
                if consts.LOG_PREFIX in key:
                    data[key] = value
            return data
    except Exception as e:
        instance_check.log.error("Could not get the logs from Datadog platform")
        instance_check.log.exception(e)
    return {}


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
    hostname = instance_check.instance.get("hostname", "Microsoft_Defender")
    tags = ", ".join(instance_check.instance.get("tags", []))

    for event in events:
        evaluted_tags = []
        if timestamp_field:
            event["timestamp"] = event.get(timestamp_field)
        if fn_to_evaluate_event:
            event, evaluted_tags = fn_to_evaluate_event(event)
        http_log_items.append(
            HTTPLogItemV1(
                ddsource="crest_data_systems_microsoft_defender",
                ddtags=tags + ("," + ",".join(evaluted_tags) if evaluted_tags else ""),
                hostname=hostname,
                message=json.dumps(event),
                service=service,
            )
        )
    return http_log_items


def make_rest_call_by_id(
    instance_check, records, endpoint, id_field, filter_field, url, name_field=None, headers=None, params=None
):
    """
    Make rest call with ID Parameter
    """
    record_details = {}
    previous_record = {}
    last_record_date_time = {endpoint: instance_check.cur_date_time_str}
    for record in records:
        id = record.get(id_field)
        try:
            response = make_rest_call(instance_check, url.format(id), headers=headers, params=params, handle_429=True)
            if name_field:
                name = record.get(name_field)
                if name:
                    id = "%s||%s" % (id, name)
            record_details.update({id: response.get("value", [])})
            previous_record = record
        except RateLimitExceedException:
            last_record_date_time[endpoint] = previous_record.get(filter_field)
        except Exception as e:
            instance_check.log.error("Could not get detail of '%s' id for '%s'", id, endpoint)
            instance_check.log.exception(e)
    return record_details, last_record_date_time


def make_rest_call(
    instance_check,
    url,
    method="get",
    headers=None,
    params=None,
    data=None,
    json=None,
    do_retry=True,
    handle_429=False,
    pagination=False,
):
    """Make rest calls"""

    if method.lower() == "get":

        response = instance_check.http.get(url, headers=headers, params=params, timeout=None)

        if response is None:
            raise Exception("Could not make request to API. url: {}".format(url))

        if handle_429 and response.status_code == 429:
            if response.headers and response.headers.get("Retry-After"):
                retry_after = int(response.headers.get("Retry-After"))
                if retry_after < 60:
                    time.sleep(retry_after)
                else:
                    raise RateLimitExceedException()
            else:
                raise RateLimitExceedException()

        if do_retry and response.status_code == 401:
            instance_check.authentication()
            response = instance_check.http.get(url, headers=instance_check.headers, params=params, timeout=None)
            if response is None:
                raise Exception("Could not make request to API. url: {}".format(url))
        response.raise_for_status()
        if pagination:
            paginated_response = {"value": []}
            for res in get_paginated_results(instance_check, response, headers, params):
                paginated_response["value"].extend(res.get("value") or [])
            return paginated_response
        else:
            return response.json()

    if method.lower() == "post":

        response = instance_check.http.post(url, headers=headers, params=params, data=data, json=json, timeout=None)

        if do_retry and response.status_code == 401:
            instance_check.authentication()
            response = instance_check.http.post(url, headers=headers, params=params, data=data, json=json, timeout=None)

        response.raise_for_status()
        return response


def get_paginated_results(instance_check, response, headers, params):
    json_response = response.json()
    yield json_response
    next_url = json_response.get("@odata.nextLink")
    if next_url:
        splitted_url = next_url.split("?")
        skip_param = splitted_url[-1].split("&")[-1].split("=")
        if skip_param[0] == "$skip":
            no_records = skip_param[1]
            endpoint = splitted_url[0].split("/")[-1]
            instance_check.log.info("'%s' data fetched of '%s'.", no_records, endpoint)
        yield make_rest_call(instance_check, next_url, method="get", headers=headers, params=params, pagination=True)
