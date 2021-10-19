"""Module for Node, Cluster Overview and Cluster Inventory"""
from .cds_dell_emc_consts import INTEGRATION_PREFIX


class CDSDellEMCNdCoCiHelper(object):
    """Class for Disk Usage and Node Details panels"""

    def __init__(self):
        self.co_prefix = "{}{}".format(INTEGRATION_PREFIX, "cluster_overview.")
        self.nd_prefix = "{}{}".format(INTEGRATION_PREFIX, "node_details.")
        self.ci_prefix = "{}{}".format(INTEGRATION_PREFIX, "cluster_inventory.")

    def co_disk_usage(self, response_json):
        """Method to get Disk Usage."""
        metric_prefix = "{}disk_usage".format(self.co_prefix)
        metric_list = list()
        for statistics in response_json.get("stats", []):
            disk_type = statistics.get("key", "")
            disk_type_tags_dict = {
                "ifs.bytes.avail": "disk-type-with-usage:HDD-AVAILABLE",
                "ifs.bytes.used": "disk-type-with-usage:HDD-USED",
                "ifs.ssd.bytes.free": "disk-type-with-usage:SSD-AVAILABLE",
                "ifs.ssd.bytes.used": "disk-type-with-usage:SSD-USED",
            }
            if disk_type in list(disk_type_tags_dict.keys()):
                metric_value = round((statistics.get("value", 0) / (1024 * 1024 * 1024)), 2)
                metric_list.append(
                    [
                        metric_prefix,
                        metric_value,
                        [INTEGRATION_PREFIX + disk_type_tags_dict.get(disk_type, "")],
                    ]
                )
        return metric_list

    def nd_disk_usage_over_time(self, response_json):
        """Method to get Disk Usage Over Time."""
        metric_prefix = "{}disk_usage_over_time".format(self.nd_prefix)
        metric_list = list()
        disk_details = {}
        for statistics in response_json.get("stats", []):
            node_id = statistics.get("devid")
            value = statistics.get("value")
            disk_type = statistics.get("key", "")

            if node_id is None or value is None:
                continue

            if disk_type == "node.ifs.bytes.used":
                if node_id not in disk_details:
                    disk_details[node_id] = {"used": value}
                else:
                    disk_details[node_id]["used"] = value

            if disk_type == "node.ifs.bytes.total":
                if node_id not in disk_details:
                    disk_details[node_id] = {"total": value}
                else:
                    disk_details[node_id]["total"] = value

        for node_id, disk_usage in disk_details.items():
            usage = disk_usage.get("used", 0) * 100 / disk_usage.get("total", 1)
            list_tag = [INTEGRATION_PREFIX + "node:node-%s" % node_id]
            metric_list.append([metric_prefix, usage, list_tag])
        return metric_list

    def nd_disk_usage(self, response_json):
        """Method to get Disk Usage."""
        metric_prefix = "{}disk_usage".format(self.nd_prefix)
        metric_list = list()
        disk_details = {}
        for statistics in response_json.get("stats", []):
            disk_detail = {
                "hdd-free": None,
                "hdd-used": None,
                "ssd-free": None,
                "ssd-used": None,
            }
            node_id = statistics.get("devid")
            value = statistics.get("value")
            disk_type = statistics.get("key", "")

            if node_id is None or value is None:
                continue

            if node_id not in disk_details:
                disk_details[node_id] = disk_detail

            if disk_type == "node.ifs.bytes.free":
                disk_details[node_id]["hdd-free"] = value

            if disk_type == "node.ifs.bytes.used":
                disk_details[node_id]["hdd-used"] = value

            if disk_type == "node.ifs.ssd.bytes.free":
                disk_details[node_id]["ssd-free"] = value

            if disk_type == "node.ifs.ssd.bytes.used":
                disk_details[node_id]["ssd-used"] = value

        for node_id, disk_usage in disk_details.items():
            if set(list(disk_usage.values())) == {None}:
                continue
            for key, value in disk_usage.items():
                final_value = round((value / (1024 * 1024 * 1024)), 2)
                metric_list.append(
                    [
                        metric_prefix,
                        final_value,
                        [
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                            INTEGRATION_PREFIX + "usage:%s" % key,
                        ],
                    ]
                )
        return metric_list

    def co_cluster_disk_usage_over_time(self, response_json):
        """Method to get Cluster Disk Usage Over Time."""
        metric_prefix = "{}cluster_disk_usage_over_time".format(self.co_prefix)
        metric_list = list()
        for statistics in response_json.get("stats", []):
            key = statistics.get("key", "")
            if key == "ifs.percent.used":
                metric_value = round(statistics.get("value", 0.00), 2)
                metric_list.append([metric_prefix, metric_value, []])
        return metric_list

    def ci_node_details(self, response_json):
        """Method to get Node Details."""
        metric_prefix = "{}".format(self.ci_prefix)
        metric_list = list()
        node_details = {}
        for statistics in response_json.get("stats", []):
            node_detail = {
                "bytes.in.rate": None,
                "bytes.out.rate": None,
                "bytes.total": None,
                "bytes.used": None,
                "ssd.bytes.total": None,
                "ssd.bytes.used": None,
                "total-b/s": None,
                "hdd-used-percentage": None,
                "ssd-used-percentage": None,
            }
            node_id = statistics.get("devid")
            value = statistics.get("value")
            disk_type = statistics.get("key", "")
            required_keys = [
                "node.ifs.bytes.in.rate",
                "node.ifs.bytes.out.rate",
                "node.ifs.bytes.total",
                "node.ifs.bytes.used",
                "node.ifs.ssd.bytes.total",
                "node.ifs.ssd.bytes.used",
            ]

            if node_id is None or value is None:
                continue
            if node_id not in node_details:
                node_details[node_id] = node_detail

            if disk_type in required_keys:
                node_details[node_id][disk_type.replace("node.ifs.", "")] = round(value / 1024, 2)

        for node_id, node_detail in node_details.items():
            if set(list(node_detail.values())) == {None}:
                continue

            node_detail["total-b/s"] = node_detail["bytes.in.rate"] + node_detail["bytes.out.rate"]
            node_detail["hdd-used-percentage"] = (
                0.0
                if node_detail["bytes.total"] == 0
                else round(
                    (node_detail["bytes.used"] / node_detail["bytes.total"]) * 100,
                    2,
                )
            )
            node_detail["ssd-used-percentage"] = (
                0.0
                if node_detail["ssd.bytes.total"] == 0
                else round(
                    (node_detail["ssd.bytes.used"] / node_detail["ssd.bytes.total"]) * 100,
                    2,
                )
            )

            list_tag = [INTEGRATION_PREFIX + "node:node-%s" % node_id]

            metric_list.append(
                [
                    metric_prefix + "node_details.in_bytes",
                    node_detail["bytes.in.rate"],
                    list_tag,
                ]
            )

            metric_list.append(
                [
                    metric_prefix + "node_details.out_bytes",
                    node_detail["bytes.out.rate"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "node_details.total_bytes",
                    node_detail["total-b/s"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "node_details.hdd_size",
                    node_detail["bytes.total"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "node_details.hdd_used_percentage",
                    node_detail["hdd-used-percentage"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "node_details.ssd_size",
                    node_detail["ssd.bytes.total"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "node_details.ssd_used_percentage",
                    node_detail["ssd-used-percentage"],
                    list_tag,
                ]
            )
        return metric_list
