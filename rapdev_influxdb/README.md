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

## Support
For support or feature requests, contact RapDev.io through the following channels:
- Support: datadog-engineering@rapdev.io
- Sales: sales@rapdev.io
- Chat: [rapdev.io][2]
- Phone: 855-857-0222

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io][3] for packaged pricing offers.

---

Made with ❤️ in Boston
*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note][4], and we'll build it!!*


[1]: https://www.influxdata.com/
[2]: https://www.rapdev.io/#Get-in-touch
[3]: mailto:ddsales@rapdev.io
[4]: mailto:datadog-engineering@rapdev.io
