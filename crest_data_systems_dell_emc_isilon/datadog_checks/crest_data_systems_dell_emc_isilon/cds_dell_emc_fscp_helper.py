"""Module for File System Cache Performance"""
from .cds_dell_emc_consts import INTEGRATION_PREFIX


class CDSDellEMCFscpHelper(object):
    """Class for File System Cache Performance panels"""

    def __init__(self):
        self.fscp_prefix = "{}{}".format(INTEGRATION_PREFIX, "file_system_cache_performance.")

    def fscp_fs_cached_data_age(self, response_json):
        """Method to get File System Cached Data Age."""
        metric_prefix = "{}file_system_cached_data_age".format(self.fscp_prefix)
        metric_list = list()
        node_data = {}
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            node_id = statistics.get("devid")
            if key is None or node_id is None:
                continue
            if key == "node.ifs.cache.oldest_page_age" and node_id not in node_data:
                node_data[node_id] = statistics.get("value", 0)

        for node_id, cached_data_age in node_data.items():
            metric_list.append(
                [
                    metric_prefix,
                    round(cached_data_age / (60 * 60), 2),
                    [INTEGRATION_PREFIX + "node:node-%s" % node_id],
                ]
            )

        return metric_list

    def fscp_l2_cache_hit_rate(self, response_json):
        """Method to get L2 Cache Hit Rate."""
        metric_prefix = "{}l2_cache_hit_rate".format(self.fscp_prefix)
        metric_list = list()
        node_data = {}
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            node_id = statistics.get("devid")
            if key is None or node_id is None:
                continue
            if key == "node.ifs.cache.l2.data.read.hit" and node_id not in node_data:
                node_data[node_id] = statistics.get("value", 0)

        for node_id, l2_cache_hit_rate in node_data.items():
            metric_list.append(
                [
                    metric_prefix,
                    round((l2_cache_hit_rate * 8) / (1024 * 1024), 2),
                    [INTEGRATION_PREFIX + "node:node-%s" % node_id],
                ]
            )

        return metric_list

    def fscp_l2_cache_miss_rate(self, response_json):
        """Method to get L2 Cache Miss Rate."""
        metric_prefix = "{}l2_cache_miss_rate".format(self.fscp_prefix)
        metric_list = list()
        node_data = {}
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            node_id = statistics.get("devid")
            if key is None or node_id is None:
                continue
            if key == "node.ifs.cache.l2.data.read.miss" and node_id not in node_data:
                node_data[node_id] = statistics.get("value", 0)

        for node_id, l2_cache_miss_rate in node_data.items():
            metric_list.append(
                [
                    metric_prefix,
                    round((l2_cache_miss_rate * 8) / (1024 * 1024), 2),
                    [INTEGRATION_PREFIX + "node:node-%s" % node_id],
                ]
            )

        return metric_list

    def fscp_l2_cache_read_wait_time(self, response_json):
        """Method to get L2 Cache Read Wait Time."""
        metric_prefix = "{}l2_cache_read_wait_time".format(self.fscp_prefix)
        metric_list = list()
        node_data = {}
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            node_id = statistics.get("devid")
            if key is None or node_id is None:
                continue
            if key == "node.ifs.cache.l2.data.read.wait" and node_id not in node_data:
                node_data[node_id] = statistics.get("value", 0)

        for node_id, l2_cache_read_wait_time in node_data.items():
            metric_list.append(
                [
                    metric_prefix,
                    round((l2_cache_read_wait_time * 8) / (1024 * 1024), 2),
                    [INTEGRATION_PREFIX + "node:node-%s" % node_id],
                ]
            )

        return metric_list

    def fscp_l2_cache_prefetch_hit_rate(self, response_json):
        """Method to get L2 Cache Prefetch Hit Rate."""
        metric_prefix = "{}l2_cache_prefetch_hit_rate".format(self.fscp_prefix)
        metric_list = list()
        node_data = {}
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            node_id = statistics.get("devid")
            if key is None or node_id is None:
                continue
            if key == "node.ifs.cache.l2.data.prefetch.hit" and node_id not in node_data:
                node_data[node_id] = statistics.get("value", 0)

        for node_id, l2_cache_prefetch_hit_rate in node_data.items():
            metric_list.append(
                [
                    metric_prefix,
                    round((l2_cache_prefetch_hit_rate * 8) / (1024 * 1024), 2),
                    [INTEGRATION_PREFIX + "node:node-%s" % node_id],
                ]
            )

        return metric_list
