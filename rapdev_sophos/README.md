# Agent Check: rapdev_sophos

## Overview

The Sophos Integration monitors the overall health of your Sophos managed endpoints to make sure your managed devices are in good health. The integration comes pre-built with 1 dashboard that provides a broad overview of several metrics that can be used to monitor the health of your devices. The Sophos Integration also comes with 2 monitors that can be used to alert when a device is no longer in good health, or if one of the Sophos services on the device stops.

### Monitors
1. Managed Endpoint Health has Changed
2. Sophos Service on Managed Endpoint is Stopped

### Dashboards
1. RapDev Sophos Dashboard

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

## Setup

Follow the instructions below to install and configure this check for an Agent running on a host. For containerized environments, see the [Autodiscovery Integration Templates][1] for guidance on applying these instructions.

### Prerequisites

You must have the Datadog Agent installed and running. Additionally, you need to be able to connect to the server with the Datadog Agent installed.

### Installation

To install the Sophos Integration on your host:

- Linux\
`sudo ‐u dd‐agent datadog‐agent integration install --third-party datadog-rapdev_sophos==1.0.1`

- Windows\
`C:\Program Files\Datadog\Datadog Agent\bin\agent.exe integration install --third-party datadog-rapdev_sophos==1.0.1`

### Configuration

1. [Create a Sophos service principal](https://developer.sophos.com/getting-started) to query the Sophos API. Make sure to copy the Client ID and Client Secret for use in the conf.yaml file.

2. Add the `base_api_url` ("https://api.central.sophos.com"), Client ID, and Client Secret to the `rapdev_sophos.d/conf.yaml` file, in the `conf.d/` folder at the root of your Agent's configuration directory. See the [sample rapdev_sophos.d/conf.yaml][2] for all available configuration options.

3. If you'd like to capture alert logs from Sophos, change `enable_alert_logs` to `true`. If you would like to collect data about individual Sophos services running on your endpoints, change `verbose_endpoints` to `true`.

4. [Restart the Agent][3].

### Validation

[Run the Agent's status subcommand][4] and look for `rapdev_sophos` under the Checks section.

Alternatively, you can get detailed information about the integration using the following commands:

- Linux\
`sudo ‐u dd‐agent datadog‐agent check rapdev_sophos`

- Windows\
`"C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" check rapdev_sophos`

## Support
For support or feature requests, contact RapDev.io through the following channels:

- Support: datadog-engineering@rapdev.io
- Sales: sales@rapdev.io
- Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
- Phone: 855-857-0222

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note](mailto:datadog-engineering@rapdev.io), and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here][5] to purchase this application.

[1]: https://docs.datadoghq.com/agent/kubernetes/integrations/
[2]: https://github.com/DataDog/integrations-core/blob/master/rapdev_sophos/datadog_checks/rapdev_sophos/data/conf.yaml.example
[3]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[4]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[5]: https://app.datadoghq.com/marketplace/app/rapdev-zoom/pricing
