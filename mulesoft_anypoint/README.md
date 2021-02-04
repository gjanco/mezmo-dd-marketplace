# Datadog Mule® Integration

## Overview

The Datadog Mule® Integration is an Agent-based integration that collects metrics from MuleSoft products and uploads them into Datadog. 

![Datadog Mule® Integration Bundle](https://raw.githubusercontent.com/DataDog/marketplace/master/mulesoft_anypoint/images/dmi_bundle.png)

You can use these metrics to take advantage of the out-of-the-box dashboards and monitors or you can create your own visualizations.

### **The observability you need for your Mule applications**

#### Operations (_Infrastructure, APIs, Alerts and Resource Allocation Dashboards_) 

- Monitor the health of your Mule servers, applications, APIs, and other IT infrastructure 
- Receive and visualize alerts about your Mule infrastructure 
- Gain insights about your Anypoint Platform resources allocation of your organization 

![Operations: Infrastructure dashboard](https://raw.githubusercontent.com/DataDog/marketplace/master/mulesoft_anypoint/images/dmi_ops_infra.png)

![Operations: Infrastructure dashboard](https://raw.githubusercontent.com/DataDog/marketplace/master/mulesoft_anypoint/images/dmi_ops_apis.png)

![Operations: Resources allocation and usage dashboard](https://raw.githubusercontent.com/DataDog/marketplace/master/mulesoft_anypoint/images/dmi_ops_allocation.png)

#### Development (_Optimization Dashboard_) 

- Quickly identify memory, CPU, and network issues in your Mule applications 
- Find bottlenecks in your Mule applications to optimize performance 
- Instrument your Mule applications with our Datadog Connector for Mule 4 for troubleshooting purposes 

![Development: Optimizations dashboard](https://raw.githubusercontent.com/DataDog/marketplace/master/mulesoft_anypoint/images/dmi_dev_optimization.png)

#### Executive (_Cost-optimization and Downtime Dashboard_) 

- Analyze and forecast your ROI based on used and unused resources 
- Get visibility of the system uptime of your Mule investment 

![Executives: Cost optimization dashboard](https://raw.githubusercontent.com/DataDog/marketplace/master/mulesoft_anypoint/images/dmi_exec_cost_optimization.png)

#### Metrics are collected from the following MuleSoft products: 

- Mule runtime for both CloudHub and on-premise standalone servers 
- Anypoint API Manager and API Analytics
- Anypoint Exchange 
- Anypoint Access Management 
- Object Store v2 

### **Instrument your Mule applications with our Datadog Mule 4 Connector**

![Datadog Connector for Mule 4](https://raw.githubusercontent.com/DataDog/marketplace/master/mulesoft_anypoint/images/dmi_mule_connector.png)

Use the Datadog Connector for Mule 4 with Datadog APM tracing to gain visibility using the out-of-the-box performance dashboards.

![Datadog APM](https://raw.githubusercontent.com/DataDog/marketplace/master/mulesoft_anypoint/images/dmi_apm_traces.png)

Measure the performance of the operations in your flows as granular as needed using spans.

![Datadog APM](https://raw.githubusercontent.com/DataDog/marketplace/master/mulesoft_anypoint/images/dmi_apm_trace.png)

Also, correlate the logs generated within a transaction in a single trace to narrow down any performance optimization or troubleshooting scope.

![Datadog APM](https://raw.githubusercontent.com/DataDog/marketplace/master/mulesoft_anypoint/images/dmi_apm_logs.png)

### **Troubleshooting**

Need help? Contact us: [support_ddp@ioconnectservices.com][9].

## Setup

Follow the instructions below to install and configure this check for an Agent running on a host. For containerized environments, see the [Autodiscovery Integration Templates][2] for guidance on applying these instructions.

### Prerequisites

1. Python 2.7+ (preferably Python 3.8)
2. pip package installer
3. Java 8+

### Installation

To install the mulesoft_anypoint check on your host:

1. [Download and install the Datadog Agent](https://app.datadoghq.com/account/settings#agent/overview).
2. Run `sudo -u dd-agent datadog-agent integration install --third-party datadog-mulesoft-anypoint==1.2.0`
  
### Configuration

1. Edit the `mulesoft_anypoint.d/conf.yaml` file, in the `conf.d/` folder at the root of your Agent's configuration directory to start collecting your mulesoft_anypoint performance data. On Linux systems, ensure the owner of the `conf.yaml` file is `dd-agent`. On OS X systems, ensure the owner of the `conf.yaml` file is the system user running the agent. See the [sample mulesoft_anypoint.d/conf.yaml][3] for all available configuration options.
2. [Restart the Agent][4].

#### Sample configuration

The Datadog Mule® Integration collects metrics from many different MuleSoft products. Configure the `mulesoft_anypoint.d/conf.yaml` file with the following instances to collect metrics from Mule runtimes, CloudHub, Anypoint Runtime Manager, Access Management and Object Store v2.

```yaml
init_config:

instances:

    ## This section contains a list of instances defined following the YAML list item notation -
    ## Each instance is scheduled independently to run a set of APIs with a specific threads number configuration

    ## @param min_collection_interval - integer - optional
    ## The time in seconds between executions
    ## If not specified it is defaulted to 86400
    #
  - min_collection_interval: 86400

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    #
    api_filter:
      - access_management

    ## @param min_collection_interval - integer - optional
    ## The time in seconds between executions
    ## If not specified it is defaulted to 10
    #
  - min_collection_interval: 60

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    #
    api_filter:
      - arm_monitoring_query

    ## @param min_collection_interval - integer - optional
    ## The time in seconds between executions
    ## If not specified it is defaulted to 10
    #
  - min_collection_interval: 60

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    #
    api_filter:
      - arm_mule_agent

    ## @param min_collection_interval - integer - optional
    ## The time in seconds between executions
    ## If not specified it is defaulted to 10
    #
  - min_collection_interval: 60

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    #
    api_filter:
      - arm_rest_services

    ## @param min_collection_interval - integer - optional
    ## The time in seconds between executions
    ## If not specified it is defaulted to 10
    #
  - min_collection_interval: 60

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    #
    api_filter:
      - cloudhub

    ## @param min_collection_interval - integer - optional
    ## The time in seconds between executions
    ## If not specified it is defaulted to 86400
    #
  - min_collection_interval: 86400

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    #
    api_filter:
      - exchange_experience

    ## @param min_collection_interval - integer - optional
    ## The time in seconds between executions
    ## If not specified it is defaulted to 60
    #
    #- min_collection_interval: 60

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    #threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    ## NOTE: This particular API needs administrator privileges
    #
    #api_filter:
    # - insight

    ## @param min_collection_interval - integer - optional
    ## The time in seconds between executions
    ## If not specified it is defaulted to 86400
    #
  - min_collection_interval: 86400

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    #
    api_filter:
      - object_store

    ## @param min_collection_interval - integer - optional
    ## The time in seconds between executions
    ## If not specified it is defaulted to 86400
    #
    #- min_collection_interval: 86400

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    # threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    ## NOTE: This particular API needs administrator privileges
    #
    #api_filter:
    # - object_store_v2_stats
    
  - min_collection_interval: 60

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    #
    api_filter:
      - api_manager
      
  - min_collection_interval: 60

    ## @param threads - integer - required
    ## The number of allowed parallel threads running the instance
    #
    threads: 32

    ## @param api_filter - string - optional
    ## List of APIs to execute within the instance following the YAML list item notation -
    ## If not specified, all the APIs are executed
    #
    api_filter:
      - api_events
```

### Validation

[Run the Agent's status subcommand][5] and look for `mulesoft_anypoint` under the Checks section.

## Data Collected

### Metrics

See [metadata.csv][6] for a list of metrics provided by this check.

### Service Checks

The mulesoft_anypoint included the following service checks:

1. MuleSoft Anypoint. This service check shows whether the metrics were correctly collected from MuleSoft Anypoint.
2. MuleSoft integration license. This service check helps to understand if the license of this MuleSoft integration for Datadog is valid.

### Events

The Datadog Mule® Integration does not include any events.

## Support

For any support inquiry, contact us at [support_ddp@ioconnectservices.com][9].

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here][13] to purchase this application.

##  End User License Agreement

A copy of the End User   License Agreement is located in the file [EULA - IO Connect Services.pdf][10]

## About IO Connect Services

IO Connect Services is a company specializing in Information Technology Consultancy Services. Our practices are Cloud Technologies, Systems Integration, Big Data, Cybersecurity, and Software Engineering. We provide services in all North America, Europe and Latin America. Our headquarters are located in the NYC metropolitan area and we also have offices in Guadalajara, Mexico and Madrid, Spain.

Visit  [https://www.ioconnectservices.com][11]

[1]: https://www.ioconnectservices.com
[2]: https://docs.datadoghq.com/agent/autodiscovery/integrations
[3]: https://github.com/DataDog/integrations-core/blob/master/mulesoft_anypoint/datadog_checks/mulesoft_anypoint/data/conf.yaml.example
[4]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[5]: https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-information
[6]: https://github.com/DataDog/integrations-core/blob/master/mulesoft_anypoint/metadata.csv
[7]: https://docs.datadoghq.com/developers/integrations/new_check_howto/?tab=configurationfile#installing
[8]: https://docs.datadoghq.com/developers/guide/custom-python-package/?tab=linux
[9]: mailto:support_ddp@ioconnectservices.com
[10]: assets/EULA%20-%20IO%20Connect%20Services.pdf
[11]: https://www.ioconnectservices.com
[12]: mailto:dmi@ioconnectservices.com
[13]: https://app.datadoghq.com/marketplace/app/ioconnect-mulesoft-anypoint/pricing
