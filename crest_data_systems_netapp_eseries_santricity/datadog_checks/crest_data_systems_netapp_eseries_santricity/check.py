# (C) Datadog, Inc. 2022-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import time
import urllib.parse as urlparse
from datetime import datetime, timedelta

import datadog_agent
import requests

try:
    from datadog_checks.base import AgentCheck, ConfigurationError
except ImportError:
    from checks import AgentCheck, ConfigurationError

from . import cds_netapp_eseries_santricity_consts as consts
from . import cds_netapp_eseries_santricity_utils as Utils


class CrestDataSystemsNetappEseriesSantricityCheck(AgentCheck):
    # This will be the prefix of every metric and service check the integration sends
    __NAMESPACE__ = consts.INTEGRATION_PREFIX

    def __init__(self, name, init_config, instances):
        super(CrestDataSystemsNetappEseriesSantricityCheck, self).__init__(name, init_config, instances)
        self.elapsed_time = 0
        self.execution_count = 0
        self.ingest_log = True

    def check(self, _):
        """Data collection starts from here."""

        # data collection started
        start_time = time.time()

        self.validateRequiredFields()
        self.setupSession()
        self.authentication()
        self.set_configurations()

        ENDPOINT_MAPPING_DICT = {
            "graph": self.ingest_graph_data,
            "analysed-volume-statistics": self.ingest_volume_data,
            "analysed-drive-statistics": self.ingest_drive_data,
            "analysed-controller-statistics": self.ingest_controller_data,
            "analysed-interface-statistics": self.ingest_interface_data,
        }

        # set log ingestion flag
        if self.elapsed_time // consts.LOG_INGESTION_INTERVAL >= self.execution_count:
            self.ingest_log = True
            self.execution_count += 1
        else:
            self.ingest_log = False

        self.elapsed_time += self.instance.get("min_collection_interval", 600)

        # ingest marketplace metric for total count of instance running
        self.gauge(
            "datadog.marketplace.crest_data_systems.netapp_eseries_santricity",
            1.0,
            tags=self.instance.get("tags", [])
            + [f"cds_netapp_eseries_santricity_instance:{self.instance.get('address')}"],
            hostname=self.instance.get("address"),
            raw=True,
        )

        for endpoint in consts.ENDPOINTS:
            try:
                response = self.getEndpoint(endpoint)
                if response.status_code != 200:
                    self.log.error(
                        "NetApp ESeries SANtricity: Unsuccessful response: "  # noqa: G001
                        "status_code = {} response = {}".format(response.status_code, response.text),
                    )
                    self.ingest_service_check_and_event_for_auth(
                        is_authenticated=False,
                        reason=f"NetApp ESeries SANtricity: Unsuccessful response: \
                            status_code = {response.status_code} response = {response.text}",
                    )
                    continue
                self.log.info(
                    "NetApp ESeries SANtricity: Successful response "  # noqa: G001
                    "from netapp endpoint={}".format(endpoint),
                )
                response = response.json()
                ENDPOINT_MAPPING_DICT[endpoint](response)
            except requests.exceptions.HTTPError as ex:
                self.log.error(
                    "NetApp ESeries SANtricity: Unsuccessful response: "  # noqa: G001
                    "status_code = {} response = {}".format(ex.response.status_code, ex.response.text),
                )
                self.log.exception(ex)
                self.ingest_service_check_and_event_for_auth(
                    is_authenticated=False,
                    reason=f"NetApp ESeries SANtricity: Unsuccessful response: status_code = {ex.response.status_code} \
                        response = {ex.response.text}",
                )
            except Exception as ex:
                self.log.error(
                    "NetApp ESeries SANtricity: Unexpected error while validation: {}".format(str(ex))  # noqa: G001
                )
                self.log.exception(ex)
                self.ingest_service_check_and_event_for_auth(
                    is_authenticated=False,
                    reason=f"NetApp ESeries SANtricity: Unexpected error while validation: {str(ex)}",
                )

        # data collection ended
        elapsed_seconds = time.time() - start_time
        self.log.info(
            "NetApp ESeries SANtricity: End of the data collection."  # noqa: G001
            " Total time taken: {:.3f} seconds".format(elapsed_seconds),
        )

    @staticmethod
    def get_headers():
        """Returns the request headers."""

        return {"Content-Type": "application/json"}

    def validateRequiredFields(self):
        """Valudate the required fields."""
        err_message = "NetApp ESeries SANtricity: Field {} is missing."

        req_fields = [
            "address",
            "username",
            "password",
            "verify_ssl",
            "system_id",
            "min_collection_interval",
        ]

        for field in req_fields:
            if self.instance.get(field) is None:
                err_msg = err_message.format(field)
                self.log.error(err_msg)
                raise ConfigurationError(err_msg)

        address = self.instance.get("address")
        parsed_url = urlparse.urlsplit(address)
        ip_port = address.split(":")

        if len(parsed_url.scheme) or len(ip_port) < 2 or (not ip_port[1]):
            err_message = f"NetApp ESeries SANtricity: address should be in valid format: IP address (without schema) \
                and port (separated by a colon). address={address}"
            self.log.error(err_message)
            raise ConfigurationError(err_message)

        intreval = self.instance.get("min_collection_interval")
        if not isinstance(intreval, int) or intreval <= 0:
            err_message = f"NetApp ESeries SANtricity: min_collection_interval should be integer and greater than 0. \
                min_collection_interval={intreval}"
            self.log.error(err_message)
            raise ConfigurationError(err_message)

    def setupSession(self):
        """To setup session."""
        self.get_base_url = consts.BASE_URL.format(self.instance.get("address"))
        self.conn = requests.Session()
        self.conn.auth = (self.instance.get("username"), self.instance.get("password"))
        self.conn.verify = self.instance.get("verify_ssl")
        self.conn.headers.update(self.get_headers())

    def authentication(self):
        """Validation of username and password."""

        try:
            self.getEndpoint()
            self.ingest_service_check_and_event_for_auth(is_authenticated=True)
            self.log.info("NetApp ESeries SANtricity: Successful authentication to Netapp Eseries Santricity.")
        except requests.exceptions.HTTPError as ex:
            self.log.error(
                "NetApp ESeries SANtricity: Unsuccessful response: status_code = {} response = {}".format(  # noqa: G001
                    ex.response.status_code, ex.response.text
                ),
            )
            self.log.exception(ex)
            self.ingest_service_check_and_event_for_auth(
                is_authenticated=False,
                reason=f"NetApp ESeries SANtricity: Unsuccessful response: status_code = {ex.response.status_code} \
                    response = {ex.response.text}",
            )
            raise ex
        except Exception as ex:
            self.log.error(
                "NetApp ESeries SANtricity: Unexpected error while validation: {}".format(str(ex))  # noqa: G001
            )
            self.log.exception(ex)
            self.ingest_service_check_and_event_for_auth(
                is_authenticated=False,
                reason=f"NetApp ESeries SANtricity: Unexpected error while validation: {str(ex)}",
            )
            raise ex

    def getResponse(self, url, params):
        """
        Check response from rest endpoint.

        :param response: response from rest endpoint
        :return:response in json format
        """
        response = None

        response = self.conn.get(url, params=params)
        response.raise_for_status()
        return response

    def getEndpoint(self, endpoint=None, params=None):
        """
        Get request to rest endpoint.

        :param endpoint: endpoint to request
        :param params:parameters to send with request
        :return:response from requested url
        """

        url = (
            self.get_base_url
            if endpoint is None
            else self.get_base_url + "/{}/{}".format(self.instance.get("system_id"), endpoint)
        )
        return self.getResponse(url, params)

    def ingest_service_check_and_event_for_auth(self, is_authenticated=None, reason=""):
        """
        Ingest Service Check and Event for authentication
        """
        msg = (
            ["Authentication successful", 0]
            if is_authenticated is True
            else [f"Authentication failed. Reason: {reason}", 2]
        )
        self.service_check(consts.AUTH_CHECK_NAME, msg[1], message=msg[0])
        self.event(
            {
                "source_type_name": consts.AUTH_EVENT_SOURCE_TYPE,
                "msg_title": "Authentication",
                "msg_text": msg[0],
            }
        )

    def set_configurations(self):
        """
        Set configurations for ingesting logs
        """
        api_key = datadog_agent.get_config("api_key")
        app_key = datadog_agent.get_config("app_key")
        log_index = self.instance.get("log_index")

        if api_key is None or app_key is None:
            err_message = "NetApp ESeries SANtricity: App Key or API Key is missing"
            self.log.error(err_message)
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
                "NetApp ESeries SANtricity: Could not connect to Datadog, App Key or API Key or Log Index is invalid"
            )
            self.log.exception(e)
            raise e

    @staticmethod
    def convert_in_GB(value):
        """Transfer the bytes to GB"""
        try:
            return round((int(value) / 1024 / 1024 / 1024), 2)
        except Exception:
            return "-"

    @staticmethod
    def convert_epoch_to_datetime(value):
        """Convert the epoch time into readable time format."""
        try:
            return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d")
        except Exception:
            return value

    # Graph Endpoint

    def ingest_array_configuration_summary(self, response):
        """Ingest the metrics for array configuration summary panel."""
        state = "Needs Attention" if response["sa"]["saData"].get("needsAttention") is True else "Healthy"
        summary_panel_list = ["volumeGroup", "volume", "drive", "tray", "controller"]
        array_summary_tag = [
            f"State:{state}",
            f'Repairing:{response["sa"]["saData"].get("fixing","-")}',
            f'BootTime:{self.convert_epoch_to_datetime(response["sa"]["saData"].get("bootTime", "-"))}',
            f"ModelName:{self.arrayName}",
        ]
        for panel in summary_panel_list:
            Utils.ingest_metric(
                self, "array.configuration." + panel + ".summary", int(len(response.get(panel))), array_summary_tag
            )

    def ingest_volume_group_and_disk_pool(self, response):
        """Ingest the logs for volume group and disk pool summary panels."""
        vol_grp = []
        disk_pool = []
        for volume_grp in response["volumeGroup"]:
            if volume_grp["volumeGroupData"].get("diskPoolData") is None:
                vol_grp.append(
                    {
                        "Volume Groups/Pools": volume_grp.get("label", "-"),
                        "State": volume_grp.get("state", "-"),
                        "Offline": volume_grp.get("offline", "-"),
                        "RAID Level": volume_grp.get("raidLevel", "-"),
                        "Encryption": volume_grp.get("securityType", "-"),
                        "Data Assurance": volume_grp["protectionInformationCapabilities"].get(
                            "protectionInformationCapable", "-"
                        ),
                        "Protection Type": volume_grp["protectionInformationCapabilities"].get("protectionType", "-"),
                        "Spindle RPM": volume_grp.get("spindleSpeed", "-"),
                        "Speeds Match": volume_grp.get("spindleSpeedMatch", "-"),
                        "Unallocated Capacity (GiB)": self.convert_in_GB(volume_grp.get("freeSpace", "-")),
                        "Allocated Capacity (GiB)": self.convert_in_GB(volume_grp.get("usedSpace", "-")),
                        "Total Capacity (GiB)": self.convert_in_GB(volume_grp.get("totalRaidedSpace", "-")),
                    }
                )
            if volume_grp["volumeGroupData"].get("type") == "diskPool":
                disk_pool.append(
                    {
                        "Disk Pool": volume_grp.get("label", "-"),
                        "State": volume_grp.get("state", "-"),
                        "Offline": volume_grp.get("offline", "-"),
                        "Encryption": volume_grp.get("securityType", "-"),
                        "Data Assurance": volume_grp["protectionInformationCapabilities"].get(
                            "protectionInformationCapable", "-"
                        ),
                        "Protection Type": volume_grp["protectionInformationCapabilities"].get("protectionType", "-"),
                        "Spindle RPM": volume_grp.get("spindleSpeed", "-"),
                        "Speeds Match": volume_grp.get("spindleSpeedMatch", "-"),
                        "Unallocated Capacity (GiB)": self.convert_in_GB(volume_grp.get("freeSpace", "-")),
                        "Allocated Capacity (GiB)": self.convert_in_GB(volume_grp.get("usedSpace", "-")),
                        "Total Capacity (GiB)": self.convert_in_GB(volume_grp.get("totalRaidedSpace", "-")),
                        "Background Priority": volume_grp["volumeGroupData"]["diskPoolData"].get(
                            "backgroundOperationPriority", "-"
                        ),
                        "Critical Reconstruct Priority": volume_grp["volumeGroupData"]["diskPoolData"].get(
                            "criticalReconstructPriority", "-"
                        ),
                        "Degraded Reconstruct Priority": volume_grp["volumeGroupData"]["diskPoolData"].get(
                            "degradedReconstructPriority", "-"
                        ),
                    }
                )
        Utils.ingest_logs(self, consts.GRAPH_SOURCE_TYPE + ".volume.groups", vol_grp)
        Utils.ingest_logs(self, consts.GRAPH_SOURCE_TYPE + ".disk.pools", disk_pool)

    def ingest_volumes(self, response):
        """Ingest the logs for volume summary panel."""
        volumes = []
        for volume in response["volume"]:
            volumes.append(
                {
                    "Volume": volume.get("label", "-"),
                    "Volume Groups/Pools": self.volume_group_mapping.get(volume.get("volumeGroupRef", "-"), "-"),
                    "Status": volume.get("status", "-"),
                    "Action": volume.get("action", "-"),
                    "Read Cache Active": volume["cache"].get("readCacheActive", "-"),
                    "Write Cache Active": volume["cache"].get("writeCacheActive", "-"),
                    "SSD Read cache": volume["perms"].get("flashReadCache", "-"),
                    "Volume Role": volume.get("volumeUse", "-"),
                    "RAID Level": volume.get("raidLevel", "-"),
                    "Capacity (GiB)": volume.get("capacity", "-"),
                    "Block Size": volume.get("blkSize", "-"),
                    "Current Controller": self.controller_mapping.get(volume.get("currentControllerId", "-"), "-"),
                    "Preferred Controller": self.controller_mapping.get(volume.get("preferredControllerId", "-"), "-"),
                    "Preferred": True
                    if volume.get("currentControllerId") == volume.get("preferredControllerId")
                    else False,
                }
            )

        Utils.ingest_logs(self, consts.GRAPH_SOURCE_TYPE + ".volumes", volumes)

    def ingest_drives(self, response):
        """Ingest the logs for drive summary panel."""
        drives = []
        for drive in response["drive"]:
            drives.append(
                {
                    "Location": self.drive_mapping.get(drive.get("driveRef", "-"))[0],
                    "Status": drive.get("status", "-"),
                    "Available": drive.get("available", "-"),
                    "Manufacturer": drive.get("manufacturer", "-"),
                    "Firmware": drive.get("softwareVersion", "-"),
                    "Drive Type": drive.get("driveMediaType", "-"),
                    "Interface": drive["interfaceType"].get("driveType", "-"),
                    "SSD Erase Count %": drive["ssdWearLife"].get("averageEraseCountPercent", "-")
                    if drive.get("driveMediaType").upper() == "SSD"
                    else "-",
                    "SSD Spare Blocks %": drive["ssdWearLife"].get("spareBlocksRemainingPercent", "-")
                    if drive.get("driveMediaType").upper() == "SSD"
                    else "-",
                    "Spindle RPM": drive.get("spindleSpeed", "-"),
                    "Current Speed": drive.get("currentSpeed", "-"),
                    "Max Speed": drive.get("maxSpeed", "-"),
                    "Drive Temp": drive["driveTemperature"].get("currentTemp", "-"),
                    "Usable Capacity (GiB)": self.convert_in_GB(drive.get("usableCapacity", "-")),
                    "Raw Capacity (GiB)": self.convert_in_GB(drive.get("rawCapacity", "-")),
                }
            )

        Utils.ingest_logs(self, consts.GRAPH_SOURCE_TYPE + ".drives", drives)

    def ingest_graph_data(self, response):
        """Iterate the graph data and ingest the metrics and logs."""
        self.arrayName = (
            response["sa"]["saData"]["storageArrayLabel"]
            if response["sa"]["saData"]["storageArrayLabel"]
            else self.instance.get("system_id")
        )
        self.controller_mapping = {"-": "-"}
        self.volume_group_mapping = {"-": "-"}
        self.drive_mapping = {"-": ["-", "-"]}
        for controller in response["controller"]:
            self.controller_mapping[controller.get("controllerRef")] = controller["physicalLocation"].get("label", "-")

        for volume_group in response["volumeGroup"]:
            self.volume_group_mapping[volume_group.get("volumeGroupRef")] = volume_group.get("label", "-")

        for drive in response["drive"]:
            self.drive_mapping[drive.get("driveRef")] = [
                drive["physicalLocation"].get("label", "-"),
                self.volume_group_mapping.get(drive.get("currentVolumeGroupRef", "-")),
            ]

        self.ingest_array_configuration_summary(response)
        self.ingest_volume_group_and_disk_pool(response)
        self.ingest_volumes(response)
        self.ingest_drives(response)

    # Volume Endpoint

    def ingest_volume_data(self, response):
        """Iterate the volume data and ingest the metrics."""
        volumegrp_and_cntrlr_panel_list = [
            "readIOps",
            "writeIOps",
            "readResponseTime",
            "writeResponseTime",
            "readThroughput",
            "writeThroughput",
        ]
        cache_hits_penel_list = ["readHitOps", "writeHitOps", "readHitBytes", "writeHitBytes"]
        for res in response:
            metric_tags_by_volume_group = [
                f"arrayName:{self.arrayName}",
                f'controllerLabel:{self.controller_mapping.get(res.get("sourceController","-"))}',
                f'volumeGroup:{self.volume_group_mapping.get(res.get("poolId","-"))}',
            ]
            metric_tags_by_volume = [
                f"arrayName:{self.arrayName}",
                f'controllerLabel:{self.controller_mapping.get(res.get("sourceController","-"))}',
                f'volumeGroup:{self.volume_group_mapping.get(res.get("poolId","-"))}',
                f'volumeName:{res.get("volumeName","-")}',
            ]
            for panel in volumegrp_and_cntrlr_panel_list:
                Utils.ingest_metric(
                    self,
                    "performance.controller." + panel + ".byvolumegrp",
                    int(res.get(panel)),
                    metric_tags_by_volume_group,
                )
                Utils.ingest_metric(
                    self, "performance.volumegrp." + panel + ".byvolume", int(res.get(panel)), metric_tags_by_volume
                )
            for panel in cache_hits_penel_list:
                Utils.ingest_metric(
                    self, "performance.cachehits." + panel + ".byvolume", int(res.get(panel)), metric_tags_by_volume
                )

    # Drive Endpoint

    def ingest_drive_data(self, response):
        """Iterate the drive data and ingest the metrics."""
        array_by_cntrlr_panel_list = [
            "readIOps",
            "writeIOps",
            "readResponseTime",
            "writeResponseTime",
            "readThroughput",
            "writeThroughput",
        ]
        for res in response:
            metric_tags_by_volume_group = [
                f"arrayName:{self.arrayName}",
                f'volumeGroup:{self.drive_mapping.get(res.get("diskId","-"))[1]}',
                f'driveLabel:{self.drive_mapping.get(res.get("diskId","-"))[0]}',
            ]
            for panel in array_by_cntrlr_panel_list:
                Utils.ingest_metric(
                    self,
                    "performance.volumegrp." + panel + ".bydrive",
                    int(res.get(panel)),
                    metric_tags_by_volume_group,
                )

    # Controller Endpoint

    def ingest_controller_data(self, response):
        """Iterate the controller data and ingest the metrics."""
        array_by_cntrlr_panel_list = [
            "readIOps",
            "writeIOps",
            "readResponseTime",
            "writeResponseTime",
            "readThroughput",
            "writeThroughput",
        ]
        for res in response:
            metric_tags_by_volume_group = [
                f"arrayName:{self.arrayName}",
                f'controllerLabel:{self.controller_mapping.get(res.get("controllerId","-"))}',
            ]
            for panel in array_by_cntrlr_panel_list:
                Utils.ingest_metric(
                    self,
                    "performance.array." + panel + ".bycontroller",
                    int(res.get(panel)),
                    metric_tags_by_volume_group,
                )
            Utils.ingest_metric(
                self,
                "performance.array.cpuAvgUtilizationPerCore.bycontroller",
                int(res.get("cpuAvgUtilizationPerCore")[0]),
                metric_tags_by_volume_group,
            )

    # Interface Endpoint

    def ingest_interface_data(self, response):
        """Iterate the interface data and ingest the metrics."""
        array_by_drive_panel_list = [
            "readIOps",
            "writeIOps",
            "readResponseTime",
            "writeResponseTime",
            "readThroughput",
            "writeThroughput",
        ]
        controllername_mapping = {"1": "A"}
        for res in response:
            if res.get("channelType") == "driveside" or res.get("channelType") == "hostside":
                metric_tags_by_volume_group = [
                    f"arrayName:{self.arrayName}",
                    f'controllerName:{controllername_mapping.get(res.get("interfaceId")[3],"B")}',
                    f'channelNumber:{res.get("channelNumber","-")}',
                ]
                for panel in array_by_drive_panel_list:
                    Utils.ingest_metric(
                        self,
                        "performance.array." + panel + ".by" + str(res.get("channelType")[:-4]) + ".channel",
                        int(res.get(panel)),
                        metric_tags_by_volume_group,
                    )
