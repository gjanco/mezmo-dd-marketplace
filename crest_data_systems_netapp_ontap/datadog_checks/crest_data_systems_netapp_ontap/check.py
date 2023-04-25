# (C) Datadog, Inc. 2022
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

from .cds_netapp_ontap_aggr import AggrIngestor
from .cds_netapp_ontap_aggr_perf import AggrPerfIngestor
from .cds_netapp_ontap_cluster import ClusterIngestor
from .cds_netapp_ontap_constants import LOGS_INTERVAL
from .cds_netapp_ontap_disk import DiskIngestor
from .cds_netapp_ontap_disk_perf import DiskPerfIngestor
from .cds_netapp_ontap_lun import LunIngestor
from .cds_netapp_ontap_lun_perf import LunPerfIngestor
from .cds_netapp_ontap_qtree import QTreeIngestor
from .cds_netapp_ontap_system_node import SystemNodeIngestor
from .cds_netapp_ontap_system_perf import SystemPerfIngestor
from .cds_netapp_ontap_utils import ingest_service_check_and_event_for_auth, is_true, search_log_in_datadog
from .cds_netapp_ontap_volume import VolumeIngestor
from .cds_netapp_ontap_volume_perf import VolumePerfIngestor
from .cds_netapp_ontap_vserver import VServerIngestor
from .OntapClient import AuthenticationError, OntapClient, SSLError


class CrestDataSystemsNetappOntapCheck(AgentCheck):
    def __init__(self, *args, **kwargs):
        super(CrestDataSystemsNetappOntapCheck, self).__init__(*args, **kwargs)
        self.configuration = {}
        self.log_index = "main"

        self.elapsed_time = 0
        self.execution_count = 0
        self.ingest_log = True

    def check(self, instance):
        # data collection started
        start_time = time.time()

        self.cur_date_time = datetime.utcnow()
        self.cur_date_time_str = self.cur_date_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        self.initialize_client()
        self.authentication()
        self.set_configurations()

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
            "datadog.marketplace.crest_data_systems.netapp_ontap",
            1.0,
            tags=self.instance.get("tags", []) + [f"cds_netapp_ontap_instance:{self.host}"],
            hostname=self.host,
        )

        lun_obj = LunIngestor(self)
        lun_obj.ingestor()

        lun_perf_obj = LunPerfIngestor(self)
        lun_perf_obj.ingestor()

        disk_obj = DiskIngestor(self)
        disk_obj.ingestor()

        disk_perf_obj = DiskPerfIngestor(self)
        disk_perf_obj.ingestor()

        vol_obj = VolumeIngestor(self)
        vol_obj.ingestor()

        vol_perf_obj = VolumePerfIngestor(self)
        vol_perf_obj.ingestor()

        aggr_obj = AggrIngestor(self)
        aggr_obj.ingestor()

        aggr_perf_obj = AggrPerfIngestor(self)
        aggr_perf_obj.ingestor()

        sys_obj = SystemPerfIngestor(self)
        sys_obj.ingestor()

        cluster_obj = ClusterIngestor(self)
        cluster_obj.ingestor()

        vserver_obj = VServerIngestor(self)
        vserver_obj.ingestor()

        q_tree_obj = QTreeIngestor(self)
        q_tree_obj.ingestor()

        sys_node_obj = SystemNodeIngestor(self)
        sys_node_obj.ingestor()

        # data collection ended
        elapsed_seconds = time.time() - start_time
        self.log.info(
            "NETAPP ONTAP INFO: End of the data collection. "  # noqa: G001
            "Total time taken: {elapsed:.3f} seconds".format(elapsed=elapsed_seconds),
        )

    def set_configurations(self):
        """Set configurations for ingesting logs."""

        api_key = datadog_agent.get_config("api_key")
        app_key = datadog_agent.get_config("app_key")
        log_index = self.instance.get("log_index")

        if not api_key or not app_key:
            err_message = "App Key or API Key is missing"
            self.log.error("NETAPP ONTAP ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)

        self.configuration = {"appKeyAuth": app_key, "apiKeyAuth": api_key}
        self.log_index = log_index if log_index else "main"
        try:
            now = datetime.utcnow()
            past_1_hour = now - timedelta(hours=1)
            now_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            past_1_hour_str = past_1_hour.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            param = {"from": past_1_hour_str, "to": now_str}
            search_log_in_datadog(self, self.log_index, **param)
        except Exception as err:
            self.log.error(
                "NETAPP ONTAP ERROR: Could not connect to Datadog, App Key or API Key or Log Index is invalid"
            )
            self.log.exception(err)
            raise err

    def initialize_client(self):
        """Initialize OnTap client."""

        # set hostname, scheme and port
        host = self.instance.get("host")
        if not host:
            err_message = "Host is missing"
            self.log.error("NETAPP ONTAP ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)

        try:
            parsed_url = urlparse.urlsplit(host)
        except Exception as err:
            self.log.error(
                "NETAPP ONTAP ERROR: Error occurred while parsing host={host}."  # noqa: G001
                " Verify the provided host in configuration file.".format(host=host),
            )
            self.log.exception(err)
            raise err

        if not parsed_url.scheme:
            err_message = f"Host scheme (http or https) is missing in host configuration. Host={host}"
            self.log.error("NETAPP ONTAP ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)
        if not parsed_url.hostname:
            err_message = f"Hostname is missing. Host={host}"
            self.log.error("NETAPP ONTAP ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)

        self.host = parsed_url.hostname
        self.log.info("NETAPP ONTAP INFO: Initializing server {host}".format(host=host))  # noqa: G001

        # validate min_collection_interval
        min_collection_interval = self.instance.get("min_collection_interval")
        try:
            min_collection_interval = int(min_collection_interval)
            if min_collection_interval <= 0:
                raise ValueError
        except ValueError:
            err_message = (
                "'min_collection_interval' must be a positive integer value greater than 0,"
                f" but found {min_collection_interval}"
            )
            self.log.error("NETAPP ONTAP ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)

        # set username and password
        transport = parsed_url.scheme.upper()
        username = self.instance.get("username")
        password = self.instance.get("password")

        if not username or not password:
            err_message = "Username or Password is missing"
            self.log.error("NETAPP ONTAP ERROR: {err_message}".format(err_message=err_message))  # noqa: G001
            raise ConfigurationError(err_message)

        kwargs = {"transport": transport, "port": 80}
        if parsed_url.port:
            kwargs["port"] = parsed_url.port
        # if transport is HTTPS, change default port 80 to 443
        elif transport == "HTTPS":
            kwargs["port"] = 443

        # set ssl verification and ca certificates
        verify_ssl = self.instance.get("verify_ssl")
        ca_cert_file = self.instance.get("ca_cert_file")

        # verify CA certificates file path and its contents
        if is_true(verify_ssl) and ca_cert_file:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.load_verify_locations(ca_cert_file)

                self.log.info("NETAPP ONTAP INFO: CA certificates loaded successfully.")
            except FileNotFoundError as err:
                err_msg = (
                    "Failed to load CA certificates because provided file path does not exist."
                    " Provide absolute path to the CA certificates file."
                )
                self.log.error("NETAPP ONTAP ERROR: {err_msg}".format(err_msg=err_msg))  # noqa: G001
                self.log.exception(err)
                raise err
            except PermissionError as err:
                err_msg = "Cannot read CA certificates file due to insufficient permission."
                self.log.error("NETAPP ONTAP ERROR: {err_msg}".format(err_msg=err_msg))  # noqa: G001
                self.log.exception(err)
                raise err
            except ssl.SSLError as err:
                err_msg = (
                    "Failed to load CA certificates because provided certificates file might not"
                    " contain valid certificates."
                )
                self.log.error("NETAPP ONTAP ERROR: {err_msg}".format(err_msg=err_msg))  # noqa: G001
                self.log.exception(err)
                raise err
            except Exception as err:
                err_msg = "Error occurred while loading CA certificates. Verify ca_cert_file path and its content."
                self.log.error("NETAPP ONTAP ERROR: {err_msg}".format(err_msg=err_msg))  # noqa: G001
                self.log.exception(err)
                raise err

        else:
            self.log.info("NETAPP ONTAP INFO: No custom CA certificates found.")

        # initialize the on-tap client
        try:
            self.client = OntapClient(self.host, username, password, self.log, **kwargs)
            if is_true(verify_ssl):
                if transport == "HTTP":
                    self.log.info("NETAPP ONTAP INFO: SSL certificate verification is disabled due to HTTP connection.")
                else:
                    self.client.connection.set_server_cert_verification(True)
                    self.log.info("NETAPP ONTAP INFO: SSL certificate verification is enabled.")
            else:
                self.log.info("NETAPP ONTAP INFO: SSL certificate verification is disabled.")

            if ca_cert_file:
                self.client.connection.set_ca_certs(ca_cert_file)

        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while initializing client.")
            self.log.exception(err)
            raise err

    def authentication(self):
        try:
            self.client.queryApi("system-get-version")
        except SSLError as err:
            self.log.error("NETAPP ONTAP ERROR: SSL verification failed.")
            self.log.exception(err)
            ingest_service_check_and_event_for_auth(
                self,
                is_authenticated=False,
                reason="Authentication failed due to failure of SSL verification.",
            )
            raise err
        except AuthenticationError as err:
            self.log.error(
                "NETAPP ONTAP ERROR: Authentication failed for provided credentials."
                " Verify username and password from conf file."
            )
            self.log.exception(err)
            ingest_service_check_and_event_for_auth(
                self,
                is_authenticated=False,
                reason="Authentication failed due to invalid credentials (username and/or password).",
            )
            raise err
        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while authenticating credentials.")
            self.log.exception(err)
            ingest_service_check_and_event_for_auth(
                self,
                is_authenticated=False,
                reason=f"Error occurred while validating NetApp OnTap credentials. Error: {err}",
            )
            raise err
