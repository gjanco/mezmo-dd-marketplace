try:
    from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
except ImportError:
    from checks import AgentCheck
import re
import requests
from .helpers import *
from requests.auth import HTTPBasicAuth
from sys import platform

REQUIRED_SETTINGS = [
    "base_api_url",
    "client_id",
    "client_secret"
]

REQUIRED_TAGS = [
    "vendor:rapdev",
]

ENDPOINTS = [
    "/common/v1/alerts",
    "/endpoint/v1/endpoints",
    "/siem/v1/alerts",
    "/siem/v1/events"
]

DD_SOURCE = "?ddsource=sophos"

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class SophosCheck(AgentCheck):

    __NAMESPACE__ = "rapdev.sophos"

    def __init__(self, *args, **kwargs):
        super(SophosCheck, self).__init__(*args, **kwargs)
        self.base_api_url = self.instance.get("base_api_url")
        self.client_id = self.instance.get("client_id")
        self.client_secret = self.instance.get("client_secret")
        self.log_url = self.instance.get("log_url")
        self.endpoint_types_monitored = self.instance.get("endpoint_types_to_monitor", [])
        self.endpoint_types_to_log = self.instance.get("endpoint_types_to_log", [])
        self.alert_logs_enabled = is_affirmative(self.instance.get("collect_alert_logs", False))
        self.siem_alerts_enabled = is_affirmative(self.instance.get("collect_siem_alerts", False))
        self.siem_events_enabled = is_affirmative(self.instance.get("collect_siem_events", False))
        self.interval = self.instance.get("min_collection_interval", 15)
        self.oauth_token_data = "grant_type=client_credentials&client_id={}&client_secret={}&scope=token".format(self.client_id, self.client_secret)
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.__NAMESPACE__)
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.api_key = self.get_config("api_key")

        dd_host = get_host_name()
        if dd_host:
            self.DD_HOST = "&hostname={}".format(dd_host)
        else:
            self.DD_HOST = "&hostname=not_available"
        
        self.check_initializations.append(self.validate_config)    

    def get_config(self, key, passthrough_exceptions=False):
        """
        function to read in the value for a specific key from the main datadog.yaml config file
        
        args:
            key (str): target key to read the value of
            passthrough_exceptions (bool): default False, flag to allow exceptions to bubble up normally instead
                                            of raising a custom exception (used because set_proxy code expects
                                            a KeyError to bubble up)
                                            
        returns:
            (multiple types): returns the parsed out value from the target key. since it's yaml, technically
                                can return str, int, list, or dict depending on the target data. here we're only
                                using it for strings though
                                
        raises:
            (Exception): custom exception is raised if the os platform is not supported, as well as for
                            all other exceptions if passthrough_exceptions is set to False
            (FileNotFoundError): raises this exeption if passthrough_exceptions is True and the datadog.yaml file
                                    can not be found
            (KeyError): raises this exception if passthrough_exceptions is True and the key specified is not present
                        (or commented out) in the main datadog.yaml
        """
        config_file_name = "datadog.yaml"
        # Windows
        if platform == "win32":
            path = os.path.join(os.getenv("PROGRAMDATA"), "Datadog")
        # Linux
        elif platform == "linux" or platform == "linux2":
            path = "/etc/datadog-agent/"
        # Mac
        elif platform == "darwin":
            path = "/opt/datadog-agent/etc/"
        # Unsupported
        else:
            raise Exception("OS Platform {} not supported.".format(platform))

        target = os.path.join(path, config_file_name)
        try:
            with open(target, "r") as infile:
                parsed_yaml = yaml.load(infile.read(), Loader=yaml.FullLoader)

            return parsed_yaml[key]

        # catching all exeptions and then filtering on type instead of catching each exception
        # separately to reduce copied code
        except Exception as e:
            exception_text = "Unexpected exception when retrieving {} from {}: {}".format(key, target, traceback.format_exc())

            if type(e) is FileNotFoundError:
                exception_text = "No configuration file {} found. Please try again with a valid configuration file.".format(target)
            elif type(e) is KeyError:
                exception_text = "{} not found in {}. Please make sure the target key is defined properly and uncommented.".format(key, target)

            if passthrough_exceptions:
                raise e
            else:
                raise Exception(exception_text)

    def check(self, instance):
        self.oauth_token = self.generate_token()
        self.api_data = self.get_api_data()
        self.tags = list(set(self.tags))
        self.tags.append("id_type:{}".format(self.api_data["idType"]))
        if "dataRegion" in self.api_data["apiHosts"].keys():
            self.org_api_url = self.api_data["apiHosts"]["dataRegion"]
            self.tags.append("api_url:{}".format(self.org_api_url))
        else:
            self.org_api_url = self.api_data["apiHosts"]["global"]
            self.tags.append("api_url:{}".format(self.org_api_url))
        self.tenant_id = self.api_data["id"]
        self.api_header = {
            "X-Tenant-ID": self.tenant_id
        }
        self.tags.append("tenant_id:{}".format(self.tenant_id))
        self.test_api_connection()
        if self.alert_logs_enabled:
            self.get_alerts()
        if self.siem_alerts_enabled:
            self.get_siem_alerts()
        if self.siem_events_enabled:
            self.get_siem_events()
        self.get_endpoints()
        
    def validate_config(self):
        if not self.base_api_url:
            raise ConfigurationError("The Sophos API URL is required.")
        if not self.client_id:
            raise ConfigurationError("Your Sophos Client ID is required.")
        if not self.client_secret:
            raise ConfigurationError("Your Sophos Client Secret is required.")
    
    def generate_token(self):
        header = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        oauth = self.http.post("https://id.sophos.com/api/v2/oauth2/token", data=self.oauth_token_data, headers=header).json()
        return oauth.get("access_token", "")

    def get_api_data(self):
        self.log.debug("Attempting to retrieve Sophos API Hosts...")
        results = self.http.get("{}/whoami/v1".format(self.base_api_url), auth=BearerAuth(self.oauth_token))
        response_code = results.status_code
        if response_code == 200:
            return results.json()
        else:
            self.log.warning("Non-200 response code returned from Sophos API. Response code: {}. Response: {}".format(response_code, results.json()))
            try:
                results.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise Exception("Non-200 response code returned from Sophos API").with_traceback(e.__traceback__)

    def test_api_connection(self):
        for endpoint in ENDPOINTS:
            api_tags = self.tags.copy()
            api_tags.append("sophos_endpoint:{}".format(endpoint))
            self.log.debug("Attempting connection test to Sophos API URL {}/{}".format(self.org_api_url, endpoint))
            try:
                x = self.http.get("{}{}".format(self.org_api_url, endpoint), auth=BearerAuth(self.oauth_token), headers=self.api_header)
                x.raise_for_status()
            except Exception as e:
                self.log.warning("Caught exception {}".format(e))
                self.log.warning("Cannot authenticate to the Sophos API endpoint {}".format(endpoint))
                self.service_check("can_connect", AgentCheck.CRITICAL, tags = api_tags)
            else:
                self.log.debug("Connection to Sophos API Successful")
                self.service_check("can_connect", AgentCheck.OK, tags = api_tags)

    def call_api(self, request_path, endpoint_type, next_page_token="", from_date="", page_size=500):
        if endpoint_type == "common":
            if page_size:
                request_path = request_path + "?pageSize={}".format(page_size)

            if next_page_token:
                request_path = request_path + "&pageFromKey={}".format(next_page_token)

            if from_date and page_size:
                request_path = request_path + "&from={}".format(from_date)

            if "endpoint" in request_path and self.endpoint_types_monitored:
                request_path = request_path + "&type={}".format(",".join(self.endpoint_types_monitored))
        
        if endpoint_type == "siem":
            if page_size:
                request_path = request_path + "?limit={}".format(page_size)

            if next_page_token:
                request_path = request_path + "&cursor={}".format(next_page_token)

            if from_date and page_size:
                request_path = request_path + "&from_date={}".format(from_date)

        while True:
            results = self.http.get("{}{}".format(self.org_api_url, request_path), auth=BearerAuth(self.oauth_token), headers=self.api_header)
            response_code = results.status_code
            if response_code == 200:
                return results.json()
            else:
                try:
                    results.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    raise Exception("Non-200 response code returned from Sophos API - {}".format(response_code)).with_traceback(e.__traceback__)
    
    def get_alerts(self):
        query_time = get_query_time(self.interval)
        dd_service = "&service=common_alert"
        log_headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": self.api_key
        }
        request_path = "/common/v1/alerts"
        response = self.call_api(request_path, "common", "", query_time)
        while True:
            logs = response["items"]
            for log in logs:
                if self.endpoint_types_to_log:
                    if log.get("managedAgent", {}).get("type") in self.endpoint_types_to_log:
                        self.http.post("{}{}{}{}".format(self.log_url, DD_SOURCE, dd_service, self.DD_HOST), headers=log_headers, json=log)
                else:
                    self.http.post("{}{}{}{}".format(self.log_url, DD_SOURCE, dd_service, self.DD_HOST), headers=log_headers, json=log)

            page_token = get_next_page_token(response)
            if page_token == "":
                break
            else:
                response = self.call_api(request_path, "common", page_token, query_time)

    def get_siem_alerts(self):
        query_time = get_query_time_siem(self.interval)
        dd_service = "&service=siem_alert"
        log_headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": self.api_key
        }
        request_path = "/siem/v1/alerts"
        response = self.call_api(request_path, "siem", "", query_time)
        while True:
            logs = response["items"]
            for log in logs:
                if self.endpoint_types_to_log:
                    if log.get("endpoint_type", "") in self.endpoint_types_to_log: 
                        self.http.post("{}{}{}{}".format(self.log_url, DD_SOURCE, dd_service, self.DD_HOST), headers=log_headers, json=log)
                else:
                    self.http.post("{}{}{}{}".format(self.log_url, DD_SOURCE, dd_service, self.DD_HOST), headers=log_headers, json=log)
            
            if response.get("has_more") == True:
                page_token = get_next_page_token_siem(response)
                response = self.call_api(request_path, "siem", page_token, query_time)
            else:
                break

    def get_siem_events(self):
        query_time = get_query_time_siem(self.interval)
        dd_service = "&service=siem_event"
        log_headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": self.api_key
        }
        request_path = "/siem/v1/events"
        response = self.call_api(request_path, "siem", "", query_time)
        while True:
            logs = response["items"]
            for log in logs:
                if self.endpoint_types_to_log:
                    if log.get("endpoint_type", "") in self.endpoint_types_to_log: 
                        self.http.post("{}{}{}{}".format(self.log_url, DD_SOURCE, dd_service, self.DD_HOST), headers=log_headers, json=log)
                else:
                    self.http.post("{}{}{}{}".format(self.log_url, DD_SOURCE, dd_service, self.DD_HOST), headers=log_headers, json=log)
            
            if response.get("has_more") == True:
                page_token = get_next_page_token_siem(response)
                response = self.call_api(request_path, "siem", page_token, query_time)
            else:
                break
        
    def get_endpoints(self):
        request_path = "/endpoint/v1/endpoints"
        response = self.call_api(request_path, "common")
        while True:
            endpoints = response["items"]
            for endpoint in endpoints:
                endpoint_tags = self.tags.copy()
                if "hostname" in endpoint.keys():
                    endpoint_tags.append("endpoint_name:{}".format(endpoint["hostname"]))
                    endpoint_tags.append("endpoint_type:{}".format(endpoint["type"]))
                    endpoint_tags.append("endpoint_platform:{}".format(endpoint["os"]["platform"]))
                    endpoint_tags.append("endpoint_os:{}".format(endpoint["os"]["name"]))
                else:
                    endpoint_tags.append("endpoint_name:data_missing")
                    endpoint_tags.append("endpoint_type:data_missing")
                    endpoint_tags.append("endpoint_platform:data_missing")
                    endpoint_tags.append("endpoint_os:data_missing")
                    self.log.warning("Endpoint missing data: {}".format(endpoint))
                self.gauge(self.billing_metric, 1, tags=endpoint_tags, raw=True)
                
                if "associatedPerson" in endpoint.keys():
                    if "name" in endpoint["associatedPerson"]:
                        endpoint_tags.append("endpoint_owner:{}".format(endpoint["associatedPerson"]["name"]))
                    elif not "name" in endpoint["associatedPerson"] and "viaLogin" in endpoint["associatedPerson"]:
                        endpoint_tags.append("endpoint_owner:{}".format(endpoint["associatedPerson"]["viaLogin"]))
                else:
                    endpoint_tags.append("endpoint_owner:missing")

                if "health" not in endpoint.keys():
                    endpoint_tags.append("health:false")
                    self.service_check("endpoint.overall_health", AgentCheck.UNKNOWN, tags=endpoint_tags)
                else:
                    endpoint_tags.append("health:true")
                    if endpoint["health"]["overall"] == "good":
                        self.service_check("endpoint.overall_health", AgentCheck.OK, tags=endpoint_tags)
                    elif endpoint["health"]["overall"] == "suspicious":
                        self.service_check("endpoint.overall_health", AgentCheck.WARNING, tags=endpoint_tags)
                    elif endpoint["health"]["overall"] == "bad":
                        self.service_check("endpoint.overall_health", AgentCheck.CRITICAL, tags=endpoint_tags)

                    verbose_mode = is_affirmative(self.instance.get("verbose_endpoints", False))
                    if verbose_mode:
                        service_details = endpoint["health"]["services"]["serviceDetails"]
                        for service in service_details:
                            service_tags = endpoint_tags.copy()
                            service_tags.append("sophos_service:{}".format(service["name"]))
                            if service["status"] == "running":
                                self.service_check("endpoint.service_running", AgentCheck.OK, tags=service_tags)
                            else:
                                self.service_check("endpoint.service_running", AgentCheck.CRITICAL, tags=service_tags)

                            service_tags.append("service_status:{}".format(service["status"]))
                            self.gauge("endpoint.service_health", 1, tags=service_tags)
                
                    endpoint_tags.append("health_status:{}".format(endpoint["health"]["overall"]))
                    endpoint_tags.append("threat_status:{}".format(endpoint["health"]["threats"]["status"]))
                    endpoint_tags.append("service_summary_status:{}".format(endpoint["health"]["services"]["status"]))
                
                if "lastSeenAt" in endpoint.keys():
                    checkin_elapsed = calculate_last_seen(endpoint["lastSeenAt"])
                else:
                    checkin_elapsed = -1
                self.gauge("endpoint.last_seen", checkin_elapsed, tags=endpoint_tags)

                if "tamperProtectionEnabled" in endpoint.keys():
                    endpoint_tags.append("tamper_status:{}".format(str(endpoint["tamperProtectionEnabled"])))
                else:
                    endpoint_tags.append("tamper_status:false")

                self.gauge("endpoint.registered", 1, tags=endpoint_tags)
            
            page_token = get_next_page_token(response)
            if page_token == "":
                break
            else:
                response = self.call_api(request_path, "common", page_token)


