# SAP NetWeaver

## Overview
The SAP NetWeaver integration monitors ABAP and J2EE stacks of the SAP **NetWeaver** and **S/4HANA** application platforms.

Using remote **agentless**  connection and preconfigured monitoring templates, this integration can go live in just a **few minutes**

Monitoring is powered by AGENTIL Software's [Pro.Monitor](https://www.agentil-software.com) platform. It is configured out of the box to cover the most relevant modules and transactions of your SAP systems: **shortdumps, SAP jobs, transaction response times, work processes, etc...**

This integration collects and analyzes data from systems in real time and produces metrics and actionable events. You can finely tune the alerts by configuring Pro.Monitor and create Datadog monitors directly on the metrics.

### Monitored modules

- ABAP instance memory
- ABAP instance response time
- ABAP locks
- ABAP parameters
- ABAP shortdumps
- Application logs
- Batch inputs
- Certificates
- Custom CCMS monitoring
- Database backups
- Database size
- DB exclusive locks
- Dispatcher queues
- ICM status and usage
- IDOC exchange monitoring
- Instances availability
- Number ranges
- PI/XI messages ABAP
- Process chains monitoring
- QRFC/TRFC
- Real time data
- RFC destinations availability
- SAP buffers
- SAP clients change settings
- SAPconnect (SCOT/SOST)
- SAP jobs monitoring
- SAP transaction times
- SAP transports
- SAP users
- Spools
- System logs
- Update requests
- Update service
- Work processes

## Setup
A Pro.Monitor collector acts as a proxy between Datadog and your SAP systems. The collector remotely connects to the systems.
### Prerequisites
- A Pro.Monitor license, requested at `support@agentil-software.com`.
- A dedicated Linux VM
- Network routes open toward SAP application ports
- A dedicated communication user created on each system
- See [AGENTIL's Pro.Monitor Prerequisites Documentation](https://wiki.agentil-software.com/doku.php?id=products:promonitor:6.8:installguide:prerequisites) for more details.

### Installation
- [Install the JAVA JRE](https://wiki.agentil-software.com/doku.php?id=products:cockpit:1.0:installguide:installjava)
- Download the latest [Pro.Monitor package](https://agentil.box.com/s/k0yp1tk58r666rfncf0nb9k1qa0guvdc).
- Copy the package into a temporary folder  - **Not in `/opt`**

```shell
tar -zxvf [PACKAGE FILE NAME]
./install.sh
systemctl start promonitor
```

Pro.Monitor should be up and running.

### Configuration
#### Connection to Datadog 
You can configure Pro.Monitor using a web interface.
- Visit `http://[PRO.MONITOR VM HOSTNAME]:8888` in a web browser. The default username/password combination is admin/admin 
- Click the gear icon on the top right to open a menu. Then, select **Plugins**.
- Select the Datadog type in the plugin selector and press create.
- Set your Datadog instance URL as such: https://api.datadoghq.[SUFFIX] (replace [SUFFIX] by the extension of your instance: com/eu/...)
- Register your Datadog API and APP keys.
- Pro.Monitor is now connected to your Datadog instance.
#### Connection to SAP
- Create the necessary groups, systems, and connectors to define how to connect to your SAP systems. You can do this by selecting **Options** in the left panel. A **group** contains multiple **systems**, which are each identified by SID.
    - Create systems in your groups.
    - Create **user profiles** using the configuration menu. Register access credentials to the SAP systems.
    - Create **connectors** in each system. A connector defines connection parameters, such as host, port, and user profile (created above).
- Get the latest [SAP JCO driver](https://softwaredownloads.sap.com/file/0020000000507122021) for Linux and unzip the file to extract a tgz archive.
- Click the gear icon on the top right to open a menu. Then, select **Admin configuration** and go the **Upload/Download** section.
- Click on **Install JCO driver** and select the driver file (file name similar to sapjco30P_17-10005328_linux.tgz).
#### Start monitoring
- Select and apply monitoring profiles.
    - From the **Profiles** section in left menu, click on **Select default profiles**.
    - Select the Datadog profile, causing it to appear into your list of default profiles.
    - Press **Assign** to assign the profile to all your systems.
- Activate the monitoring: Go to **System view**, select all connectors then **Bulk Action** > **Activate**.

There are several ways to register your SAP systems. See the [product documentation](https://wiki.agentil-software.com/doku.php?id=products:promonitor:6.8:userguide:configuration) for a complete overview.
Monitoring is now active for all your systems, which you should see in Datadog.

## Uninstallation
1. Connect to the Pro.Monitor server using an SSH client
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

