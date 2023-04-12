# BoomiWatch

## Overview

BoomiWatch by Kitepipe is an Agent-based integration that collects metrics from Boomi processes, cluster nodes, and related infrastructure to inform both Datadog and Boomi customers about the health of the integration.

BoomiWatch version 1.0 contains 4 dashboards, 13 custom metrics, and 12 monitors that report on Boomi execution statistics, cluster status, and infrastructure health.  These metrics are available to Datadog and Boomi customers for extended time-trending analysis (over the standard of 30 days for Boomi Process Reporting availability).

Datadog customers who purchase BoomiWatch must manage the Boomi Java Runtime in either an Atom or Molecule configuration. Kitepipe includes a one hour set-up and configuration session with the initial 14 Day Free Trial.

### [About Kitepipe](https://www.kitepipe.com/)

Kitepipe is a Boomi Platinum Implementation Partner, and is the premier Boomi integration development team in North America. Kitepipe was founded in 2011 in response to the need for a Boomi-focused services team that could deliver all the promises of this powerful integration platform. 

Today, the Kitepipe team of certified Boomi on-shore developers help dozens of Boomi customers quickly achieve business value with the industry-leading Boomi integration platform.

The Datadog service BoomiWatch is a new offering from Kitepipe with a focus on Boomi managed services in AWS. Kitepipe is the leader in a number of integration areas, verticals, and domains, including AWS migrations of Boomi processes, AWS managed Boomi, Biotech vertical solutions built on Boomi, NetSuite, SAP, Coupa, Workday, and HRIS, Data Mart/BI, and more endpoints.

### Dashboards

The following dashboards are available to BoomiWatch customers. 

| Name  | Purpose |
| ------------- |-------------|
| **BoomiWatch Overview** | A dashboard displaying a high-level summary of Compute, Cluster, and Workload metrics. |
| **Boomi Workload Monitoring** | A dashboard displaying enhanced Process Reporting with associated graphs. |
| **Boomi Compute Monitoring** | A dashboard displaying infrastructure metrics to check resource health. |
| **Boomi Cluster Monitoring** | A dashboard about Boomi-recommended cluster status inspection. |

### Log Collection

This integration makes API calls to the Boomi Platform on your behalf, retrieving execution records and sending them to Datadog as logs.

### Recommended Monitors

The following monitors are provided. You can subscribe to alerts on each of these monitors, and create others as needed for your use cases:

| Name  | Purpose |
| ------------- |-------------|
| **Execution Duration Anomaly** | Detect long- and short-running executions. |
| **BoomiWatch is Down** | Detect if BoomiWatch has stopped working. |
| **Runtime Online Status** | Detect if Boomi datacenter shows that your runtimes are online. |
| **Boomi Cluster Node "View File" is Missing** | Detect if Boomi is not running on a cluster node. |
| **Boomi Cluster Node "View File" is Too Old** | Detect if a cluster node is offline or operating with lag. |
| **Boomi Cluster Problem** | Detect if a cluster node has reported a problem. |
| **Boomi Infrastructure: Molecule Node Disk Usage High** | Detect if a molecule node is running out of disk space. |
| **Boomi Infrastructure: Molecule Node CPU Usage High** | Detect if a molecule node is at high CPU usage. |
| **Boomi Infrastructure: Molecule Node Memory Usage High** | Detect if a molecule node is at high RAM usage. |
| **Boomi Infrastructure: API Gateway Node Disk Usage High** | Detect if an API gateway node is running out of disk space. |
| **Boomi Infrastructure: API Gateway Node CPU Usage High** | Detect if an API gateway node is at high CPU usage. |
| **Boomi Infrastructure: API Gateway Node Memory Usage High** | Detect if an API gateway node is at high RAM usage. |

### Events

This integration retrieves AuditLog records from the Boomi API, and sends them to Datadog as events. The events are visible in filtered form in the Boomi Workload Monitoring Dashboard or in the [Events Explorer][1]. You can build your own monitors to inspect the unfiltered AuditLog records.

### Metrics

You can explore a list of metrics in the **Data Collected** tab. Metrics cover the following categories:

| Type                   | Categories                                             | Definition                                                   |
|------------------------|--------------------------------------------------------|--------------------------------------------------------------|
| Workload Metrics       | - Executions<br>- Documents                            | Enhanced version of Boomi Process Reporting data.            |
| Cluster Metrics        | - File Existence<br>- File Age <br>- Reported Problems | Enhanced versions of Boomi Cluster Status data.              |
| Infrastructure Metrics | - CPU <br>- Network <br>- Disk <br>- RAM               | Standard Datadog infrastructure metrics in these categories. |

## Setup

Follow the instructions below to install and configure this integration for an Agent running on a host server. Containerized environments are not supported.

Kitepipe support engineers are available to assist customers in configuring and installing the Boomi Monitoring suite. Several advanced features require mapping of server or node to Boomi resources in the config file.  See the [Support](#support) section for more details.

### Prerequisites


1. Boomi Atom or Molecule running on server or virtual server (not containerized).
2. Optionally, Boomi API Gateway running on server or virtual server.
3. Ability to remote into each server with admin permissions and edit files using the command line.
4. Admin privileges in your Boomi account.
5. Knowledge of how to create a user in Boomi, assign permissions, and generate an API token.
6. An email address to use as the login ID for a newly created Boomi user.


### Boomi User Creation

This Datadog integration makes calls to the Boomi API on your behalf. You must supply Boomi user credentials to be used in these API calls. It is recommended to create a service user identity for this purpose.  

Follow these steps:

1.  In your Boomi account, create a service user with the following permissions:
     -  API Access
     -  Atom Management
     -  Build Read Access
     -  Execute
     -  View Audit Logs
     -  View Data
     -  View Results
2.  Log in to Boomi as this user and [generate an API token][2].
3. Save this user's login ID and the API token for later use.
4. [Add this role][3] to every Boomi Environment that you want to monitor.

### Installing the Agent

The Datadog Agent must be installed on each node of the Molecule or API Gateway.

1. If not already done, [download and install the Datadog Agent][5] on the node.
2. Install BoomiWatch with this command: `sudo -u dd-agent datadog-agent integration install --third-party datadog-kitepipe-boomiwatch==1.0.0`.

### Prepare the "Last Datetime File"

As part of making Boomi AtomSphere API calls, the integration stores a timestamp in a text file on your Molecule shared disk or Atom installation directory. You must create this file and set permissions manually. You only need to do this once because only one server or node will be making API calls.
- Remote into a Molecule node or your Atom server.
- From the [Boomi Atom Management - Startup Properties panel](https://help.boomi.com/bundle/integration/page/r-atm-Startup_Properties_panel.html), determine your Atom Installation Directory.  You will use this in later steps.
- Create an empty file owned by `dd-agent` using this command: 
`sudo touch <YOUR_INSTALLATION_DIRECTORY>/work/kitepipe-boomiwatch-last-end-datetime.txt && sudo chown dd-agent:dd-agent <YOUR_INSTALLATION_DIRECTORY>/work/kitepipe-boomiwatch-last-end-datetime.txt`

### Configuring the Agent

#### Edit datadog.yaml

In the `# tags` section, add the following values:
```
- env:<your environment name>
- role:<molecule, api-gateway, or atom>
- boomi-hostname:"<hostname of this server; must be in quotes>"
- integration:kitepipe-boomiwatch
```

Uncomment `# process_config` and configure as follows:
```
process_config
    enabled: true
```


#### Edit conf.yaml

An example configuration file can be found at `<DATADOG-AGENT-INSTALLATION-ROOT>/conf.d/kitepipe_boomiwatch.d/conf.yaml.example`. Copy this to `conf.yaml` in the same directory using these commands:

```
cd <DATADOG-AGENT-INSTALLATION-ROOT>/conf.d/kitepipe_boomiwatch.d
sudo cp conf.yaml.example conf.yaml
sudo chown dd-agent:dd-agent conf.yaml
```
Then, edit the `conf.yaml` as follows:

```
instances:

  - dd_api_key: <API_KEY>

    ## Uncomment the following if this is the node that will make Boomi API calls
    ##
    # boomi_api_url: https://api.boomi.com
    # boomi_api_userid: <LOGIN_ID_OF_BOOMI_USER>
    # boomi_api_token: <API_TOKEN_OF_BOOMI_USER>
    # boomi_account_id: <BOOMI_ACCOUNT_ID>

    ## Required
    ##
    boomi_atom_or_molecule_install_dir: <ABSOLUTE_PATH_OF_BOOMI_INSTALL_DIR>

    ## Optional - UNCOMMENT AND SUPPLY VALUES IF APPLIABLE
    ##
    # boomi_api_gateway_install_dir: <some absolute disk path>
    # boomi_molecule_node_id: '<BOOMI_MOLECULE_NODE_ID>'
    # boomi_api_gateway_node_id: '<BOOMI_API_GATEWAY_NODE_ID>'

```
- Restart the Datadog Agent: `sudo systemctl restart datadog-agent`.
- Verify that Datadog Agent is running the `kitepipe_boomiwatch` check by running: `sudo -u dd-agent datadog-agent status`. If successful, you should see a recent "Last Successful Execution Date" as in the example below:

```
    kitepipe_boomiwatch (1.0.0)
    --------------------------------
      Instance ID: kitepipe_boomiwatch:3dcc48da6d736c4a [OK]
      Configuration Source: file:/etc/datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml
      Total Runs: 1
      Metric Samples: Last Run: 12, Total: 12
      Events: Last Run: 0, Total: 0
      Service Checks: Last Run: 7, Total: 7
      Average Execution Time : 55ms
      Last Execution Date : 2022-12-17 15:18:21 UTC (1671290301000)
      Last Successful Execution Date : 2022-12-17 15:18:21 UTC (1671290301000)`
```

## Uninstallation

- Remote into each node where BoomiWatch was installed.
  - Uninstall the Kitepipe BoomiWatch Integration from the Datadog Agent: `$ sudo -u dd-agent -- datadog-agent integration remove --third-party-datadog-kitepipe-boomiwatch`.
  - Delete the `<DATADOG-AGENT-INSTALLATION-ROOT>/conf.d/kitepipe_boomiwatch.d/conf.yaml` file.
  - Restart the Datadog Agent: `sudo systemctl restart datadog-agent`.
  - Verify that BoomiWatch integration is no longer running: `sudo -u dd-agent datadog-agent status`. You should no longer see a "kitepipe_boomiwatch" section in the output.
- Log on to the Boomi console.
  - Revoke the API token you created during BoomiWatch installation.
  - Delete the Boomi user you created during BoomiWatch installation.


## Support

BoomiWatch customers may send a troubleshooting request to `BoomiWatch@kitepipe.com`. Kitepipe support hours for BoomiWatch are designated during the business hours of 9AM to 3PM across US and Canadian time zones.  BoomiWatch troubleshooting requests will be answered within 24 to 48 hours from the notification receipt to the BoomiWatch email alias.
  
For best response results, include the customer name, Boomi configuration, and a brief description of the event or troubleshooting question. Enhanced support programs are available from Kitepipe upon request.

[1]: https://app.datadoghq.com/event/explorer
[2]: https://help.boomi.com/bundle/atomsphere_platform/page/int-Adding_API_tokens.html
[3]: https://help.boomi.com/bundle/integration/page/t-atm-Attaching_a_role_to_an_Environment.html
[4]: https://app.datadoghq.com/logs
[5]: https://app.datadoghq.com/account/settings#agent/overview
[6]: https://help.boomi.com/bundle/integration/page/r-atm-Startup_Properties_panel.html
[7]: https://help.boomi.com/bundle/integration/page/r-atm-Cluster_Status_panel.html
[8]: https://help.boomi.com/bundle/api_management/page/api-API_Gateway_settings.html
