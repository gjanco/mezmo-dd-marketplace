# RapDev Nutanix

## Overview
The Nutanix Integration monitors storage, CPU usage, read/write IOPS, and other metrics within Nutanix Clusters, to ensure that your environment is running at optimal performance at all times. The integration comes with 4 Dashboards which allows you to view your Nutanix Clusters from an overview, as well as getting granular and pin-pointing potential performance degradations. The Nutanix Integration also comes with monitors for key metrics such as storage utilization and deduplication savings, which are integral to the overall performance of the Nutanix environment.

### Nutanix Overview Dashboard 
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_nutanix/images/4.png)

### Nutanix VMs Dashboard
![Screenshot2](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_nutanix/images/5.png)

### Nutanix Clusters Dashboard 
![Screenshot3](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_nutanix/images/6.png)

### Nutanix Hosts and Disks Dashboard
![Screenshot3](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_nutanix/images/7.png)

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
## Setup
Find specific step-by-step configuration instructions for this integration.

### Prerequisites
* You must be able to connect to your Nutanix CVM from the server with the Datadog Agent installed.

### Install the Nutanix Integration
To install the Nutanix check on your host:

`sudo ‐u dd‐agent datadog‐agent integration install --third-party datadog-rapdev_nutanix==1.1.0`

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
```
sudo ‐u dd‐agent datadog‐agent check rapdev_nutanix
```
## Pricing
$5 per CPU core.

## Support
For support or feature requests, contact RapDev.io through the following channels:

- Email: integrations@rapdev.io
- Chat: RapDev.io/products
- Phone: 855-857-0222

Made with ❤️ in Boston

---

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:integrations@rapdev.io), and we'll build it!!*
