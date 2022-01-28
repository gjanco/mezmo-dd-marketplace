"""Module for Cluster Infromation"""
import calendar
import datetime
import time

from .cds_dell_emc_consts import INTEGRATION_PREFIX


class CDSDellEMCCiHelper(object):
    """Class for Disk Details Panels"""

    def __init__(self):
        self.ci_prefix = "{}{}".format(INTEGRATION_PREFIX, "cluster_inventory.")

    def ci_storage_drive_details(self, response_json):
        """Method to get Hard Drive Details."""
        metric_prefix = "{}storage_drive_details".format(self.ci_prefix)
        metric_list = list()
        disk_details = prepare_disk_details(response_json)

        for disk_index, nodes in disk_details.items():

            for node_id, disk_detail in nodes.items():

                logical_number = disk_detail.get("lnum", "")
                bay_name = disk_detail.get("name", "")
                bay_name = bay_name.replace(" ", "-") if bay_name else ""
                metric_list.append(
                    [
                        metric_prefix,
                        disk_index,
                        [
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                            INTEGRATION_PREFIX + "status:%s" % disk_detail.get("health", ""),
                            INTEGRATION_PREFIX + "logical-number:%s" % logical_number,
                            INTEGRATION_PREFIX + "bay:%s" % bay_name,
                            INTEGRATION_PREFIX + "type:%s" % disk_detail.get("type", ""),
                            INTEGRATION_PREFIX + "hdd-time:%s" % disk_detail.get("time", ""),
                        ],
                    ]
                )
        return metric_list


def prepare_disk_details(response_json):
    """Used to prepare Disk Details Object"""
    disk_health = {
        "0": "Healthy",
        "1": "Drive not pre-formatted",
        "-1": "Drive not detected in bay",
        "6": "Drive not in use by cluster",
    }
    disk_details = {}
    for statistics in response_json.get("stats", []):
        node_id = statistics.get("devid")
        utc_timestamp = (
            datetime.datetime.utcfromtimestamp(statistics.get("time", calendar.timegm(time.gmtime()))).strftime(
                "%Y-%m-%d %H:%M:%S %p"
            )
            + " (UTC)"
        )

        key = statistics.get("key")
        splitted_key = key.split(".")
        if not key or len(splitted_key) != 4 or not node_id:
            continue

        disk_index = splitted_key[3]
        disk_key = splitted_key[2]
        value = (
            statistics.get("value", "")
            if disk_key != "health"
            else disk_health.get(str(statistics.get("value", "")), "")
        )
        if disk_index in disk_details:
            if node_id in disk_details[disk_index]:
                disk_details[disk_index][node_id][disk_key] = value
                disk_details[disk_index][node_id]["time"] = utc_timestamp
            else:
                disk_details[disk_index][node_id] = {
                    disk_key: value,
                    "time": utc_timestamp,
                }
        else:
            disk_details[disk_index] = {node_id: {disk_key: value, "time": utc_timestamp}}

    return disk_details
