## Overview

[![Microsoft Office 365 Introduction](https://raw.githubusercontent.com/DataDog/marketplace/master/o365/images/video.png)](https://www.youtube.com/watch?v=sBg8HI3Oz64)

The Microsoft Office 365 integration monitors product activity, usage and licensing of Exchange, Outlook, Sharepoint, OneDrive, Yammer, Teams, and Skype. The integration also runs synthetic operations in Outlook, Teams, and OneDrive to provide application performance monitoring from multiple locations worldwide. The Office 365 integration comes with a dashboard that allows you to filter based on User, OneDrive, Sharepoint URL, and more. It also uses Datadog Synthetic checks to validate that the Office 365 URLs are online and responding in an acceptable timeframe.

All integrations can be toggled on and off in the ```o365.yaml``` file as part of the integration.  Its recommended to disable any products you dont want to monitor to avoid usage of additional metrics.

Below are some screenshots of the dashboard that is included with the integration.

### Synthetic Mail and response times
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/o365/images/1.png)

### Outlook Mailbox metrics per user and devices
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/o365/images/2.png)

### Sharepoint site usage per URL
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/o365/images/3.png)

### License usage per product and user
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/o365/images/4.png)

### Teams, Calendar and OneDrive synthetics
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/o365/images/5.png)

## Setup

### Microsoft Office 365 Configuration

The Microsoft Office 365 integration requires permissions managed through your organization's Azure Active Directory as well as a dedicated "integration user account" to perform synthetic operations.

1. [Create a new Office 365 user account](https://support.microsoft.com/en-us/office/add-a-new-user-10d7c185-34d1-4648-9b1d-40c45305d2cb). The integration user account should not be shared with an active user in your organization. Retain the user account username (email) and password for use in the datadog agent configuration step.

2. Add the `username` and `password` parameters to the `o365.d/o365.yaml` configuration file.  `username` should be the email address (UPN) of the Office 365 user created in step 1.

3. [Create a new Azure Active Directory Application Registration](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app).

	3.1. Create a [New Registration](https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps). Select a name that will clearly distinguish the application registration, e.g. *DatadogIntegration*.

	3.2. In the App registration detail, make note of the `Application (client) ID` and the `Directory (tenant) ID` values to the `o365.d/o365.yaml` configuration file as `client_id` and `tenant_id`, respectively.
	
	3.2. Configure the DatadogIntegration application API permissions. 

	- Select `Add a permission`, `Microsoft Graph`, and then `Application Permissions`. Add the following permissions:
		- Reports.Read.All

	- Select `Add a permission`, `Office 365 Management APIs`, and then `Application Permissions`. Add the following permissions:
		- ActivityFeed.Read
		- ActivityFeed.ReadDlp 
		- ServiceHealth.Read

	- Select `Add a permission`, `Microsoft Graph`, and then `Delegated Permissions`. Add the following permissions:
		- Calendars.ReadWrite
		- Channel.Create
		- ChannelMessage.Send
		- Directory.ReadWrite.All
		- email
		- Files.ReadWrite
		- Group.ReadWrite.All
		- offline_access
		- openid
		- profile
		- Reports.Read.All
		- Team.ReadBasic.All

	- Select `Grant Admin Consent for {Organization}` to give consent to the app registration to consume the configured API permissions.

	3.3. From the app registration `Overview`, add the `Application (client) ID` and `Directory (tenant) ID` values to the `o365.d/o365.yaml` file as `client_id` and `tenant_id`, respectively.

	3.4. Select `Certificates & secrets` and `New client secret`. It's recommended to use `Never` for expiration unless you are actively managing the secret for your agent installation. Copy the client secret value promptly from the Microsoft Azure UI as the secret will be masked after a short period of time.

	3.5. Add the generated `client_secret` value to the `o365.d/o365.yaml` file.

4. [Create a Microsoft Teams group and channel](https://docs.microsoft.com/en-us/microsoftteams/get-started-with-teams-create-your-first-teams-and-channels) for the integration Teams synthetic checks.

	4.1. The Group/Teams name must be `dd-agent-synthetic`. The integration specifically looks for a Group/Teams called `dd-agent-synthetic`.

	4.2. Add the integration user created in step 1 to the Microsoft Teams `dd-agent-synthetic`. The synthetic check will use the default `General` channel to send and reply to messages.


5. [Configure the integration user account mailbox to auto-forward emails](https://docs.microsoft.com/en-us/exchange/recipients-in-exchange-online/manage-user-mailboxes/configure-email-forwarding) to `probe@synth-rapdev.io`. Optionally set your email forwarding configuration to disable copies of forwarded email.

6. The agent's synthetic email check is disabled by default, set `enable_email_synthetics: true` and set the target email address configured in step 3.6 by adding `email_address: {integration_user@email.address}` in the `o365.d/o365.yaml`.

7. [Restart the Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7).

## Validation

[Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-status-and-information) and look for `o365` under the Checks section.

## FAQ
### How often does the Microsoft Graph API update the reports?
The Microsoft Graph Reports API updates reports approximately every 24 hours.

### What aggregation period is the integration using?
Microsoft Graph provides aggregation periods of 7, 30, 90 and 180 days. The Microsoft Office 365 integration is using the 7 day aggregation period for reports pulled from the Graph API.

### What events are captured by this integration?
Microsoft's Office 365 Service Communications API is leveraged to create events from incident messages.

## Pricing
$0.10 per user per month

## Support
For support or feature requests please contact RapDev.io through the following channels: 

 - Email: integrations@rapdev.io 
 - Chat: [RapDev.io/products](https://rapdev.io/products)
 - Phone: 855-857-0222 

## Vendor Information
[RapDev.io](http://rapdev.io)

Made with ❤️ in Boston

---

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:integrations@rapdev.io) and we'll build it!!*