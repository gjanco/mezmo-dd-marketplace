"""Module for Cluster Overview"""
from .cds_dell_emc_consts import INTEGRATION_PREFIX


class CDSDellEMCCoHelper(object):
    """Class for CPU Usage Panel"""

    def __init__(self):
        self.co_prefix = "{}{}".format(INTEGRATION_PREFIX, "cluster_overview.")

    def co_cpu_usage_over_time(self, response_json):
        """Method for CPU Usage over time"""
        metric_prefix = "{}cpu_usage_over_time".format(self.co_prefix)
        metric_list = list()
        for statistics in response_json.get("stats", []):
            key = statistics.get("key", "")
            key_type_tags_dict = {
                "cluster.cpu.user.max": "used-by:USER",
                "cluster.cpu.sys.max": "used-by:SYSTEM",
            }
            if key in list(key_type_tags_dict.keys()):
                metric_value = round(statistics.get("value", 0) / 10, 1)
                metric_list.append(
                    [
                        metric_prefix,
                        metric_value,
                        [INTEGRATION_PREFIX + key_type_tags_dict.get(key, "")],
                    ]
                )
        return metric_list
