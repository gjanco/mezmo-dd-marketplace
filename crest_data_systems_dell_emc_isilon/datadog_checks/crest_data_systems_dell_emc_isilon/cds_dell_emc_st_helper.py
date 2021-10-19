"""Module for Storage and Node Pool Details"""
from .cds_dell_emc_consts import INTEGRATION_PREFIX


class CDSDellEMCStHelper(object):
    """Class for Storage and Node Pool Details panels"""

    def __init__(self):
        self.ci_prefix = "{}{}".format(INTEGRATION_PREFIX, "cluster_inventory.")

    def ci_storage_tiers(self, response_json):
        """Method to get Storage Tiers."""
        metric_prefix = "{}".format(self.ci_prefix)
        metric_list = list()
        storage_tiers = {}
        for storagepool in response_json.get("storagepools", []):
            storage_tier = {
                "disk-used": None,
                "total-disk": None,
                "virtual-hot-spare": None,
                "ssd-used": None,
                "total-ssd": None,
            }
            usage = storagepool.get("usage")
            pool_id = storagepool.get("id")
            pool_name = storagepool.get("name")

            if usage is None or pool_id is None or pool_name is None:
                continue

            if pool_id not in storage_tiers:
                storage_tiers[pool_id] = storage_tier

            storage_tiers[pool_id]["total-disk"] = round((int(usage.get("total_bytes", 0.0))) / (1024 * 1024 * 1024), 2)
            avail_bytes = round((int(usage.get("avail_bytes", 0.0))) / (1024 * 1024 * 1024), 2)
            storage_tiers[pool_id]["virtual-hot-spare"] = round(
                (int(usage.get("virtual_hot_spare_bytes", 0.0))) / (1024 * 1024 * 1024),
                2,
            )
            storage_tiers[pool_id]["total-ssd"] = round(
                (int(usage.get("total_ssd_bytes", 0.0))) / (1024 * 1024 * 1024), 2
            )
            avail_ssd_bytes = round((int(usage.get("avail_ssd_bytes", 0.0))) / (1024 * 1024 * 1024), 2)
            storage_tiers[pool_id]["ssd-used"] = (
                0.00
                if storage_tiers[pool_id]["total-ssd"] == 0.00
                else round(
                    (storage_tiers[pool_id]["total-ssd"] - avail_ssd_bytes) * 100 / storage_tiers[pool_id]["total-ssd"],
                    2,
                )
            )
            storage_tiers[pool_id]["disk-used"] = (
                0.00
                if (storage_tiers[pool_id]["total-disk"] - storage_tiers[pool_id]["virtual-hot-spare"]) == 0.00
                else round(
                    (storage_tiers[pool_id]["total-disk"] - storage_tiers[pool_id]["virtual-hot-spare"] - avail_bytes)
                    * 100
                    / (storage_tiers[pool_id]["total-disk"] - storage_tiers[pool_id]["virtual-hot-spare"]),
                    2,
                )
            )

            list_tag = [
                INTEGRATION_PREFIX + "storage-tier-id:%s" % pool_id,
                INTEGRATION_PREFIX + "storage-tier-name:%s" % pool_name,
            ]

            metric_list.append(
                [
                    metric_prefix + "storage_tiers.disk_used",
                    storage_tiers[pool_id]["disk-used"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "storage_tiers.total_disk",
                    storage_tiers[pool_id]["total-disk"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "storage_tiers.virtual_hot_spare",
                    storage_tiers[pool_id]["virtual-hot-spare"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "storage_tiers.ssd_used",
                    storage_tiers[pool_id]["ssd-used"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "storage_tiers.total_ssd",
                    storage_tiers[pool_id]["total-ssd"],
                    list_tag,
                ]
            )
        return metric_list

    def ci_node_pools(self, response_json):
        """Method to get Node Pools."""
        metric_prefix = "{}".format(self.ci_prefix)
        metric_list = list()
        node_pool_details = {}
        for nodepool in response_json.get("nodepools", []):
            node_detail = {
                "disk-used": None,
                "total-disk": None,
                "virtual-hot-spare": None,
                "ssd-used": None,
                "total-ssd": None,
            }
            usage = nodepool.get("usage")
            pool_id = nodepool.get("id")
            pool_name = nodepool.get("name")
            l3_status = nodepool.get("l3_status")

            if usage is None or pool_id is None or pool_name is None or l3_status is None:
                continue

            if pool_id not in node_pool_details:
                node_pool_details[pool_id] = node_detail

            node_pool_details[pool_id]["total-disk"] = round(
                (int(usage.get("total_bytes", 0.0))) / (1024 * 1024 * 1024), 2
            )

            node_pool_details[pool_id]["virtual-hot-spare"] = round(
                (int(usage.get("virtual_hot_spare_bytes", 0.0))) / (1024 * 1024 * 1024),
                2,
            )

            node_pool_details[pool_id]["total-ssd"] = round(
                (int(usage.get("total_ssd_bytes", 0.0))) / (1024 * 1024 * 1024), 2
            )

            avail_ssd_bytes = round((int(usage.get("avail_ssd_bytes", 0.0))) / (1024 * 1024 * 1024), 2)
            node_pool_details[pool_id]["ssd-used"] = (
                0.00
                if node_pool_details[pool_id]["total-ssd"] == 0.00
                else round(
                    (node_pool_details[pool_id]["total-ssd"] - avail_ssd_bytes)
                    * 100
                    / node_pool_details[pool_id]["total-ssd"],
                    2,
                )
            )

            avail_bytes = round((int(usage.get("avail_bytes", 0.0))) / (1024 * 1024 * 1024), 2)
            node_pool_details[pool_id]["disk-used"] = (
                0.00
                if (node_pool_details[pool_id]["total-disk"] - node_pool_details[pool_id]["virtual-hot-spare"]) == 0.00
                else round(
                    (
                        node_pool_details[pool_id]["total-disk"]
                        - node_pool_details[pool_id]["virtual-hot-spare"]
                        - avail_bytes
                    )
                    * 100
                    / (node_pool_details[pool_id]["total-disk"] - node_pool_details[pool_id]["virtual-hot-spare"]),
                    2,
                )
            )

            list_tag = [
                INTEGRATION_PREFIX + "node-pool-id:%s" % pool_id,
                INTEGRATION_PREFIX + "node-pool-name:%s" % pool_name,
                INTEGRATION_PREFIX + "node-pool-l3-status:%s" % l3_status,
            ]

            metric_list.append(
                [
                    metric_prefix + "node_pools.disk_used",
                    node_pool_details[pool_id]["disk-used"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "node_pools.total_disk",
                    node_pool_details[pool_id]["total-disk"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "node_pools.virtual_hot_spare",
                    node_pool_details[pool_id]["virtual-hot-spare"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "node_pools.ssd_used",
                    node_pool_details[pool_id]["ssd-used"],
                    list_tag,
                ]
            )
            metric_list.append(
                [
                    metric_prefix + "node_pools.total_ssd",
                    node_pool_details[pool_id]["total-ssd"],
                    list_tag,
                ]
            )
        return metric_list
