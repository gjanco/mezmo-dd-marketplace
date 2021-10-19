## Overview

This integration monitors the performance and usage of Dell EMC Isilon cluster and nodes. It captures crucial metrics and provides insights into health and operation of the Dell EMC Isilon cluster.

Dashboard Name | Description
---------------|------------
Cluster Infromation | This dashboard provides cluster level information.
Node Details | This dashboard provides node level information.
Protocol Details | This dashboard provides cluster wide protocol details.
File System | This dashboard provides file system details at the node level.
Quota Information | This dashboard provides quota information.

## Setup

### Prerequisites

1. You must have the Datadog Agent installed and running. Additionally, you need to be able to connect to the server with the Datadog Agent installed.

### Datadog Integration Installation

1. `sudo -u dd-agent datadog-agent integration install --third-party datadog-crest_data_systems_dell_emc_isilon==1.0.0`

### Datadog Integration Configuration

1. Copy the `conf.yaml.example` file.

    ```sh
    cp /etc/datadog/conf.d/crest_data_systems_dell_emc_isilon.d/conf.yaml.example /etc/datadog/conf.d/crest_data_systems_dell_emc_isilon.d/conf.yaml
    ```

2. Edit `/etc/datadog/conf.d/crest_data_systems_dell_emc_isilon.d/conf.yaml` file. Add the configurations ip_address, username, password and port.

     ```yaml
    init_config:

    instances:
        ## @param ip_address - string - required
        ## IP Address needed in URL
        #
        - ip_address: <IP_ADDRESS>

        ## @param username - string - required
        ## Username for API call
        #
        username: <USERNAME>

        ## @param password - string - required
        ## Password for API call
        #
        password: <PASSWORD>

        ## @param port - string - required
        ## Port for API call
        #
        port: '8080'

        ## @param min_collection_interval - number - required
        ## This changes the collection interval of the check. For more information, see:
        ## https://docs.datadoghq.com/developers/write_agent_check/#collection-interval
        #
        min_collection_interval: 120
    ```
3. [Restart the Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent).

### Validation

1. [Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information) and look for `crest_data_systems_dell_emc_isilon` under the Checks section. Alternatively, you can get detailed information about the integration using the following command:

    ```
    sudo ‐u dd‐agent datadog‐agent check crest_data_systems_dell_emc_isilon
    ```

## Support

For support or feature requests, contact crestdatasys.com through the following channel:

 - Email: datadog.integrations@crestdatasys.com