
from typing import Any
import json
from datadog_checks.base import AgentCheck, ConfigurationError
from datadog_checks.base.errors import CheckException
from requests.exceptions import ConnectionError, HTTPError, InvalidURL, Timeout
import socket

REQUIRED_TAGS = [
    "vendor:rapdev",
]
HOSTNAME = socket.gethostname()

LOG_API_URL_MAP = {
    "com": "datadoghq.com",
    "eu": "datadoghq.eu",
    "us3": "us3.datadoghq.com",
    "us5": "us5.datadoghq.com",
    "gov": "ddog-gov.com"
}


class BoxCheck(AgentCheck):

    # This will be the prefix of every metric and service check the integration sends
    __NAMESPACE__ = 'rapdev.box'

    def __init__(self, name, init_config, instances):
        super(BoxCheck, self).__init__(name, init_config, instances)
        self.box_url = self.instance.get("box_url", "https://api.box.com/")
        self.admin_logs_enabled = self.instance.get(
            "admin_logs_enabled", False)
        self.dd_site = self.instance.get("dd_site", "com")
        self.log_intake = f"https://http-intake.logs.{LOG_API_URL_MAP.get(self.dd_site)}/api/v2/logs"
        self.dd_api_key = self.instance.get("dd_api_key")
        self.enterprise_id = self.instance.get("enterprise_id")
        self.client_id = self.instance.get("client_id")
        self.client_secret = self.instance.get("client_secret")
        self.next_stream_position = ''

        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.check_initializations.append(self.validate_config)

    def check(self, _):
        self.token = self.bearer_token()
        self.get_users()
        if self.admin_logs_enabled:
            self.get_admin_logs()

    def validate_config(self):
        if not self.client_id:
            raise ConfigurationError("CLIENT ID WAS NOT SUPPLIED")
        if not self.client_secret:
            raise ConfigurationError("CLIENT SECRET WAS NOT SUPPLIED")
        if not self.enterprise_id:
            raise ConfigurationError("ENTERPRISE ID WAS NOT SUPPLIED")
        if not self.dd_api_key:
            raise ConfigurationError("DATADOG API KEY WAS NOT SUPPLIED")

    def call_api(self, http_method, url, data):
        try:
            if http_method == 'POST':
                response = self.http.post(url, data=data)
            elif http_method == 'GET':
                response = self.http.get(url, headers=data)
        except (HTTPError, InvalidURL, ConnectionError) as e:
            self.service_check(
                "can_connect",
                AgentCheck.CRITICAL,
                self.tags,
                message="Request failed: {}, {}".format(url, e),
            )
            raise CheckException(f"Agent Check error {e}")
        else:
            response_json = response.json()
            self.service_check(
                "can_connect",
                AgentCheck.OK,
                self.tags,
            )
            return response_json

    def bearer_token(self):
        auth = "oauth2/token"
        body = {
            "Content-Type": "application/x-www-form-urlencoded",
            "grant_type": "client_credentials",
            "client_id": f"{self.client_id}",
            "client_secret": f"{self.client_secret}",
            "box_subject_type": "enterprise",
            "box_subject_id": f"{self.enterprise_id}"
        }
        response = self.call_api('POST', self.box_url + auth, body)
        token = response.get('access_token', '')
        if token:
            self.service_check(
                "got_bearer",
                AgentCheck.OK
            )
            return token
        else:
            self.service_check(
                "got_bearer",
                AgentCheck.CRITICAL
            )
            raise ValueError("DID NOT GET BEARER TOKEN FROM RESPONSE")

    def get_users(self):
        offset = 0  # default page offset is 0
        header = {
            "Authorization": f"Bearer {self.token}"
        }
        status_dict = {
            "active": 0,
            "inactive": 0,
            "cannot_delete_edit": 0,
            "cannot_delete_edit_upload": 0
        }
        while True:
            # how many results to return in entries[]
            limit = 100
            query = f"""?limit={limit}&offset={offset}"""
            response = self.call_api(
                'GET', self.box_url + f"2.0/users{query}", data=header)

            # api recommends getting limit from response
            limit = response.get("limit")

            # get total count of users
            total = response.get("total_count")
            self.gauge(
                "users.count",
                int(total),
                tags=[
                    f'status:all'
                ].append(self.tags)
            )
            self.log.debug(f"Total Box Users: {total}")
            self.log.debug(f"Offset: {offset}")

            for user in response.get("entries"):
                email = user.get("login")
                id = user.get("id")
                quota = user.get("space_amount")
                used = user.get("space_used")
                status = user.get("status")
                if status == "active":
                    status_dict['active'] += 1
                if status == "inactive":
                    status_dict['inactive'] += 1
                if status == "cannot_delete_edit":
                    status_dict['cannot_delete_edit'] += 1
                if status == "cannot_delete_edit_upload":
                    status_dict['cannot_delete_edit_upload'] += 1
                self.gauge(
                    "users.storage.max",
                    int(quota),
                    tags=[
                        f'user_id:{id}',
                        f'user_login:{email}',
                        f'user_status:{status}'
                    ] + self.tags
                )
                self.gauge(
                    "users.storage.used",
                    int(used),
                    tags=[
                        f'user_id:{id}',
                        f'user_login:{email}',
                        f'user_status:{status}'
                    ] + self.tags
                )
                self.gauge(
                    "datadog.marketplace.rapdev.box",
                    1,
                    tags=[
                        f'user_login:{email}'
                    ],
                    raw=True
                )
            for k, v in status_dict.items():
                self.gauge(
                    "users.count",
                    int(v),
                    tags=[
                        f'status:{k}'
                    ].append(self.tags)
                )
            offset = offset + limit  # increment offset
            if offset > total:
                break

    def get_admin_logs(self):
        events = '2.0/events'
        box_header = {
            "Authorization": f"Bearer {self.token}"
        }
        dd_header = {
            'DD-API-KEY': f'{self.dd_api_key}',
            'Content-Type': 'application/json'
        }
        dd_entries = []
        if not self.next_stream_position:
            query = f'''?stream_type=admin_logs_streaming'''
        else:
            query = f'''?stream_type=admin_logs_streaming&stream_position={self.next_stream_position}'''
        response = self.call_api(
            'GET', f'{self.box_url}{events}{query}', box_header)
        self.next_stream_position = response.get('next_stream_position')
        for entry in response.get("entries"):
            dumped = json.dumps(entry)
            LOG = {
                "hostname": f"{HOSTNAME}",
                "ddsource": "box",
                "service": "admin_logs",
                "ddtags": self.tags,
                "message": f"{dumped}"
            }
            dd_entries.append(LOG)
        try:
            r = self.http.post(
                self.log_intake, headers=dd_header, json=dd_entries)
            r.raise_for_status()
        except (HTTPError, InvalidURL, ConnectionError) as e:
            self.log.error("ERROR POSTING LOGS: {e}")
