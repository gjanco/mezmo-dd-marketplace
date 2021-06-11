# CHANGELOG - o365

## 2.0.3 / 2026-06-26

* [Added] updated app registration permissions to more specific scopes.
* [Added] added requests timeouts to authorization token invocations.
* [Fixed] updated README on Microsoft 365 integration user license requirement and permissions.
* [Fixed] updated dashboards.
* [Fixed] updated ServiceComms URI path with configured TenantId.

## 2.0.2 / 2021-03-22

* [Added] added 'app:o365' tag to Microsoft 365 incident events to support filtering.
* [Added] added SharePoint and OneDrive usage detail report aggregated metrics.
* [Fixed] updated o365 dashboards.

## 2.0.1 / 2020-12-22

* [Fixed] added requests timeout (30s)

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

* [Added] initial marketplace release.