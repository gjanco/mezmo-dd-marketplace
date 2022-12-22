## Overview

The ServiceNow integration monitors the health and performance of your ServiceNow instances with rich insights into transactions, jobs, database, and cache metrics. The integration also tracks open ITSM incidents, providing actionable data points on both SLAs and the age of business impacting incidents.

## Setup

### Prerequisites

1. You must have the Datadog Agent installed and running. Additionally, you need to be able to connect to the server with the Datadog Agent installed.

### Installation

1. `sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_servicenow==1.2.4`

### Configuration

1. Copy the `conf.yaml.example` file.

```sh
cp /etc/datadog/conf.d/rapdev_servicenow.d/conf.yaml.example /etc/datadog/conf.d/rapdev_servicenow.d/conf.yaml
```

2. Edit `/etc/datadog/conf.d/rapdev_sevicenow.d/conf.yaml` file. Change `instance_name` to your ServiceNow instance name.

3. Statistics collection from stats.do is enabled by default. See the comments of the `/etc/datadog/conf.d/rapdev_servicenow.d/conf.yaml` for all available configuration options.
   
   3.1 Default access to `stats.do` is enabled out of the box in ServiceNow. 

   3.2 If authentication is required to access `stats.do` in the ServiceNow account, install the [ServiceNow Monitoring - Datadog UpdateSet](https://files.rapdev.io/public/ServiceNow+Monitoring+-+Datadog+-+1.0.0.xml) following the linked [instructions](https://docs.servicenow.com/en-US/bundle/tokyo-application-development/page/build/system-update-sets/task/t_CommitAnUpdateSet.html)

   3.3 In the `/etc/datadog/conf.d/rapdev_servicenow.d/conf.yaml`, uncomment the following parameters to configure Datadog to use authenticated stats.do:
   ```yaml
       
    ## @param statsdo_auth - boolean - optional - default: false
    ## require auth to collect metrics from stats.do.
    #
    # statsdo_auth: false

    ## @param username - string - optional - default: dd_agent
    ## the basic auth user name for collecting ITSM credentials
    #
    username: {servicenow-username}

    ## @param password - string - optional
    ## basic auth password for collecting ITSM credentials
    #
    password: {servicenow-password}
    ```
    
    3.4 Set `statsdo_auth` to the value `true`

    3.5 Provide the user credentials for authentication using Basic Auth to access ServiceNow's authenticated stats.do.


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
    4.7 (Optional) Update `/etc/datadog/conf.d/rapdev_servicenow.d/conf.yaml`, uncommenting and setting the time format to match the ServiceNow settings:
    ```yaml
    ## @param time_format
    time_format: "%Y-%m-%d %H:%M:%S"
    ```
5. [Install optional Custom Python Packages to the Agent](https://docs.datadoghq.com/developers/guide/custom-python-package/?tab=linux). Optional packages include beautifulsoup and lxml.

5. [Restart the Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent).

### Validation

1. [Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-information) and look for `rapdev_servicenow` under the Checks section. Alternatively, you can get detailed information about the integration using the following command:

    ```
    sudo ‐u dd‐agent datadog‐agent check rapdev_servicenow
    ```

## Uninstallation

### Agent Integration Uninstall 

1. Run the following command to remove the integration:

    - Linux: `sudo -u dd-agent datadog-agent integration remove datadog-rapdev_servicenow`

    - Windows: `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-rapdev_servicenow”`
        
2. Restart the Datadog Agent by using your OS's [Restart Command](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#restart-the-agent).

3. Run the Agent status command as described in the Validation section, and verify the integration is no longer running.

YAML Config Cleanup:
- If you plan to reinstall or need to keep the config files:
    - Navigate to your Agent's `conf.d` directory and locate the `rapdev_servicenow.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as API keys.
    
- If you plan to fully uninstall with config removal:
    - Navigate to your Agent's `conf.d` directory, and remove the `rapdev_servicenow.d` folder.

ServiceNow Cleanup:
- As a best practice, remove any associated API keys and users created exclusively for this integration. For more details, reference the Configuration section.

For any questions or problems, view our Support section for ways to get in touch.

## Support
For support or feature requests, contact RapDev.io through the following channels:

 - Email: support@rapdev.io
 - Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
 - Phone: 855-857-0222

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

---

Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:support@rapdev.io) and we'll build it!!*
