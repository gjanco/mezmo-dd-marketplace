"""Module for Node Details"""
from .cds_dell_emc_consts import INTEGRATION_PREFIX


class CDSDellEMCNdHelper(object):
    """Class for Client Connections and Event Rate panels"""

    def __init__(self):
        self.co_prefix = "{}{}".format(INTEGRATION_PREFIX, "cluster_overview.")
        self.pd_prefix = "{}{}".format(INTEGRATION_PREFIX, "protocol_details.")
        self.fs_prefix = "{}{}".format(INTEGRATION_PREFIX, "file_system_performance.")
        self.nd_prefix = "{}{}".format(INTEGRATION_PREFIX, "node_details.")

    def co_client_connections_over_time(self, response_json):
        """Method to get Client COnnections Over Time."""
        metric_prefix = "{}client_connections_over_time".format(self.co_prefix)
        metric_list = list()
        node_data = {}
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            node_id = statistics.get("devid")
            if key is None or len(key.split(".")) != 4 or node_id is None:
                continue

            protocol = key.split(".")[3]
            if key == "node.clientstats.connected." + protocol:
                node_data[node_id] = node_data.get(node_id, 0) + statistics.get("value", 0)

        for node_id, metric_value in node_data.items():
            tags = [INTEGRATION_PREFIX + "node:node-%s" % node_id]
            metric_list.append([metric_prefix, metric_value, tags])

        return metric_list

    def pd_client_connections(self, response_json):
        """Method to get Client Connections."""
        metric_prefix = "{}client_connections".format(self.pd_prefix)
        metric_list = list()
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            node_id = statistics.get("devid")

            if key is None or len(key.split(".")) != 4 or node_id is None:
                continue

            metric_value = statistics.get("value")
            protocol = key.split(".")[3]

            if key == "node.clientstats.active." + protocol:
                metric_list.append(
                    [
                        metric_prefix,
                        metric_value,
                        [
                            INTEGRATION_PREFIX + "protocol:%s" % protocol,
                            INTEGRATION_PREFIX + "connection-type:active",
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                        ],
                    ]
                )

            if key == "node.clientstats.connected." + protocol:
                metric_list.append(
                    [
                        metric_prefix,
                        metric_value,
                        [
                            INTEGRATION_PREFIX + "protocol:%s" % protocol,
                            INTEGRATION_PREFIX + "connection-type:connected",
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                        ],
                    ]
                )
        return metric_list

    def fsp_event_rate_by_node_ot(self, response_json):
        """
        Method to get Event Rate By Node Over Time For Critical Events.
        """
        metric_prefix = "{}event_rate_by_node_over_time_for_critical_events".format(self.fs_prefix)
        metric_list = list()
        disk_details = {}

        for statistics in response_json.get("stats", []):
            disk_detail = {
                "blocked": None,
                "contended": None,
                "locked": None,
                "deadlocked": None,
            }
            node_id = statistics.get("devid")
            metric_value = statistics.get("value")
            disk_type = statistics.get("key", "")

            if node_id is None or metric_value is None:
                continue

            if node_id not in disk_details:
                disk_details[node_id] = disk_detail

            if disk_type == "node.ifs.heat.lock.total":
                disk_details[node_id]["locked"] = metric_value

            if disk_type == "node.ifs.heat.contended.total":
                disk_details[node_id]["contended"] = metric_value

            if disk_type == "node.ifs.heat.deadlocked.total":
                disk_details[node_id]["deadlocked"] = metric_value

            if disk_type == "node.ifs.heat.blocked.total":
                disk_details[node_id]["blocked"] = metric_value

        for node_id, disk_usage in disk_details.items():
            for key, metric_value in disk_usage.items():
                metric_list.append(
                    [
                        metric_prefix,
                        metric_value,
                        [
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                            INTEGRATION_PREFIX + "usage:%s" % key,
                        ],
                    ]
                )
        return metric_list

    def fsp_event_rate_by_type_ot(self, response_json):
        """Method to get Event Rate By Event Type Over Time."""
        metric_prefix = "{}event_rate_by_event_type_over_time".format(self.fs_prefix)
        metric_list = list()

        disk_details = {}

        for statistics in response_json.get("stats", []):
            disk_detail = {
                "getattr": None,
                "link": None,
                "lookup": None,
                "read": None,
                "rename": None,
                "setattr": None,
                "unlink": None,
                "write": None,
            }
            key = statistics.get("key")
            node_id = statistics.get("devid")
            metric_value = statistics.get("value")
            required_keys = [
                "node.ifs.heat.getattr.total",
                "node.ifs.heat.link.total",
                "node.ifs.heat.lookup.total",
                "node.ifs.heat.read.total",
                "node.ifs.heat.rename.total",
                "node.ifs.heat.setattr.total",
                "node.ifs.heat.unlink.total",
                "node.ifs.heat.write.total",
            ]
            if key is None or node_id is None or metric_value is None:
                continue

            if node_id not in disk_details:
                disk_details[node_id] = disk_detail

            if key in required_keys:
                disk_details[node_id][key.split(".")[3]] = metric_value

        for node_id, disk_usage in disk_details.items():
            for key, metric_value in disk_usage.items():
                metric_list.append(
                    [
                        metric_prefix,
                        metric_value,
                        [
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                            INTEGRATION_PREFIX + "usage:%s" % key,
                        ],
                    ]
                )

        return metric_list

    def fsp_file_system_critical_events(self, response_json):
        """Method to get File System Critical Events."""
        metric_prefix = "{}file_system_critical_events".format(self.fs_prefix)
        metric_list = list()
        disk_details = {}
        for statistics in response_json.get("stats", []):
            disk_detail = {
                "blocked": None,
                "contended": None,
                "locked": None,
                "deadlocked": None,
            }
            node_id = statistics.get("devid")
            metric_value = statistics.get("value")
            disk_type = statistics.get("key", "")

            if node_id is None or metric_value is None:
                continue

            if node_id not in disk_details:
                disk_details[node_id] = disk_detail

            if disk_type == "node.ifs.heat.lock.total":
                disk_details[node_id]["locked"] = metric_value

            if disk_type == "node.ifs.heat.contended.total":
                disk_details[node_id]["contended"] = metric_value

            if disk_type == "node.ifs.heat.deadlocked.total":
                disk_details[node_id]["deadlocked"] = metric_value

            if disk_type == "node.ifs.heat.blocked.total":
                disk_details[node_id]["blocked"] = metric_value

        for node_id, disk_usage in disk_details.items():
            for key, metric_value in disk_usage.items():
                metric_list.append(
                    [
                        metric_prefix,
                        metric_value,
                        [
                            INTEGRATION_PREFIX + "node:node-%s" % node_id,
                            INTEGRATION_PREFIX + "event-rate:%s" % key,
                        ],
                    ]
                )
        return metric_list
