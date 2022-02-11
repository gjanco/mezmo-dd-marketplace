# RapDev Terraform Integration

## Overview

The Terraform integration allows organizations to actively monitor their Terraform accounts to gain a better understanding of how well it's working and how often it's being used. The integration even goes as deep as providing a permissions audit. 

### Dashboards

1. RapDev Terraform Dashboard

## Setup

Follow the step-by-step instructions below to install and configure this check for an Agent running on a host. 

### Prerequisites

You must have the Datadog Agent installed and running. Additionally, you need to be able to connect to the server with the Datadog Agent installed.

### Installation

```
sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_terraform==1.2.0
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
     - api_token: <YOUR_API_TOKEN>
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


## Support
For support or feature requests, contact RapDev.io through the following channels:

- Support: datadog-engineering@rapdev.io
- Sales: sales@rapdev.io
- Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
- Phone: 855-857-0222

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note](mailto:datadog-engineering@rapdev.io), and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here][4] to purchase this application.

[1]: https://www.terraform.io/docs/cloud/users-teams-organizations/users.html#api-tokens
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[3]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[4]: https://app.datadoghq.com/marketplace/app/rapdev-terraform/pricing
