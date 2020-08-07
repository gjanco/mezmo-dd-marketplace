# Trek10 AWS Coverage Advisor

## Overview
Coverage Advisor helps you rest easy knowing critical AWS CloudWatch Metrics that are in your Datadog account are being monitored. With monitor alerting, dashboarding, and coverage reports you will be able to keep monitors up to date with your AWS infrastructure as it evolves.

After signup our integration will clone over a dashboard into your Datadog account. We will also expose two event monitors in the Datadog recommended monitors page. The first event monitor will alert you when Trek10 discovers important AWS CloudWatch metrics that have recently been addeded in your account which don't have corresponding monitors. The second event monitor will let you know when we have added new CloudWatch metrics to our recommendations list. Finally the dashboard will give you a view of your Datadog's account monitoring status as well as let you generate a report of what metrics are / are not monitored.

![](https://raw.githubusercontent.com/DataDog/marketplace/master/trek10_coverage_advisor/images/maindashview.png)


*Have a specific request for this Datadog tool, looking for an AWS managed services partner, or need something with completely related to AWS or Datadog? Reach out to our sales team and let us explore how we can help you*

### Metrics
* Trek10 will push a metric nightly, trek10.coverage.aws_metric_count, that can be used to see how many metrics are currently being ingested into your Datadog account that don't have monitors for them. The metric will have the tag `metric_type` that can be filtered down to the values `all_metrics`, `metrics_monitored`, and `monitoring_recommendations`. 
![](https://raw.githubusercontent.com/DataDog/marketplace/master/trek10_coverage_advisor/images/metric_image.png)
   
### Events
* Trek10 also pushes events when we find unmonitored services. The event will link you back to the primary dashboard so you can see recent recommendations as well generate a report.
![](https://raw.githubusercontent.com/DataDog/marketplace/master/trek10_coverage_advisor/images/event_image.png)
   
### Monitors
* Trek10 provides a monitor to alert you when you have unmonitored services.
    
### Dashboards
* Trek10 provides a centralized, high level, dashboard that allows you to see a count of unmonitored services, generate PDF reports, see last updated time, and more.

## Setup
No big setup required!
  1.  Click the configuration tab.
  2. Fill in your email and hit submit.
  3. You will receive an email (within 1 business day) from Trek10 with a one-time link.
  4. Click link.
  5. Fill out the form with Datadog API and APP keys. To read more about Datadog API/APP keys see [datadog docs](https://docs.datadoghq.com/account_management/api-app-keys/). 
  6. After the keys are submitted, we will be automatically clone over your custom dashboard.
  7. Finally head over to Datadog's recommended monitors and clone over the two event monitors.



## Support
* We will clone over the dashboard & monitor into your account on setup. We will use the API key provided at setup - if you rotate the API key given please reach out to us at trek10-coverage-advisor@trek10.com. Similarly, if you experience any issues or questions about the integration please open a ticket by emailing trek10-coverage-advisor@trek10.com (and following emailed instructions).
* We are also happy to help answer any questions regarding AWS operations, monitoring, and development - just reach us at:
    * email (support): trek10-coverage-advisor@trek10.com
    * email (other questions): info@trek10.com
    * website: https://www.trek10.com/contact





## Pricing
* They say nothing in life is free, but this integration is.



## Usage
The main use of this integration is to allow you to quickly see which AWS metrics you have in your account that you don't have corresponding monitors for. You can check in on the dashboard weekly and generate a report, or you can set up monitors to alert you daily if you would rather be notified that way. 

## Vendor Information
* Trek10 
* Bio: We are technical gurus and builders at heart. Long time users of AWS and Datadog we have helped numerous companies in their adoptions of both with professional service and training engagements. We primarily use Datadog as a tool in our managed services for AWS. We took an internal tool that lets us know when we need to add monitors to one of our client's accounts and modified it for your use.
* website: trek10.com