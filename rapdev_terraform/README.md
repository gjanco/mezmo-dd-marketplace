# RapDev Terraform Integration

## Overview

The Terraform integration allows organizations to actively monitor their Terraform accounts to gain a better understanding of how well it's working and how often it's being used. The integration even goes as deep as providing a permissions audit. 

### Dashboards

1. RapDev Terraform Dashboard

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

## Setup

Follow the step-by-step instructions below to install and configure this check for an Agent running on a host. 

### Prerequisites

You must have the Datadog Agent installed and running. Additionally, you need to be able to connect to the server with the Datadog Agent installed.

### Installation

```
sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_terraform==1.3.0
``` 

### Configuration
1. Copy the `conf.yaml.example` file. 

  ```
  cp /etc/datadog/conf.d/rapdev_terraform.d/conf.yaml.example /etc/datadog/conf.d/rapdev_terraform.d/conf.yaml
  ```

2. Follow the steps in the [Terraform User Token Docs][1] to create a new API token. The token should be read-only. 

3. Since you are using a user token, each workspace that you want to monitor should have the user added to it so that API token
can access data from the workspace.

4. Finish the configuration by filling in the `api_token` from the previous steps. See below for an example:
   
   ```
   init_config:

   instances:
     - base_api_url: "https://app.terraform.io/api/v2/"
       api_token: <YOUR_API_TOKEN>
       min_collection_interval: 60
       collect_agents: False # If using non-hosted deployments and you want to set this to "True" to collect agent-pools/agent info
   ```
   
5. [Restart the Agent][2].

### Validation

1. [Run the Agent's status subcommand][3] and look for `rapdev_terraform` under the Checks section.

    Alternatively, you can get detailed information about the integration using the following command.
    
    ```
    sudo -u dd-agent datadog-agent check rapdev_terraform
    ```

## Uninstallation

### Agent Integration Uninstall 

1. Run the following command to remove the integration:

    - Linux: `sudo -u dd-agent datadog-agent integration remove datadog-rapdev_terraform`

    - Windows: `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-rapdev_terraform”`
        
2. Restart the Datadog Agent by using your OS's [Restart Command](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#restart-the-agent).

3. Run the Agent status command as described in the Validation section, and verify the integration is no longer running.

YAML Config Cleanup:
- If you plan to reinstall or need to keep the config files:
    - Navigate to your Agent's `conf.d` directory and locate the `rapdev_terraform.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as API tokens.
    
- If you plan to fully uninstall with config removal:
    - Navigate to your Agent's `conf.d` directory, and remove the `rapdev_terraform.d` folder.

Terraform Cleanup:
- As a best practice, remove any associated Client IDs and secrets created exclusively for this integration. For more details, reference the Configuration section.

For any questions or problems, view our Support section for ways to get in touch.

## Support
For support or feature requests, contact RapDev.io through the following channels:

- Support: support@rapdev.io
- Sales: sales@rapdev.io
- Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
- Phone: 855-857-0222

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note](mailto:support@rapdev.io), and we'll build it!!*

[1]: https://www.terraform.io/docs/cloud/users-teams-organizations/users.html#api-tokens
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[3]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
