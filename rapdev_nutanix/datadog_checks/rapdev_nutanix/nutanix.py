from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
from datadog_checks.base.utils.subprocess_output import get_subprocess_output
import json
import requests
import time
import re
import datetime
from requests.auth import HTTPBasicAuth

REQUIRED_SETTINGS = [
    "cvm_host",
    "username",
    "password"
]
REQUIRED_TAGS = [
    "vendor:rapdev",
]

STANDARD_METRICS = [
    "num_io",
    "write_io_ppm",
    "avg_io_latency_usecs",
    "num_read_iops",
    "num_write_iops",
    "read_io_bandwidth_kBps",
    "write_io_bandwidth_kBps",
    "content_cache_hit_ppm",
    "storage.usage_bytes",
    "storage.capacity_bytes",
    "storage.free_bytes",
    "content_cache_logical_memory_usage_bytes",
    "content_cache_physical_memory_usage_bytes",
    "data_reduction.compression.saving_ratio_ppm",
    "data_reduction.dedup.saving_ratio_ppm",
    "hypervisor_cpu_usage_ppm",
    "hypervisor_memory_usage_ppm",
    "hypervisor_num_read_iops",
    "hypervisor_num_write_iops",
    "hypervisor_avg_read_io_latency_usecs",
    "hypervisor_avg_write_io_latency_usecs",
    "hypervisor.cpu_ready_time_ppm",
    "memory_usage_ppm",
    "controller_num_iops",
    "controller_num_write_io",
    "controller_num_write_iops",
    "controller_num_read_iops",
    "controller_avg_io_latency_usecs",
    "controller_avg_write_io_latency_usecs",
    "controller_avg_read_io_latency_usecs",
    "controller_io_bandwidth_kBps"
]


class NutanixCheck(AgentCheck):
    def __init__(self, *args, **kwargs):
        super(NutanixCheck, self).__init__(*args, **kwargs)
        self.cvm_host = self.instance.get("cvm_host")
        self.username = self.instance.get("username")
        self.password = self.instance.get("password")
        self.collect_events = is_affirmative(self.instance.get("collect_events", False))
        self.verbose_collection = is_affirmative(self.instance.get("verbose", False))
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.tags.append("nutanix_cvm:{}".format(self.cvm_host))
        self.metric_prefix = "rapdev.nutanix"

    def check(self, instance):
        self.test_cvm_connection()
        self.validate_config()
        self.get_clusters()
        self.get_storage_containers()
        self.get_storage_pools()
        self.get_disks()
        self.get_hosts()
        self.get_vms()
        self.get_virtual_disks()
        self.get_license()
        self.cluster_name = self.retrieve_cluster_name()
        self.tags.append("nutanix_cluster:{}".format(self.cluster_name))
        if self.collect_events == True:
            self.get_events()

    def test_cvm_connection(self):
        self.log.debug("Attempting connection test to Nutanix CVM host %s with username %s...", self.cvm_host)
        x = self.http.get("https://" + self.cvm_host + "/PrismGateway/services/rest/v1/cluster")
        response_code = x.status_code
        if response_code == 200:
            self.log.debug("Connection successful")
            self.service_check("{}.can_connect".format(self.metric_prefix), AgentCheck.OK, tags=self.tags)
        else:
            self.log.debug("Cannot authenticate to CVM REST API. The check will not run")
            self.service_check("{}.can_connect".format(self.metric_prefix), AgentCheck.CRITICAL, tags=self.tags)

    def validate_config(self):
        if not self.username or not self.password:
            raise ConfigurationError("Nutanix username and password is needed")
        if not self.cvm_host:
            raise ConfigurationError("Nutanix Controller VM ip address and port is needed")

    def call_api(self, entity):
        results = self.http.get("https://" + self.cvm_host + "/PrismGateway/services/rest/v1/" + entity).json()
        return results

    def get_clusters(self):
        entity = "clusters"
        response = self.call_api(entity)
        clusters = response["entities"]
        cluster_metadata = response["metadata"]
        for cluster in clusters:
            stats = cluster["stats"]
            usage_stats = cluster["usageStats"]
            nodes = cluster["rackableUnits"]
            metric_tags = self.tags.copy()
            metric_tags.append("nutanix_cluster_name:{}".format(cluster["name"]))
            metric_tags.append("nutanix_cluster_version:{}".format(cluster["fullVersion"]))
            metric_tags.append("nutanix_type:cluster")

            for node in nodes:
                node_count = node["nodes"][0]
                self.gauge("{}.{}.nodes".format(self.metric_prefix, entity), node_count, tags=metric_tags)

            if self.verbose_collection == False:
                self.submit_standard_metrics(stats, entity, metric_tags)
                self.submit_standard_metrics(usage_stats, entity, metric_tags)
            else:
                self.submit_metrics(stats, entity, metric_tags)
                self.submit_metrics(usage_stats, entity, metric_tags)

            current_redundancy = cluster["clusterRedundancyState"]["currentRedundancyFactor"]
            desired_redundancy = cluster["clusterRedundancyState"]["desiredRedundancyFactor"]
            self.gauge("{}.{}.currentRedundancyFactor".format(self.metric_prefix, entity), current_redundancy,
                       tags=metric_tags)
            self.gauge("{}.{}.desiredRedundancyFactor".format(self.metric_prefix, entity), desired_redundancy,
                       tags=metric_tags)
        total_clusters = cluster_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_clusters, tags=metric_tags)

    def get_storage_containers(self):
        entity = "containers"
        response = self.call_api(entity)
        containers = response["entities"]
        container_metadata = response["metadata"]
        for container in containers:
            stats = container["stats"]
            usage_stats = container["usageStats"]
            metric_tags = self.tags.copy()
            metric_tags.append("nutanix_storage_container:{}".format(container["name"]))
            metric_tags.append("nutanix_type:storage_container")

            if self.verbose_collection == False:
                self.submit_standard_metrics(stats, entity, metric_tags)
                self.submit_standard_metrics(usage_stats, entity, metric_tags)
            else:
                self.submit_metrics(stats, entity, metric_tags)
                self.submit_metrics(usage_stats, entity, metric_tags)

        total_containers = container_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_containers, tags=metric_tags)

    def get_storage_pools(self):
        entity = "storage_pools"
        response = self.call_api(entity)
        storage_pools = response["entities"]
        storage_pools_metadata = response["metadata"]
        for storage_pool in storage_pools:
            stats = storage_pool["stats"]
            usage_stats = storage_pool["usageStats"]
            metric_tags = self.tags.copy()
            metric_tags.append("nutanix_storage_pool:{}".format(storage_pool["name"]))
            metric_tags.append("nutanix_type:storage_pool")

            if self.verbose_collection == False:
                self.submit_standard_metrics(stats, entity, metric_tags)
                self.submit_standard_metrics(usage_stats, entity, metric_tags)
            else:
                self.submit_metrics(stats, entity, metric_tags)
                self.submit_metrics(usage_stats, entity, metric_tags)

        total_storage_pools = storage_pools_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_storage_pools, tags=metric_tags)

    def get_disks(self):
        entity = "disks"
        response = self.call_api(entity)
        disks = response["entities"]
        disk_metadata = response["metadata"]
        for disk in disks:
            stats = disk["stats"]
            usage_stats = disk["usageStats"]
            disk_status = disk["diskStatus"]
            metric_tags = self.tags.copy()
            metric_tags.append("disk_storage_type:{}".format(disk["storageTierName"]))
            metric_tags.append("nutanix_type:disk")
            metric_tags.append("disk_serialnumber:{}".format(disk["diskHardwareConfig"]["serialNumber"]))
            if disk_status == "NORMAL":
                self.log.debug("Disk is NORMAL")
                self.service_check("{}.{}.disk_status".format(self.metric_prefix, entity), AgentCheck.OK,
                                   tags=metric_tags)
            elif disk_status != "NORMAL":
                self.log.debug("Disk is not NORMAL")
                self.service_check("{}.{}.disk_status".format(self.metric_prefix, entity), AgentCheck.CRITICAL,
                                   tags=metric_tags)

            if self.verbose_collection == False:
                self.submit_standard_metrics(stats, entity, metric_tags)
                self.submit_standard_metrics(usage_stats, entity, metric_tags)

            else:
                self.submit_metrics(stats, entity, metric_tags)
                self.submit_metrics(usage_stats, entity, metric_tags)

        total_disks = disk_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_disks, tags=metric_tags)

    def get_hosts(self):
        entity = "hosts"
        response = self.call_api(entity)
        hosts = response["entities"]
        host_metadata = response["metadata"]
        for host in hosts:
            stats = host["stats"]
            usage_stats = host["usageStats"]
            nutanix_host = host["name"]
            metric_tags = self.tags.copy()
            metric_tags.append("nutanix_type:host")
            metric_tags.append("nutanix_host:{}".format(host["name"]))
            total_hosts = host_metadata["totalEntities"]
            self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_hosts, tags=metric_tags)
            if self.verbose_collection == False:
                self.submit_standard_metrics(stats, entity, metric_tags, nutanix_host)
                self.submit_standard_metrics(usage_stats, entity, metric_tags, nutanix_host)
            else:
                self.submit_metrics(stats, entity, metric_tags, nutanix_host)
                self.submit_metrics(usage_stats, entity, metric_tags, nutanix_host)
            num_cores = host["numCpuCores"]
            self.gauge("{}.{}.num_cores".format(self.metric_prefix, entity), num_cores, tags=metric_tags)
            for x in range(num_cores):
                x += 1
                metric_tags.append("core:{}".format(x))
                self.gauge("datadog.marketplace.{}".format(self.metric_prefix), 1.0, tags=metric_tags)

    def get_vms(self):
        entity = "vms"
        response = self.call_api(entity)
        vms = response["entities"]
        vm_metadata = response["metadata"]
        for vm in vms:
            if vm["powerState"] == "on":
                stats = vm["stats"]
                metric_tags = self.tags.copy()
                vmname = vm["vmName"]
                metric_tags.append("nutanix_host:{}".format(vm["hostName"]))
                metric_tags.append("vm_description:{}".format(vm["description"]))
                metric_tags.append("guest_os:{}".format(vm["guestOperatingSystem"]))
                metric_tags.append("hypervisor:{}".format(vm["hypervisorType"]))
                metric_tags.append("nutanix_type:vm")

                if self.verbose_collection == False:
                    self.submit_standard_metrics(stats, entity, metric_tags, vmname)
                else:
                    self.submit_metrics(stats, entity, metric_tags, vmname)

        total_vms = vm_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_vms, tags=metric_tags)

    def get_virtual_disks(self):
        entity = "virtual_disks"
        response = self.call_api(entity)
        virtual_disks = response["entities"]
        virtual_disks_metadata = response["metadata"]
        for virtual_disk in virtual_disks:
            stats = virtual_disk["stats"]
            metric_tags = self.tags.copy()
            metric_tags.append("nutanix_type:virtual_disk")

            if self.verbose_collection == False:
                self.submit_standard_metrics(stats, entity, metric_tags)
            else:
                self.submit_metrics(stats, entity, metric_tags)
        total_virtual_disks = virtual_disks_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_virtual_disks, tags=metric_tags)

    def get_license(self):
        entity = "license"
        response = self.call_api(entity)
        metric_tags = self.tags.copy()
        nodes = response["nodeLicenseList"]
        cluster_license = response["clusterExpiryUsecs"]
        self.gauge("{}.{}.clusterExpiryUsecs".format(self.metric_prefix, entity), cluster_license, tags=metric_tags)
        for node in nodes:
            num_days_remaining = node["numDaysRemaining"]
            current = datetime.datetime.now().timestamp()
            diff = num_days_remaining - current
            days_left = diff // 86400

            metric_tags.append("license_id:{}".format(node["licenseId"]))
            metric_tags.append("license_model:{}".format(node["model"]))
            self.gauge("{}.{}.days_left".format(self.metric_prefix, entity), days_left,
                       tags=metric_tags)

    def get_events(self):
        entity = "events"
        interval = int(self.instance.get("min_collection_interval", 15))
        start_time = str(interval + 3000000)
        response = self.http.get("https://" + self.cvm_host + "/PrismGateway/services/rest/v1/" + entity + "/?startTimeInUsecs=" + start_time).json()
        events = response["entities"]
        usecs = events[0]["createdTimeStampInUsecs"]
        timestamp = (usecs / 1000000)
        for event in events:
            contextTypes = event["contextTypes"]
            contextValues = event["contextValues"]
            context_dict = {contextTypes[x]: contextValues[x] for x in range(len(contextTypes))}
            raw_msg_title = event["message"]
            raw_msg_text = event["detailedMessage"]
            event_id = event["id"]

            msg_title = self.parse_string(raw_msg_title, context_dict)
            msg_text = self.parse_string(raw_msg_text, context_dict)

            self.event({
                "timestamp": timestamp,
                "msg_title": "{}".format(msg_title),
                "msg_text": "{}".format(msg_text),
                "aggregation_key": "{}".format(event_id),
                "source_type_name": "nutanix",
                "tags": self.tags
                })

    def parse_string(self, string, dictionary):
        newstring = string.replace("{", "")
        newerstring = newstring.replace("}", "")
        formatted_string = " ".join(dictionary.get(ele, ele) for ele in newerstring.split())
        return formatted_string

    def submit_standard_metrics(self, stats_dict, entity, metric_tags, host=None):
        ppm = "_ppm"
        for metric in STANDARD_METRICS:
            if metric in stats_dict.keys():
                metric_value = int(stats_dict[metric])
                if metric_value != -1:
                    if host == None:
                        metric_name = "{}.{}.{}".format(self.metric_prefix, entity, metric)
                    else:
                        metric_name = "{}.{}".format(self.metric_prefix, metric)
                    if ppm in metric_name:
                        metric_value = metric_value / 10000
                        metric_name = metric_name.replace(ppm, "")
                    self.gauge(metric_name, metric_value, tags=metric_tags, hostname=host)

    def submit_metrics(self, stats_dict, entity, metric_tags, host=None):
        ppm = "_ppm"
        for key, value in stats_dict.items():
            value = int(value)
            if value != -1:
                if host == None:
                    metric_name = "{}.{}.{}".format(self.metric_prefix, entity, key)
                else:
                    metric_name = "{}.{}".format(self.metric_prefix, key)
                if ppm in metric_name:
                    value = value / 10000
                    metric_name = metric_name.replace(ppm, "")
                self.gauge(metric_name, value, tags=metric_tags, hostname=host)

    def retrieve_cluster_name(self):
        results = self.http.get("https://" + self.cvm_host + "/PrismGateway/services/rest/v1/clusters").json()
        cluster_name = results["entities"][0]["name"]
        return cluster_name