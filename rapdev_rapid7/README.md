# rapdev_rapid7

## Overview
This integration tracks the status of currently open and recently closed Rapid7 investigations. This integration will post to the event stream when an event opens and closes, and aggregates these events around the investigation's ID.

The log portion of the check (if enabled) uses the Rapid7 REST API to query IDR log streams. The integration returns all logs that are not considered Rapid7 platform-level logs. These logs are submitted to Datadog. **Note:** Submission of these logs may incur extra fees based on your Datadog pricing plan, as described in the [Datadog Log Management pricing structure](https://www.datadoghq.com/pricing/?product=log-management#log-management). These logs are typically composed of Rapid7 endpoint agent summaries and the statuses of their processes at a given time. 

### Dashboards
1. This integration comes with an out-of-the-box dashboard that summarizes Rapid 7 Investigations
2. This integration also includes an example dashboard based on logs. This dashboard is available upon installation of the integration, but it requires creating a facet for the R7 log source in order to begin seeing data flow.

### Events
This integration generates Datadog events for new open/closed investigations. The integration tracks the state of an investigation based on its ID and aggregates the open and close events generated together.

### Metrics
The count of logs processed per check is reported as a metric.

### Log Collection
Log collection is optional and disabled by default.
This integration calls to Rapid7 logs API to query all logs available in the last time interval. The default time interval is the last minute. You can specify 
specific [Log Sets][4] as detailed in Rapid7 insightIDR [Log Search Documentation][5] to get only those logs.

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

## Setup
Follow the step-by-step instructions below to install and configure this check for an Agent running on a host. 

### Prerequisites
You must have the Datadog Agent installed and running. Additionally, you need to be able to connect to the server with the Datadog Agent installed.


### Installation
```
sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_rapid7==2.0.0
```

#### The minimum collection interval for this check should be 60 seconds. Intervals smaller than this will result in duplicate logs.
1. Navigate to:  [Rapid7 platform configuration][1]
2. Generate Rapid7 API key
3. Copy and paste the key into your Agent check configuration file, `conf.d/rapdev_rapid7.d/conf.yaml`

    ```
    init_config:
    
    instances:
      - r7_api_key: <RAPID7_IDR_API_KEY>                         
        dd_api_key: <DD_API_KEY>                               
        
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

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note](mailto:datadog-engineering@rapdev.io), and we'll build it!!*

[1]: https://insight.rapid7.com/platform#/apiKeyManagement/organization
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[3]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[4]: https://us.idr.insight.rapid7.com/op/D8A1412BEA86A11F15E5#/search
[5]: https://docs.rapid7.com/insightidr/log-search/
