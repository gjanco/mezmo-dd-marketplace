# SAP BusinessObjects

## Overview
The SAP BusinessObjects integration monitors SAP **BusinessObjects** systems.

This integration uses a remote agentless connection and preconfigured monitoring templates, enabling it to go live in a few minutes.

Monitoring is powered by AGENTIL Software's [Pro.Monitor](https://www.agentil-software.com) platform, which is configured out of the box to cover the most relevant modules and transactions of your SAP systems: **connections**, **services**, **reports**, **schedules**, **audit warnings**, etc.

This integration collects and analyzes data from systems in real time, and produces metrics and actionable events. You can create customized alerts on this data by configuring Pro.Monitor or by creating Datadog monitors directly on the metrics.

### Monitored modules

- Server status
- Concurrent users
- Server metrics
- Server properties
- Schedules and reports
- CMC and audit warnings

## Setup
A Pro.Monitor collector acts as a proxy between Datadog and your SAP systems. The collector remotely connects to your SAP systems.

### Prerequisites

- A Pro.Monitor license, which you can request by emailing [support@agentil-software.com](mailto:support@agentil-software.com).
- A dedicated Linux VM.
- Network routes open toward SAP application ports.
- A dedicated communication user created on each system.

See [AGENTIL's Pro.Monitor Prerequisites Documentation](https://wiki.agentil-software.com/doku.php?id=products:promonitor:6.8:installguide:prerequisites) for more details.

### Installation
- [Install the JAVA JRE](https://wiki.agentil-software.com/doku.php?id=products:cockpit:1.0:installguide:installjava).
- Download the latest [Pro.Monitor package](https://agentil.box.com/s/k0yp1tk58r666rfncf0nb9k1qa0guvdc).
- Copy the package into a temporary folder. **Note**: Do not copy it into `/opt`.

Run the following commands in your shell: 
```shell
tar -zxvf [PACKAGE FILE NAME]
./install.sh
systemctl start promonitor
```

Pro.Monitor is now running.

### Configuration
#### Connection to Datadog 
You can configure Pro.Monitor using a web interface.
- Visit `http://[PRO.MONITOR VM HOSTNAME]:8888` in a web browser. The default username/password combination is `admin`/`admin`.
- Click the gear icon on the top right to open a menu. Then, select **Plugins**.
- Select the Datadog type in the plugin selector and press create.
- Set your Datadog instance URL as `https://api.datadoghq.[SUFFIX]` and replace `[SUFFIX]` with the extension of your instance, for example: `com` or `eu`.
- Register your Datadog API and application keys.
- Pro.Monitor is now connected to your Datadog instance.
#### Connection to SAP
- Create the necessary groups, systems, and connectors to define how to connect to your SAP systems. You can do this by selecting **Options** in the left panel. A **group** contains multiple **systems**, which are each identified by SID.
    - Create systems in your groups.
    - Create **user profiles** using the configuration menu. Register access credentials to the SAP systems.
    - Create **connectors** in each system. A connector defines connection parameters, such as host, port, and user profile (created above).
#### Start monitoring
- Select and apply monitoring profiles.
    - From the **Profiles** section in left menu, click on **Select default profiles**.
    - Select the Datadog profile, adding it to your list of default profiles.
    - Press **Assign** to assign the profile to all your systems.
- Activate the monitoring: Go to **System view**, select all connectors, then click **Bulk Action** > **Activate**.

There are several ways to register your SAP systems. See the [product documentation](https://wiki.agentil-software.com/doku.php?id=products:promonitor:6.8:userguide:configuration) for a complete overview.
Monitoring is now active for all your systems, which you should see in Datadog.

## Uninstallation

1. Connect to the Pro.Monitor server using an SSH client.
2. Stop Pro.Monitor service and remove installed files by running the following commands:
```shell
systemctl stop promonitor
rm -rf /opt/Pro.Monitor*
rm -f /etc/systemd/system/promonitor.service
```
## Support
For support or feature requests, contact AGENTIL Software at support@agentil-software.com

*If you are looking for a trustworthy partner for specific integrations with SAP or other platforms, you are in the right place - just get in touch with us.*

---
This product is engineered and developed in Geneva, Switzerland. 

