"""Constants"""
INTEGRATION_PREFIX = "cds.emc.isilon."

APIS = [
    {
        "api_interval": 120,
        "interval_offset": 1,
        "api_list": [
            {
                "helper_module": "cds_dell_emc_co_helper",
                "helper_class": "CDSDellEMCCoHelper",
                "api_url": "/platform/1/statistics/current?keys=cluster.cpu.user.max,cluster.cpu.sys.max,ifs.bytes.in."
                "rate,ifs.bytes.out.rate,cluster.net.ext.bytes.in.rate,cluster.net.ext.bytes.out.rate",
                "dashboard_panels": ["co_cpu_usage_over_time"],
            },
            {
                "helper_module": "cds_dell_emc_helper",
                "helper_class": "CDSDellEMCHelper",
                "api_url": "/platform/1/statistics/current?keys=node.net.ext.bytes.in.rate,node.net.ext.bytes.out.rate,"
                "node.ifs.bytes.in.rate,node.ifs.bytes.out.rate,node.cpu.user.max,node.cpu.sys.max,node."
                "health,node.memory.free,node.memory.used&devid=all",
                "dashboard_panels": [
                    "co_file_system_throughput_ot",
                    "co_ex_nw_throughput_rate_ot",
                    "fsp_fs_performance_by_node_ot",
                    "nd_external_network_throughput",
                    "nd_file_system_throughput",
                    "nd_cpu_usage_over_time",
                    "nd_memory_usage",
                ],
            },
            {
                "helper_module": "cds_dell_emc_pd_helper",
                "helper_class": "CDSDellEMCPdHelper",
                "api_url": "/platform/1/statistics/current?substr=true&keys=cluster.protostats",
                "dashboard_panels": [
                    "pd_operations_rate_over_time",
                    "pd_iops",
                    "pd_latency",
                ],
            },
            {
                "helper_module": "cds_dell_emc_nd_helper",
                "helper_class": "CDSDellEMCNdHelper",
                "api_url": "/platform/1/statistics/current?substr=true&keys=node.clientstats.active,node.clientstats."
                "connected,node.ifs.heat,node.sensor.volt.volts,node.sensor.temp.celsius,node.sensor.fan."
                "rpms,sensor.power.watts&devid=all",
                "dashboard_panels": [
                    "co_client_connections_over_time",
                    "pd_client_connections",
                    "fsp_event_rate_by_node_ot",
                    "fsp_event_rate_by_type_ot",
                    "fsp_file_system_critical_events",
                ],
            },
            {
                "helper_module": "cds_dell_emc_fscp_helper",
                "helper_class": "CDSDellEMCFscpHelper",
                "api_url": "/platform/1/statistics/current?substr=true&keys=node.ifs.cache.oldest_page,node.ifs.cache."
                "l2.data.read.hit,node.ifs.cache.l2.data.read.miss,node.ifs.cache.l2.data.prefetch.hit,node."
                "ifs.cache.l2.data.read.wait&devid=all",
                "dashboard_panels": [
                    "fscp_fs_cached_data_age",
                    "fscp_l2_cache_hit_rate",
                    "fscp_l2_cache_miss_rate",
                    "fscp_l2_cache_prefetch_hit_rate",
                    "fscp_l2_cache_read_wait_time",
                ],
            },
            {
                "helper_module": "cds_dell_emc_none_helper",
                "helper_class": "CDSDellEMCNoneHelper",
                "api_url": "/platform/1/statistics/current?key=cluster.node.count.down",
                "dashboard_panels": [],
            },
        ],
    },
    {
        "api_interval": 240,
        "interval_offset": 4,
        "api_list": [
            {
                "helper_module": "cds_dell_emc_nd_co_ci_helper",
                "helper_class": "CDSDellEMCNdCoCiHelper",
                "api_url": "/platform/1/statistics/current?keys=node.ifs.bytes.in.rate,node.ifs.bytes.out.rate,node."
                "ifs.bytes.used,node.ifs.bytes.free,node.ifs.bytes.total,node.ifs.ssd.bytes.used,node.ifs."
                "ssd.bytes.total,node.ifs.ssd.bytes.free,ifs.bytes.avail,ifs.bytes.free,ifs.bytes.used,ifs."
                "bytes.total,ifs.percent.used,ifs.percent.avail,ifs.ssd.bytes.free,ifs.ssd.bytes.used&devid"
                "=all",
                "dashboard_panels": [
                    "nd_disk_usage_over_time",
                    "co_disk_usage",
                    "co_cluster_disk_usage_over_time",
                    "ci_node_details",
                    "nd_disk_usage",
                ],
            },
            {
                "helper_module": "cds_dell_emc_ci_helper",
                "helper_class": "CDSDellEMCCiHelper",
                "api_url": "/platform/1/statistics/current?substr=true&keys=node.disk.name,node.disk.lnum,node.disk."
                "type,node.disk.health&devid=all",
                "dashboard_panels": ["ci_storage_drive_details"],
            },
        ],
    },
    {
        "api_interval": 3600,
        "interval_offset": 30,
        "api_list": [
            {
                "helper_module": "cds_dell_emc_st_helper",
                "helper_class": "CDSDellEMCStHelper",
                "api_url": "/platform/1/storagepool/storagepools",
                "dashboard_panels": ["ci_storage_tiers"],
            },
            {
                "helper_module": "cds_dell_emc_none_helper",
                "helper_class": "CDSDellEMCNoneHelper",
                "api_url": "/platform/1/cluster/config",
                "dashboard_panels": [],
            },
            {
                "helper_module": "cds_dell_emc_st_helper",
                "helper_class": "CDSDellEMCStHelper",
                "api_url": "/platform/1/storagepool/nodepools",
                "dashboard_panels": ["ci_node_pools"],
            },
            {
                "helper_module": "cds_dell_emc_li_helper",
                "helper_class": "CDSDellEMCLiHelper",
                "api_url": "/platform/1/license/licenses",
                "dashboard_panels": ["ci_license_details"],
            },
            {
                "helper_module": "cds_dell_emc_qu_helper",
                "helper_class": "CDSDellEMCQuHelper",
                "api_url": "/platform/11/quota/quotas-summary",
                "dashboard_panels": ["qi_quota_type_count"],
            },
            {
                "helper_module": "cds_dell_emc_qu_helper",
                "helper_class": "CDSDellEMCQuHelper",
                "api_url": "/platform/11/quota/quotas",
                "dashboard_panels": ["qi_quota_type_information"],
            },
        ],
    },
]
