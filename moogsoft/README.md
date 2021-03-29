# Moogsoft Observability Cloud

## Overview

Easily integrate Datadog and Moogsoft for combined AI monitoring and observability power!  Whether you are completely digital or have legacy applications, or a hybrid of both, this solution reduces the alert noise and improves operational efficiency across teams and IT Operations.

Moogsoft provides an advanced self-servicing AI-driven observability platform that allows software engineers, developers, and operations to instantly see everything, know what's wrong, and fix things faster.

Moogsoft delivers an enterprise-class, cloud-native platform that empowers customers to drive adoption at their own pace at a much lower cost.

![Moogsoft Correlation](https://raw.githubusercontent.com/DataDog/marketplace/master/moogsoft/images/moogsoft.correlation.png)

![Moogsoft Dashboard](https://raw.githubusercontent.com/DataDog/marketplace/master/moogsoft/images/moogsoft.dashboard.png)

### Observe

Improve service delivery quality. We only elevate critical situations, so you and your team can move swiftly, stay focused, and resolve incidents before they cause outages.

### Monitor

Watch alert volumes go down and see productivity go up. We help eliminate event fatigue with a consolidated monitoring panel and by correlating similar events to significantly minimize actionable alerts.

### Collaborate

See everything in one view. We aggregate all of your apps, services, and infrastructure alerts to a single console for increased agility, fewer alerts, and faster resolution times.

### Moogsoft Observability Cloud Data Flow

![Moogsoft Correlation](https://raw.githubusercontent.com/DataDog/marketplace/master/moogsoft/images/moogsoft.main.jpg)

![Moogsoft Main](https://raw.githubusercontent.com/DataDog/marketplace/master/moogsoft/images/moogsoft.flow.png)

## Setup

All that's needed to integrate Datadog to Moogsoft is, from in Moogsoft's UI, to click on Integrations > Datadog and provide your Datadog API key and Application key as detailed [here](https://docs.moogsoft.com/en/datadog-integration-mcp.html)

Then, for the bi-directional integration from Moogsoft to Datadog, just create an outbound Incident Webhook from Moogsoft with the following configuration (you can also perform this step from the Moogsoft UI):

URL = https://api.datadoghq.com/api/v2/incidents



Headers:

- Content-Type = application/json
- DD-API-KEY = "your API key value here"
- DD-APPLICATION-KEY = "your APPLICATION key value here"

Body:

{"data":{"attributes":{"customer_impacted":true,"customer_impact_scope":"$services","title":"$description","fields":{"services":{"type":"autocomplete","value":["$services"]},"severity":{"type":"dropdown","value":"SEV-1"},"detection_method":{"type":"dropdown","value":"other"}}},"relationships":{"commander":{"data":{"id":"00000000-0000-0000-0000-000000000000","type":"users"}}},"type":"incidents"}}

Last step is to create a second outbound webhook in Moogsoft with identical settings as the one above except using the following as the body:

{"series":[{"metric":"datadog.marketplace.moogsoft","points":[["$last_event_time","1"]]}]}



## Support
Contact Moogsoft Support at [https://support.moogsoft.com][1].

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here][2] to purchase this application.

[1]: https://support.moogsoft.com
[2]: https://app.datadoghq.com/marketplace/app/moogsoft/pricing
