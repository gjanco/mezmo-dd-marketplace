# NetApp ESeries SANtricity

## Overview

This integration collects configuration and performance details from the NetApp ESeries SANtricity platform by capturing crucial metrics and visualizing the performance of array configured in the NetApp ESeries SANtricity.

## Setup

### Prerequisites

1. You have the Datadog Agent installed and running.
2. You can connect to the server with the Datadog Agent.

### NetApp ESeries SANtricity Configuration

- A user must have read permissions on the NetApp ESeries SANtricity API to configure the integration and collect data.

### Installation

To install the integration, run the following command:

- Linux:
  - `sudo -u dd-agent datadog-agent integration install --third-party datadog-crest_data_systems_netapp_eseries_santricity==1.1.0`.
- Windows:
  - `"C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-crest_data_systems_netapp_eseries_santricity==1.1.0`

### Configuration

#### Set up `datadog.yaml`

1. The app_key and api_key needs to be set in the `datadog.yaml` file. For more information, see [Agent Configuration Files][4].

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
   cp /etc/datadog/conf.d/crest_data_systems_netapp_eseries_santricity.d/conf.yaml.example /etc/datadog/conf.d/crest_data_systems_netapp_eseries_santricity.d/conf.yaml
   ```

2. Edit the `/etc/datadog/conf.d/crest_data_systems_netapp_eseries_santricity.d/conf.yaml` file. Add configurations for the IP address, username, password, and port.

   ```yaml
    init_config:

    instances:

        ## @param address - string - required
        ## The IP address and port (separated by a colon) of the Web Services Proxy. For example: 10.1.1.1:8443
        #
       - address: <ADDRESS>

        ## @param username - string - required
        ## Username of the web service proxy
        #
        username: <USERNAME>

        ## @param tenant_id - string - required
        ## password of the web service proxy
        #
        password: <PASSWORD>

        ## @param verify_ssl - bool/cert path - required
        ## SSL verification flag of the web service proxy
        #
        verify_ssl: False

        ## @param system_id - string - required
        ## System ID: The GUID of the target array
        #
        system_id: <SYSTEM_ID>

        ## @param log_index - string - required
        ## Index of Log in Datadog platform
        #
        log_index: main

        min_collection_interval: 600
   ```

3. Install the third-party dependency `datadog-api-client` Python package:

   ```sh
   sudo -Hu dd-agent /opt/datadog-agent/embedded/bin/pip install datadog-api-client
   ```

4. [Restart the Agent][1].

### Validation

[Run the Agent's status subcommand][2] and look for `crest_data_systems_netapp_eseries_santricity` under the Checks section.

Alternatively, use the following command to obtain detailed information about the integration:

```
sudo datadog‐agent check crest_data_systems_netapp_eseries_santricity
```

## Uninstallation

Uninstall the integration from the Datadog Agent by running the following command:

- Linux:
  - `sudo -u dd-agent datadog-agent integration remove datadog-crest_data_systems_netapp_eseries_santricity`
- Windows:
  - `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-crest_data_systems_netapp_eseries_santricity`

YAML Config Cleanup:

- If you plan to reinstall or need to keep the config files:
  - Navigate to your Agent's `conf.d` directory and locate the `crest_data_systems_netapp_eseries_santricity.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as API keys.
- If you plan to fully uninstall with config removal:
  - Navigate to your Agent's `conf.d` directory, and remove the `crest_data_systems_netapp_eseries_santricity.d` folder.

## Support

For support or feature requests, contact Crest Data Systems through the following channels:

- Support Email: datadog.integrations@crestdatasys.com
- Sales Email: sales@crestdatasys.com
- Website: [crestdatasys.com][3]

[1]: https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[3]: https://www.crestdatasys.com/
[4]: https://docs.datadoghq.com/agent/guide/agent-configuration-files/?tab=agentv6v7
