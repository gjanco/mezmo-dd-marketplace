import socket
import json
import datetime
import time
from typing import cast

from datadog_checks.base import AgentCheck, ConfigurationError
from requests.exceptions import HTTPError

try:
    from datadog_agent import get_config
except ImportError:
    def get_config(key):
        return ""

HOSTNAME = socket.gethostname()
LOG_URL = "https://http-intake.logs.datadoghq.com/v1/input"
DD_SOURCE = f"?ddsource=r7&service=IDR&host={HOSTNAME}"

REQUIRED_TAGS = [
    "vendor:rapdev",
]

# PERSISTENT CACHE FILE PATH
# /opt/datadog-agent/run/test/*

class Rapid7Check(AgentCheck):

    __NAMESPACE__ = 'rapdev.rapid7'

    def __init__(self, name, init_config, instances):
        super(Rapid7Check, self).__init__(name, init_config, instances)
        # dd api/app keys
        # try and get from init_config
        self.dd_api_key = self.init_config.get("dd_api_key")
        # if no key in init_config try getting from instance
        if self.dd_api_key is None:
            self.dd_api_key = self.instance.get("dd_api_key","")

        # try and get from init_config
        self.dd_app_key = self.init_config.get("dd_app_key")
        if self.dd_app_key is None:
            self.dd_app_key = self.instance.get("dd_app_key","")
        
        # r7 api config
        # try and get from init_config
        self.r7_api_key = self.init_config.get("r7_api_key")
        # try and get from init_config
        if self.r7_api_key is None:
            self.r7_api_key = self.instance.get("r7_api_key","")

        # TO TURN ON LOGS
        self.logs_enabled = self.instance.get("r7_logs_enabled", False)

        # dd check interval
        self.interval = self.instance.get("min_collection_interval", 60)
        
        self.region = self.instance.get("r7_region", "us")
        self.api_url = f'https://{self.region}.api.insight.rapid7.com'

        # log specific settings (if enabled)
        self.to_select = self.instance.get("select", [])
        self.log_interval = self.instance.get("log_interval", "last 1 minutes")

        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.tags = list(set(self.tags))

        self.check_initializations.append(self.validate_config)
        self.check_initializations.append(self.test_api_connection)

        self.r7_headers = {
            "Content-Type": "application/json",
            "x-api-key": self.r7_api_key
        }

        self.dd_headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": self.dd_api_key
        }

        self.ts_last = time.mktime(datetime.datetime.now().timetuple())*1e3

        self.body = {"logs": [], "leql": {
            "during": {"time_range": self.log_interval}}}


    def check(self, _):
        # READ FROM PERSISTENT CACHE
        self.read_from_cache()

        # TEST DATADOG API CONNECTION
        self.test_api_connection()

        # RUN INVESTIGATIONS CHECK
        self.investigations()

        # IF LOGS ENABLED, PROCESS LOGS
        if self.logs_enabled:
            self.collect_logs()
        
        # WRITE TO PERSISTENT CACHE
        self.write_to_cache()

    def validate_config(self):
        if not self.dd_api_key:
            raise ConfigurationError("Unable to retrieve DataDog API Key")
        if not self.dd_app_key:
            raise ConfigurationError("Unable to retrieve DataDog API Key")
        if not self.r7_api_key:
            raise ConfigurationError("Unable to retrieve Rapid7 API Key")

    def read_from_cache(self):
        # READ LASTEST STATE OF DICT FROM PERSISTENT STORAGE AND LOAD AS JSON
        self.persistent = self.read_persistent_cache('dict')
        # TRY TO LOAD CACHE AS JSON
        try:
            self.persistent = json.loads(self.persistent)
            self.duringfrom = self.persistent.get('log_ts', '')
        except ValueError:
            self.persistent = {
                'open': {},
                'log_ts': f'{self.ts_last}',
            }
            self.log.error(
                f'ERROR READING PERSISTENT DICTIONARY TO JSON\nCREATING NEW DICT: {self.persistent}')

    def write_to_cache(self):
        try:
            self.write_persistent_cache('dict', json.dumps(self.persistent))
        except ValueError:
            self.log.error(
                f'ERROR WRITING DICTIONARY TO CACHE')
        

    # DEF FOR INVESTIGATIONS CHECK
    def investigations(self):
        # START EVENT HELPER DEF
        def post_event(e):
            self.log.debug(f'EVENT POSTING HELPER CALLED FOR EVENT: {e}\n')
            # GET R7 INVESTIGATION ID
            r7_id = e.get('id','')
            # GET R7 INVESTIGATION TITLE
            r7_title = e.get('title','')
            # GET R7 INVESTIGATION STATUS
            r7_status = e.get('status','')
            # DON'T POST EVENT AND EXIT IF ID, TITLE, STATUS NOT DEFINED 
            if not r7_id or not r7_title or not r7_status:
                self.log.warn(f'Investigation event does not contain required fields')
                return
            else:
                # MAP R7 INVESTIGATION STATUS TO DD ALERT_TYPE
                # "OPEN" -> 'error'
                # "CLOSED" -> 'warning'
                if r7_status in "OPEN":
                    dd_alert_type = "error"
                else:
                    dd_alert_type = "warning"

                # GET R7 INVESTIGATION SOURCE
                r7_source = e.get('source')
                # GET R7 INVESTIGATION ASSIGNEE JSON
                r7_assignee = e.get('assignee', {})
                # GET R7 ASSIGNEE FIELDS
                r7_assignee_name = r7_assignee.get('name', 'Unassigned')
                r7_assignee_email = r7_assignee.get('email', 'Unassigned')
                # GET R7 INVESTIGATION ALERT JSON
                try:
                    r7_alerts = e.get('alerts', [{}])[0]
                except IndexError:
                    r7_alerts = {}
                # GET R7 INVESTIGATION ALERT FIELDS
                r7_alerts_name = r7_alerts.get('type', 'N/A')
                r7_alerts_desc = r7_alerts.get('type_description', 'N/A')
                r7_alerts_created = r7_alerts.get('first_event_time', 'N/A')

                # EVENT API SUPPORTS MD FORMATTING IN TEXT FIELD
                dd_text = (
                    f"%%% \n"
                    f"**Investigation Information** \n"
                    f"Title: **{r7_title}**\n"
                    f"ID: {r7_id}\n"
                    f"Status (Open/Closed): **{r7_status}**\n"
                    f"Investigation Source: **{r7_source}**\n"
                    f"\n"
                    f"**Alert Content** \n"
                    f"Type: **{r7_alerts_name}**\n"
                    f"Description: {r7_alerts_desc}\n"
                    f"Date Created: {r7_alerts_created}\n"
                    f"\n"
                    f"**Investigation Assignee** \n"
                    f"Name: {r7_assignee_name}\n"
                    f"Email: {r7_assignee_email}\n"
                    f"\n %%%"
                )

                self.event(
                    {
                        "event_type": f'{dd_alert_type}',
                        "msg_title": f'{r7_title}',
                        "msg_text": f'{dd_text}',
                        "aggregation_key": f'{r7_id}',
                        "alert_type": f'{dd_alert_type}',
                        "source_type_name": "my_apps",
                        "host": f'{HOSTNAME}',
                        "tags": ["rapid7:investigations"] + REQUIRED_TAGS + [f'status:{r7_status}'],
                    }
                )
        # END EVENT HELPER DEF
    
        r = self.http.get(
            "https://us.api.insight.rapid7.com/idr/v1/investigations", headers=self.r7_headers)
        r = r.json().get('data')

        open = [x for x in r if x.get('status') in 'OPEN']
        closed = [x for x in r if x.get('status') in 'CLOSED']
        closed_ids = [x.get('id') for x in closed]

        for item in open + closed:
            item_id = item.get('id')
            p_open = self.persistent.get('open', {}).keys()

            # IF ITEM NOT IN PERSISTENT DICT AND NOT IN CLOSED, ADD AND POST
            # NEW EVENT & OPEN EVENT
            if item_id not in p_open and item_id not in closed_ids:
                self.persistent.get('open', {})[item_id] = item
                post_event(item)

            # IF ITEM NOT IN PERSISTENT DICT BUT IS CLOSED, IGNORE IT
            # NEW EVENT & CLOSED EVENT
            if item_id not in p_open and item_id in closed_ids:
                continue

            # IF ITEM IN PERSISTENT DICT BUT IS CLOSED, REMOVE AND POST
            # EXISTING EVENT & CLOSED EVENT
            if item_id in p_open and item_id in closed_ids:
                self.persistent.get('open', {}).pop(item_id)
                post_event(item)

            # IF ITEM IN PERSISTENT DICT BUT IS NOT CLOSED, INVESTIGATION STILL OPEN
            # EXISTING EVENT & OPEN EVENT
            if item_id in p_open and item_id not in closed_ids:
                continue

    def edit_url(self, url):
        copy = url.replace('&per_page=50&', '&per_page=500&')
        return copy

    def collect_logs(self):
        r = self.http.get(
            "https://us.api.insight.rapid7.com/log_search/management/logs", extra_headers=self.r7_headers)
        rjson = r.json()
        for i in rjson.get('logs'):
            setname = i.get('logsets_info')[0].get('name')
            if setname in 'Endpoint Agents' or setname in 'Endpoint Activity':
                self.body.get('logs').append(i.get('id'))

        r = self.http.post("https://us.api.insight.rapid7.com/log_search/query/logs?&per_page=500&",
                           json=self.body,
                           extra_headers=self.r7_headers
                           )
        while True:
            rjson = r.json()
            response_code = r.status_code
            # if response is 200, logs are in the json.events

            if response_code == 200:
                self.log.debug(f'{len(rjson.get("events"))} R7_IDR logs found')
                self.http.post(f'{LOG_URL}{DD_SOURCE}',
                               extra_headers=self.dd_headers,
                               json=rjson.get('events'))
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
            "DD-API-KEY": dd_api_key
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
