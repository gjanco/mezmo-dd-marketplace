import json
import re
from datetime import datetime, timedelta
from typing import Any

from opcua import Client, ua
from requests.exceptions import ConnectionError, HTTPError, InvalidURL, Timeout

from datadog_checks.base import AgentCheck, ConfigurationError

try:
    from datadog_agent import get_config
except ImportError:

    def get_config(key):
        return ""


REQUIRED_TAGS = ["vendor:scadamods"]

REQUIRED_METRICS = [
    "system.total_tag_count:ns=2;s=_System._TotalTagCount",
    "system.active_tag_count:ns=2;s=_System._ActiveTagCount",
    "system.client_count:ns=2;s=_System._ClientCount",
    "statistics.successful_reads:ns=2;s=<Channel Name>._Statistics._SuccessfulReads",
    "statistics.successful_writes:ns=2;s=<Channel Name>._Statistics._SuccessfulWrites",
    "statistics.failed_reads:ns=2;s=<Channel Name>._Statistics._FailedReads",
    "statistics.failed_writes:ns=2;s=<Channel Name>._Statistics._FailedWrites",
    "statistics.rx_bytes:ns=2;s=<Channel Name>._Statistics._RxBytes",
    "statistics.tx_bytes:ns=2;s=<Channel Name>._Statistics._TxBytes",
    "statistics.max_pending_reads:ns=2;s=<Channel Name>._Statistics._MaxPendingReads",
    "statistics.max_pending_writes:ns=2;s=<Channel Name>._Statistics._MaxPendingWrites",
    "statistics.next_read_writes:ns=2;s=<Channel Name>._Statistics._NextReadPriority",
    "statistics.pending_reads:ns=2;s=<Channel Name>._Statistics._PendingReads",
    "statistics.pending_writes:ns=2;s=<Channel Name>._Statistics._PendingWrites",
    "devices.seconds_in_error:ns=2;s=<Channel Name>.<Device Name>._System._SecondsInError",
]


class KepserverCheck(AgentCheck):
    def __init__(self, name, init_config, instances):
        super(KepserverCheck, self).__init__(name, init_config, instances)
        self.host = self.instance.get("host")
        self.port = self.instance.get("port")
        self.opcua_host = self.instance.get("opcua_host")
        self.logging_endpoint = self.instance.get("logging_endpoint")
        self.base_api_url = "{}:{}".format(self.host, self.port)
        self.kepserver_tag_filters = self.instance.get("kepserver_tag_filters")
        self.kepserver_tag_regex = r"^\/channels\/(\*|([a-z0-9]+\/devices\/(\*|[a-z0-9]+\/tags\/(\*|[a-z0-9]+))))$"
        self.config_api_url = self.instance.get("config_api_url")
        self.eventlog_api_url = self.instance.get("eventlog_api_url")
        self.event_limit = 10
        self.event_window_mins = 1
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.metrics_map = REQUIRED_METRICS
        self.tags.append("kepserver_api:{}".format(self.base_api_url))
        self.metric_prefix = "scadamods.kepserver"
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.metric_prefix)
        self.check_initializations.append(self.validate_config)

    def check(self, _):
        # type: (Any) -> None
        if self.test_api_connect():
            self.get_eventlogs(self.tags)

            channels, devices, tags = self._get_api_endpoints(self.kepserver_tag_filters)

            # if channels devices or tags are empty, we can't proceed
            if not channels or not devices or not tags:
                self.service_check(
                    "scadamods_kepserver.api_connect",
                    AgentCheck.CRITICAL,
                    message="No channels, devices or tags found in Kepserver API",
                )
            else:
                # if we have channels, devices or tags, we can proceed
                self.get_configured_count_metrics(channels, devices, tags)
                self.send_cfg_tag_data_as_log(channels, devices, tags)

        if self.test_opcua_connect():
            self.get_opcua_metrics(channels, devices)

        self.gauge(self.billing_metric, 1.0, tags=self.tags)

        self.service_check("scadamods_kepserver.can_connect", AgentCheck.OK)

    def validate_config(self):
        self.log.debug("Validating configuration.")
        if self.kepserver_tag_filters is []:
            raise ConfigurationError("Must provide some filter value, if no filter provide '/*'")

    def test_api_connect(self):
        self.log.debug("Attempting connection test to Kepserver API URL %s.", self.base_api_url)
        try:
            self._http_request(self.base_api_url)
            return True
        except Exception:
            return False

    def test_opcua_connect(self):
        self.log.debug("Attempting connection test to OPC UA server %s.", self.opcua_host)
        try:
            if self.opcua_host is not None:
                client = Client(self.opcua_host)
                client.connect()
                client.disconnect()
                return True
            else:
                self.log.error("OPC UA host is required in conf.yaml")
                return False
        except ua.uaerrors.UaStatusCodeError as e:
            self.service_check(
                "scadamods_kepserver.opcua.can_connect",
                AgentCheck.CRITICAL,
                message="Request failed: {}, {}".format(self.opcua_host, e),
            )
            return False
        except Exception as e:
            self.service_check(
                "scadamods_kepserver.opcua.can_connect",
                AgentCheck.CRITICAL,
                message="Request failed: {}, {}".format(self.opcua_host, e),
            )
            return False

    def get_opcua_metrics(self, channels, devices):
        # try to get the metrics from the OPC UA server
        try:
            # read all metrics that are not 'tags', remaining are opc based not api
            client = Client(self.opcua_host)
            client.connect()
            metrics = []
            for metric_map in self.metrics_map:
                # try to grab the metric
                try:
                    m = metric_map.split(":")
                    name = "{}.{}".format(self.metric_prefix, m[0])
                    path = m[1]
                    if "<Channel Name>" in path and "<Device Name>" in path:
                        for channel in channels:
                            for device in devices:
                                # try to get the real channel name and device name
                                channel_name = ""
                                device_name = ""
                                try:
                                    channel_name = channel["data"]["common.ALLTYPES_NAME"]
                                    device_name = device["data"]["common.ALLTYPES_NAME"]
                                    path = path.replace("<Channel Name>", channel_name).replace(
                                        "<Device Name>", device_name
                                    )
                                    # try to get the opc metric value
                                    try:
                                        value = client.get_node(path).get_value()
                                        metrics.append(
                                            {
                                                "name": name,
                                                "value": value,
                                                "tags": [
                                                    "channel:{}".format(channel_name),
                                                    "device:{}".format(device_name),
                                                ],
                                            }
                                        )
                                    except Exception as e:
                                        if "(BadNodeIdUnknown)" in e:
                                            # tell user to check if channel has diagnostics enabled
                                            self.service_check(
                                                "scadamods_kepserver.opcua.diagnostics",
                                                AgentCheck.WARNING,
                                                message="Channel {} may not have diagnostics enabled".format(
                                                    channel_name
                                                ),
                                            )
                                        self.log.error(
                                            "Failed to get opc metric %s: %s - channel:%s, device:%s",
                                            path,
                                            e,
                                            channel_name,
                                            device_name,
                                        )
                                        continue
                                except Exception as e:
                                    self.log.error(
                                        "Could not get channel %s or device %s name for %s, %s",
                                        channel_name,
                                        device_name,
                                        path,
                                        e,
                                    )
                                    continue

                    else:
                        if "<Device Name>" in path:
                            for device in devices:
                                device_name = device["data"]["common.ALLTYPES_NAME"]
                                path = path.replace("<Device Name>", device_name)
                                # try to get the opc metric value
                                try:
                                    value = client.get_node(path).get_value()
                                    metrics.append(
                                        {
                                            "name": name,
                                            "value": value,
                                            "tags": ["device:{}".format(device_name)],
                                        }
                                    )
                                except Exception as e:
                                    self.log.error("Failed to get opc metric %s: %s", path, e)

                        if "<Channel Name>" in path:
                            for channel in channels:
                                channel_name = channel["data"]["common.ALLTYPES_NAME"]
                                path = path.replace("<Channel Name>", channel_name)
                                # try to get the opc metric value
                                try:
                                    value = client.get_node(path).get_value()
                                    metrics.append(
                                        {
                                            "name": name,
                                            "value": value,
                                            "tags": ["channel:{}".format(channel_name)],
                                        }
                                    )
                                except Exception as e:
                                    self.log.error("Failed to get opc metric %s: %s", path, e)
                        # If channel, or device not in path
                        if "<Channel Name>" not in path and "<Device Name>" not in path:
                            # try to get the opc metric value
                            try:
                                value = client.get_node(path).get_value()
                                metrics.append({"name": name, "value": value, "tags": []})
                            except Exception as e:
                                self.log.error("Failed to get opc metric %s: %s", path, e)
                except Exception as e:
                    self.log.error("OPC UA metric request failed: %s", e)
                    continue

            for metric in metrics:
                self.gauge(
                    name=metric["name"],
                    value=metric["value"],
                    tags=self.tags + metric["tags"],
                )
            client.disconnect()

        except Exception as e:
            self.log.error("Error while getting OPC UA metrics: %s", e)
            return False

    def get_eventlogs(self, tags):
        self.log.debug("Retrieving local Kepserver Event Logs")
        # Limit = Maximum number of log entries to return.
        #  The default setting is 100 entries.
        # Start = Earliest time to be returned
        # End = Latest time to be returned
        #  YYYY-MM-DDTHH:mm:ss.sss (UTC) format.
        # http://127.0.0.1:57412/config/v1/event_log?
        # limit=10&start=2021-04-03T00:00:00.000&end=2021-04-03T20:00:00.000
        #
        limit = self.event_limit
        mins = self.event_window_mins
        x_minute = timedelta(minutes=mins)
        start = (datetime.now() - x_minute).isoformat(timespec="microseconds")
        end = datetime.now().isoformat(timespec="microseconds")
        url_args = "?" + "&".join(["limit={}".format(limit), "start={}".format(start), "end={}".format(end)])

        # try to get the event logs
        try:

            kepserver_event_logs = self._http_request(url=self.base_api_url + "/" + self.eventlog_api_url + url_args)
            self.log.debug("Retrieved Kepserver Event Logs")
            # test if we have any logs
            if kepserver_event_logs is not None:
                for event in kepserver_event_logs:
                    alert_type = "info"
                    if event["event"].lower() in [
                        "error",
                        "warning",
                        "success",
                        "info",
                    ]:
                        alert_type = event["event"].lower()
                    self.event(
                        {
                            "timestamp": datetime.fromisoformat(event["timestamp"]).timestamp(),
                            "event_type": event["event"],
                            "msg_title": "Kepserver - " + event["message"],
                            "msg_text": event["message"],
                            "alert_type": alert_type,
                            "aggregation_key": event["source"],
                            "source_type_name": event["source"],
                            "tags": tags,
                        }
                    )
        except Exception as e:
            self.log.error("Failed to retrieve Kepserver Event Logs: %s", e)

    def send_cfg_tag_data_as_log(self, channels, devices, tags):
        headers = {
            "Content-type": "application/json",
            "DD-API-KEY": get_config("api_key"),
        }
        try:
            msg = []
            for tag in tags:
                msg.append(tag["data"])

            self.http.post(
                self.logging_endpoint,
                headers=headers,
                data=json.dumps(
                    {
                        "message": msg,
                        "ddtags": "env:kepserver_configuration_api_logging_endpoint",
                        "ddsource": "scadamods_kepserver",
                        "hostname": self.host,
                        "service": "kepserver",
                    }
                ),
            )
        except Exception as e:
            self.log.error("Error sending logs: {}", str(e))

    def get_configured_count_metrics(self, channels, devices, tags):
        self.gauge(
            name="{}.configured.tags.count".format(self.metric_prefix),
            value=len(tags),
            tags=self.tags,
        )
        self.gauge(
            name="{}.configured.devices.count".format(self.metric_prefix),
            value=len(devices),
            tags=self.tags,
        )
        self.gauge(
            name="{}.configured.channels.count".format(self.metric_prefix),
            value=len(channels),
            tags=self.tags,
        )

    def _get_api_endpoints(self, tag_filters):
        # try to get the api endpoints
        try:

            tag_result = []
            device_result = []
            channel_result = []
            endpoints = self._get_unique_patterns(tag_filters)
            for endpoint in endpoints:
                cnt = endpoint.count("/")
                if cnt == 6:  # tag (fully qualified path for tag data)
                    device = self._get_device_api(endpoint.rsplit("/", 2)[0])
                    channel = self._get_channel_api(endpoint.rsplit("/", 4)[0])
                    device_result.append(device)
                    channel_result.append(channel)
                    t = self._get_tag_api(endpoint)
                    t["data"]["device"] = device
                    t["data"]["channel"] = channel
                    tag_result.append(t)
                elif cnt == 5:  # tags/*
                    device = self._get_device_api(endpoint.rsplit("/", 1)[0])
                    channel = self._get_channel_api(endpoint.rsplit("/", 3)[0])
                    device_result.append(device)
                    channel_result.append(channel)
                    for t in self._get_tags_api(endpoint):
                        t["data"]["device"] = device
                        t["data"]["channel"] = channel
                        tag_result.append(t)
                elif cnt == 3:  # device/*
                    channel = self._get_channel_api(endpoint.rsplit("/", 1)[0])
                    channel_result.append(channel)
                    for d in self._get_devices_api(endpoint):
                        device_result.append(d)
                        for t in self._get_tags_api(d["path"]):
                            t["data"]["device"] = d["data"]
                            t["data"]["channel"] = channel
                            tag_result.append(t)
                else:  # channel/*
                    for c in self._get_channels_api(endpoint):
                        channel_result.append(c)
                        for d in self._get_devices_api(c["path"]):
                            device_result.append(d)
                            for t in self._get_tags_api(d["path"]):
                                t["data"]["device"] = d["data"]
                                t["data"]["channel"] = c["data"]
                                tag_result.append(t)
            channels = self._unique(channel_result)
            devices = self._unique(device_result)
            tags = self._unique(tag_result)
            return channels, devices, tags
        except Exception as e:
            self.log.error("Failed to get API endpoints: %s", e)
            return [], [], []

    def _unique(self, lst):
        # intilize a null list
        unique_list = []
        # traverse for all elements
        for x in lst:
            # check if exists in unique_list or not
            if x not in unique_list:
                unique_list.append(x)
        return unique_list

    def _get_tag_api(self, path, endpoint):
        return self._http_request(endpoint)

    def _get_tags_api(self, path):
        endpoint = path + "/tags"
        results = self._http_request(endpoint)
        r = [{"path": endpoint + "/" + item["common.ALLTYPES_NAME"], "data": item} for item in results]
        return r

    def _get_devices_api(self, path):
        endpoint = path + "/devices"
        results = self._http_request(endpoint)
        r = [{"path": endpoint + "/" + item["common.ALLTYPES_NAME"], "data": item} for item in results]
        return r

    def _get_device_api(self, path):
        endpoint = "{}/{}/{}".format(self.base_api_url, self.config_api_url, path)
        result = self._http_request(endpoint)
        r = {"path": endpoint, "data": result}
        return r

    def _get_channel_api(self, path):
        endpoint = "{}/{}/{}".format(self.base_api_url, self.config_api_url, path)
        result = self._http_request(endpoint)
        r = {"path": endpoint, "data": result}
        return r

    def _get_channels_api(self, path):
        endpoint = "{}/{}/{}".format(self.base_api_url, self.config_api_url, path)
        results = self._http_request(endpoint)
        r = [{"path": endpoint + "/" + item["common.ALLTYPES_NAME"], "data": item} for item in results]
        return r

    def _get_unique_patterns(self, tag_filters):
        result = []
        tag_filters.sort()
        treeroot = "$$"
        for endpoint in tag_filters:
            match = re.search(self.kepserver_tag_regex, endpoint, re.IGNORECASE)
            if match:
                # Check for last *
                if endpoint.find(treeroot) != -1:
                    continue
                else:
                    if endpoint.endswith("*"):
                        treeroot = endpoint[:-2]
                        result.append(treeroot)
                    else:
                        result.append(endpoint)
        return result

    def _http_request(self, url):
        # Perform HTTP Requests with our HTTP wrapper.
        # More info at https://datadoghq.dev/integrations-core/base/http/
        try:
            response = self.http.get(url)
            response.close()
            response.raise_for_status()
            response_json = response.json()

        except ConnectionError as e:
            self.service_check(
                "scadamods_kepserver.can_connect",
                AgentCheck.CRITICAL,
                message="Request failed: {}, {}".format(url, e),
            )
            self.log.debug("Connection error : %s, %s", url, e)
            return "{}"

        except Timeout as e:
            self.service_check(
                "scadamods_kepserver.can_connect",
                AgentCheck.CRITICAL,
                message="Request timeout: {}, {}".format(url, e),
            )
            raise

        except (HTTPError, InvalidURL, ConnectionError) as e:
            self.service_check(
                "scadamods_kepserver.can_connect",
                AgentCheck.CRITICAL,
                message="Request failed: {}, {}".format(url, e),
            )
            raise

        except ValueError as e:
            self.service_check(
                "scadamods_kepserver.can_connect",
                AgentCheck.CRITICAL,
                message="JSON Parse failed: {}, {}".format(url, e),
            )
            raise

        return response_json
