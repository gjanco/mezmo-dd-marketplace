## Overview

This integration monitors the performance and usage of Dell EMC Isilon cluster and nodes. It captures crucial metrics and provides insights into the health and operation of the Dell EMC Isilon cluster. This integration also supports monitors to alert for the CPU, Memory, and Disk Usage of each Node and Cluster.

| Dashboard Name      | Description                                                                             |
| ------------------- | --------------------------------------------------------------------------------------- |
| Cluster Information | This dashboard provides cluster level information.                                      |
| Node Details        | This dashboard provides node level information.                                         |
| Protocol Details    | This dashboard provides cluster wide protocol details.                                  |
| File System         | This dashboard provides file system details at the node level.                          |
| Quota Information   | This dashboard provides quota information.                                              |
| Monitors Summary    | This dashboard provides a summary of monitors, which are supported by this integration. |

## Setup

### Prerequisites

1. You have the Datadog Agent installed and running.
2. You can connect to the Dell EMC Isilon server with the Datadog Agent.

### Dell EMC Isilon Configuration

- The Dell EMC Isilon server should be able to connect with the Datadog Agent without any network restrictions.
- For any custom user of the Dell EMC Isilon server, the following roles and permissions are required:
  - Platform API
  - Quota
  - SmartPools
  - Statistics
- Basic Login credentials work to configure the Datadog integration.
- Datadog Integration works with the Dell EMC Isilon’s admin user without any additional configuration.
- For more information on user and permission-related settings in the Dell EMC Isilon server, see the [Dell documentation][4].

### Installation

Run the following:

- Linux:
  - `sudo -u dd-agent datadog-agent integration install --third-party datadog-crest_data_systems_dell_emc_isilon==3.0.1`.
- Windows:
  - `"C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-crest_data_systems_dell_emc_isilon==3.0.1`

### Configuration

1. Copy the `conf.yaml.example` file.

   ```sh
   cp /etc/datadog/conf.d/crest_data_systems_dell_emc_isilon.d/conf.yaml.example /etc/datadog/conf.d/crest_data_systems_dell_emc_isilon.d/conf.yaml
   ```

2. Edit the `/etc/datadog/conf.d/crest_data_systems_dell_emc_isilon.d/conf.yaml` file. Add configurations for the IP address, username, password, and port.

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

[Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information) and look for `crest_data_systems_dell_emc_isilon` under the Checks section.

Alternatively, you can get detailed information about the integration using the following command:

    ```
    sudo -u dd‐agent datadog-agent check crest_data_systems_dell_emc_isilon
    ```

### Monitor Configuration

1. Navigate to the **Monitors** tab in the Integration tile.

2. Select a monitor from the list.

3. Update the monitor configuration based on the requirements and save the monitor.

## Uninstallation

Uninstall the integration from the Datadog agent by running the following command on the agent host:

- Linux:
  - `sudo -u dd-agent datadog-agent integration remove datadog-crest_data_systems_dell_emc_isilon`
- Windows:
  - `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-crest_data_systems_dell_emc_isilon==3.0.1`

YAML Config Cleanup:

- If you plan to reinstall or need to keep the config files:
  - Navigate to your Agent's `conf.d` directory and locate the `crest_data_systems_dell_emc_isilon.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information.
- If you plan to fully uninstall with config removal:
  - Navigate to your Agent's `conf.d` directory, and remove the `crest_data_systems_dell_emc_isilon.d` folder.

## Support

For support or feature requests, contact Crest Data Systems through the following channels:

- Support Email: datadog.integrations@crestdatasys.com
- Sales Email: datadog-sales@crestdatasys.com
- Website: [crestdatasys.com][3]

### Further Reading

Additional helpful documentation, links, and articles:

- [Monitor Dell EMC Isilon with Crest Data Systems' integration in the Datadog Marketplace][1]
- [Setup Guide: Dell EMC Isilon Monitors in Datadog Platform][2]

[1]: https://www.datadoghq.com/blog/dell-emc-isilon-monitoring-crest-data-systems-datadog-marketplace/
[2]: https://www.crestdatasys.com/data_sheet/datadog-setup-monitor/
[3]: https://www.crestdatasys.com/
[4]: https://www.dell.com/support/manuals/en-in/isilon-onefs/ifs_pub_administration_guide_cli/administrative-roles-and-privileges
