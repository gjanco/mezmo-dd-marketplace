## Overview

The ServiceNow integration monitors the health and performance of your ServiceNow instances with rich insights into transactions, jobs, database, and cache metrics. The integration also tracks open ITSM incidents, providing actionable data points on both SLAs and the age of business impacting incidents.

## Setup

### Prerequisites

1. You must have the Datadog Agent installed and running. Additionally, you need to be able to connect to the server with the Datadog Agent installed.

### Datadog Integration Installation

1. `sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_servicenow==1.1.0`

### Datadog Integration Configuration

1. Copy the `conf.yaml.example` file.

```sh
cp /etc/datadog/conf.d/rapdev_servicenow.d/conf.yaml.example /etc/datadog/conf.d/rapdev_servicenow.d/conf.yaml
```

2. Edit `/etc/datadog/conf.d/rapdev_sevicenow.d/conf.yaml` file. Change `instance_name` to your ServiceNow instance name.

3. Statistics collection from stats.do is enabled by default. See the comments of the `/etc/datadog/conf.d/rapdev_servicenow.d/conf.yaml` for all available configuration options.

4. (Optional) If Incident metrics are being collected, then a ServiceNow Service Account must be configured by a ServiceNow admin.

    4.1 As a ServiceNow system administrator, in the target ServiceNow instance, navigate to `User Administration > Users`.

    4.2 Click `new` to create a new user.

    4.3 Name the user whatever you choose and set an appropriate password.

    4.4 Assign the user the `itil` role. If the `itil` role is not used at your organization, then the user must have __read__ access to `sys_user`, `incident`, `cmn_location`, `incident_sla`, `contract_sla`.

    4.5 Update `/etc/datadog/conf.d/rapdev_servicenow.d/conf.yaml`, uncommenting and setting the following parameters:
    ```yaml
    ## @param collect_itsm_metrics - boolean - optional - default: true
    ## collect ITSM metrics. defaults to false
    #
    collect_itsm_metrics: true

    ## @param username - string - optional - default: dd_agent
    ## the basic auth user name for collecting ITSM credentials
    #
    username: {servicenow-username}

    ## @param password - string - optional
    ## basic auth password for collecting ITSM credentials
    #
    password: {servicenow-password}
    ```
    4.6 (Optional) Update `/etc/datadog/conf.d/rapdev_servicenow.d/conf.yaml`, uncommenting and setting the following parameters for additional fields to be added as incident tags:
    ```yaml
    ## @param opt_fields - list of fields to be added as optional tags to incident metric - optional
    ## Additional fields can be found in ServiceNow Incident module
     opt_fields:
       - subcategory
       - knowledge
       - sys_class_name

    ```

5. [Restart the Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent).

### Validation

1. [Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-information) and look for `rapdev_servicenow` under the Checks section. Alternatively, you can get detailed information about the integration using the following command:

    ```
    sudo ‐u dd‐agent datadog‐agent check rapdev_servicenow
    ```

## Support
For support or feature requests, contact RapDev.io through the following channels:

 - Email: datadog-engineering@rapdev.io
 - Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
 - Phone: 855-857-0222

---

Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:datadog-engineering@rapdev.io) and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here](https://app.datadoghq.com/marketplace/app/rapdev-o365/pricing) to purchase this application.
