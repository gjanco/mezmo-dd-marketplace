from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
import time
import datetime

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
    "storage.logical_usage_bytes",
    "content_cache_logical_memory_usage_bytes",
    "content_cache_physical_memory_usage_bytes",
    "controller_num_iops",
    "controller_num_write_io",
    "controller_num_write_iops",
    "controller_num_read_iops",
    "controller_avg_io_latency_usecs",
    "controller_avg_write_io_latency_usecs",
    "controller_avg_read_io_latency_usecs",
    "controller_io_bandwidth_kBps",
    "data_reduction.compression.saving_ratio_ppm",
    "data_reduction.dedup.saving_ratio_ppm",
    "hypervisor_cpu_usage_ppm",
    "hypervisor_memory_usage_ppm",
    "hypervisor_num_read_iops",
    "hypervisor_num_write_iops",
    "hypervisor_avg_read_io_latency_usecs",
    "hypervisor_avg_write_io_latency_usecs",
    "hypervisor.cpu_ready_time_ppm",
    "replication_transmitted_bandwidth_kBps",
    "replication_received_bandwidth_kBps",
    "memory_usage_ppm"
]


class NutanixCheck(AgentCheck):
    def __init__(self, *args, **kwargs):
        super(NutanixCheck, self).__init__(*args, **kwargs)
        self.cvm_host = self.instance.get("cvm_host")
        self.username = self.instance.get("username")
        self.password = self.instance.get("password")
        self.collect_events = is_affirmative(self.instance.get("collect_events", False))
        self.verbose_collection = is_affirmative(self.instance.get("verbose_collection", False))
        self.enable_protection_domains = is_affirmative(self.instance.get("protection_domains_enabled", False))
        self.use_vm_fqdn = is_affirmative(self.instance.get("use_vm_fqdn", False))
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.tags.append("nutanix_cvm:{}".format(self.cvm_host))
        self.metric_prefix = "rapdev.nutanix"

    def check(self, instance):
        self.validate_config()
        self.test_cvm_connection()
        self.cluster_name = self.retrieve_cluster_name()
        self.tags.append("nutanix_cluster:{}".format(self.cluster_name))
        self.tags = list(set(self.tags))
        self.get_clusters()
        self.get_storage_containers()
        self.get_storage_pools()
        self.get_disks()
        self.get_hosts()
        self.get_vms()
        self.get_virtual_disks()
        self.get_license()
        if self.collect_events == True:
            self.get_events()
        if self.enable_protection_domains:
            self.get_protection_domains()

    def test_cvm_connection(self):
        self.log.debug("Attempting connection test to Nutanix CVM host {} with username {}...".format(self.cvm_host, self.username))
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
        results = self.http.get("https://{}/PrismGateway/services/rest/v1/{}".format(self.cvm_host, entity))
        if results.status_code == 200:
            return results.json()
        else:
            self.log.error("Error making Nutanix API call: {}".format(results.text))
            return {}

    def get_clusters(self):
        entity = "clusters"
        response = self.call_api(entity)
        clusters = response["entities"]
        cluster_metadata = response["metadata"]
        total_clusters = cluster_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_clusters, tags=self.tags)
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
            node_count = cluster["numNodes"]
            block_count = len(cluster["blockSerials"])
            self.gauge("{}.{}.currentRedundancyFactor".format(self.metric_prefix, entity), current_redundancy, tags=metric_tags)
            self.gauge("{}.{}.desiredRedundancyFactor".format(self.metric_prefix, entity), desired_redundancy, tags=metric_tags)
            self.gauge("{}.{}.blockCount".format(self.metric_prefix, entity), block_count, tags=metric_tags)
            self.gauge("{}.{}.nodeCount".format(self.metric_prefix, entity), node_count, tags=metric_tags)

    def get_storage_containers(self):
        entity = "containers"
        response = self.call_api(entity)
        containers = response["entities"]
        container_metadata = response["metadata"]
        total_containers = container_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_containers, tags=self.tags)
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

    def get_storage_pools(self):
        entity = "storage_pools"
        response = self.call_api(entity)
        storage_pools = response["entities"]
        storage_pools_metadata = response["metadata"]
        total_storage_pools = storage_pools_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_storage_pools, tags=self.tags)
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

    def get_disks(self):
        entity = "disks"
        response = self.call_api(entity)
        disks = response["entities"]
        disk_metadata = response["metadata"]
        total_disks = disk_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_disks, tags=self.tags)
        for disk in disks:
            stats = disk["stats"]
            usage_stats = disk["usageStats"]
            disk_status = disk["diskStatus"]
            metric_tags = self.tags.copy()
            metric_tags.append("disk_storage_type:{}".format(disk["storageTierName"]))
            metric_tags.append("nutanix_disk_host:{}".format(disk["hostName"]))
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

    def get_hosts(self):
        entity = "hosts"
        response = self.call_api(entity)
        hosts = response["entities"]
        host_metadata = response["metadata"]
        total_hosts = host_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_hosts, tags=self.tags)
        for host in hosts:
            stats = host["stats"]
            usage_stats = host["usageStats"]
            nutanix_host = host["name"]
            metric_tags = self.tags.copy()
            metric_tags.append("nutanix_type:host")
            metric_tags.append("nutanix_host:{}".format(host["name"]))
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
                metric_tags.append("core:{}_core{}".format(nutanix_host, x))
                self.gauge("datadog.marketplace.{}".format(self.metric_prefix), 1.0, tags=metric_tags)

    def get_vms(self):
        entity = "vms"
        response = self.call_api(entity)
        vms = response["entities"]
        vm_metadata = response["metadata"]
        total_vms = vm_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_vms, tags=self.tags)
        for vm in vms:
            if vm["powerState"] == "on":
                stats = vm["stats"]
                metric_tags = self.tags.copy()
                if self.use_vm_fqdn:
                    from socket import gethostbyname_ex
                    try:
                        vmname = gethostbyname_ex(vm["vmName"])[0]
                    except:
                        self.log.error("Could not find an FQDN for VM named {} in DNS, resorting to using display name".format(vm["vmName"]))
                        vmname = vm["vmName"]
                else:
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

    def get_virtual_disks(self):
        entity = "virtual_disks"
        response = self.call_api(entity)
        virtual_disks = response["entities"]
        virtual_disks_metadata = response["metadata"]
        total_virtual_disks = virtual_disks_metadata["totalEntities"]
        self.gauge("{}.{}.count".format(self.metric_prefix, entity), total_virtual_disks, tags=self.tags)
        for virtual_disk in virtual_disks:
            stats = virtual_disk["stats"]
            metric_tags = self.tags.copy()
            metric_tags.append("nutanix_type:virtual_disk")

            if self.verbose_collection == False:
                self.submit_standard_metrics(stats, entity, metric_tags)
            else:
                self.submit_metrics(stats, entity, metric_tags)

    def get_protection_domains(self):
        entity = "protection_domains"
        response = self.call_api(entity)
        for pd in response:
            stats = pd["stats"]
            usage_stats = pd["usageStats"]
            metric_tags = self.tags.copy()
            metric_tags.append("nutanix_type:protection_domain")
            metric_tags.append("protection_domain:{}".format(pd["name"]))
            self.gauge("{}.{}.vms_count".format(self.metric_prefix, entity), len(pd["vms"]), tags=metric_tags)
            self.gauge("{}.{}.nfs_files_count".format(self.metric_prefix, entity), len(pd["nfsFiles"]), tags=metric_tags)
            self.gauge("{}.{}.volume_groups_count".format(self.metric_prefix, entity), len(pd["volumeGroups"]), tags=metric_tags)
            self.gauge("{}.{}.remote_sites_count".format(self.metric_prefix, entity), len(pd["remoteSiteNames"]), tags=metric_tags)
            self.gauge("{}.{}.cron_schedules_count".format(self.metric_prefix, entity), len(pd["cronSchedules"]), tags=metric_tags)
            self.gauge("{}.{}.pending_replication_count".format(self.metric_prefix, entity), pd["pendingReplicationCount"], tags=metric_tags)
            self.gauge("{}.{}.ongoing_replication_count".format(self.metric_prefix, entity), pd["ongoingReplicationCount"], tags=metric_tags)
            self.gauge("{}.{}.total_user_written_bytes".format(self.metric_prefix, entity), pd["totalUserWrittenBytes"], tags=metric_tags)
            
            if pd["active"] == True:
                self.service_check("{}.{}.is_active".format(self.metric_prefix, entity), AgentCheck.OK, tags=metric_tags)
            else:
                self.service_check("{}.{}.is_active".format(self.metric_prefix, entity), AgentCheck.CRITICAL, tags=metric_tags)
            
            self.submit_metrics(stats, entity, metric_tags)
            self.submit_metrics(usage_stats, entity, metric_tags)
            snapshots = self.call_api("{}/{}/dr_snapshots".format(entity, pd["name"]))
            self.gauge("{}.{}.snapshots.count".format(self.metric_prefix, entity), snapshots["metadata"]["totalEntities"], tags=metric_tags)
            for snap in snapshots["entities"]:
                metric_tags.append("snapshot_id:{}".format(snap["snapshotId"]))
                metric_tags.append("located_remote_site:{}".format(snap["locatedRemoteSiteName"]))
                if snap["state"] == "AVAILABLE":
                    self.gauge("{}.{}.snapshots.available".format(self.metric_prefix, entity), 1, tags=metric_tags)
                else:
                    self.gauge("{}.{}.snapshots.available".format(self.metric_prefix, entity), 0, tags=metric_tags)
                self.gauge("{}.{}.snapshots.size".format(self.metric_prefix, entity), snap["sizeInBytes"], tags=metric_tags)
                if snap["exclusiveUsageInBytes"] != -1:
                    self.gauge("{}.{}.snapshots.exclusive_usage".format(self.metric_prefix, entity), snap["exclusiveUsageInBytes"], tags=metric_tags)

    def get_license(self):
        entity = "license"
        response = self.call_api(entity)
        metric_tags = self.tags.copy()
        nodes = response["nodeLicenseList"]
        cluster_license = response["clusterExpiryUsecs"]
        self.gauge("{}.{}.clusterExpiryUsecs".format(self.metric_prefix, entity), cluster_license, tags=metric_tags)
        if nodes is not None:
            for node in nodes:
                num_days_remaining = node["numDaysRemaining"]
                current = datetime.datetime.now().timestamp()
                diff = num_days_remaining - current
                days_left = diff // 86400

                metric_tags.append("license_id:{}".format(node["licenseId"]))
                metric_tags.append("license_model:{}".format(node["model"]))
                self.gauge("{}.{}.days_left".format(self.metric_prefix, entity), days_left, tags=metric_tags)

    def get_events(self):
        entity = "events"
        interval = int(self.instance.get("min_collection_interval", 15))
        current_time = round(time.time())
        start_time = str((current_time - interval)*1000000)
        response = self.http.get("https://" + self.cvm_host + "/PrismGateway/services/rest/v1/" + entity + "/?startTimeInUsecs=" + start_time).json()
        events = response["entities"]
        
        for event in events:
            usecs = event["createdTimeStampInUsecs"]
            timestamp = (usecs / 1000000)
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
