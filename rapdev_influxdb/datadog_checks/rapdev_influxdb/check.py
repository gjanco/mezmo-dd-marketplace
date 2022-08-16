from copy import deepcopy

from datadog_checks.base import OpenMetricsBaseCheckV2

from .metrics import METRIC_MAP, construct_metrics_config

REQUIRED_TAGS = [
    "vendor:rapdev",
]


class InfluxdbCheck(OpenMetricsBaseCheckV2):

    __NAMESPACE__ = "rapdev.influxdb"

    def __init__(self, name, init_config, instances):
        super(InfluxdbCheck, self).__init__(name, init_config, instances)
        self.instance["tags"] = REQUIRED_TAGS + self.instance.get("tags", [])
        self.instance["tags"].append(
            "influxdb_endpoint:{}".format(self.instance.get("openmetrics_endpoint"))
        )

    def check(self, _):
        self.gauge(
            "datadog.marketplace.rapdev.influxdb",
            1,
            tags=[
                "influxdb_endpoint:{}".format(self.instance.get("openmetrics_endpoint"))
            ],
        )
        super(InfluxdbCheck, self).check(_)

    def get_default_config(self):
        metric_map = deepcopy(METRIC_MAP)
        return {"metrics": construct_metrics_config(metric_map)}
