# Copyright (C) 2023 Crest Data Systems.
# All rights reserved

import json
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, Iterator, List, Tuple, Union

from datadog_api_client.exceptions import ApiException, ForbiddenException
from datadog_api_client.v1.api.authentication_api import AuthenticationApi
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.models import MetricContentEncoding
from datadog_api_client.v2 import ApiClient, Configuration
from datadog_api_client.v2.api.logs_api import LogsApi
from datadog_api_client.v2.models import ContentEncoding, LogsSort
from dateutil.parser import parse as dateutil_parser

from . import cds_netskope_constants as constants


def utc_time_from_timestamp(timestamp):
    """Coverts timestamp to the UTC datetime string."""
    return datetime.utcfromtimestamp(timestamp).strftime(constants.LOGS_TIME_FORMAT)


class DatadogAPIError(Exception):
    """Base exception class of Datadog API client."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidAPIKeyError(DatadogAPIError):
    """Raised when API key validation fails."""

    pass


class InvalidKeyError(DatadogAPIError):
    """Raised when API key or app key validation fails."""

    pass


def retry_on_api_exception(func):
    """Retries on Datadog API status error exceptions."""

    def retried_func(self, *args, **kwargs):
        tries = 0
        while True:
            try:
                resp = func(*args, **kwargs)
            except ForbiddenException as ex:
                forbidden_msg = (
                    "Received access forbidden error from Datadog API. Verify the configured api key and app key."
                )
                self.log.exception(f"Netskope | HOST={self.host} | MESSAGE={forbidden_msg}")  # noqa: G00
                raise InvalidKeyError(forbidden_msg) from ex
            except ApiException as ex:
                if ex.status in constants.DD_STATUS_TO_RETRY and tries < constants.DD_MAX_TRIES:
                    tries += 1
                    wait_for = constants.DD_WAIT_FOR
                    warn_msg = (
                        f"Datadog API error occurred with status code={ex.status},"
                        f" retrying for attempt {tries} after default wait time {wait_for} seconds..."
                    )
                    if ex.headers and ex.headers.get("x-ratelimit-reset"):
                        warn_msg = (
                            f"Datadog API error occurred with status code={ex.status},"
                            f" retrying for attempt {tries} after {wait_for} seconds..."
                        )
                        wait_for = float(ex.headers["x-ratelimit-reset"])

                    self.log.warning(f"Netskope | HOST={self.host} | MESSAGE={warn_msg}")  # noqa: G00

                    time.sleep(wait_for)
                    continue
                raise
            break
        return resp

    return retried_func


class DatadogClient:
    def __init__(self, site: str, api_key: str, instance_check: object):
        """Initializes DatadogClient object with API key.

        :param site: Datadog site
        :type site: str
        :param api_key: Datadog API key
        :type api_key: str
        :param instance_check: instance check object
        :type instance_check: object
        """
        self.api_client = ApiClient(Configuration(host=constants.API_SITE.format(site), api_key=api_key))
        self.log_client = ApiClient(Configuration(host=constants.LOGS_INTAKE_SITE.format(site), api_key=api_key))
        self.instance_check = instance_check
        self.host = instance_check.host
        self.log = instance_check.log

    def close(self):
        """DatadogClient object destructor."""
        self.api_client.close()
        self.log_client.close()

    def validate_api_key(self) -> None:
        """Validates API key and raises error if it is invalid.

        :raises InvalidAPIKeyError: raised when api key validation fails.
        """
        try:
            auth_api = AuthenticationApi(self.api_client)
            response = auth_api.validate()

            if response.get("valid") is True:
                success_msg = "Connection with datadog is successful."
                self.log.info(f"Netskope | HOST={self.host} | MESSAGE={success_msg}")  # noqa: G00
            else:
                err_message = f"Something went wrong while validating Datadog API key: {response}"
                self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
                raise InvalidAPIKeyError(err_message)

        except ForbiddenException as err:
            forbidden_msg = "Datadog API key validation failed. Verify the configured API key."
            self.log.error(f"Netskope | HOST={self.host} | MESSAGE={forbidden_msg}")  # noqa: G00
            raise InvalidAPIKeyError(forbidden_msg) from err

        except Exception:
            err_message = "Error occurred while validating datadog API key."
            self.log.exception(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
            raise

    def validate_keys(self) -> None:
        """Validates API key and app key.

        :raises InvalidKeyError: raised when api key or app key validation fails.
        """
        try:
            current_time = time.time()
            past_1_hour = current_time - 3600
            params = {"from": utc_time_from_timestamp(past_1_hour), "to": utc_time_from_timestamp(current_time)}
            self.search_log_in_datadog(self.instance_check.log_index, **params)

            success_msg = "Connection with datadog is successful."
            self.log.info(f"Netskope | HOST={self.host} | MESSAGE={success_msg}")  # noqa: G00

        except InvalidKeyError as err:
            forbidden_msg = "Datadog api/app key validation failed. Verify the configured api key and app key."
            self.log.error(f"Netskope | HOST={self.host} | MESSAGE={forbidden_msg}")  # noqa: G00
            raise InvalidKeyError(forbidden_msg) from err

        except Exception:
            err_message = "Error occurred while validating datadog api/app key."
            self.log.exception(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
            raise

    def create_chunks_for_events(
        self, events: List, chunk_size_limit: int, chunk_length_limit: Union[int, None] = 1000
    ) -> Iterator:
        """Creates chunks of events to handle Datadog API restrictions.

        :param events: list of events
        :type events: list
        :param chunk_size_limit: maximum size of chunks
        :type chunk_size_limit: int
        :param chunk_length_limit: maximum length of chunks
        :type chunk_length_limit: Union[int, None]

        :return: list of chunks of events
        :rtype: Generator
        """
        chunk = list()
        buffer_size = 0
        for event in events:
            size_of_event = len(json.dumps(event).encode("utf-8"))
            if (buffer_size + size_of_event) > chunk_size_limit or (
                chunk_length_limit is not None and len(chunk) >= chunk_length_limit
            ):
                yield chunk
                chunk = list()
                buffer_size = 0
            chunk.append(event)
            buffer_size += size_of_event
        if len(chunk) > 0:
            yield chunk

    def submit_metrics(self, metrics_list: List[Tuple], latest: bool = False, include_prefix: bool = True) -> None:
        """Submits metrics to the Datadog.

        :param metrics_list: list of metrics tuples. Index wise breakdown of tuples
            of metrics properties is as following.
                0: metrics name
                1: metrics value
                2: list of metrics tags
                3: metrics timestamp
        :type metrics_list: List[Tuple]
        :param latest: flag to indicate whether current timestamp should be used
            as a metrics timestamp. Defaults to False.
        :type latest: bool
        :param include_prefix: indicate whether constant metric prefix should be
            added to metric name
        :type include_prefix: bool
        """
        metrics_series = []
        submitted_metrics_count = 0
        for metrics in metrics_list:
            metrics_series.append(
                {
                    "metric": f"{constants.INTEGRATION_PREFIX}.{metrics[0]}" if include_prefix else metrics[0],
                    "type": "gauge",
                    "points": [[metrics[3] if not latest else int(time.time()), metrics[1]]],
                    "tags": metrics[2] + [f"time:{datetime.fromtimestamp(metrics[3]) if not latest else 'current'}"],
                    "host": self.instance_check.host,
                }
            )

        chunks = self.create_chunks_for_events(metrics_series, constants.METRICS_MAX_CHUNK_SIZE)
        for chunk in chunks:
            metrics_body = {"series": chunk}

            metrics_api = MetricsApi(self.api_client)
            try:
                submit_metrics_with_retry = retry_on_api_exception(metrics_api.submit_metrics)
                response = submit_metrics_with_retry(self, metrics_body, content_encoding=MetricContentEncoding.GZIP)
                if response.get("status") == "ok":
                    submitted_metrics_count += len(chunk)
                else:
                    self.log.error(
                        f"Netskope | HOST={self.host} | MESSAGE=Something went wrong while submitting"  # noqa: G00
                        f" metrics. Response: {response}"
                    )
            except ApiException as err:
                self.log.exception(
                    f"Netskope | HOST={self.host} | MESSAGE=API error occurred while submitting"  # noqa: G00
                    f" metrics: {err}"
                )
                raise
        self.log.info(
            f"Netskope | HOST={self.host} | MESSAGE={submitted_metrics_count}/{len(metrics_list)} metrics"  # noqa: G00
            " are ingested into Datadog platform.",
        )

    def submit_logs(
        self, service: str, events: List, timestamp_field: str = None, fn_to_evaluate_event: Callable = None
    ) -> None:
        """Submits logs to the Datadog.

        :param service: service name of the log.
        :type service: str
        :param events: list of events
        :type events: List
        :param timestamp_field: name of the timestamp field from events data. Defaults to None.
        :type timestamp_field: str
        :param fn_to_evaluate_event: function that will return events and tags list from events data. Defaults to None.
        :type: Callable
        """
        ingested_logs_count = 0
        # add integration prefix to service name
        service = ".".join([constants.INTEGRATION_PREFIX, service])
        api_instance = LogsApi(self.log_client)
        chunks = self.create_chunks_for_events(events, constants.LOGS_MAX_CHUNK_SIZE, constants.LOGS_MAX_CHUNK_LENGTH)
        for chunk in chunks:
            body_items = self._prepare_body(service, chunk, timestamp_field, fn_to_evaluate_event)
            body = body_items
            try:
                # Send logs
                submit_log_with_retry = retry_on_api_exception(api_instance.submit_log)
                submit_log_with_retry(self, body, content_encoding=ContentEncoding.GZIP)
                ingested_logs_count += len(chunk)
            except ApiException as err:
                self.log.exception(
                    f"Netskope | HOST={self.host} | MESSAGE=API error occurred while submitting"  # noqa: G00
                    f" logs: {err}"
                )
                raise
        self.log.info(
            f"Netskope | HOST={self.host} | MESSAGE={ingested_logs_count}/{len(events)} Logs"  # noqa: G00
            f" are ingested into Datadog platform with service: '{service}'",
        )

    def _prepare_body(
        self, service: str, events: List, timestamp_field: str = None, fn_to_evaluate_event: Callable = None
    ) -> List:
        """Prepares body of events to ingest as logs.

        :param service: service name of the log.
        :type service: str
        :param events: list of events
        :type events: List
        :param timestamp_field: name of the timestamp field from events data. Defaults to None.
        :type timestamp_field: str
        :param fn_to_evaluate_event: function that will return events and tags list from events data. Defaults to None.
        :type: func

        :return: list of prepare logs
        :rtype: List
        """
        http_log_items = list()
        tags = ", ".join(self.instance_check.instance.get("tags", list()))

        for event in events:
            evaluated_tags = list()
            if fn_to_evaluate_event:
                event, evaluated_tags = fn_to_evaluate_event(event)

            # add host as a instance tag
            evaluated_tags.append(f"{constants.HOST_TAG_NAME}:{self.instance_check.host}")
            if timestamp_field:
                event["timestamp"] = utc_time_from_timestamp(event.get(timestamp_field))

            http_log_items.append(
                {
                    "ddsource": "crest_data_systems_netskope",
                    "ddtags": tags + ("," + ",".join(evaluated_tags) if evaluated_tags else ""),
                    "hostname": self.instance_check.host,
                    "message": json.dumps(event, default=str),
                    "service": service,
                }
            )
        return http_log_items

    def search_log_in_datadog(self, index, query="", **kwargs) -> List:
        """Searches log data with query.

        :param index: log index name
        :type index: str
        :param query: search query string
        :type query: str

        :return: searched log data
        :rtype: List
        """
        api_instance = LogsApi(self.api_client)
        filter_query = query
        filter_from = dateutil_parser(kwargs.get("from"))
        filter_to = dateutil_parser(kwargs.get("to"))
        filter_index = index
        sort = LogsSort("-timestamp")

        try:
            # Get a list of logs
            list_logs_get_with_retry = retry_on_api_exception(api_instance.list_logs_get)
            api_response = list_logs_get_with_retry(
                self,
                filter_query=filter_query,
                filter_index=filter_index,
                sort=sort,
                filter_from=filter_from,
                filter_to=filter_to,
                page_limit=1,
            )
            return api_response
        except ApiException as err:
            if (
                err.status == 400
                and err.body
                and isinstance(err.body, dict)
                and err.body.get("errors") == constants.NO_LOG_ERROR_MESSAGE
            ):
                err_message = (
                    "Received 'no valid index specified' error while searching logs, which indicates no logs"
                    " are present in the Datadog platform at the moment so returning empty log dictionary."
                )
                self.log.info(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
                return constants.EMPTY_SEARCH_LOG
            self.log.exception(
                f"Netskope | HOST={self.host} | MESSAGE=Could not search log in Datadog with"  # noqa: G00
                f" query filter: {filter_query}."
            )
            raise

    def save_checkpoint(self, name: str, data: Dict) -> None:
        """Saves checkpoint as a datadog log with host and endpoint.

        :param name: checkpoint name
        :type name: str
        :param data: checkpoint data
        :type data: dict
        """

        def checkpoint_event_evaluator(event: dict):
            return event.get("event"), event.get("tags")

        data["timestamp"] = int(time.time())
        checkpoint = [
            {
                "event": data,
                "tags": [f"host: {self.instance_check.host}"],
            }
        ]
        self.submit_logs(
            ".".join([name, constants.CHECKPOINT_SERVICE]),
            checkpoint,
            "timestamp",
            fn_to_evaluate_event=checkpoint_event_evaluator,
        )

    def get_checkpoint(self, name: str, search_host: bool = True, raise_error: bool = True) -> Dict:
        """Fetches and returns checkpoint log from datadog.

        :param name: checkpoint name
        :type name: str
        :param search_host: True if logs should be searched by host else False, defaults to True
        :type search_host: bool
        :param raise_error: whether error should be raised or ignored, defaults to True
        :type raise_error: bool

        :return: checkpoint dictionary
        :rtype: dict
        """
        now_time = datetime.utcnow()
        from_time = now_time - timedelta(seconds=constants.CHECKPOINT_TIME_OFFSET)
        now_time_str = now_time.strftime(constants.LOGS_TIME_FORMAT)
        from_time_str = from_time.strftime(constants.LOGS_TIME_FORMAT)

        kwargs = {"from": from_time_str, "to": now_time_str}
        filter_query = "service:{}".format(".".join([constants.INTEGRATION_PREFIX, name, constants.CHECKPOINT_SERVICE]))
        if search_host:
            filter_query += f" host:{self.instance_check.host}"
        try:
            response = self.search_log_in_datadog(
                index=self.instance_check.log_index,
                query=filter_query,
                **kwargs,
            )

            # if data parse the result, we will return last checkpoint log
            if len(response["data"]) > 0:
                checkpoint_data = response["data"][0]["attributes"]["attributes"]
                return checkpoint_data
        except Exception:
            self.log.exception(
                f"Netskope | HOST={self.host} | MESSAGE=Could not get the checkpoint log of '{name}' from"  # noqa: G00
                " datadog platform."
            )
            if raise_error:
                raise
        return dict()
