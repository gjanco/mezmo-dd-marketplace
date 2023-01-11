# Hardware Sentry

## Overview

**[Hardware Sentry](https://www.sentrysoftware.com/products/hardware-sentry.html)** is an agent specialized in the monitoring of the hardware components of any server, network switch, or storage system in your data center, packaged with a collection of dashboards and monitors for Datadog.

### Hardware monitoring

**Hardware Sentry** is a monitoring agent capable of reporting the physical health of servers, network switches, and storage systems. It collects metrics periodically to report the status of each processor, controller, disk, or power supply, the temperatures, the speed of the fans, the link status and speed of the network cards, etc.:

* **Remote**: One agent to monitor hundreds of systems, through SNMP, WBEM, WMI, SSH, IPMI, REST APIs, etc.
* **Multi-platform**: 100+ platforms already supported with 250+ connectors (Cisco, Dell EMC, HP, Huawei, IBM, Lenovo, NetApp, Oracle, Pure, etc. [See the full list](https://www.sentrysoftware.com/docs/hws-doc/latest/platform-requirements.html))
* **Simple**: Monitoring a system requires minimal configuration effort to specify the hostname or IP address and credentials. **Hardware Sentry** will automatically detect the available instrumentation and start the monitoring right away.
* **Normalized**: All the necessary information is reported through standardized metrics in Datadog. The same `hw.temperature` metric, for example, is used to represent the temperature in a NetApp filer, an HP BladeSystem, a Dell PowerEdge running Windows, a Cisco UCS running Linux, or any other platform. These metrics follow [OpenTelemetry's semantic conventions](https://opentelemetry.io/docs/reference/specification/metrics/semantic_conventions/hardware-metrics/).

**Hardware Sentry** comes with predefined monitors to detect and even predict failures in processors, memory modules, disks, network cards, controllers, power supplies, fans, temperature sensors, etc.

### Energy usage and carbon footprint reports

In addition to physical health monitoring, **Hardware Sentry** also reports the energy usage of each monitored system. Combined with metrics representing the electricity cost and the carbon density, the provided dashboards report the electricity usage of your infrastructure in kWh and its carbon footprint in tons of CO₂.

**100% Software**: No smart PDUs required, even for systems that are not equipped with an internal power sensor!

### Dashboards

This integration comes with a set of dashboards that leverage the metrics collected by **[Hardware Sentry OpenTelemetry Collector](https://www.sentrysoftware.com/products/hardware-sentry-opentelemetry-collector.html)**:

| Dashboard | Description |
|---|---|
| Hardware Sentry - Main | Overview of all monitored hosts, with a focus on sustainability |
| Hardware Sentry - Site | Metrics associated to one *site* (a data center or a server room) and its monitored *hosts* |
| Hardware Sentry - Host | Metrics associated to one *host* and its internal devices |

## Setup

You need to run the **Hardware Sentry** agent on-prem to collect hardware metrics from your infrastructure, and [configure its embedded OpenTelemetry Collector to push these metrics to your Datadog environment](https://www.sentrysoftware.com/docs/hws-doc/latest/integration/datadog.html).

1. [Download](https://www.sentrysoftware.com/downloads/products-for-opentelemetry.html) the latest version of [Hardware Sentry](https://www.sentrysoftware.com/products/hardware-sentry.html).
2. Follow the [installation instructions](https://www.sentrysoftware.com/docs/hws-doc/latest/install.html). (It is recommended that you install one agent on each site &mdash; that is, each data center, each server room, etc.).
3. Configure the [Datadog exporter](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/datadogexporter) in the OpenTelemetry Collector to push metrics to Datadog by [editing `otel-config.yaml`](https://www.sentrysoftware.com/docs/hws-doc/latest/integration/datadog.html), as in the example below:

    ```yaml
    exporters:
      # Datadog
      datadog/api:
        api:
          key: <apikey> # API key in your Datadog organization's settings
          # site: datadoghq.eu # Uncomment for Europe only
        metrics:
          resource_attributes_as_tags: true # IMPORTANT
    ```

4. Start the agent.
5. Configure the hosts to monitor by [editing `hws-config.yaml`](https://www.sentrysoftware.com/docs/hws-doc/latest/configuration/configure-agent.html).

To report hardware failures in Datadog, use the **Manage Monitors > Create New Monitor** interface to add all monitors listed for **Hardware Sentry** in the *Recommended* tab.

## Uninstallation

To uninstall **Hardware Sentry** and remove its integration:

1. Follow the [uninstallation instructions](https://www.sentrysoftware.com/docs/hws-otel-collector/latest/install.html) to stop and uninstall the **Hardware Sentry** agent.
2. In Datadog, navigate to your **Organization Settings** and delete the API and app key associated with this integration.
3. Delete all monitors that are prefixed with `[Hardware Sentry]`.
4. Once you've canceled your subscription through the Datadog Marketplace, your access to [Sentry Desk](https://www.sentrysoftware.com/desk) will be revoked.

## Support

A subscription to **Hardware Sentry** through the Datadog Marketplace grants access to all services provided by [Sentry Desk](https://www.sentrysoftware.com/desk):

* Technical Support through [Jira Service Management](https://sentrydesk.atlassian.net/servicedesk/customer/portals)
* Knowledge Base
* Patches

Upon subscription, your organization will receive an invitation to manage your *Sentry Desk* account.
