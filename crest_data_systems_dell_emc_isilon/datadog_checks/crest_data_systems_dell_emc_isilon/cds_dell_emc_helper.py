"""Module for Helper of Dashboards"""
from .cds_dell_emc_consts import INTEGRATION_PREFIX


class CDSDellEMCHelper(object):
    """Class for CPU, Memory Usage and Throughput details panels"""

    def __init__(self):
        self.co_prefix = "{}{}".format(INTEGRATION_PREFIX, "cluster_overview.")
        self.nd_prefix = "{}{}".format(INTEGRATION_PREFIX, "node_details.")
        self.fs_prefix = "{}{}".format(INTEGRATION_PREFIX, "file_system_performance.")

    def co_file_system_throughput_ot(self, response_json):
        """Method to get File System Throughput Over Time."""
        metric_prefix = "{}file_system_throughput_over_time".format(self.co_prefix)
        metric_list = list()
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            metric_value = round((statistics.get("value", 0) * 8) / (1000 * 1000), 2)
            node_id = statistics.get("devid")
            if key is None or node_id is None:
                continue
            key_type_tags_dict = {
                "node.ifs.bytes.in.rate": "traffic-type:INBOUND",
                "node.ifs.bytes.out.rate": "traffic-type:OUTBOUND",
            }
            if key in list(key_type_tags_dict.keys()):
                metric_list.append(
                    [
                        metric_prefix,
                        metric_value,
                        [
                            INTEGRATION_PREFIX + key_type_tags_dict.get(key, ""),
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                        ],
                    ]
                )
        return metric_list

    def co_ex_nw_throughput_rate_ot(self, response_json):
        """Method to get External Network Throughput Over Time."""
        metric_prefix = "{}external_network_throughput_rate_over_time".format(self.co_prefix)
        metric_list = list()
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            metric_value = round((statistics.get("value", 0) * 8) / (1024 * 1024), 2)
            node_id = statistics.get("devid")
            if key is None or node_id is None:
                continue
            key_type_tags_dict = {
                "node.net.ext.bytes.in.rate": "traffic-type:INBOUND",
                "node.net.ext.bytes.out.rate": "traffic-type:OUTBOUND",
            }
            if key in list(key_type_tags_dict.keys()):
                metric_list.append(
                    [
                        metric_prefix,
                        metric_value,
                        [
                            INTEGRATION_PREFIX + key_type_tags_dict.get(key, ""),
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                        ],
                    ]
                )
        return metric_list

    def fsp_fs_performance_by_node_ot(self, response_json):
        """Method to get File System Performance By Node Over Time."""
        metric_prefix = "{}file_system_performance_by_node_over_time".format(self.fs_prefix)
        metric_list = list()
        disk_details = {}
        for statistics in response_json.get("stats", []):
            disk_detail = {"in-rate": None, "out-rate": None}
            node_id = statistics.get("devid")
            metric_value = statistics.get("value")
            disk_type = statistics.get("key", "")

            if node_id is None or metric_value is None:
                continue

            if node_id not in disk_details:
                disk_details[node_id] = disk_detail

            if disk_type == "node.ifs.bytes.out.rate":
                disk_details[node_id]["out-rate"] = metric_value

            if disk_type == "node.ifs.bytes.in.rate":
                disk_details[node_id]["in-rate"] = metric_value

        for node_id, disk_usage in disk_details.items():
            for key, metric_value in disk_usage.items():
                final_value = metric_value * 8 / (1024 * 1024)
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

    def nd_external_network_throughput(self, response_json):
        """Method to get External Network Throughput."""
        metric_prefix = "{}external_network_throughput".format(self.nd_prefix)
        metric_list = list()
        disk_details = {}
        for statistics in response_json.get("stats", []):
            disk_detail = {
                "in-rate": None,
                "out-rate": None,
            }
            node_id = statistics.get("devid")
            metric_value = statistics.get("value")
            disk_type = statistics.get("key", "")

            if node_id is None or metric_value is None:
                continue

            if node_id not in disk_details:
                disk_details[node_id] = disk_detail

            if disk_type == "node.net.ext.bytes.in.rate":
                disk_details[node_id]["in-rate"] = metric_value

            if disk_type == "node.net.ext.bytes.out.rate":
                disk_details[node_id]["out-rate"] = metric_value

        for node_id, disk_usage in disk_details.items():
            usage = round(
                (disk_usage.get("in-rate", 0) + disk_usage.get("out-rate", 0)) * 8 / (1024 * 1024),
                2,
            )
            metric_list.append([metric_prefix, usage, [INTEGRATION_PREFIX + "node:node-%s" % node_id]])
        return metric_list

    def nd_file_system_throughput(self, response_json):
        """Method to get File System Throughput."""
        metric_prefix = "{}file_system_throughput".format(self.nd_prefix)
        metric_list = list()
        disk_details = {}
        for statistics in response_json.get("stats", []):
            disk_detail = {
                "inbound": None,
                "outbound": None,
            }
            node_id = statistics.get("devid")
            metric_value = statistics.get("value")
            disk_type = statistics.get("key", "")

            if node_id is None or metric_value is None:
                continue

            if node_id not in disk_details:
                disk_details[node_id] = disk_detail

            if disk_type == "node.ifs.bytes.in.rate":
                disk_details[node_id]["inbound"] = metric_value

            if disk_type == "node.ifs.bytes.out.rate":
                disk_details[node_id]["outbound"] = metric_value

        for node_id, disk_usage in disk_details.items():
            for key, metric_value in disk_usage.items():
                usage = round((metric_value * 8 / (1000 * 1000)), 2)
                metric_list.append(
                    [
                        metric_prefix,
                        usage,
                        [
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                            INTEGRATION_PREFIX + "usage:%s" % key,
                        ],
                    ]
                )
        return metric_list

    def nd_cpu_usage_over_time(self, response_json):
        """Method to get CPU Usage Over Time."""
        metric_prefix = "{}cpu_usage_over_time".format(self.nd_prefix)
        metric_list = list()
        disk_details = {}
        for statistics in response_json.get("stats", []):
            disk_detail = {"system": None, "user": None}
            node_id = statistics.get("devid")
            value = statistics.get("value")
            disk_type = statistics.get("key", "")

            if node_id is None or value is None:
                continue

            if node_id not in disk_details:
                disk_details[node_id] = disk_detail

            if disk_type == "node.cpu.sys.max":
                disk_details[node_id]["system"] = value

            if disk_type == "node.cpu.user.max":
                disk_details[node_id]["user"] = value

        for node_id, disk_usage in disk_details.items():
            for key, value in disk_usage.items():
                usage = round((value / 10), 1)
                metric_list.append(
                    [
                        metric_prefix,
                        usage,
                        [
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                            INTEGRATION_PREFIX + "cpu-usage:%s" % key,
                        ],
                    ]
                )
        return metric_list

    def nd_memory_usage(self, response_json):
        """Method to get Memory Usage."""
        metric_prefix = "{}memory_usage".format(self.nd_prefix)
        metric_list = list()
        disk_details = {}
        for statistics in response_json.get("stats", []):
            disk_detail = {
                "memory-free": None,
                "memory-used": None,
            }
            node_id = statistics.get("devid")
            value = statistics.get("value")
            disk_type = statistics.get("key", "")

            if node_id is None or value is None:
                continue

            if node_id not in disk_details:
                disk_details[node_id] = disk_detail

            if disk_type == "node.memory.used":
                disk_details[node_id]["memory-free"] = value

            if disk_type == "node.memory.free":
                disk_details[node_id]["memory-used"] = value

        for node_id, disk_usage in disk_details.items():
            for key, value in disk_usage.items():
                usage_in_gb = round((value / (1024 * 1024 * 1024)), 2)
                metric_list.append(
                    [
                        metric_prefix,
                        usage_in_gb,
                        [
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                            INTEGRATION_PREFIX + "usage:%s" % key,
                        ],
                    ]
                )
        return metric_list
