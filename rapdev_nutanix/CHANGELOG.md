# CHANGELOG - Nutanix

## 1.1.1 / 2021-04-07

* [BugFix] Fixed bug where total entities was being submitted for each entity, not whole cluster at a time
* [BugFix] Fixed bug where first round of metrics would be submitted without the cluster tag, causing incorrect data reporting on dashboards
* [BugFix] Rearranged dashboards
* 
## 1.1.0 / 2021-01-12

* [Added] added Nutanix Overview, Clusters, Hosts and Disks and VMs Dashboards
* [Added] added storage.logical_usage_bytes , replication_transmitted_bandwidth_kBps , replication_received_bandwidth_kBps metrics
