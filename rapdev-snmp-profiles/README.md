# RapDev SNMP Profiles
## Overview

[![RapDev SNMP Profiles Introduction](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev-snmp-profiles/images/video.png)](https://www.youtube.com/watch?v=SVT9hqV7aD4&list=PLa2zzueYDhHrjODIXryBX_RakQIL6nmOh)

The RapDev SNMP Profiles package supports over 150 device profiles natively, and has pre-built dashboards for all supported hardware devices to help you monitor them instantly. Several hundred hours have gone into tuning the profiles to ensure that they collect all relevant metrics with the necessary tags, including serial numbers, firmware versions, hardware versions, and more. This integration can be deployed in minutes and start monitoring, visualizing, and alerting immediately.

The integration will give you access to hundreds of YAML profiles, and will auto-deploy a number of new dashboards on your instance. It will then use the native Datadog SNMP Autodiscovery to automatically detect any supported hardware, and start polling the OIDs using the native Datadog SNMP integration.
There is no need for you to manage, edit, modify, or update any SNMP profiles on your Datadog agent or YAML. All of that is taken care of with this integration, and you can simply start monitoring and alerting.

Below are some screenshots of the dashboards that come out of the box with this integration.

### Dashboard for Cisco Meraki
![Screenshot6](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev-snmp-profiles/images/6.png)

### Dashboard for Palo Alto firewalls
![Screenshot2](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev-snmp-profiles/images/2.png)

### Dashboard for Dell iDRAC servers
![Screenshot3](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev-snmp-profiles/images/3.png)

### Sample of tags collected for server hardware
![Screenshot5](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev-snmp-profiles/images/5.png)

### Sample list of metrics collected for HP iLO3/4
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev-snmp-profiles/images/1.png)

### Sample list of metrics collected for Dell iDRAC
![Screenshot4](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev-snmp-profiles/images/4.png)

Below is a list of the currently supported devices, please visit our website for a full updated list of all devices.

| Manufacturer | Model                 | Version       |
| ------------ | --------------------- | ------------- |
| Dell         | iDRAC                 | 7             |
| Dell         | iDRAC                 | 8             |
| Dell         | iDRAC                 | 9             |
| HP           | ProLiant Gen8         | iLO 4         |
| HP           | ProLiant Gen9         | iLO 4         |
| HP           | ProLiant Gen10        | iLO 5         |
| APC          | Smart UPS             | All           |
| APC          | SmartCard             | All           |
| F5           | Big-IP                | 9.4.x to 15.x |
| Cisco        | ASA                   | 5505          |
| Cisco        | ASA                   | 5510          |
| Cisco        | ASA                   | 5525          |
| Cisco        | ASA                   | 5540          |
| Cisco        | UCS                   | M2            |
| Cisco        | UCS                   | M3            |
| Cisco        | UCS                   | M4            |
| Cisco        | Catalyst              | 2960          |
| Cisco        | Catalyst              | 3650          |
| Cisco        | Catalyst              | 4500          |
| Cisco        | Catalyst              | 3750          |
| Cisco        | Nexus                 | 2k            |
| Cisco        | Nexus                 | 3k            |
| Cisco        | Nexus                 | 4k            |
| Cisco        | Nexus                 | 5k            |
| Cisco        | Nexus                 | 6k            |
| Cisco        | Nexus                 | 7k            |
| Cisco        | Nexus                 | 9k            |
| Cisco        | ISR                   | 44XX          |
| Cisco        | ISR                   | 38XX          |
| Cisco        | CUBE                  | IOS           |
| Cisco        | Unified Call Manager  | 8.x to 12.x   |
| Cisco        | ASR                   | All           |
| Checkpoint   | GAIA                  | 77 to 80.30   |
| Checkpoint   | Cloud Firewall        | 77 to 80.30   |
| Barracuda    | Next Gen Firewall     | 6, 7, 8       |
| Barracuda    | SPAM Filter           | 6, 7, 8       |
| Palo Alto    | Next Gen Firewall     | 9.x           |
| Nutanix      | Cluster               | All           |
| Nutanix      | Container Stats       | All           |
| Nutanix      | Controllers           | All           |
| Nutanix      | Disks                 | All           |
| Nutanix      | Hypervisors           | All           |
| Nutanix      | Storage Pools         | All           |
| Nutanix      | Virtual Machine Stats | All           |
| FortiNet     | FortiGate             | All           |
| Cisco        | Meraki                | MR-Series     |
| Cisco        | Meraki                | Z-Series      |
| Cisco        | Meraki                | MX-Series     |
| Cisco        | Meraki                | MS-Series     |
| Dell         | Powerconnect          | 2000          |
| Dell         | Powerconnect          | 3000          |
| Dell         | Powerconnect          | 5000          |
| Dell         | Powerconnect          | 6000          |
| Dell         | Powerconnect          | 7000          |
| Dell         | Powerconnect          | 8000          |
| Dell         | PowerEdge Chassis     | M1000e        |
| Dell         | PowerEdge Chassis     | MX7000        |
| HP           | C7000                 | All           |
| Citrix       | Netscaler             | All           |
| Kemp         | Loadmaster            | All           |
| Arista       | Ethernet Switches     | 7500          |
| Arista       | Ethernet Switches     | 7400          |
| Arista       | Ethernet Switches     | 7300          |
| Arista       | Ethernet Switches     | 7200          |
| Arista       | Ethernet Switches     | 7100          |

## Setup

1. Delete the default DataDog profiles in the following directories: 

Linux\
`/etc/datadog-agent/conf.d/snmp.d/profiles/*`\
`/opt/datadog-agent/embedded/lib/python<VER>/site-packages/datadog_checks/snmp/data/profiles/*`
 
 Windows\
 `%PROGRAMDATA%\Datadog\conf.d\snmp.d\profiles\*`\
 `%PROGRAMFILES%\Datadog\Datadog Agent\embedded\lib\site-packages\datadog_checks\snmp\data\profiles\*`

2. Download the [snmp-profiles.zip](https://files.rapdev.io/datadog/snmp-profiles.zip) file from RapDev's site.

3. Unzip the snmp-profiles.zip file, and move the `snmp-profiles\profiles` into the Datadog SNMP profiles directory on the system that has the Datadog agent installed. This includes moving any of the cisco profiles out of the downloaded `snmp-profiles\profiles\cisco` directory into:

Linux\
`/etc/datadog-agent/conf.d/snmp.d/profiles/`

Windows\
`%PROGRAMDATA%\Datadog\conf.d\snmp.d\profiles\`

4. Fill in your conf.yaml with the necessary IP or network addresses for discovery. See the file `snmp-profiles\conf.yaml.example_rapdev` for example configuration.

## Tiered Pricing

| SNMP Devices       | $ / Device / Month |
| ------------------ | ------------------ |
| 1 - 49             | $6                 |
| 50 - 99            | $5                 |
| 100 - 499          | $4.50              |
| 500+               | $4                 |

## Support
For support or feature requests please contact RapDev.io through the following channels: 

 - Email: integrations@rapdev.io 
 - Chat: [RapDev.io/products](https://rapdev.io/products)
 - Phone: 855-857-0222 

Made with ❤️  in Boston

 ---

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:integrations@rapdev.io) and we'll build it!!*

