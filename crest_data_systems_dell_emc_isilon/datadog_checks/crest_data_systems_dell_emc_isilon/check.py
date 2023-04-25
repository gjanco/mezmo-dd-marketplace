"""Module for EMC Isilon Integration."""
import importlib
import re

from requests.exceptions import ConnectionError

try:
    from datadog_checks.base import AgentCheck
except ImportError:
    from checks import AgentCheck

from .cds_dell_emc_consts import APIS, INTEGRATION_PREFIX, V9_EXCLUSIVE_API


class CrestDataSystemsDellEmcIsilonCheck(AgentCheck):
    """Class for Dell EMC Isilon Check."""

    def __init__(self, name, init_config, instances):
        """Initialize DellEmcIsilonCheck class."""
        super(CrestDataSystemsDellEmcIsilonCheck, self).__init__(name, init_config, instances)
        self.is_authenticated = False
        self.cluster_name = ""
        self.count = 0
        self.ip_address = None
        self.port = None
        self.base_uri = None

    def check(self, instance):
        """Get the list of APIs to hit."""
        api_list = self.get_api_list()

        self.count += 1
        if self.count > 30:
            self.count = 1
        if not self.is_authenticated or self.count % 7 == 0:
            self.authentication()

        if self.is_authenticated:
            self.get_session_cookie()
            self.set_cluster_name()
            self.gauge(
                "datadog.marketplace.crest_data_systems.dell_emc_isilon",
                1.0,
                tags=self.instance.get("tags", []),
            )
            self.ingest_data_for_dashboards(api_list)

    def get_major_version(self, release_version):
        match = re.findall(r"\d+", release_version)
        if match:
            self.major_version = int(match[0])
            self.log.info(f"Major version of Dell EMC Isilon is '{self.major_version}'.")  # noqa: G004
        else:
            self.major_version = 9
            self.log.info("No major version found of Dell EMC Isilon.")

    def set_cluster_name(self):
        """To set the cluster name."""
        url = self.base_uri + "/platform/1/cluster/config"
        try:
            response_json = self._make_request(url)
            self.get_major_version(response_json.get("onefs_version")["release"])

            if "tags" in self.instance and isinstance(self.instance["tags"], list):
                tag_set = set(self.instance["tags"])
                cluster_tag = INTEGRATION_PREFIX + "cluster:%s" % self.cluster_name
                tag_set.discard(cluster_tag)
                self.instance["tags"] = list(tag_set)
            else:
                self.instance["tags"] = []

            self.cluster_name = response_json.get("name", self.cluster_name)
            cluster_tag = INTEGRATION_PREFIX + "cluster:%s" % self.cluster_name
            self.instance["tags"].append(cluster_tag)

            self.log.info("Cluster info is set successfully")
        except ConnectionError as exception:
            self.log.error("Connection Error")
            self.log.exception(exception)
            raise exception
        except Exception as exception:
            self.log.error("Error while setting Cluster Info")
            self.log.exception(exception)
            raise exception

    def ingest_data_for_dashboards(self, api_list):
        """Ingest data for Dashboard by calling API respectively."""
        for api in api_list:
            if self.major_version < 9 and api.get("api_url") in V9_EXCLUSIVE_API:
                self.log.info(
                    "Found dell EMC Isilon version less than 9. "  # noqa: G001*
                    "Skipping '{}' endpoint as ".format(api.get("api_url"))
                )
            url = self.base_uri + api.get("api_url", "")
            response_json = None
            try:
                response_json = self._make_request(url)
            except Exception as exception:
                self.log.exception(exception)
                continue

            if response_json is None:
                self.log.error("Request Failed of url : %s", url)
                continue

            if api.get("helper_module") == "cds_dell_emc_none_helper":
                continue

            try:
                helper_module = "datadog_checks.crest_data_systems_dell_emc_isilon." + api.get("helper_module")
                cds_dell_emc_helper_module = importlib.import_module(helper_module)
            except Exception:
                helper_module = api.get("helper_module")
                cds_dell_emc_helper_module = __import__(name=helper_module)

            helper_class = api.get("helper_class")
            cds_dell_emc_helper_class_ = getattr(cds_dell_emc_helper_module, helper_class)
            for panel in api.get("dashboard_panels", []):
                panel_to_call = getattr(cds_dell_emc_helper_class_(), panel)
                if panel_to_call is not None:
                    try:
                        metrics_list = panel_to_call(response_json)
                        for metric in metrics_list:
                            tags = metric[2] + self.instance.get("tags", [])
                            self.gauge(metric[0], metric[1], tags=tags)
                    except Exception as exception:
                        error = "Error occurred while ingesting the data of {} panel.".format(panel)
                        self.log.error(error)
                        self.log.exception(exception)
                        continue

                    self.log.info("Data for %s panel is ingested successfully.", panel)

    def get_header(self):
        csrf = self.cookie.get("isicsrf")
        sessid = self.cookie.get("isisessid")
        headers = {
            "X-CSRF-Token": str(csrf),
            "Cookie": "isisessid=" + str(sessid),
            "Referer": str(self.base_uri),
        }
        return headers

    def get_session_cookie(self):
        url = "https://%s:%s/session/1/session" % (self.ip_address, self.port)
        payload = {
            "username": self.username,
            "password": self.password,
            "services": ["platform", "namespace"],
        }
        response = None
        try:
            response = self.http.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                verify=self.instance.get("certificate_path", False),
            )
            if response.status_code == 201 and response.cookies:
                self.cookie = dict(response.cookies)
            else:
                self.cookie = None
                self.node_dict = None
        except Exception as ex:
            self.log.exception(ex)

    def authentication(self):
        """Method to do Authentication."""
        self.is_authenticated = False

        auth_check_name = INTEGRATION_PREFIX + "can_connect"
        event_source_type = INTEGRATION_PREFIX + "auth"

        if not (
            "ip_address" in self.instance
            and "username" in self.instance
            and "password" in self.instance
            and "port" in self.instance
        ):
            self.service_check(auth_check_name, 2, message="Authentication failed")
            self.event(
                {
                    "source_type_name": event_source_type,
                    "msg_title": "Authentication",
                    "msg_text": "Authentication failed. Reason: Missing data in configuration file",
                }
            )
            self.log.error("Could not connect to EMC Server as configurations are missing in configuration file.")
            raise Exception("Could not connect to EMC Server as configurations are missing in configuration file.")

        ip_address = self.instance.get("ip_address")
        username = self.instance.get("username")
        password = self.instance.get("password")
        port = self.instance.get("port")
        verify_certificate = self.instance.get("certificate_path", False)

        if isinstance(verify_certificate, str) and len(verify_certificate.strip()) == 0:
            verify_certificate = False

        if ip_address is None or username is None or password is None or port is None:
            self.service_check(auth_check_name, 2, message="Authentication failed")
            self.event(
                {
                    "source_type_name": event_source_type,
                    "msg_title": "Authentication",
                    "msg_text": "Authentication failed. Reason: Missing data in configuration file",
                }
            )
            self.log.error("Could not connect to EMC Server as configurations are missing in configuration file.")
            raise Exception("Could not connect to EMC Server as configurations are missing in configuration file.")

        url = "https://%s:%s/session/1/session" % (ip_address, port)
        payload = {
            "username": username,
            "password": password,
            "services": ["platform", "namespace"],
        }
        response = None
        try:
            response = self.http.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                verify=verify_certificate,
            )
            if not response:
                response.raise_for_status()
        except ConnectionError as exception:
            self.service_check(auth_check_name, 2, message="Authentication failed")
            self.event(
                {
                    "source_type_name": event_source_type,
                    "msg_title": "Authentication",
                    "msg_text": "Authentication failed. Could not made request reason: {}".format(str(exception)),
                }
            )
            self.log.error("Connection Error")
            self.log.exception(exception)
            raise exception
        except Exception as exception:
            self.service_check(auth_check_name, 2, message="Authentication failed")
            self.event(
                {
                    "source_type_name": event_source_type,
                    "msg_title": "Authentication",
                    "msg_text": "Authentication failed. Could not made request reason: {}".format(str(exception)),
                }
            )
            self.log.exception(exception)
            raise exception

        if response is None:
            self.service_check(auth_check_name, 2, message="Authentication failed")
            self.event(
                {
                    "source_type_name": event_source_type,
                    "msg_title": "Authentication",
                    "msg_text": "Authentication failed. Reason: Could not connect to EMC Server",
                }
            )
            self.log.error("Could not connect to EMC Server.")
            raise Exception("Could not connect to EMC Server.")

        self.service_check(auth_check_name, 0, message="Authentication successful")
        self.event(
            {
                "source_type_name": event_source_type,
                "msg_title": "Authentication",
                "msg_text": "Authentication successful",
            }
        )
        self.log.info("Authentication successful with host '%s' and port '%s'", ip_address, port)
        self.is_authenticated = True
        self.ip_address = ip_address
        self.port = port
        self.base_uri = "https://%s:%s" % (ip_address, port)
        self.username = username
        self.password = password
        return

    def _make_request(self, url):
        """Make REST Calls."""
        verify_certificate = self.instance.get("certificate_path", False)

        if isinstance(verify_certificate, str) and len(verify_certificate.strip()) == 0:
            verify_certificate = False

        response = self.http.get(url, headers=self.get_header(), verify=verify_certificate)
        if response is None:
            raise Exception("Could not make request to API. url: {}".format(url))

        if response.status_code == 401:
            self.cookie = {}
            self.authentication()
            self.get_session_cookie()
            if self.is_authenticated and self.cookie:
                response = self.http.get(url, verify=verify_certificate)
                if response is None:
                    raise Exception("Could not make request to API. url: {}".format(url))

        response_json = response.json()
        error_json = response_json.get("errors", [])
        if error_json:
            error_list = []
            for error in error_json:
                status_code = error.get("code", "UNKNOWN_CODE")
                message = error.get("message", "Unknown Error")
                error_list.append("status : %s, message : %s" % (status_code, message))
            raise Exception("Could not make request to API. url: %s reason: %s" % (url, ",".join(error_list)))
        else:
            response.raise_for_status()
        return response.json()

    def get_api_list(self):
        """Returns the APIs which need to be called in this interval."""
        api_list = []
        for api_detail in APIS:
            if self.count == 0 or self.count % api_detail.get("interval_offset", 1) == 0:
                api_list.extend(api_detail.get("api_list", []))
        return api_list
