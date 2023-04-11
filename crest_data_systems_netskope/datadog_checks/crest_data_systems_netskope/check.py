# Copyright (C) 2023 Crest Data Systems.
# All rights reserved

import re
import time
from typing import Tuple

import datadog_agent
import requests

from datadog_checks.base import AgentCheck
from datadog_checks.base.errors import ConfigTypeError, ConfigurationError, ConfigValueError

from . import cds_netskope_constants as constants
from . import cds_netskope_utils as utils
from .cds_netskope_api_client import NetskopeClient
from .cds_netskope_datadog_client import DatadogClient, InvalidKeyError
from .cds_netskope_errors import BillingSubmitError
from .cds_netskope_events import EVENTS_CONFIG


def handle_errors(func):
    def handler(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception:
            raise
        finally:
            self.dd_client.close()

    return handler


class CrestDataSystemsNetskopeCheck(AgentCheck):
    # This will be the prefix of every metric and service check the integration sends
    __NAMESPACE__ = "cds.netskope"

    def __init__(self, name, init_config, instances):
        super(CrestDataSystemsNetskopeCheck, self).__init__(name, init_config, instances)

        # Set log index to all for searching checkpoint logs from Datadog platform
        self.log_index = "*"

        # Read and set api_key and app_key for datadog API authentication
        self._api_key = datadog_agent.get_config("api_key")
        self._app_key = datadog_agent.get_config("app_key")

        self._site = datadog_agent.get_config("site") or constants.DEFAULT_SITE

        # Use self.instance to read the check configuration
        self.host = self.instance.get("host")
        self.v2_api_token = self.instance.get("v2_api_token")
        self.min_collection_interval = self.instance.get("min_collection_interval")
        self.events = self.instance.get("events", constants.DEFAULT_EVENTS)
        self.collect_alerts = self.instance.get("collect_alerts")
        self.ingest_metrics = self.instance.get("ingest_metrics")

        # Initialize Datadog API client
        self.initialize_dd_client()

    @handle_errors
    def check(self, _):
        # Validate user configurations
        try:
            self.validate_configurations()
            msg = "All the provided configurations in conf.yaml are valid."
            self.log.info(f"Netskope | HOST={self.host} | MESSAGE={msg}")  # noqa: G00

            # Using checks and events, show that validations are successful.
            self.ingest_service_check_and_event(
                status=0,
                tags=constants.CONF_VAL_TAG,
                message=msg,
                title=constants.CONF_VAL_TITLE,
                source_type=constants.CONF_VAL_SOURCE_TYPE,
            )
        except Exception:
            err_message = (
                "Error occurred while validating the provided configurations in conf.yaml."
                " Please check logs for more details."
            )
            # Using checks and events, show that validations are not successful.
            self.ingest_service_check_and_event(
                status=2,
                tags=constants.CONF_VAL_TAG,
                message=err_message,
                title=constants.CONF_VAL_TITLE,
                source_type=constants.CONF_VAL_SOURCE_TYPE,
            )
            raise

        # Initialize Netskope API client for data collection
        self.initialize_client()

        # Authenticate Netskope API using V2 token
        try:
            self.authentication()
            msg = "Authentication with Netskope is successful."
            self.log.info(f"Netskope | HOST={self.host} | MESSAGE={msg}")  # noqa: G00

            # Using checks and events, show that authentication is successful.
            self.ingest_service_check_and_event(
                status=0,
                tags=constants.AUTH_TAG,
                message=msg,
                title=constants.AUTH_TITLE,
                source_type=constants.AUTH_SOURCE_TYPE,
            )
        except Exception:
            err_message = (
                "Error occurred while authenticating the Netskope credentials. Please check logs for more details."
            )
            # Using checks and events, show that authentication is not successful.
            self.ingest_service_check_and_event(
                status=2,
                tags=constants.AUTH_TAG,
                message=err_message,
                title=constants.AUTH_TITLE,
                source_type=constants.AUTH_SOURCE_TYPE,
            )
            raise

        self.log.info(f"Netskope | HOST={self.host} | MESSAGE=Start of the data collection.")  # noqa: G00
        start_time = time.time()

        # Netskope event data collection and Datadog ingestion
        for event_conf in EVENTS_CONFIG:
            event_type = event_conf.get("type")

            # Check if event type is configured in configuration
            if (event_type != "alert" and event_type not in self.events) or (
                event_type == "alert" and not self.collect_alerts
            ):
                self.log.info(
                    f"Netskope | HOST={self.host} | MESSAGE=Skipping data collection for"  # noqa: G00
                    f" '{event_type}' event, since it's not specified in the configuration."
                )
                continue

            self.log.info(
                f"Netskope | HOST={self.host} | MESSAGE=Collecting data for '{event_type}' event."  # noqa: G00
            )

            checkpoint = self.dd_client.get_checkpoint(event_type)
            index, from_timestamp = self.parse_checkpoint(event_type, checkpoint)

            event_data = self.client.fetch_events_data(event_type, index, from_timestamp=from_timestamp)
            event_collected = False

            try:
                for events in event_data:
                    event_collected = True
                    self.log.info(
                        f"Netskope | HOST={self.host} | MESSAGE=Fetched {len(events)} events of"  # noqa: G00
                        f" '{event_type}' event."
                    )

                    if not events:
                        continue

                    # Submit billing metrics with events count
                    self.submit_billing_metrics(len(events))

                    for panel_name, panel_conf in event_conf.get("dashboard_panels", {}).items():
                        if panel_conf.get("type") not in ["metric", "log"]:
                            self.log.error(
                                f"Netskope | HOST={self.host} | MESSAGE=Invalid data type provided"  # noqa: G00
                                f" for '{panel_name}' panel, hence skipping data collection of this panel. Allowed"
                                f" data types are metric and log but found: {panel_conf.get('type')}"
                            )
                            continue

                        try:
                            self.ingest_dashboard_data(events, panel_name, panel_conf)
                        except Exception:
                            err_msg = (
                                f"Netskope | HOST={self.host} | MESSAGE=Error occurred while ingesting"  # noqa: G00
                                f" {panel_conf['type']}s data of '{panel_name}' panel, hence skipping"
                                f" {panel_conf['type']}s ingestion of this panel."
                            )
                            self.log.exception(err_msg)
            except BillingSubmitError:
                err_message = "Error occurred while submitting billing logs/metrics, hence stopping the execution..."
                self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
                raise
            except InvalidKeyError:
                self.log.error(
                    f"Netskope | HOST={self.host} | MESSAGE=Datadog API access forbidden error occurred"  # noqa: G00
                    f" while collecting/ingesting data of '{event_type}' event, hence skipping further data"
                    " collection and ingestion for all the events."
                )
                raise
            except Exception:
                self.log.exception(
                    f"Netskope | HOST={self.host} | MESSAGE=Error occurred while collecting/ingesting"  # noqa: G00
                    f" data of '{event_type}' event, hence skipping further data collection and ingestion for"
                    " this event."
                )

            if not event_collected:
                self.log.info(
                    f"Netskope | HOST={self.host} | MESSAGE=No data found of '{event_type}' event,"  # noqa: G00
                    " hence no data will be ingested."
                )
            else:
                self.log.info(
                    f"Netskope | HOST={self.host} | MESSAGE='{event_type}' event data ingestion is"  # noqa: G00
                    " completed."
                )

            self.log.info(
                f"Netskope | HOST={self.host} | MESSAGE=Submitting checkpoint log for '{event_type}'"  # noqa: G00
                " event."
            )
            self.dd_client.save_checkpoint(event_type, {"index": index})

        elapsed_time = time.time() - start_time
        self.log.info(
            f"Netskope | HOST={self.host} | MESSAGE=End of the data collection."  # noqa: G00
            f" Time taken: {elapsed_time:.3f} seconds"
        )

    def ingest_dashboard_data(self, event_data, panel_name, panel_conf):
        """Ingests event data to datadog platform in form of metrics and logs."""
        if panel_conf.get("type") == "metric" and self.ingest_metrics:
            self.log.info(
                f"Netskope | HOST={self.host} | MESSAGE=Ingesting metrics for '{panel_name}' panel."  # noqa: G00
            )
            metrics_list = utils.generate_metrics(
                event_data,
                panel_name,
                panel_conf["event_fields"],
                panel_conf["alias_fields"],
                panel_conf["tag_fields"],
                panel_conf["metric_fields"],
                panel_conf.get("is_count", False),
                panel_conf.get("timestamp_field"),
            )
            metrics_payload = []
            for metric in metrics_list:
                metric_field = metric[0].split(".")[-1]
                tags = (
                    metric[2]
                    + self.instance.get("tags", [])
                    + panel_conf.get("custom_metric_tags", {}).get(metric_field, (None, []))[1]
                    + [f"{constants.HOST_TAG_NAME}:{self.host}"]
                )
                metric_name_prefix = ".".join(metric[0].split(".")[:-1])
                metric_name = ".".join(
                    [
                        metric_name_prefix,
                        panel_conf.get("custom_metric_tags", {}).get(metric_field, [None])[0] or metric_field,
                    ]
                )
                if not utils.is_float(metric[1]):
                    metric[1] = 0
                metrics_payload.append((metric_name, metric[1], tags, metric[3]))
            self.dd_client.submit_metrics(metrics_payload)

        elif panel_conf.get("type") == "log":
            self.log.info(
                f"Netskope | HOST={self.host} | MESSAGE=Ingesting logs for '{panel_name}' panel."  # noqa: G00
            )
            self.dd_client.submit_logs(
                panel_name,
                utils.generate_logs(
                    event_data,
                    panel_conf["event_fields"],
                    panel_conf["alias_fields"],
                    panel_conf.get("conditions"),
                ),
                panel_conf.get("timestamp_field"),
                fn_to_evaluate_event=lambda event: (
                    utils.field_parser(
                        event,
                        panel_conf["log_fields"],  # noqa: B023
                    ),
                    utils.tag_generator(event, panel_conf["tag_fields"]),  # noqa: B023
                ),
            )

    def validate_configurations(self):
        """Validates the configurations provided by the user."""

        # Validating host field
        if not re.match(r"^((?!-)[A-Za-z0-9-\.]*)$", self.host):
            err_message = (
                "'Host' is not valid. Please provide a proper hostname without protocol, "
                "any special characters, and slashes. Permitted characters are (A-Z), (a-z), (0-9), "
                "hyphen(-) and period(.)"
            )
            self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
            raise ConfigTypeError(err_message)

        # Validate events field
        if self.events is None or self.events == []:
            no_events_message = (
                "'events' field is provided but no value is found. No data will be collected for any endpoints."
            )
            self.events = []
            self.log.info(f"Netskope | HOST={self.host} | MESSAGE={no_events_message}")  # noqa: G00

        for event in self.events:
            if event not in constants.DEFAULT_EVENTS:
                err_message = (
                    f"'{event}' value for 'events' field is not valid. "
                    "Permitted values are 'infrastructure', 'network', 'connection', 'audit', 'application', "
                    "and 'incident'."
                )
                self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
                raise ConfigurationError(err_message)

        events_conf_msg = f"The list of configured events is {self.events}."
        self.log.info(f"Netskope | HOST={self.host} | MESSAGE={events_conf_msg}")  # noqa: G00

        # Validate collect_alerts
        if not isinstance(self.collect_alerts, bool):
            err_message = "'collect_alerts' field is not valid. Permitted values are true and false."
            self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
            raise ConfigTypeError(err_message)

        alerts_conf_msg = "Alerts data collection is marked true."
        if not self.collect_alerts:
            alerts_conf_msg = "Alerts data collection is marked false."
        self.log.info(f"Netskope | HOST={self.host} | MESSAGE={alerts_conf_msg}")  # noqa: G00

        # Validate ingest_metrics
        if not isinstance(self.ingest_metrics, bool):
            err_message = "'ingest_metrics' field is not valid. Permitted values are true and false."
            self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
            raise ConfigTypeError(err_message)

        metrics_conf_msg = (
            "Metrics data ingestion is marked true, hence metrics data will be ingested to Datadog platform."
        )
        if not self.ingest_metrics:
            metrics_conf_msg = "Metrics data ingestion is marked false, hence metrics data ingestion will be skipped."
        self.log.info(f"Netskope | HOST={self.host} | MESSAGE={metrics_conf_msg}")  # noqa: G00

        # validate min_collection_interval
        try:
            self.min_collection_interval = int(self.min_collection_interval)
            if self.min_collection_interval <= 0:
                raise ValueError
        except (ValueError, TypeError):
            if self.min_collection_interval is None:
                err_message = "'min_collection_interval' field is missing."
                self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
                raise ConfigurationError(err_message)

            err_message = (
                "'min_collection_interval' must be a positive integer value greater than 0,"
                f" but found {self.min_collection_interval}."
            )
            self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
            raise ConfigValueError(err_message)

    def authentication(self):
        """Validates the Netskope credentials."""
        try:
            event_types = self.events.copy()
            if self.collect_alerts:
                event_types.append("alert")
            forbidden_event_type = self.client.authenticate(event_types, constants.AUTH_INDEX)

            if forbidden_event_type:
                err_message = (
                    f"Insufficient API permission of following event's endpoints: {forbidden_event_type}."
                    " Verify the V2 token and its permission for mentioned events."
                )
                self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
                raise ConfigurationError(err_message)

        except requests.exceptions.SSLError as err:
            err_message = "SSL verification failed."
            self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message} Error: {err}")  # noqa: G00
            raise ConfigurationError(err_message) from err

        except requests.exceptions.ConnectionError as err:
            err_message = "Authentication failed for provided credentials. Please check the provided host."
            self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message} Error: {err}")  # noqa: G00
            raise ConfigurationError(err_message) from err

        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 403:
                err_message = (
                    "Authentication failed for provided credentials."
                    " Please check the provided token and its permissions."
                )
                self.log.error(
                    f"Netskope | HOST={self.host} | STATUS_CODE={err.response.status_code} "  # noqa: G00
                    f"| MESSAGE={err_message} Error: {err}"
                )
                raise ConfigurationError(err_message) from err
            else:
                err_message = (
                    "Error occurred while validating the Netskope credentials. Please check the provided credentials."
                )
                self.log.error(
                    f"Netskope | HOST={self.host} | STATUS_CODE={err.response.status_code} "  # noqa: G00
                    f"| MESSAGE={err_message} Error: {err}"
                )
                raise ConfigurationError(err_message) from err

        except Exception as err:
            err_message = (
                "Error occurred while validating the Netskope credentials. Please check the provided credentials."
            )
            self.log.exception(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00
            raise ConfigurationError(err_message) from err

    def initialize_dd_client(self):
        """Validates API key and initializes datadog API client for submitting logs and metrics through API."""

        if not self._api_key or not self._app_key:
            err_message = "API Key is missing." if not self._api_key else "App Key is missing."
            self.log.error(f"Netskope | HOST={self.host} | MESSAGE={err_message}")  # noqa: G00

            # Using checks and events, show that Datadog API key or app key is missing.
            self.ingest_service_check_and_event(
                status=2,
                tags=constants.API_VAL_TAG,
                message=err_message,
                title=constants.API_VAL_TITLE,
                source_type=constants.API_VAL_SOURCE_TYPE,
            )
            raise ConfigurationError(err_message)

        api_key_auth = {"apiKeyAuth": self._api_key, "appKeyAuth": self._app_key}

        try:
            self.dd_client = DatadogClient(self._site, api_key_auth, self)
            self.dd_client.validate_keys()
        except Exception as ex:
            raise ConfigurationError(ex) from ex

    def initialize_client(self):
        """Initializes Netskope client with v2 API token."""

        self.client = NetskopeClient(self.host, self.v2_api_token, self.log)

    def ingest_service_check_and_event(self, **service_check_event_args):
        """
        Ingest Service Check and Event for any particular milestone with success or error status.
        **service_check_event_args =
            - For check = [<STATUS>, <TAGS>, <MESSAGE>]
            - For Event = [<STATUS>, <TAGS>, <MESSAGE>, <TITLE>, <SOURCE_TYPE>]
        """
        self.service_check(
            constants.NETSKOPE_CHECK_NAME,
            service_check_event_args.get("status"),
            service_check_event_args.get("tags"),
            self.host,
            service_check_event_args.get("message"),
        )
        self.event(
            {
                "host": self.host,
                "alert_type": constants.STATUS_NUMBER_TO_VALUE[service_check_event_args.get("status")],
                "tags": service_check_event_args.get("tags"),
                "msg_text": service_check_event_args.get("message"),
                "msg_title": service_check_event_args.get("title"),
                "source_type_name": service_check_event_args.get("source_type"),
            }
        )

    def get_netskope_index(self, event_name: str) -> str:
        """Generates and returns netskope index with current timestamp as a unique identifier.

        :param event_name: netskope event name
        :type event_name: str

        :return: generated index string
        :rtype: str
        """
        timestamp = int(time.time())
        return ".".join([constants.NETSKOPE_INDEX_PREFIX, event_name, str(timestamp)])

    def submit_billing_metrics(self, count: int) -> None:
        """Submits billing metrics with events count.

        :param count: event count
        :type count: int
        """
        try:
            checkpoint = self.dd_client.get_checkpoint(
                constants.BILLING_CHECKPOINT, search_host=False, raise_error=True
            )
            event_count = 0
            tag_count = 0
            if checkpoint:
                event_count = checkpoint.get("event-count")
                tag_count = checkpoint.get("tag-count")

            event_count += count

            while event_count // constants.BILLING_PER_EVENTS >= tag_count:
                tag_count += 1

                billing_metrics_body = (
                    constants.MARKETPLACE_BILLING_METRIC,
                    event_count,
                    [f"event_tag:{time.time()}", f"event-count:{event_count}", f"tag-count:{tag_count}"],
                )
                self.log.info(
                    f"Netskope | HOST={self.host} | MESSAGE=Submitting marketplace billing metric"  # noqa: G00
                    " with current timestamp."
                )
                self.dd_client.submit_metrics([billing_metrics_body], latest=True, include_prefix=False)

            self.dd_client.save_checkpoint(
                constants.BILLING_CHECKPOINT, {"event-count": event_count, "tag-count": tag_count}
            )
        except Exception as ex:
            raise BillingSubmitError from ex

    def parse_checkpoint(self, event_type: str, checkpoint: dict) -> Tuple[str, bool]:
        """Parses checkpoint data and finds netskope index.

        :param event_type: netskope event type
        :type event_type: str
        :param checkpoint: checkpoint data
        :type checkpoint: dict

        :return: index and from_timestamp flag
        :rtype: (str, bool)
        """
        index = None
        from_timestamp = True

        if not checkpoint:
            self.log.info(
                f"Netskope | HOST={self.host} | MESSAGE=No checkpoint found of '{event_type}' event,"  # noqa: G00
                f" hence data will be collected from default collection time(={constants.TIMESTAMP_OFFSET} seconds)."
            )
        else:
            index = checkpoint.get("index")
            checkpoint_timestamp = utils.get_epoch_timestamp(checkpoint.get("timestamp"))
            if checkpoint_timestamp and int(time.time()) - checkpoint_timestamp > constants.TIMESTAMP_OFFSET:
                self.log.info(
                    f"Netskope | HOST={self.host} | MESSAGE=Found checkpoint for '{event_type}' event,"  # noqa: G00
                    " but checkpoint time is older than default collection time so data will be collected"
                    f" from default collection time(={constants.TIMESTAMP_OFFSET} seconds). Checkpoint: {checkpoint}"
                )
            else:
                from_timestamp = False
                self.log.info(
                    f"Netskope | HOST={self.host} | MESSAGE=Found checkpoint for '{event_type}' event,"  # noqa: G00
                    f" hence collecting the data from last checkpoint. Checkpoint: {checkpoint}"
                )

        index = self.get_netskope_index(event_type) if not index else index

        return index, from_timestamp
