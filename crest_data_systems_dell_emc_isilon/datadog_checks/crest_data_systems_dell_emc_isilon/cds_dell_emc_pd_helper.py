"""Module for Protocol Details"""
from .cds_dell_emc_consts import INTEGRATION_PREFIX


class CDSDellEMCPdHelper(object):
    """Class for Protocol Details panels"""

    def __init__(self):
        self.pd_prefix = "{}{}".format(INTEGRATION_PREFIX, "protocol_details.")

    def pd_operations_rate_over_time(self, response_json):
        """Method to get Operations Rate Over Time."""
        metric_prefix = "{}operations_rate_over_time".format(self.pd_prefix)
        metric_list = list()
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            node_id = statistics.get("devid")
            if key is None or len(key.split(".")) < 3 or node_id is None:
                continue
            protocol = key.split(".")[2]
            stats_value = statistics.get("value", [])

            if key == "cluster.protostats." + protocol + ".total":
                if stats_value == []:
                    metric_list.append(
                        [
                            metric_prefix,
                            0.00,
                            [INTEGRATION_PREFIX + "protocol:%s" % protocol],
                        ]
                    )
                for value in stats_value:
                    metric_list.append(
                        [
                            metric_prefix,
                            value.get("op_rate", 0.00),
                            [INTEGRATION_PREFIX + "protocol:%s" % protocol],
                        ]
                    )
        return metric_list

    def pd_iops(self, response_json):
        """Method to get IOPS."""
        metric_prefix = "{}iops".format(self.pd_prefix)
        metric_list = list()
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            node_id = statistics.get("devid")
            if key is None or len(key.split(".")) < 3 or node_id is None:
                continue
            protocol = key.split(".")[2]
            stats_value = statistics.get("value", [])
            if key == "cluster.protostats." + protocol + ".total":
                if stats_value == []:
                    metric_list.append(
                        [
                            metric_prefix,
                            0.0,
                            [
                                INTEGRATION_PREFIX + "protocol:%s" % protocol,
                                INTEGRATION_PREFIX + "rate-type:in-rate",
                            ],
                        ]
                    )

                    metric_list.append(
                        [
                            metric_prefix,
                            0.0,
                            [
                                INTEGRATION_PREFIX + "protocol:%s" % protocol,
                                INTEGRATION_PREFIX + "rate-type:out-rate",
                            ],
                        ]
                    )
                for value in stats_value:
                    metric_list.append(
                        [
                            metric_prefix,
                            round(value.get("in_rate", 0.00), 3),
                            [
                                INTEGRATION_PREFIX + "protocol:%s" % protocol,
                                INTEGRATION_PREFIX + "rate-type:in-rate",
                            ],
                        ]
                    )

                    metric_list.append(
                        [
                            metric_prefix,
                            round(value.get("out_rate", 0.00), 3),
                            [
                                INTEGRATION_PREFIX + "protocol:%s" % protocol,
                                INTEGRATION_PREFIX + "rate-type:out-rate",
                            ],
                        ]
                    )
        return metric_list

    def pd_latency(self, response_json):
        """Method to get Latency."""
        metric_prefix = "{}latency".format(self.pd_prefix)
        metric_list = list()
        for statistics in response_json.get("stats", []):
            key = statistics.get("key")
            node_id = statistics.get("devid")
            if key is None or len(key.split(".")) < 3 or node_id is None:
                continue
            protocol = key.split(".")[2]
            stats_value = statistics.get("value", [])
            if key == "cluster.protostats." + protocol + ".total":
                if stats_value == []:
                    metric_list.append(
                        [
                            metric_prefix,
                            0.0,
                            [INTEGRATION_PREFIX + "protocol:%s" % protocol],
                        ]
                    )
                for value in stats_value:
                    metric_list.append(
                        [
                            metric_prefix,
                            round((value.get("time_avg", 0.0) / 1000000), 3),
                            [INTEGRATION_PREFIX + "protocol:%s" % protocol],
                        ]
                    )
        return metric_list
