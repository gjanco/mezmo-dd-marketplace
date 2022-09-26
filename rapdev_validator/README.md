# RapDev Validator

## Overview
The RapDev validator solves the problem for monitoring tag and Agent compliance in your Datadog environment. The integration accepts a list of tag keys and their values that you deem as acceptable per your environments tagging strategy, then reports these as metrics and service checks into your Datadog instance. This way, you can display whether the hosts in your environment have the correct tags applied to them.

### Dashboards
1. RapDev Validator Dashboard

### Monitors
1. Host is missing required tag key
2. Host has non-compliant value for tag key

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

## Setup
Find specific step-by-step configuration instructions for this integration.

### Prerequisites

Please note that this integration does not work on Python 2.X.X versions. 

### Install the Validator Integration
To install the Validator check on your host:

- Linux

`sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_validator==2.1.2`
- Windows

`C:\Program Files\Datadog\Datadog Agent\bin\agent.exe integration install --third-party datadog-rapdev_validator==2.1.2`

### Prepare the Validator

The only pre-requisite to the RapDev Validator integration is having an application key. Create an application key in the Datadog application by following the [Datadog documentation](https://docs.datadoghq.com/account_management/api-app-keys/#add-application-keys).

### Configuration

1. Edit the `rapdev_validator.d/conf.yaml` file, in the `conf.d/` folder at the root of your Agent's configuration directory.
  ```
  init_config:
  
  instances:
  - api_key: ********************************
    app_key: ****************************************
    dd_site: com
    required_tags:
      name:
        - "*"
      env:
        - "dev"
        - "qa"
        - "prod"
    ignore_paas: true
    hosts_to_ignore:
      - "sqlserver_.*"
      - ".*_adserver"
      - "i-.*00"
    validate_synthetics: true
    synthetic_tags:
      env:
        - "dev"
        - "qa"
        - "prod"
      application:
        - "*"
    empty_default_hostname: true
  ```
2. [Restart the Datadog Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent).

### Validation
1. [Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-information) and look for `rapdev_validator` under the Checks section.

Alternatively, you can get detailed information about the integration using the following command.
- Linux

`sudo ‐u dd‐agent datadog‐agent check rapdev_validator`
- Windows

`C:\Program Files\Datadog\Datadog Agent\bin\agent.exe check rapdev_validator`

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
