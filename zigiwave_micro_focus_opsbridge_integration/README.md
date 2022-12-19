# Micro Focus OpsBridge Integration


## Overview

ZigiOps is the most flexible, no-code integration platform. The ZigiOps product
helps your businesses identify, report, and resolve issues in your IT 
environments faster than ever. Integrate ZigiOps into your software ecosystem to connect to popular enterprise 
software tools for ITSM, ITOM, and DevOps: Jira, ServiceNow, VMware 
vROps, Micro Focus Ops Bridge, BMC, Cherwell, Splunk, and more.

### Datadog – Micro Focus OBM Integration with ZigiOps

With the ZigiWave Datadog - OpsBridge integration, you can extract incidents from OpsBridge and populate them in Datadog. ZigiOps syncs all fields such as the incident summary, detection method, severity, status, and more. This integration is bi-directional so whenever there is an update in either Datadog or OpsBridge, ZigiOps will automatically send that update to the relevant system.


Datadog Autodiscovery finds hosts that are not in
the OpsBridge database but need to be monitored. ZigiOps takes the host 
information and reports it to OpsBridge RTSM, enriching the topology 
information with data from Datadog. The topology is kept up-to-date with 
regular checks by ZigiOps.

ZigiOps collects Datadog events and reports them to OpsBridge as events.
The platform syncs all related host details such as metrics, topology, and more.

ZigiOps collects Datadog metrics and reports them, along with related host information, to the MF Operations 
Connector. These metrics can then be 
accessed by the OpsBridge Performance Perspective and used for 
building dashboards. 

This integration will give your IT Operations team a bird’s eye view of
your OpsBridge infrastructure and help detect issues before they become real 
problems.

### Topology, Metrics, Events, Incidents

ZigiOps offers fully customizable integration templates for four use cases of the Datadog – Micro Focus OBM integration. The templates help users to quickly start to begin seeing data flow. Users can modify data mappings and filters provided by the templates to fit their use case. We currently have these templates available: OpsBridge events - Datadog incidents, Datadog events - OpsBridge events,  Datadog metrics - OBM metrics, and Datadog hosts - OBM topology. If your use case doesn’t fit any of those templates, you can also create your own integration from scratch. Integration consultants will guide you along the way.

## Setup

A member of the ZigiWave team will be in touch with you via email to provide access to the ZigiOps environment and set up your 14-day free trial. After the trial expires, they will get in touch again to see if you would like to subscribe and continue using ZigiOps. Trials are subject to 30-day extensions in case users need more time to test ZigiOps.

**Step 1** 

For the on-prem version of the tool, the first step of the integration process is to install ZigiOps. For the cloud version, the process starts by simply logging in from the UI for the cloud version. Either way, it only takes a few clicks.

After logging into ZigiOps, you are taken to the Dashboard. It provides valuable information regarding the health and status of your integrations, as well as other important information such as licenses, troubleshooting options, and more.  

**Step 2**

Open the menu and choose the systems that you'd like to connect. For this integration, select Datadog and MicroFocus OpsBridge. You can connect to Datadog with your instance URLs and API keys. The connection to OpsBridge is done with your instance URL, admin, and password. Once this information is entered, ZigiOps checks if the connection is successful.

**Step 3**

Once the connection to your systems is verified, you can go to the “Configurator” menu and choose a ready-to-use integration template and load it. Our templates are fully-customizable. You can configure all the fields that you'd like to synchronize between the two systems. You can also start an integration from scratch. Our integration consultants will guide you through the configuration from start to finish in case you start from scratch.

**Step 4**

Once you load a template or create a new integration from scratch, you will need to define the target system and destination system for the integration. Once completed, the following actions must also be configured: data collection, filtering, conditions, and field mappings. 

Once completed, save the integration and it will start syncing data between Datadog and OpsBridge. If you need any help with customizations or setting up your integrations, our consultants can guide you. 


Visit our [MicroFocus integration documentation](https://zigiwave.com/microfocus-integrations/) for more details on setting up your integrations.

## Uninstallation

1. Log into your ZigiOps instance.
2. Navigate to Connected Systems and remove the connection between Datadog and MicroFocus OpsBridge.
3. Log into Datadog.
4. Delete any associated API and Application keys.

## Support

ZigiWave is dedicated to providing the best customer experience 
for our users.  If you are an existing user, you can submit a ticket from 
support.zigiwave.com or email our team at support@zigiwave.com. 
