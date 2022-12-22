# InfluxDB

## Overview

This integration reports metrics about the health and operation of [InfluxDB][1].

### Dashboards

This integration provides several out-of-the-box dashboards named **InfluxDB Summary**, 
**InfluxDB API Statistics**, **InfluxDB System**, and **InfluxDB Tasks and Services**. 
These dashboards display the metrics produced by the integration and split them into different categories.

## Setup
For Linux, use`sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_influxdb==1.0.0`.

For Windows, use `C:\Program Files\Datadog\Datadog Agent\bin\agent.exe integration install --third-party datadog-rapdev_influxdb==1.0.0`.

Provide the `metrics` endpoint to the integrations configuration file, `conf.d/rapdev_influxdb.d/rapdev_influxdb.yaml`:

```yaml
init_config:
instances:
  - openmetrics_endpoint: "http://myinfluxdbinstance.com:8086/metrics"
```

## Uninstallation

### Agent Integration Uninstall 

1. Run the following command to remove the integration:

    - Linux: `sudo -u dd-agent datadog-agent integration remove datadog-rapdev_influxdb`

    - Windows: `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-rapdev_influxdb”`
        
2. Restart the Datadog Agent by using your OS's [Restart Command](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#restart-the-agent).

3. Run the Agent status command as described in the Validation section, and verify the integration is no longer running.

YAML Config Cleanup:
- If you plan to reinstall or need to keep the config files:
    - Navigate to your Agent's `conf.d` directory and locate the `rapdev_influxdb.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as API tokens.
    
- If you plan to fully uninstall with config removal:
    - Navigate to your Agent's `conf.d` directory, and remove the `rapdev_influxdb.d ` folder.

For any questions or problems, view our Support section for ways to get in touch.

## Support
For support or feature requests, contact RapDev.io through the following channels:
- Support: support@rapdev.io
- Sales: sales@rapdev.io
- Chat: [rapdev.io][2]
- Phone: 855-857-0222

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io][3] for packaged pricing offers.

---

Made with ❤️ in Boston
*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note][4], and we'll build it!!*


[1]: https://www.influxdata.com/
[2]: https://www.rapdev.io/#Get-in-touch
[3]: mailto:sales@rapdev.io
[4]: mailto:support@rapdev.io
