"""Module for License Information"""
import time

from .cds_dell_emc_consts import INTEGRATION_PREFIX


class CDSDellEMCLiHelper(object):
    """Class for License Details panel"""

    def __init__(self):
        self.ci_prefix = "{}{}".format(INTEGRATION_PREFIX, "cluster_inventory.")

    def ci_license_details(self, response_json):
        """Method to get License Details."""
        metric_prefix = "{}license_details".format(self.ci_prefix)
        metric_list = list()
        index = 0
        for licenses in response_json.get("licenses", []):
            license_name = licenses.get("name", "")
            license_status = licenses.get("status", "")
            license_duration = licenses.get("duration") if licenses.get("duration") is not None else "null"
            expiry_date = (
                time.strftime(
                    "%d/%m/%Y %I:%M:%S %p",
                    time.localtime(licenses.get("expiration")),
                )
                if licenses.get("expiration") is not None
                else ""
            )
            epoc_time = int(str(time.time()).split(".", maxsplit=1)[0])
            metric_list.append(
                [
                    metric_prefix,
                    index,
                    [
                        INTEGRATION_PREFIX + "License_Name:%s" % license_name,
                        INTEGRATION_PREFIX + "Status:%s" % license_status,
                        INTEGRATION_PREFIX + "Duration:%s" % license_duration,
                        INTEGRATION_PREFIX + "Expiry_Date:%s" % expiry_date,
                        INTEGRATION_PREFIX + "license_time:%s" % epoc_time,
                    ],
                ]
            )
            index = index + 1
        return metric_list
