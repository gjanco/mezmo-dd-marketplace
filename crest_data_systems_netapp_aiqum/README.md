# Crest Data Systems NetApp AIQUM

## Overview

This integration monitors the performance and usage of NetApp AIQUM Cluster, Aggregate, QTree, Interface, Port, FibreChannel, and Volume. It captures crucial metrics and provides insight into the storage and performance of the NetApp AIQUM Data.

### Monitors

This integration monitors NetApp AIQUM Cluster, Aggregate, QTree, Interface, Port, FibreChannel, and Volume.

## Setup

### Prerequisites

1. You have the Datadog Agent installed and running.
2. You can connect to the server with the Datadog Agent.

### NetApp AIQUM Configuration

- A user must have read permissions on the NetApp AIQUM API to configure the integration and collect data.

### Installation

To install the integration, run the following command:

- Linux:
  - `sudo -u dd-agent datadog-agent integration install --third-party datadog-crest_data_systems_netapp_aiqum==1.0.1`.
- Windows:
  - `"C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-crest_data_systems_netapp_aiqum==1.0.1`

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
   cp /etc/datadog/conf.d/crest_data_systems_netapp_aiqum.d/conf.yaml.example /etc/datadog/conf.d/crest_data_systems_netapp_aiqum.d/conf.yaml
   ```

2. Edit the `/etc/datadog/conf.d/crest_data_systems_netapp_aiqum.d/conf.yaml` file. Add configurations for the IP address, username, password, and port.

   ```yaml
    init_config:

    instances:
        ## @param host - string - required
        ## The IP address and port (separated by a colon) where the Web Services Proxy is running with protocol (HTTP or HTTPS). For example: https://10.1.0.1:8443.
        #
       - host: <HOST>

        ## @param username - string - required
        ## Username of the NetApp AIQUM
        #
        username: <USERNAME>

        ## @param password - string - required
        ## Password of the NetApp AIQUM
        #
        password: <PASSWORD>

        ## @param verify_ssl - bool - optional
        ## SSL verification of the web service proxy
        #
        verify_ssl: <VERIFY_SSL>

        ## @param ca_cert_file - string - optional
        ## CA Certificate file path for SSL verification
        ca_cert_file: <CA_CERT_FILE>

        ## @param min_collection_interval - number - required
        ## This changes the collection interval of the check. For more information, see:
        ## https://docs.datadoghq.com/developers/write_agent_check/#collection-interval
        #
        min_collection_interval: 600
   ```

3. Install the third-party dependency `datadog-api-client` Python package:

   ```sh
   sudo -Hu dd-agent /opt/datadog-agent/embedded/bin/pip install datadog-api-client
   ```

4. [Restart the Agent][1].

### Validation

[Run the Agent's status subcommand][2] and look for `crest_data_systems_netapp_aiqum` under the Checks section.

Alternatively, use the following command to obtain detailed information about the integration:

```
sudo datadog-agent check crest_data_systems_netapp_aiqum
```

## Uninstallation

Uninstall the integration from the Datadog Agent by running the following command:

- Linux:
  - `sudo -u dd-agent datadog-agent integration remove datadog-crest_data_systems_netapp_aiqum`
- Windows:
  - `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-crest_data_systems_netapp_aiqum`

YAML Config Cleanup:

- If you plan to reinstall or need to keep the config files:
  - Navigate to your Agent's `conf.d` directory and locate the `crest_data_systems_netapp_aiqum.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as API keys.
- If you plan to fully uninstall with config removal:
  - Navigate to your Agent's `conf.d` directory, and remove the `crest_data_systems_netapp_aiqum.d` folder.

## Support

For support or feature requests, contact Crest Data Systems through the following channels:

- Support Email: datadog.integrations@crestdatasys.com
- Sales Email: datadog-sales@crestdatasys.com
- Website: [crestdatasys.com][3]

[1]: https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[3]: https://www.crestdatasys.com/
[4]: https://docs.datadoghq.com/agent/guide/agent-configuration-files/?tab=agentv6v7
