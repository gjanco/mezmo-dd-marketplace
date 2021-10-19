"""Module for Quota Information"""
from .cds_dell_emc_consts import INTEGRATION_PREFIX


class CDSDellEMCQuHelper(object):
    """Class for Quota Information panels"""

    def __init__(self):
        self.qi_prefix = "{}{}".format(INTEGRATION_PREFIX, "quota_information.")

    def qi_quota_type_count(self, response_json):
        """Method to get Quota Type Count."""
        metric_prefix = "{}quota_type_count".format(self.qi_prefix)
        metric_list = list()
        quotas_count = response_json.get("summary", {})

        quota_type_count = {
            "user_quotas_count": quotas_count.get("user_quotas_count", 0),
            "directory_quotas_count": quotas_count.get("directory_quotas_count", 0),
            "group_quotas_count": quotas_count.get("group_quotas_count", 0),
        }

        for quota_type, quota_count in quota_type_count.items():
            metric_list.append(
                [
                    metric_prefix,
                    quota_count,
                    [INTEGRATION_PREFIX + "quota-type:%s" % quota_type],
                ]
            )
        return metric_list

    def qi_quota_type_information(self, response_json):
        """Method to get Quota Type Information."""
        metric_prefix = "{}quota_type_information".format(self.qi_prefix)
        metric_list = list()

        for quotas in response_json.get("quotas", []):
            quota_id = quotas.get("id")
            quota_type = quotas.get("type")

            if quota_id is None or quota_type is None:
                continue

            quota_usage = quotas.get("usage", {})
            quota_used = round(quota_usage.get("fslogical", 0) / (1024 * 1024), 2)
            quota_available = round(
                (quota_usage.get("fsphysical", 0) - quota_usage.get("fslogical", 0)) / (1024 * 1024),
                2,
            )
            metric_list.append(
                [
                    metric_prefix,
                    quota_used,
                    [
                        INTEGRATION_PREFIX + "quota-space:used",
                        INTEGRATION_PREFIX + "quota-type:%s" % quota_type,
                        INTEGRATION_PREFIX + "quota-id:%s" % quota_id,
                    ],
                ]
            )
            metric_list.append(
                [
                    metric_prefix,
                    quota_available,
                    [
                        INTEGRATION_PREFIX + "quota-space:available",
                        INTEGRATION_PREFIX + "quota-type:%s" % quota_type,
                        INTEGRATION_PREFIX + "quota-id:%s" % quota_id,
                    ],
                ]
            )
        return metric_list
