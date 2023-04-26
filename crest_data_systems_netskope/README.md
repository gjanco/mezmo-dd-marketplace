# Crest Data Systems Netskope

## Overview

Netskope is a cloud security platform that provides security solutions to manage and secure cloud-based applications and data. Several features include cloud access security broker (CASB), data loss prevention (DLP), threat protection, and web security.

This integration monitors alerts triggered in Netskope as well as events generated for infrastructure, network, connection, audit, application, and incident.

## Setup

### Prerequisites

1. You have the Datadog Agent installed and running.
2. You can connect to the server with the Datadog Agent.
3. You must have a Netskope API V2 token for data monitoring.

### Get an API V2 token from the Netskope Portal

1. Sign in to Netskope web portal.
2. Open `Settings` and navigate to the `Tools` section on left side bar.
3. Select `Tools`, click on `REST API v2`, and create a new token by clicking on the `NEW TOKEN` button.
4. In the `Create REST API Token` dialog box, add the following endpoints in the `SCOPE` section by clicking on `ADD ENDPOINT`:
   - `/api/v2/events/dataexport/events/alert`
   - `/api/v2/events/dataexport/events/application`
   - `/api/v2/events/dataexport/events/audit`
   - `/api/v2/events/dataexport/events/incident`
   - `/api/v2/events/dataexport/events/infrastructure`
   - `/api/v2/events/dataexport/events/network`
   - `/api/v2/events/dataexport/events/page`
5. After adding all the required endpoints, click `SAVE` and copy the token.

### Installation

To install the integration, run the following command:

- Linux:
  - `sudo -u dd-agent datadog-agent integration install --third-party datadog-crest_data_systems_netskope==1.1.0`.
- Windows:
  - `"C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-crest_data_systems_netskope==1.1.0`

### Configuration

#### Set up `datadog.yaml`

1. The `app_key` and `api_key` needs to be set in the `datadog.yaml` file if not already configured. For more information, see [Agent Configuration Files][4].

   ```yaml
   ## @param api_key - string - optional
   ## Datadog API Key
   #
   api_key: <API_KEY>

   ## @param app_key - string - required
   ## Datadog App Key
   #
   app_key: <APP_KEY>
   ```

#### Set up `conf.yaml`

1. Copy the `conf.yaml.example` file.

   ```sh
   cp /etc/datadog/conf.d/crest_data_systems_netskope.d/conf.yaml.example /etc/datadog/conf.d/crest_data_systems_netskope.d/conf.yaml
   ```

2. Edit the `/etc/datadog/conf.d/crest_data_systems_netskope.d/conf.yaml` file. Add configurations for the host, v2_api_token, events, and collect alerts.

   ```yaml
   instances:
     ## @param host - string - required
     ## The host of Netskope instance to monitor.
     #
     - host: demoenterprise.ce.goskope.com

       ## @param v2_api_token - string - required
       ## The token of Netskope API V2.
       #
       v2_api_token: <API_TOKEN>

       ## @param events - list of strings - optional - default: ['infrastructure', 'network', 'connection', 'audit', 'application', 'incident']
       ## Provide the event endpoints to monitor the events data. Only lower case characters are accepted.
       ## If no events field is provided then data will be collected for all the endpoints.
       ## If events field is found and if no value is provided then data will not be collected for any of the endpoints.
       #
       # events:
       #   - infrastructure
       #   - network
       #   - connection
       #   - audit
       #   - application
       #   - incident

       ## @param collect_alerts - boolean - required
       ## Whether to collect alert data or not. Permitted values are true and false.
       #
       collect_alerts: true

       ## @param ingest_metrics - boolean - required
       ## Whether to ingest custom metrics data to Datadog platform or not. Permitted values are true and false.
       #
       ingest_metrics: false

       ## @param min_collection_interval - number - required
       ## This changes the collection interval of the check. For more information, see:
       ## https://docs.datadoghq.com/developers/write_agent_check/#collection-interval
       #
       min_collection_interval: 15
   ```

3. Install the third-party dependency `datadog-api-client` Python package:

   ```sh
   sudo -Hu dd-agent /opt/datadog-agent/embedded/bin/pip install datadog-api-client=2.10.0
   ```

4. [Restart the Agent][1].

### Validation

[Run the Agent's status subcommand][2] and look for `crest_data_systems_netskope` under the Checks section.

Alternatively, use the following command to obtain detailed information about the integration:

```
sudo datadog-agent check crest_data_systems_netskope
```

**Note**: The following dashboards populated with metrics will be affected by the ingest_metrics parameter of conf.yaml. If metrics ingestion is disabled, these panels will not be populated.

1.  Netskope - Overview
    - Group: Connection Events Overview
      - Average Cloud Confidence Index Over Time
2.  Netskope - Application Events
    - Group: Application Event Details
      - Bytes Transferred
3.  Netskope - Connection Events
    - Group: Connection Events Overview
      - Average Cloud Confidence Index Over Time
4.  Netskope - Network Events
    - Group: Network Event Insights
      - Bytes Transferred Over Time
      - Packets Transferred Over Time
      - Maximum Session Duration Over Time

## Uninstallation

Uninstall the integration from the Datadog Agent by running the following command:

- Linux:
  - `sudo -u dd-agent -- datadog-agent integration remove datadog-crest_data_systems_netskope`
- Windows:
  - `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-crest_data_systems_netskope`

YAML Config Cleanup:

- If you plan to reinstall or need to keep the config files:
  - Navigate to your Agent's `conf.d` directory and locate the `crest_data_systems_netskope.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as API keys.
- If you plan to fully uninstall with config removal:
  - Navigate to your Agent's `conf.d` directory, and remove the `crest_data_systems_netskope.d` folder.

## Support

For support or feature requests, contact Crest Data Systems through the following channels:

- Support Email: datadog.integrations@crestdatasys.com
- Sales Email: sales@crestdatasys.com
- Website: [crestdatasys.com][3]

[1]: https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[3]: https://www.crestdatasys.com/
[4]: https://docs.datadoghq.com/agent/guide/agent-configuration-files/?tab=agentv6v7
