# TriggerMesh Oracle Cloud Metrics to Datadog Integration

## Overview

[TriggerMesh](https://www.triggermesh.com) provides a mechanism to get all [Oracle Cloud Metrics](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Concepts/monitoringoverview.htm) into Datadog. This is done by building a TriggerMesh Bridge and configuring the OCI so-called source as well as the Datadog [target](https://docs.triggermesh.io/targets/datadog/).

![OCI to datadog Bridge](https://raw.githubusercontent.com/DataDog/marketplace/master/triggermesh/images/ocidatadogtm.png)

## Setup

TriggerMesh OCI metrics exporter is available on the TriggerMesh Cloud or On-prem.

* Go to [TriggerMesh Cloud](https://cloud.triggermesh.io) and create a Bridge as shown in the [documentation](https://docs.triggermesh.io/sources/ocimetrics/)
* For an on-prem deployment contact TriggerMesh [support team](mailto:info@triggermesh.com)

## Data Collected

All Oracle Cloud services listed [here](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Concepts/monitoringoverview.htm#SupportedServices) are supported. The metrics listed in this catalog entry are the ones for an Oracle autonomous database but all OCI metrics can be collected including Compute Instance [metrics](https://docs.oracle.com/en-us/iaas/Content/Compute/References/computemetrics.htm#Compute_Instance_Metrics).

### Metrics

All the metrics that can be collected for an autonomous database are listed in the links below.

* Autonomous Database [metrics](https://docs.oracle.com/en-us/iaas/Content/Database/References/databasemetrics_topic-Overview_of_the_Database_Service_Autonomous_Database_Metrics.htm#overview)


## Support

If you have any questions about the TriggerMesh OCI to Datadog integration please contact us [info@triggermesh.com](mailto:info@triggermesh.com) or create an issue in this GitHub repository.

If you want to schedule a demo for the on-prem deployment scenario please contact [sales@triggermesh.com](mailto:sales@triggermesh.com)
