# RapDev Nutanix

## Overview
The Nutanix Integration monitors storage, CPU usage, read/write IOPS, and other metrics within Nutanix Clusters, to ensure that your environment is running at optimal performance at all times. The integration comes with 4 Dashboards which allows you to view your Nutanix Clusters from an overview, as well as getting granular and pin-pointing potential performance degradations. The Nutanix Integration also comes with monitors for key metrics such as storage utilization and deduplication savings, which are integral to the overall performance of the Nutanix environment.

### Monitors

1. Nutanix Cluster Storage Utilization
2. Nutanix Cluster CPU Utilization
3. Nutanix Cluster Deduplication Savings Ratio
4. Nutanix Cluster Compression Savings Ratio

### Dashboards

RapDev Nutanix Overview
RapDev Nutanix Clusters
RapDev Nutanix Hosts and Disks
RapDev Nutanix VMs

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

## Setup
Find specific step-by-step configuration instructions for this integration.

### Prerequisites
* You must be able to connect to your Nutanix CVM from the server with the Datadog Agent installed.

### Install the Nutanix Integration
To install the Nutanix check on your host:

Linux

`sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_nutanix==1.3.6`

Windows

`C:\Program Files\Datadog\Datadog Agent\bin\agent.exe integration install --third-party datadog-rapdev_nutanix==1.3.6`

### Prepare the Nutanix CVM
To make REST API calls to the Nutanix CVM, make sure your monitoring user account has the appropriate level of permissions. For more information, see [User Permissions](https://portal.nutanix.com/page/documents/details?targetId=Web-Console-Guide-Prism-v55:wc-user-create-wc-t.html)

1. Connect to the Prism Element Web Console.

2. Click on the Gear Icon and select `Local User Management`.

3. Click `+ New User`.

4. Select the Role of `Cluster Admin` and then save the new user information. Please note if you select a different Role, it must have access to utilize the Nutanix REST API.

### Configuration

1. Edit the `rapdev_nutanix.d/conf.yaml` file, in the `conf.d/` folder at the root of your Agent's configuration directory.
  ```
  - cvm_host:
    username:
    password:
    verbose_collection:
    tls_verify:
    tls_ca_cert:
    collect_events:
  ```
2. [Restart the Datadog Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent).

### Validation
1. [Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-information) and look for `rapdev_nutanix` under the Checks section.

Alternatively, you can get detailed information about the integration using the following command.

- Linux\
`sudo -u dd-agent datadog-agent check rapdev_nutanix`
- Windows\
`C:\Program Files\Datadog\Datadog Agent\bin\agent.exe check rapdev_nutanix`

### Tagging
Many of the metrics contain a tag called `nutanix_type`. This tag is used to separate metrics where different pieces of infrastructure might have the same metric name. You'll see values of `cluster`, `host`, `vm`, `storage_container`, `storage_pool`, `disk`, `virtual_disk`, and `protection_domain`.

## Uninstallation

### Agent Integration Uninstall 

1. Run the following command to remove the integration:

    - Linux: `sudo -u dd-agent datadog-agent integration remove datadog-rapdev_nutanix`

    - Windows: `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-rapdev_nutanix”`
        
2. Restart the Datadog Agent by using your OS's [Restart Command](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#restart-the-agent).

3. Run the Agent status command as described in the Validation section, and verify the integration is no longer running.

YAML Config Cleanup:
- If you plan to reinstall or need to keep the config files:
    - Navigate to your Agent's `conf.d` directory and locate the `rapdev_nutanix.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as user/password info and API keys.
    
- If you plan to fully uninstall with config removal:
    - Navigate to your Agent's `conf.d` directory, and remove the `rapdev_nutanix.d` folder.

Nutanix CVM Cleanup:
- As a best practice, remove any associated users and permissions created exclusively for this integration. For more details, reference the **Prepare the Nutanix CVM** section.

For any questions or problems, view our Support section for ways to get in touch.

## Support
For support or feature requests, contact RapDev.io through the following channels:

- Email: support@rapdev.io
- Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
- Phone: 855-857-0222

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:support@rapdev.io), and we'll build it!!*
