# Microsoft 365 Defender

## Overview

This integration collects endpoint details, vulnerabilities, alerts, and incidents from the Microsoft 365 Defender for Endpoint platform. It also provides information on the missing KBs on endpoints. This integration provides various out of the box dashboards and a monitor to alert for the missing KBs on endpoints.

### Monitors

 - Missing KBs of Endpoint

### Dashboards

 - Microsoft 365 Defender Endpoint Overview
 - Endpoint Overview
 - Alerts Overview
 - Threats and Vulnerability Overview
 - Software Overview
 - Incident Overview

## Setup

### Prerequisites

1. You have the Datadog Agent installed and running. 
2. You can connect to the server with the Datadog Agent.

### Datadog Integration Installation

To install the integration, run: `sudo -u dd-agent datadog-agent integration install --third-party datadog-crest_data_systems_microsoft_defender==1.0.1`

### Datadog Integration Configuration

1. Copy the `conf.yaml.example` file:

   ```sh
   cp /etc/datadog/conf.d/crest_data_systems_microsoft_defender.d/conf.yaml.example /etc/datadog/conf.d/crest_data_systems_microsoft_defender.d/conf.yaml
   ```

2. Edit the `/etc/datadog/conf.d/crest_data_systems_microsoft_defender.d/conf.yaml` file to add the configuration of Client ID, Client Secret, Tenant ID, API key, and App key:

   ```yaml
   init_config:
   
   instances:
   
       ## @param client_id - string - required
       ## Client ID of registered Application in Azure
       #
       - client_id: <CLIENT_ID>
   
       ## @param client_secret - string - required
       ## Client Secret of registered Application in Azure
       #
       client_secret: <CLIENT_SECRET>
   
       ## @param tenant_id - string - required
       ## Tenant Id of your organization in Azure
       #
       tenant_id: <TENANT_ID>
   
       ## @param api_key - string - required
       ## API Key of Datadog Platform
       #
       api_key: <API_KEY>
   
       ## @param app_key - string - required
       ## App Key of Datadog Platform
       #
       app_key: <APP_KEY>
   
       ## @param is_recover - boolean - optional - default: true
       ## If true then it will recover data in case of 429 status code.
       #
       # is_recover: true
   
       ## @param min_collection_interval - number - required
       ## This changes the collection interval of the check. For more information, see:
       ## https://docs.datadoghq.com/developers/write_agent_check/#collection-interval
       #
       min_collection_interval: 7200
   ```

3. Install the third-party dependency `datadog-api-client` python package:

   ```sh
   sudo -Hu dd-agent /opt/datadog-agent/embedded/bin/pip install datadog-api-client
   ```

4. [Restart the Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent).

### Validation

[Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information) and look for `crest_data_systems_microsoft_defender` under the Checks section. 
 
Alternatively, you can get detailed information about the integration using the following command:

    ```
    sudo -u dd‐agent datadog-agent check crest_data_systems_microsoft_defender
    ```

### Monitor Configuration

 1. Navigate to the **Monitors** tab within Datadog.
 2. Click on **New Monitor** and then click on the **Recommended Monitors** tab.
 3. Search for the **Crest Data Systems Microsoft Defender** monitor.

## Support

For support or feature requests, contact Crest Data Systems through the following channel:

 - Email: datadog.integrations@crestdatasys.com
 - Website: [crestdatasys.com](https://www.crestdatasys.com/microsoft-365-defender-integration/)
 