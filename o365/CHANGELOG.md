# CHANGELOG - o365

## 2.0.0 / 2020-10-15

* [Fixed] corrected missing Message Center incidents collection to Datadog events.
* [Fixed] switched to count metrics in reports to reduce Datadog metric units.
* [Added] enable flags for Activations and Groups Activity reports.
* [Added] SharePoint performance metrics included with Office 365 application synthetic operations
* [Fixed] updated monitors and dashboards.

## 1.1.0 / 2020-09-23

* [Added] added "probe_mode" configuration flag to support synthetic branch office deployments.
* [Fixed] added min_collection_interval to instance configuration to support windows agents.
* [Fixed] replaced dependency on deprecated get_instance_proxy() method of AgentCheck base class.

## 1.0.0 / 2020-08-11

[Added] initial marketplace release.