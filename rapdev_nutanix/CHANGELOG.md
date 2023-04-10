# CHANGELOG - Nutanix

## 1.3.5 / 2023-04-04
* [BugFix] Fix bug with call for getting license information due to change in Nutanix API

## 1.3.4 / 2022-05-13
* [BugFix] Fix bug in reporting days left in node licenses
* [BugFix] Fix titles and widget names in dashboards due to inconsistency and wrong metric names

## 1.3.3 / 2022-04-27
* [BugFix] Better error handling for calling the Nutanix API
* [BugFix] Added metric units and descriptions to metric metadata
* [Added] Added Dashboard for Protection Domains
* [Updated] Updated out of the box dashboards with links, new widgets and layout

## 1.3.2 / 2021-09-13
* [BugFix] Swap use_vm_fqdn to use gethostbyname_ex instead of getfqdn due to this method only checking first DNS server

## 1.3.1 / 2021-08-30
* [BugFix] General bug fixes

## 1.3.0 / 2021-08-16
* [Added] Configuration option for using a VM's FQDN as found in DNS

## 1.2.0 / 2021-06-11
* [Added] Added metrics for protection domains if enabled

## 1.1.1 / 2021-04-07

* [BugFix] Fixed bug where total entities was being submitted for each entity, not whole cluster at a time
* [BugFix] Fixed bug where first round of metrics would be submitted without the cluster tag, causing incorrect data reporting on dashboards
* [BugFix] Rearranged dashboards
* 
## 1.1.0 / 2021-01-12

* [Added] added Nutanix Overview, Clusters, Hosts and Disks and VMs Dashboards
* [Added] added storage.logical_usage_bytes , replication_transmitted_bandwidth_kBps , replication_received_bandwidth_kBps metrics
