## Overview

The RapDev Microsoft Teams integration monitors call quality reports and provides metrics, monitors and dashboards that provide insights into call activity and experience. 

This integration includes 
1. Multiple dashboards
2. Recommended monitors on call quality metrics
3. Metric lookup tables for call metadata and performance qualifiers

The Microsoft Teams integration requires minimum permissions on your Active Directory tenant and is simple to install, enabling your organization to quickly deploy and begin reporting on Microsoft Teams call quality reports.

### Pricing

Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers. *Volume pricing is available upon request through a private offer.* 

## Setup

### Installation

1. Install the integration on the Datadog Agent:

	Linux:
	```sh
	sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_msteams==1.0.0
	```

	Windows:
	```sh
	"%ProgramFiles%\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_msteams==1.0.0
	```

2. If your organization uses an egress http proxy, you will need to allow the following URLs:
	- **https://login.microsoftonline.com**
	- **https://graph.microsoft.com**
	- **https://msgraph-subscriptions-notifications.synth-rapdev.io**

### Configuration

The Microsoft Teams integration requires permissions managed through your organization's Azure Active Directory.

1. [Create a new Azure Active Directory Application Registration](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app).

	1.1. Create a [New Registration](https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps). Select a name that will clearly distinguish the application registration, e.g. *DDMSTeamsIntegration*.
	
	1.2. Configure the application registration API permissions:

	- Select `Add a permission`, `Microsoft Graph`, and then `Application Permissions`. Add the following permissions:
		
		- **CallRecords.Read.All**

	- Select `Grant Admin Consent for {Organization}` to give consent to the app registration to consume the configured API permissions.

	1.3. Select `Certificates & secrets` and `New client secret`. Copy the client secret value promptly and save it in a secure location.

	1.4. From the app registration `Overview`, retain the `Application (client) ID` and `Directory (tenant) ID` values, which are added to the integration configuration file along with the client secret value from the previous step.

2. Create the Microsoft Teams integration configuration file.
	
	2.1 Make a copy of the sample configuration file.

	Linux:
	```sh
	cd /etc/datadog-agent/conf.d/rapdev_msteams.d/
	cp conf.yaml.example conf.yaml
	```

	Windows:
	```sh
	cd %ProgramData%\Datadog\conf.d\rapdev_msteams.d
	copy conf.yaml.example conf.yaml
	```

	2.2 Update the required fields of the `conf.yaml` file using the values retained from the steps `1.3` and `1.4`.
	```yaml
	tenant_id: {App Registration Tenant ID}
	client_id: {App Registration Client ID}
	client_secret: {App Registration Client Secret}
	```
3. [Restart the Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7).

### Validation

[Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-status-and-information) and look for `rapdev_msteams` under the Checks section.

### Composite Monitors

The Microsoft Teams integration supports composite monitors to align with the official Microsoft Teams audio and video poor performance qualifiers. The following steps explain how to install the recommended monitors and define the poor performance composite monitors for both audio and video quality on Microsoft Teams calls.

1. Install the Microsoft Teams recommended monitors. Repeat the following steps for each of the monitors listed below:

	- `[Microsoft Teams] - average audio network jitter exceeds poor performance classifier`
	- `[Microsoft Teams] - average packet loss rate exceeds poor performance classifier`
	- `[Microsoft Teams] - packet utilization is below poor performance classifier`
	- `[Microsoft Teams] - average round-trip time exceeds poor performance classifier`
	- `[Microsoft Teams] - average video frame rate exceeds poor performance classifier`
	- `[Microsoft Teams] - video forward error correction packet loss rate average exceeds poor performance classifier`
	- `[Microsoft Teams] - average video frame loss percentage exceeds poor performance classifier`

	1.1 Select `New Monitor` from `Monitors -> Manage Monitors` in your Datadog instance.

	1.2 Select `Recommended` and in the `Integrations` selection filter, enter `RapDev Microsoft Teams`.

	1.3 Select and add each monitor by name from the list provided above without modification of the configuration. 

	*These monitors are used by a composite monitor, which is created after these monitors are installed. Accept the monitor configuration as provided since these are not intended to have direct notifications.*

2. Create the composite monitor for the poor audio performance qualifier.

	2.1 Select `Custom -> Composite` from `Monitors -> New Monitors` in your Datadog instance.

	2.2 Under `Select monitors and set triggering conditions`, select the following monitors. **Note, the precedence is important to the qualifier, so match the monitors to their labels: a, b, c and d.**

	a. `[Microsoft Teams] - packet utilization is below poor performance classifier`

	b. `[Microsoft Teams] - average round-trip time exceeds poor performance classifier`

	c. `[Microsoft Teams] - average packet loss rate exceeds poor performance classifier`

	d. `[Microsoft Teams] - average audio network jitter exceeds poor performance classifier`

	2.3 Enter the value `!a && ( b || c || d )` in the `Trigger When` field.

	2.4 Under `Say what's happening`, enter the following text as the title:

	```
	[Microsoft Teams] - one or more sessions on call exceeds the poor audio performance qualifier
	```

	2.5 Under `Say what's happening`, enter the following text as the body:

	```
	@slack-msteams-notifications

	{{#is_alert}}The Microsoft Teams call audio quality of {{call_id.name}} organized by {{call_organizer_name.name}} and started at {{call_start.name}} exceeds the poor performance classifier definition.{{/is_alert}}
	```

	2.6 Change `@slack-msteams-notifications` to the intended notification destination(s) for Microsoft Teams call quality alerts.

	2.7 Leave all other settings with the provided default values.

	2.8 Test the composite monitor to validate successful delivery of the configured notification destination(s).

	2.9 `Save` the composite monitor.

3. Create the composite monitor for the poor video performance qualifier.

	3.1 Select `Custom -> Composite` from `Monitors -> New Monitors` in your Datadog instance.

	3.2 Under `Select monitors and set triggering conditions`, select the following monitors. **Note, the precedence is important to the qualifier, so match the monitors to their labels: a, b and c.**

	a. `[Microsoft Teams] - average video frame loss percentage exceeds poor performance classifier`

	b. `[Microsoft Teams] - average video frame rate exceeds poor performance classifier`

	c. `[Microsoft Teams] - video forward error correction packet loss rate average exceeds poor performance classifier`

	3.3 Enter the value `a || ( a && b ) || ( a && b && c )` in the `Trigger When` field.

	3.4 Under `Say what's happening`, enter the following text as the title:

	```
	[Microsoft Teams] - one or more sessions on call exceeds the poor video performance qualifier
	```

	3.5 Under `Say what's happening`, enter the following text as the body:

	```
	@slack-msteams-notifications

	{{#is_alert}}The Microsoft Teams call has one or more session with the video quality of {{call_id.name}} organized by {{call_organizer_name.name}} and started at {{call_start.name}} exceeding the poor performance classifier definition.{{/is_alert}}
	```

	3.6 Change `@slack-msteams-notifications` to the intended notification destination(s) for Microsoft Teams call quality alerts.

	3.7 Leave all other settings with the provided default values.

	3.8 Test the composite monitor to validate successful delivery of the configured notification destination(s).

	3.9 `Save` the composite monitor.

## Uninstallation

1. Run the Datadog Agent uninstall command for the integration:

	Linux:
	```
	sudo -u dd-agent datadog-agent integration remove datadog-rapdev_msteams
	```

	Windows:
	```
	"%ProgramFiles%\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-rapdev_msteams
	```

2. [Optional] Remove the integration configuration file(s) which contain the App Registration secret:

	Linux:
	```
	cd /etc/datadog-agent/conf.d/rapdev_msteams.d/
	rm conf.yaml
	```

	Windows:
	```
	cd %ProgramData%\Datadog\conf.d\rapdev_msteams.d
	del conf.yaml
	```


## Support
For support or feature requests please contact RapDev.io through the following channels: 

 - Email: support@rapdev.io 
 - Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
 - Phone: 855-857-0222 

---

Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:support@rapdev.io) and we'll build it!!*

