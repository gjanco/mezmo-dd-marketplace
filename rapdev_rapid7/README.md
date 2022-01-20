# rapdev_rapid7
## Overview
This integration uses the Rapid7 REST API to query IDR log streams. The integration returns all logs that are not considered Rapid7 Platform level logs. These logs are submitted to datadog, and will incur additional cost based on log volume. These logs are typically composed of Rapid7 endpoint agent summaries and the statuses of their processes at a given time. 

### Metrics
The count of logs processed per check is reported as a metric.

### Log Collection
This integration calls to Rapid7 logs API to query all logs available in the last time interval. The default time interval is the last minute. You can specify specific [Log Sets][5] as detailed in Rapid7 insightIDR [Log Search Documentation][6] to get only those logs.

## Setup

Follow the step-by-step instructions below to install and configure this check for an Agent running on a host. 

### Prerequisites

You must have the Datadog Agent installed and running. Additionally, you need to be able to connect to the server with the Datadog Agent installed.


### Installation
```
sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_rapid7==1.0.0
``` 
#### The minimum collection interval for this check should be 60 seconds. Intervals smaller than this will result in duplicate logs.

1. Navigate to:  [Rapid7 platform configuration][1]
2. Generate Rapid7 API key
3. Copy and paste the key into your Agent check configuration file, `conf.d/rapdev_rapid7.d/conf.yaml`

    ```
    init_config:
    
    instances:
      - api_key: <RAPID7_IDR_API_KEY>                         #rapid7 platform key
        dd_api_key: <DD_API_KEY>                              #datadog api key
        url: https://us.api.insight.rapid7.com
        
    #    log_interval: "last 1 minutes"                     #past x amount of time in which we are querying logs
    #    select: ["name of logset to select", "optional"]   #log set to optionally select instead of getting all
    ``` 

4. [Restart the Agent][2].

### Validation

1. [Run the Agent's status subcommand][3] and look for `rapdev_rapid7` under the Checks section.

    Alternatively, you can get detailed information about the integration using the following command.
    
    ```
    sudo -u dd-agent datadog-agent check rapdev_rapid7
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

[1]: https://insight.rapid7.com/platform#/apiKeyManagement/organization
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[3]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[4]: https://app.datadoghq.com/marketplace/app/rapdev-rapid7/pricing
[5]: https://us.idr.insight.rapid7.com/op/D8A1412BEA86A11F15E5#/search
[6]: https://docs.rapid7.com/insightidr/log-search/