# Microsoft 365 Defender

## Overview

This integration collects endpoint details, vulnerabilities, alerts, and incidents from the Microsoft 365 Defender for Endpoint platform. It also provides information on the missing KBs on endpoints. This integration provides various out of the box dashboards and a monitor to alert for the missing KBs on endpoints.

> Note: Our recommendation is Datadog's "Microsoft 365 Defender" integration if you're seeking a consolidated solution for four different defender services (Endpoint, Cloud Apps, Office 365, Identity).

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

### Microsoft Defender Configuration

1. Log in to your Azure Account.
2. Search for App Registrations in the search bar of Azure Portal.
3. Click on New Registration.
4. Give a name to App and Select the Supported account types as Accounts in any organizational directory (Any Azure AD directory - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)
5. Click on Register.
6. App's Overview page will have the Application (client) Id under Essential section and that would be Client ID of Application that we will use in authentication.
7. Generate Client Secret by navigating Certificates & Secrets.
8. Click on New client secret.
9. Give any description and set the Expiration time (Note: Max 2 years can be set).
10. Copy the secret value and it wiil be used as Client Secret.
11. After that navigate to API Permissions.
12. Click on Add a Permission and select Microsoft Graph.
13. Under Request API permissions, select API permissions. Then, click Add permissions. You need to provide the following permissions:
    1. MicrosoftGraph.User.Read
    2. MicrosoftThreatProtection.AdvanceHunting.Read.All
    3. MicrosoftThreatProtection.CustomDetection.ReadWrite.All
    4. MicrosoftThreatProtection.Incident.Read.All
    5. MicrosoftThreatProtection.IncidentWrite.All
    6. WindowsDefenderATP.AdvancedQuery.Read.All
    7. WindowsDefenderATP.Alert.Read.All
    8. WindowsDefenderATP.Alert.ReadWrite.All
    9. WindowsDefenderATP.Event.Write
    10. WindowsDefenderATP.File.Read.All
    11. WindowsDefenderATP.IntegrationConfiguration.ReadWrite.All
    12. WindowsDefenderATP.IP.Read.All
    13. WindowsDefenderATP.Library.Manage
    14. WindowsDefenderATP.Machine.CollectForensics
    15. WindowsDefenderATP.Machine.Isolate
    16. WindowsDefenderATP.Machine.LiveResponse
    17. WindowsDefenderATP.Machine.Offboard
    18. WindowsDefenderATP.Machine.Read.All
    19. WindowsDefenderATP.Machine.ReadWrite.All
    20. WindowsDefenderATP.Machine.RistrictExecution
    21. WindowsDefenderATP.Machine.Scan
    22. WindowsDefenderATP.Machine.StopAndQuarantine
    23. WindowsDefenderATP.RemediationTask.Read.All
    24. WindowsDefenderATP.SecurityBaselinesAssessment.Read.All
    25. WindowsDefenderATP.SecurityConfiguration.Read.All
    26. WindowsDefenderATP.SecurityConfiguration.ReadWrite.All
    27. WindowsDefenderATP.SecurityRecommendations.Read.All
    28. WindowsDefenderATP.Software.Read.All
    29. WindowsDefenderATP.Ti.Read.All
    30. WindowsDefenderATP.Ti.ReadWrite
    31. WindowsDefenderATP.Ti.ReadWrite.All
    32. WindowsDefenderATP.Url.Read.All
    33. WindowsDefenderATP.User.Read.All
    34. WindowsDefenderATP.Vulnerability.Read.All
14. After selecting all permissions, click on **Add Permission**.
15. After that click on the "Grant admin for consent" button.
16. After saving make sure the above-mentioned permissions are added.
17. Now we can use the Client ID and Client Secret for the integration.

### Datadog Integration Installation

To install the integration, run the following command:

- Linux:
  - `sudo -u dd-agent datadog-agent integration install --third-party datadog-crest_data_systems_microsoft_defender==1.0.2`
- Windows:
  - `"C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-crest_data_systems_microsoft_defender==1.0.2`

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

1.  Navigate to the **Monitors** tab within Datadog.
2.  Click on **New Monitor** and then click on the **Recommended Monitors** tab.
3.  Search for the **Crest Data Systems Microsoft Defender** monitor.

## Uninstallation

Uninstall the integration from the Datadog agent by running the following command:

- Linux:
  - `sudo -u dd-agent datadog-agent integration remove datadog-crest_data_systems_microsoft_defender`
- Windows:
  - `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-crest_data_systems_microsoft_defender`

YAML Config Cleanup:

- If you plan to reinstall or need to keep the config files:
  - Navigate to your Agent's `conf.d` directory and locate the `crest_data_systems_microsoft_defender.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as API keys.
- If you plan to fully uninstall with config removal:
  - Navigate to your Agent's `conf.d` directory, and remove the `crest_data_systems_microsoft_defender.d` folder.

## Support

For support or feature requests, contact Crest Data Systems through the following channels:

- Support Email: datadog.integrations@crestdatasys.com
- Sales Email: sales@crestdatasys.com
- Website: [crestdatasys.com](https://www.crestdatasys.com/microsoft-365-defender-integration/)
