# Agent Check: Fairwinds Insights

## Overview

![Dashboard](https://raw.githubusercontent.com/DataDog/marketplace/master/fairwinds_insights/images/dashboard.png)

### Software to protect and optimize your mission-critical Kubernetes applications

#### Streamline handoffs from development to operations

* Define and control custom policies across multiple clusters
* Enforce guardrails and best practices with an admission controller
* Integration container scanning and deployment validation into CI/CD workflows

#### Monitor and optimize Kubernetes costs

* Gain visibility into workload resource usage and estimated costs
* Determine the right CPU and memory settings for your workloads

#### Save time

* Integrate Kubernetes configuration recommendations with your existing Datadog dashboards
* Improve collaboration with Slack integration

#### Reduce risk

* Monitor containers for known vulnerabilities
* Validate Kubernetes deployment configurations

## Setup

### Installation

Login to Fairwinds Insights and navigate to your Organization's Settings page, then enter your Datadog API key in the API Key field under the Datadog section.

### Configuration

Login to [Fairwinds Insights][1] and navigate to the settings page for your organization and input your Datadog API key in the section marked Datadog.

### Validation

After providing your API key to Insights an initial Event should appear in Datadog showing that the integration is set up.

## Data Collected

### Metrics

Action Items from Fairwinds Insights will appear in Datadog with tags so that you can perform any analysis you need.

### Service Checks

Fairwinds Insights does not include any service checks.

### Events

* An initial Event will appear when you first setup the integration
* Event per new Action Item in Fairwinds Insights
* Event per event fixed Aciton Item in Fairwinds Insights

## Support

For support or requests, please contact Fairwinds through the following channels:

Phone: +1 617-202-3659 Email: sales@fairwinds.com

Documentation is available [here](https://insights.docs.fairwinds.com/). It covers setup and integration as well as ongoing usage to get the most out of Fairwinds Insights.

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here](https://app.datadoghq.com/marketplace/app/fairwinds-insights/pricing) to purchase this application.

### Frequently Asked Questions

**How does Fairwinds Insights work?**

Fairwinds Insights provides a unified, multi-cluster view into three categories of Kubernetes configuration issues: security, efficiency, and reliability. Fairwinds Insights makes it easy to deploy multiple open-source tools through a single helm installation. This one-time install helps engineers avoid custom work for installing and configuring each tool. The software also adds policy management capabilities so engineering teams can define and enforce guardrails for deployments into Kubernetes clusters.
 
**What’s a plugin?**

Fairwinds Insights refers to the tools integrated with the software as ‘plugins.’

**What’s an Agent?**

Fairwinds Insights refers to the included helm chart as the ‘Fairwinds Insights Agent.’

**What happens to my data?**

Fairwinds Insights aggregates findings from each plugin and publishes it into a multi-cluster view for easy consumption, prioritization, and issue tracking.

**What plugins does Fairwinds Insights include?**

Fairwinds Insights provides integrations for a variety of great open source tools you use today, including [Polaris](https://github.com/FairwindsOps/polaris), [Goldilocks](https://github.com/FairwindsOps/goldilocks/), [Open Policy Agent](https://www.openpolicyagent.org/), and [Trivy Container Scanning](https://github.com/aquasecurity/trivy). For the complete list, please visit the [Fairwinds Insights documentation center](https://insights.docs.fairwinds.com/). Just a few of the example findings are listed below:

* Container vulnerabilities
* Security issues with Kubernetes deployments (e.g., deployments configured to run as root)
* Cluster-level weaknesses (e.g., exposed pods, information disclosures, etc.)
* Kubernetes CVEs
* Automated notification of Helm charts that are out of date
* Custom Kubernetes policies and configuration checks

[1]: https://insights.fairwinds.com

### Refund Policy

Insights Cancellation and Refund Policy:

Fairwinds Insights is provided as a month-to-month subscription that you, the customer, may discontinue at any time in the ways made available to you through your DataDog Marketplace account. If you discontinue your subscription, you will be billed only for the remainder of the monthly billing period then in effect. Insights does not provide refunds of any fees already paid.
