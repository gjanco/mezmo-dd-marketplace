import socket
import json
from datadog_checks.base import AgentCheck, ConfigurationError
from requests.exceptions import HTTPError

try:
    from datadog_agent import get_config
except ImportError:
    def get_config(key):
        return ""

HOSTNAME = socket.gethostname()
LOG_URL = "https://http-intake.logs.datadoghq.com/v1/input"
DD_SOURCE = "?ddsource=r7&service=IDR_logs&host={}".format(HOSTNAME)

REQUIRED_TAGS = [
    "vendor:rapdev",
]


class Rapid7Check(AgentCheck):

    __NAMESPACE__ = 'rapdev.rapid7'

    def __init__(self, name, init_config, instances):
        super(Rapid7Check, self).__init__(name, init_config, instances)
        self.logs_from_conf = self.instance.get("log_dict")
        self.interval = self.instance.get("min_collection_interval", 60)
        self.dd_api_key = self.instance.get("dd_api_key")
        self.dd_app_key = self.instance.get("dd_app_key")
        self.base_api_url = self.instance.get("url")
        self.x_api_key = self.instance.get("api_key")
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.log_interval = self.instance.get("log_interval", "last 1 minutes")
        self.to_select = self.instance.get("select", [])
        self.tags = list(set(self.tags))
        self.logs_processed = 0
        self.check_initializations.append(self.validate_config)

        self.r7_headers = {
            "Content-Type": "application/json",
            "x-api-key": self.x_api_key
        }
        self.log_headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": self.dd_api_key
        }

        self.body = {"logs": [], "leql": {
            "during": {"time_range": self.log_interval}}}

    def check(self, _):
        self.test_api_connection()
        self.create_body()
        self.post_handler()

    def validate_config(self):
        if not self.base_api_url:
            raise ConfigurationError("Events api endpoint not provided")
        if not self.dd_api_key:
            raise ConfigurationError("Unable to retrieve DataDog API Key")
        if not self.x_api_key:
            raise ConfigurationError("IDR x_api_key not provided")

    def get_log_streams(self):
        r = self.http.get(
            "https://us.api.insight.rapid7.com/log_search/management/logs", extra_headers=self.r7_headers)
        logs = {}
        response_iter = r.json().get("logs")
        for i in response_iter:
            if i.get("source_type") != 'internal':
                logs[i.get("id")] = {"logstream_name": i.get("name"),
                                     "logset_name": i.get('logsets_info')[0].get("name"),
                                     "source_type": i.get('source_type')}
        return logs

    def edit_url(self, url):
        copy = url.replace('&per_page=50&', '&per_page=500&')
        return copy

    def create_body(self):
        log_dict = self.get_log_streams()
        self.log.debug(f"Log dict: {log_dict}")
        self.log.debug(f"self.to_select: {self.to_select}")
        if self.to_select != []:
            for k in log_dict:
                if log_dict[k].get('logset_name') in self.to_select:
                    self.body.get("logs").append(k)
                    self.log.debug(f"Body: {self.body}")
        else:
            for k in log_dict:
                self.body.get("logs").append(k)

    def post_handler(self):
        self.logs_processed = 0
        r = self.http.post("https://us.api.insight.rapid7.com/log_search/query/logs?&per_page=500&",
                           json=self.body,
                           extra_headers=self.r7_headers
                           )
        while True:
            rjson = r.json()
            response_code = r.status_code
            # if response is 200, logs are in the json.events
            if response_code == 200:
                self.log.debug("{} R7_IDR logs found".format(
                    len(rjson.get('events'))))
                self.http.post("{}{}".format(LOG_URL, DD_SOURCE),
                               extra_headers=self.log_headers,
                               json=rjson.get('events'))
                self.logs_processed += len(rjson.get('events'))
                self.gauge("logs.processed",
                           self.logs_processed,
                           tags=self.tags
                           )
                if rjson.get('links') is [] or rjson.get('links') is None:
                    break
                else:
                    r = self.http.get(self.edit_url(rjson.get("links")[
                                      0].get("href")), extra_headers=self.r7_headers)
            if response_code == 202:
                r = self.http.get(self.edit_url(rjson.get("links")[
                                  0].get("href")), extra_headers=self.r7_headers)
            else:
                try:
                    r.raise_for_status()
                except HTTPError as e:
                    raise Exception(
                        "Non-200 response code returned from R7 IDR API - {}".format(
                            response_code)
                    ).with_traceback(e.__traceback__)

    def test_api_connection(self):
        self.log.debug("Attempting connection test to Datadog API.")

        x = self.call_api("validate", self.dd_api_key,
                          self.dd_app_key, jsonify=False)

        response_code = x.status_code
        if response_code == 200:
            self.log.debug("Connection successful")
            self.service_check("can_connect", AgentCheck.OK, tags=self.tags)
        else:
            self.log.warning(
                "Cannot authenticate to Datadog API. The check will not run")
            self.service_check(
                "can_connect", AgentCheck.CRITICAL, tags=self.tags)

    def call_api(self, request_path, dd_api_key, dd_app_key, jsonify=True, api_version_number=1):
        """Helper function used to call the DD API
        :param string request_path: the endpoint that we are calling from the Datadog API
        :param string dd_api_key: Datadog api key used to authenticate to API
        :param string dd_app_key: Datadog app key used to authenticate to API
        :param boolean jsonify: whether or not to return the json of the response
        :param int api_version_number: the version of the Datadog API we are calling
        :return: json of request made
        """

        headers = {
            "content-type": "application/json",
            "DD-API-KEY": dd_api_key,
            "DD-APPLICATION-KEY": dd_app_key,
        }

        api_version = f'v{str(api_version_number)}/'

        try:
            # Make DD API GET request
            results = self.http.get(
                "https://api.datadoghq.com/api/" + api_version + request_path,
                extra_headers=headers
            )

            # Raise an error if there was one
            results.raise_for_status()
            # If call is successful, return json result
            if jsonify:
                return results.json()
            else:
                return results
        except HTTPError as e:
            raise Exception(
                "Non-200 response code returned from DD API: {}").with_traceback(e.__traceback__)
