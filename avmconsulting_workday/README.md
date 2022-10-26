# Agent Check: Workday

## Overview

This Workday integration monitors the state of your integrations in Workday, offering rich metrics regarding job executions, including total job executions, failure job executions, and the duration of each job execution. This integration also retrieves job execution logs and provides monitors that alert on the state of each integration.

### Monitors

This integration includes the following recommended monitors:

1. Connect to Workday, which monitors your connection to Workday.
2. Workday Integration Status, a multi-monitor that is grouped by integrations and checks the last Workday integration event state.

### Dashboards

This integration includes an out-of-the-box dashboard named **Workday Integrations Trends** that provides a visual summary of Workday job executions, as well as the state of the monitors configured for each Workday integration.

### Log Collection

This integration uses the Workday API to collect logs for integration executions and submit those logs to Datadog through the Datadog REST API. Execution-related tags are assigned dynamically to those logs.

## Setup

### Prerequisites

[Install or upgrade the `pytz` library][4] using the Agent's embedded Python. This library is required for the check to run:
 
   **If you're running on Linux, run the following command**:
    
   `sudo -Hu dd-agent /opt/datadog-agent/embedded/bin/pip install pytz --upgrade`
   
   **If you're running on Windows, run the following command:**
   
   `%PROGRAMFILES%\Datadog\"Datadog Agent"\embedded<PYTHON_MAJOR_VERSION>\python -m pip install pytz --upgrade`

### Installation

To install this integration, follow the steps below.

1. [Download and install the Datadog Agent][1].
2. Run `sudo -u dd-agent datadog-agent integration install --third-party datadog-avmconsulting_workday==1.0.1`.

### Configuration

1.  To start collecting Workday performance data, edit the `avmconsulting_workday.d/conf.yaml` file in the `conf.d/` folder at the root of your Agent's configuration directory. See the sample `avmconsulting_workday.d/conf.yaml.example` file provided during the integration installation for all available configuration options.

**To find your Workday URL:**

* Login to your Workday tenant
* Navigate to `public web services` -> `...` -> `Web Services` -> `View URLs`
* Right click on `Workday XML` -> `Copy URL`
* Construct the Workday URL by appending`/Integrations` to the end of the base URL that you just copied, to achieve the following format: 
    * `https://<WORKDAY_SERVER_ADDRESS>/<INTEGRATION>/Integrations`
    * Example Workday URL:`https://wd2-impl-services1.workday.com/ccx/service/alignt_tenant/Integrations`
    
2. [Restart the Datadog Agent][2].

### Validation

[Run the Agent's status subcommand][3] and look for `avmconsulting_workday` under the Checks section.



### Service checks

The Workday integration includes the following service checks:

1. **avmconsulting.workday.can_connect**: This service check shows whether a connection to Workday can be established and data can be processed.
2. **avmconsulting.workday.integration.state**: This service check shows the state of integrations within Workday.

## Support

For support or feature requests, contact AVM Consulting through the following channels: 

 - Email: integrations@avmconsulting.net 
 - Phone: 855-AVM-0555 

## Further Reading

Additional helpful documentation, links, and articles:

- [Monitor Workday with AVM Consulting’s integration in the Datadog Marketplace][5]

[1]: https://app.datadoghq.com/account/settings#agent/overview
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent
[3]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[4]: https://docs.datadoghq.com/developers/guide/custom-python-package/?tab=linux
[5]: https://www.datadoghq.com/blog/workday-monitoring-with-avm-and-datadog/