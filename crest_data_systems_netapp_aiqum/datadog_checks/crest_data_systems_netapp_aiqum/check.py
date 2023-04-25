# (C) Datadog, Inc. 2022-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import ssl
import time
import urllib.parse as urlparse
from datetime import datetime, timedelta

import datadog_agent

try:
    # first, try to import the base class from new versions of the Agent...
    from datadog_checks.base import AgentCheck, ConfigurationError
except ImportError:
    # ...if the above failed, the check is running in Agent version < 6.6.0
    from checks import AgentCheck, ConfigurationError

from . import cds_netapp_aiqum_utils as Utils
from .cds_netapp_aiqum_api_client import AIQUMAPIClient
from .cds_netapp_aiqum_constants import LOGS_INTERVAL
from .cds_netapp_aiqum_endpoints import api_list
from .cds_netapp_aiqum_errors import InvalidAPICredentialsError, SSLError


class CrestDataSystemsNetappAiqumCheck(AgentCheck):
    def __init__(self, *args, **kwargs):
        super(CrestDataSystemsNetappAiqumCheck, self).__init__(*args, **kwargs)
        self.configuration = {}
        self.log_index = "main"

        self.elapsed_time = 0
        self.execution_count = 0
        self.ingest_log = True

    def check(self, instance):
        # data collection started
        start_time = time.time()

        self.initialize_client()
        self.set_configurations()
        self.authentication()

        if self.execution_count != 0:
            self.elapsed_time += self.instance.get("min_collection_interval", 0)
        # set log ingestion flag
        if self.elapsed_time // LOGS_INTERVAL >= self.execution_count:
            self.ingest_log = True
            self.execution_count += 1
        else:
            self.ingest_log = False

        # ingest marketplace metric for total count of instance running
        self.gauge(
            "datadog.marketplace.crest_data_systems.netapp_aiqum",
            1.0,
            tags=self.instance.get("tags", []) + [f"cds_netapp_aiqum_instance:{self.host}"],
            hostname=self.host,
        )

        # data ingestion logic
        self.ingest_data_for_dashboards()

        # data collection ended
        elapsed_seconds = time.time() - start_time
        self.log.info(
            "NETAPP AIQUM INFO: End of the data collection."  # noqa: G001
            " Total time taken: {elapsed:.3f} seconds".format(elapsed=elapsed_seconds),
        )

    def ingest_data_for_dashboards(self):
        for api in api_list:
            url = self.client.build_url(api.get("url"))
            try:
                response = self.client.get(url)
            except Exception as ex:
                self.log.exception(ex)

            if response is None:
                self.log.error("NETAPP AIQUM ERROR: Request Failed of url: {url}".format(url=url))  # noqa: G001
                continue

            for panel_name, panel_data in api.get("dashboard_panels", {}).items():
                if panel_data.get("type") == "metric":
                    try:
                        metrics_list = Utils.generate_metrics(
                            response,
                            panel_name,
                            panel_data["event_fields"],
                            panel_data["alias_fields"],
                            panel_data["tag_fields"],
                            panel_data["metric_fields"],
                            panel_data.get("distinct_count"),
                        )
                        for metric in metrics_list:
                            metric_field = metric[0].split(".")[-1]
                            tags = (
                                metric[2]
                                + self.instance.get("tags", [])
                                + panel_data.get("custom_metric_tags", {}).get(metric_field, (None, []))[1]
                                + [f"cds_netapp_aiqum_instance:{self.host}"]
                            )
                            metric_name_prefix = ".".join(metric[0].split(".")[:-1])
                            metric_name = ".".join(
                                [
                                    metric_name_prefix,
                                    panel_data.get("custom_metric_tags", {}).get(metric_field, [None])[0]
                                    or metric_field,
                                ]
                            )
                            if not Utils.is_float(metric[1]):
                                metric[1] = 0
                            self.gauge(metric_name, metric[1], tags=tags, hostname=self.host)
                    except Exception as exception:
                        error = "NETAPP AIQUM ERROR: Error occurred while ingesting the data of '{}' panel.".format(
                            panel_name
                        )
                        self.log.error(error)
                        self.log.exception(exception)
                        continue

                elif panel_data.get("type") == "log":
                    Utils.ingest_logs(
                        self,
                        panel_name,
                        Utils.generate_logs(
                            response,
                            panel_data["event_fields"],
                            panel_data["alias_fields"],
                            panel_data.get("conditions"),
                        ),
                        fn_to_evaluate_event=lambda event: (
                            Utils.field_parser(
                                event,
                                panel_data["log_fields"],  # noqa: B023
                            ),
                            Utils.tag_generator(event, panel_data["tag_fields"]),  # noqa: B023
                        ),
                    )

                else:
                    self.log.error(
                        "NETAPP AIQUM ERROR: No valid data type found for '{panel_name}' panel.".format(  # noqa: G001
                            panel_name=panel_name
                        ),
                    )
                    continue

                self.log.info(
                    "NETAPP AIQUM INFO: Data for '{panel_name}' panel is ingested successfully.".format(  # noqa: G001
                        panel_name=panel_name
                    ),
                )

    def set_configurations(self):
        """Set configurations for ingesting logs."""

        api_key = datadog_agent.get_config("api_key")
        app_key = datadog_agent.get_config("app_key")
        log_index = self.instance.get("log_index")

        if not api_key or not app_key:
            err_message = "App Key or API Key is missing."
            self.log.error("NETAPP AIQUM ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)

        self.configuration = {"appKeyAuth": app_key, "apiKeyAuth": api_key}
        self.log_index = log_index if log_index else "main"
        try:
            now = datetime.utcnow()
            past_1_hour = now - timedelta(hours=1)
            now_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            past_1_hour_str = past_1_hour.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            param = {"from": past_1_hour_str, "to": now_str}
            Utils.search_log_in_datadog(self, self.log_index, **param)
        except Exception as e:
            self.log.error(
                "NETAPP AIQUM ERROR: Could not connect to Datadog, App Key or API Key or Log Index is invalid."
            )
            self.log.exception(e)
            raise e

    def initialize_client(self):
        """Initialize AIQUM client."""

        # set hostname, scheme and port
        host = self.instance.get("host")
        if not host:
            err_message = "Host is missing."
            self.log.error("NETAPP AIQUM ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)

        try:
            parsed_url = urlparse.urlsplit(host)
        except Exception as err:
            self.log.error(
                "NETAPP AIQUM ERROR: Error occurred while parsing host={host}."  # noqa: G001
                " Verify the provided host in configuration file.".format(host=host),
            )
            self.log.exception(err)
            raise err

        if not parsed_url.scheme:
            err_message = f"Host scheme (http or https) is missing in host={host}."
            self.log.error("NETAPP AIQUM ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)
        if not parsed_url.hostname:
            err_message = f"Hostname is missing in host={host}."
            self.log.error("NETAPP AIQUM ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)

        self.host = parsed_url.hostname
        self.log.info("NETAPP AIQUM INFO: Initializing server {host}".format(host=self.host))  # noqa: G001

        # validate min_collection_interval
        min_collection_interval = self.instance.get("min_collection_interval")
        try:
            min_collection_interval = int(min_collection_interval)
            if min_collection_interval <= 0:
                raise ValueError
        except (ValueError, TypeError):
            if min_collection_interval is None:
                err_message = "'min_collection_interval' field is missing."
                self.log.error("NETAPP AIQUM ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
                raise ConfigurationError(err_message)

            err_message = (
                "'min_collection_interval' must be a positive integer value greater than 0,"
                f" but found {min_collection_interval}."
            )
            self.log.error("NETAPP AIQUM ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)

        # set username and password
        transport = parsed_url.scheme.upper()
        username = self.instance.get("username")
        password = self.instance.get("password")

        if not username or not password:
            err_message = "Username or Password is missing."
            self.log.error("NETAPP AIQUM ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)

        port = 80
        if parsed_url.port:
            port = parsed_url.port
        # if transport is HTTPS, change default port 80 to 443
        elif transport == "HTTPS":
            port = 443

        # set ssl verification and ca certificates
        verify_ssl = self.instance.get("verify_ssl")
        ca_cert_file = self.instance.get("ca_cert_file")

        # verify CA certificates file path and it's contents
        if Utils.is_true(verify_ssl) and ca_cert_file:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.load_verify_locations(ca_cert_file)

                self.log.info("NETAPP AIQUM INFO: CA certificates loaded successfully.")
            except FileNotFoundError as err:
                err_msg = (
                    "Failed to load CA certificates because provided file path does not exist."
                    " Provide absolute path to the CA certificates file."
                )
                self.log.error("NETAPP AIQUM ERROR: {err_msg}".format(err_msg=err_msg))  # noqa: G001
                self.log.exception(err)
                raise err
            except PermissionError as err:
                err_msg = "Cannot read CA certificates file due to insufficient permission."
                self.log.error("NETAPP AIQUM ERROR: {err_msg}".format(err_msg=err_msg))  # noqa: G001
                self.log.exception(err)
                raise err
            except ssl.SSLError as err:
                err_msg = (
                    "Failed to load CA certificates because provided certificates file might"
                    " not contain valid certificates."
                )
                self.log.error("NETAPP AIQUM ERROR: {err_msg}".format(err_msg=err_msg))  # noqa: G001
                self.log.exception(err)
                raise err
            except Exception as err:
                err_msg = "Error occurred while loading CA certificates. Verify ca_cert_file path and its content."
                self.log.error("NETAPP AIQUM ERROR: {err_msg}".format(err_msg=err_msg))  # noqa: G001
                self.log.exception(err)
                raise err

        else:
            self.log.info("NETAPP AIQUM INFO: No custom CA certificates found.")

        # initialize the on-tap client
        try:
            self.client = AIQUMAPIClient(f"{transport}://{self.host}:{port}", username, password, self.log)
            if Utils.is_true(verify_ssl):
                if transport == "HTTP":
                    self.log.info("NETAPP AIQUM INFO: SSL certificate verification is disabled due to HTTP connection.")
                elif ca_cert_file:
                    self.client.set_server_cert_verification(ca_cert_file)
                    self.log.info(
                        "NETAPP AIQUM INFO: SSL certificate verification is enabled with provided CA certificates."
                    )
                else:
                    self.client.set_server_cert_verification(True)
                    self.log.info("NETAPP AIQUM INFO: SSL certificate verification is enabled.")
            else:
                self.log.info("NETAPP AIQUM INFO: SSL certificate verification is disabled.")

        except Exception as err:
            self.log.error("NETAPP AIQUM ERROR: Error occurred while initializing client.")
            self.log.exception(err)
            raise err

    def authentication(self):
        try:
            username = self.instance.get("username")
            password = self.instance.get("password")

            url = self.client.build_url("login")
            self.client.post(url, data={"username": username, "password": password})

            self.log.info("NETAPP AIQUM INFO: Authentication successful.")

        except SSLError as err:
            self.log.error("NETAPP AIQUM ERROR: SSL verification failed.")
            self.log.exception(err)
            Utils.ingest_service_check_and_event_for_auth(
                self,
                is_authenticated=False,
                reason="Authentication failed due to failure of SSL verification.",
            )
            raise err

        except InvalidAPICredentialsError as err:
            self.log.error(
                "NETAPP AIQUM ERROR: Authentication failed for provided credentials."
                " Verify username and password from conf file."
            )
            self.log.exception(err)
            Utils.ingest_service_check_and_event_for_auth(
                self,
                is_authenticated=False,
                reason="Authentication failed due to invalid credentials (username and/or password).",
            )
            raise err

        except Exception as err:
            self.log.error("NETAPP AIQUM ERROR: Error occurred while authenticating credentials.")
            self.log.exception(err)
            Utils.ingest_service_check_and_event_for_auth(
                self,
                is_authenticated=False,
                reason=f"Error occurred while validating NetApp AIQUM credentials. Error: {err}",
            )
            raise err
