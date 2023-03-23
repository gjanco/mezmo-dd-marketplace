# Shoreline.io

## Overview

Shoreline incident automation enables DevOps and Site Reliability Engineers (SREs) to interactively **debug at scale** and quickly **build remediations** to eliminate repetitive work.

The debug and repair feature allows you to execute commands in real-time across your server farm without needing to SSH into the servers individually. You can execute anything that can be typed at the Linux command prompt such as Linux commands, shell scripts, and calls to cloud provider APIs, and turn these debug sessions into automations connected to Datadog monitors.

The Shoreline app automatically executes the automation when the monitor is triggered, significantly reducing Mean Time to Repair (MTTR) and manual work.

Shoreline helps everyone on call be as good as your best SRE. Shoreline arms your on-call team with debugging tools and approved remediation actions, helping you fix incidents faster with fewer escalations and ensuring that incidents are fixed correctly the first time with fewer mistakes.

To get started, set up a trial account on [Shoreline][1].

## Setup

### Installation

Follow the steps below to install and configure Shoreline's Datadog integration.

1. [Install the Shoreline Agent][3] on your hosts.
2. [Install the Shoreline integration][4] from [Shoreline's Datadog marketplace tile][10].
3. Navigate to your **Shoreline UI** > **Integrations** > **Datadog** page (such as `https://<SHORELINE_UI_URL>/integrations/datadog/`) to [install the Datadog integration][8].

#### Shoreline Agent

An Agent is an efficient, non-intrusive process running in the background of your monitored hosts. Agents collect, aggregate, and send data from the host and all connected pods and containers to Shoreline's backend, which uses the data to create metrics.

Agents serve as the secure link between Shoreline and your environment's resources. Agents can execute actions on your behalf, from simple Linux commands to remediation playbooks. Operational language statements pass an API request through Shoreline's backend and to the relevant Agents which execute the command across targeted resources.

Agents receive commands from Shoreline's backend and take automatic remediation steps based on the alarms, actions, and bots you configure. These objects work in tandem to monitor your fleet and dispatch the appropriate response if something goes wrong.

Install Shoreline Agents on every host you want Shoreline to monitor and act upon.

To install the Shoreline Agent, follow one of three methods:

1. [Kubernetes][5]
2. [Kubernetes via Helm][6] 
3. [Virtual Machines][7]

#### Datadog integration

To configure Shoreline's Datadog integration, you need a Datadog API and Application Key.

![integration_example](images/integrate_shoreline_and_datadog.png)

For detailed setup instructions, see the [Shoreline documentation][4].

## Uninstallation

1. Navigate to your **Shoreline UI** > **Integrations** > **Datadog** page (such as `https://<SHORELINE_UI_URL>/integrations/datadog/`).  
2. Click the **Uninstall** button.

   **Note**: Uninstalling the integration automatically removes the associated Datadog dashboard and webhook from your Datadog account.

3. Once you've canceled your subscription, Shoreline will reach out to confirm and disconnect your account.

## Support

For support and feature requests, contact Shoreline through the following channel:

- Email: [support@shoreline.io][2]

### Further Reading

Additional helpful documentation, links, and articles:

- [Debug issues and automate remediation with Shoreline and Datadog][11]
- [Shoreline Documentation][9]

[1]: https://shoreline.io/datadog?source=DatadogMarketplace
[2]: mailto:support@shoreline.io
[3]: https://docs.shoreline.io/installation
[4]: https://docs.shoreline.io/integrations/datadog#install-the-shoreline-integration
[5]: https://docs.shoreline.io/installation/kubernetes
[6]: https://docs.shoreline.io/installation/kubernetes#install-with-helm
[7]: https://docs.shoreline.io/installation/virtual-machines
[8]: https://docs.shoreline.io/integrations/datadog#install-the-shoreline-integration
[9]: https://docs.shoreline.io/
[10]: https://app.datadoghq.com/account/settings#integrations/shoreline-integration
[11]: https://www.datadoghq.com/blog/shoreline-io-marketplace-datadog/