# Crest Data Systems NetApp OnTap

## Overview

This integration monitors the performance and usage of NetApp OnTap clusters and nodes. It captures crucial metrics and provides insight into the storage and performance of the NetApp OnTap cluster.

## Setup

### Prerequisites

1. You have the Datadog Agent installed and running.
2. You can connect to the server with the Datadog Agent.

### Installation

To install the integration, run: `sudo -u dd-agent datadog-agent integration install --third-party datadog-crest_data_systems_netapp_ontap==1.0.0`.

### Configuration

#### Setup datadog.yaml

1. The app_key and api_key needs to be set in the datadog.yaml if not already configured.([Read Here][4])
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

#### Setup conf.yaml

1. Copy the `conf.yaml.example` file.

   ```sh
   cp /etc/datadog/conf.d/crest_data_systems_netapp_ontap.d/conf.yaml.example /etc/datadog/conf.d/crest_data_systems_netapp_ontap.d/conf.yaml
   ```

2. Edit the `/etc/datadog/conf.d/crest_data_systems_netapp_ontap.d/conf.yaml` file. Add configurations for the IP address, username, password, and port.

   ```yaml
    init_config:

    instances:
        ## @param host - string - required
        ## The IP address and port (separated by a colon) where the Web Services Proxy is running with protocol (HTTP or HTTPS). For example: https://10.1.1.1:8443.
        #
       - host: <HOST>

        ## @param username - string - required
        ## Username of the NetApp OnTap
        #
        username: <USERNAME>

        ## @param password - string - required
        ## Password of the NetApp OnTap
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

[Run the Agent's status subcommand][2] and look for `crest_data_systems_netapp_ontap` under the Checks section.

Alternatively, see detailed information about the integration using the following command:

```
sudo -u dd‐agent datadog-agent check crest_data_systems_netapp_ontap
```

## Uninstallation

Uninstall the integration from the Datadog Agent by running the following command on a host:

`sudo -u dd-agent datadog-agent integration remove datadog-crest_data_systems_netapp_ontap`

## Support

For support or feature requests, contact Crest Data Systems through the following channels:

- Email: datadog.integrations@crestdatasys.com
- Website: [crestdatasys.com][3]


[1]: https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[3]: https://www.crestdatasys.com/
[4]: https://docs.datadoghq.com/agent/guide/agent-configuration-files/?tab=agentv6v7