## Overview

The Microsoft Office 365 integration monitors product activity, usage, and licensing of Exchange, Outlook, Sharepoint, OneDrive, Yammer, Teams, and Skype. The integration also runs synthetic operations in Outlook, Teams, and OneDrive to provide application performance monitoring from multiple locations worldwide. The Office 365 integration comes with a dashboard that allows you to filter based on User, OneDrive, Sharepoint URL, and more. It also uses Datadog Synthetic checks to validate that the Office 365 URLs are online and responding in an acceptable time frame.

All integrations can be toggled on and off in the ```o365.yaml``` file as part of the integration. It is recommended to disable any products you do not want to monitor in order to avoid usage of additional metrics.

### Pricing
##### *Volume pricing is only available upon request through a private offer*
| Units | Discount % | Cost/Unit |
|---|---|---|
| 1 - 2499 | 0% | $1 |
| 2500 - 4999 | 25% | $0.75 |
| 5000 + | Variable | Contact [sales@rapdev.io][1] for more information. |
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io][1] for packaged pricing offers.

## Setup

### Datadog Integration Install

Linux:
* `sudo -u dd-agent datadog-agent integration install --third-party datadog-o365==2.1.1`

Windows:
* `"C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-o365==2.1.1`

### Microsoft Office 365 Configuration

The Microsoft Office 365 integration requires permissions managed through your organization's Azure Active Directory as well as a dedicated "integration user account" to perform synthetic operations.

1. [Create a new Office 365 user account][2]. The integration user account should not be shared with an active user in your organization. The integration user should be a native M365 user, assigned a standard O365 license, and configured to not require MFA. Retain the user account username, email address, and password for use in the Datadog Agent configuration step.

2. Add the `username` and `password` parameters to the `o365.d/o365.yaml` configuration file.  `username` should be the email address (UPN) of the Office 365 user created in Step 1.

3. [Create a new Azure Active Directory Application Registration][3]. For the delegated permissions, the effective permissions are those provided to the M365 user created in Step 1. The App Registration permissions are an additional restriction limiting the scope of API calls allowed by the O365 Datadog integration.

	3.1. Create a [New Registration][4]. Select a name that will clearly distinguish the application registration, such as *DatadogIntegration*.
	
	3.2. Configure the DatadogIntegration application API permissions. 

	- Select `Add a permission`, `Microsoft Graph`, and then `Application Permissions`. Add the following permissions:
		
		- Reports.Read.All
		- ServiceHealth.Read.All
		- ServiceMessage.Read.All

	- Select `Add a permission`, `Office 365 Management APIs`, and then `Application Permissions`. Add the following permissions:
		
		- ActivityFeed.Read
		- ActivityFeed.ReadDlp
		- ServiceHealth.Read

	- Select `Add a permission`, `Microsoft Graph`, and then `Delegated Permissions`. Add the following permissions:

		- email
		- openid
		- profile
		- offline_access
		- Calendars.ReadWrite
		- Channel.ReadBasic.All
		- ChannelMessage.Send
		- Files.ReadWrite
		- Sites.Read.All
		- Team.ReadBasic.All

	- Select `Grant Admin Consent for {Organization}` to give consent to the app registration to consume the configured API permissions.

	3.3. From the app registration `Overview`, add the `Application (client) ID` and `Directory (tenant) ID` values to the `o365.d/o365.yaml` file as `client_id` and `tenant_id`, respectively.

	3.4. Select `Certificates & secrets` and `New client secret`. Copy the client secret value promptly from the Microsoft Azure UI as the secret will be masked after a short period of time.

	3.5. Add the generated `client_secret` value to the `o365.d/o365.yaml` file.

4. [Create a Microsoft Teams group and channel][5] for the integration Teams Synthetic checks.

	4.1. The Group/Teams name must be `dd-agent-synthetic`. The integration specifically looks for a Group/Teams called `dd-agent-synthetic`.

	4.2. Add the integration user created in Step 1 to the Microsoft Teams `dd-agent-synthetic`. The Synthetic check will use the default `General` channel to send and reply to messages.

5. [Configure the integration user account mailbox to auto-forward emails][6] to `probe@synth-rapdev.io`. Optionally, set your email forwarding configuration to disable copies of forwarded email.

6. [Modify the OneDrive storage configuration for the integration user account][7]. Specify a minimum of thirty (30) days and 1024 GB to prevent the integration user Synthetic files from consuming all allocated storage. The default settings, unless modified by your organization, should be thirty (30) days and 1204 GB. 

7. Configure the email Synthetic metrics by configuring the email mailbox setup in Step 5 by adding `email_address: {integration_user@email.address}` in the `o365.d/o365.yaml`.

8. Add SharePoint sites to the `o365.d/o365.yaml` file to enable collection of SharePoint performance metrics. Ten (10) sites can be added under the configuration section `sharepoint_sites`. See the configuration example for syntax. The configured username and password for the performance Synthetic user is used for the SharePoint login and the SharePoint site(s) must be readable by the configured user.

9. The integration configuration defaults to `probe_mode: true`, which will operate with application performance Synthetics only. For your primary integration location, change `probe_mode: false` in the configuration YAML file to enable report metrics and your tenant's Office 365 incident events.

10. Optionally, on the primary site running the O365 reports, which is configured with `probe_mode: true`, enable TopN for Outlook Mailbox Storage and Deleted Used metrics by user. Update the `o365.d/o365.yaml` file and set the `outlook_mailbox_topn` parameter to an appropriate positive integer value of your choosing. A value of `0` disables TopN Outlook mailbox metrics, while a value of `-1` enables collection of all users Outlook mailbox used metrics.

11. Add the `office` tag to the integration configuration in `o365.d/o365.yaml` file to correspond to each office location from which the integration will be running Synthetic checks, for example:

    ```
    tags:
      - "office:boston"
    ```

12. [Restart the Agent][8].

### Validation

[Run the Agent's status subcommand][9] and look for `o365` under the Checks section.

### Known Issues

- **After enabling `outlook_mailbox_topn` the `upn` and `display_name` tags are displayed as Azure Object GUIDs, masking expected user information.**

	Microsoft 365 reports show anonymous user names instead of the actual user names by default as of September 1, 2021. The display of user principal names in Microsoft Graph Reports can be enabled through [Microsoft's troubleshooting instructions][10].

- **Synthetic Email with Outlook data is not displayed in the Office365 dashboard. The Datadog Agent O365 integration reports successful execution and the Synthetic email user mailbox shows properly forwarded emails.**

	Microsoft M365 Exchange implements the [Sender Rewriting Scheme (SRS)][11], which targets auto-forwarding incompatibility with SPF. When this feature is triggered, the Office 365 integration Synthetic email probes are re-enveloped by M365 Exchange and are no longer recognized as responses to the initial Synthetic email probes.

	As a resolution, create a user mailbox redirect rule in the Synthetic user's Outlook instead of a forwarding rule.

		1. Log in to Outlook with the Synthetic user created for the O365 integration.
		2. Navigate to `Settings` -> `View all Outlook settings` -> `Rules` -> `Add new rule`.
		3. Configure the following rule:
			3.1 [Name] "Redirect Synthetic Probe"
			3.2 [Condition] "Subject Includes" = "Synthetic Email Probe"
			3.3 [Add an action] "Redirect to" = "probe@synth-rapdev.io"
			3.4 (Optional) [Add an action] "Mark as read"
			3.5 (Optional) [Add an action] "Delete"

	Once the rule is configured, email responses will populate Datadog metrics and dashboards within 5-10 minutes.

- **Office 365 Incidents are not displayed in the Office 365 Dashboard or in the Datadog Events feed.**

	Microsoft migrated Service Messages from the Management API to the Microsoft Graph API. Upgrade the Office 365 integration on all Datadog Agent systems to version 2.1.1.

	```bash
	# Linux
	sudo -u dd-agent datadog-agent integration install --third-party datadog-o365==2.1.1
	sudo service datadog-agent restart

	# Windows
	"C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-o365==2.1.1
	"C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" restart-service
	```

## Uninstallation

### Agent Integration Uninstall 

1. Run the following command to remove the integration:

    - Linux: `sudo -u dd-agent datadog-agent integration remove datadog-o365`

    - Windows: `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-o365”`

2. Restart the Datadog Agent by using your OS's [restart command][8].

3. Run the Agent status command as described in the Validation section, and verify the integration is no longer running.

YAML Config Cleanup:
- If you plan to reinstall the integration, or need to keep the config files:
    - Navigate to your Agent's `conf.d` directory, and locate the `o365.d` folder to access the YAML configs. **Note**: These files contain sensitive information such as user/password and API keys.
	
- If you plan to fully uninstall with config removal:
    - Navigate to your Agent's `conf.d` directory, and remove the `o365.d` folder.

Microsoft Office 365 Cleanup:
- As a best practice, remove any associated users, apps, and API keys created exclusively for this integration in your o365 account(s). For more details, reference the **Microsoft Office Configuration** section.

## Support

For support or feature requests please contact RapDev.io through the following channels: 

 - Email: support@rapdev.io 
 - Chat: [rapdev.io][12]
 - Phone: 855-857-0222 

### Further Reading

Additional helpful documentation, links, and articles:

- [Monitor Microsoft 365 with RapDev’s integration in the Datadog Marketplace][14]

### Pricing
##### *Volume pricing is only available upon request through a private offer*
| Units | Discount % | Cost/Unit |
|---|---|---|
| 1 - 2499 | 0% | $1 |
| 2500 - 4999 | 25% | $0.75 |
| 5000 + | Variable | Contact [sales@rapdev.io][1] for more information. |
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io][1] for packaged pricing offers.

---

Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note][13] and we'll build it!!*

[1]: mailto:sales@rapdev.io
[2]: https://support.microsoft.com/en-us/office/add-a-new-user-10d7c185-34d1-4648-9b1d-40c45305d2cb
[3]: https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app
[4]: https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps
[5]: https://docs.microsoft.com/en-us/microsoftteams/get-started-with-teams-create-your-first-teams-and-channels
[6]: https://docs.microsoft.com/en-us/exchange/recipients-in-exchange-online/manage-user-mailboxes/configure-email-forwarding
[7]: https://docs.microsoft.com/en-us/onedrive/set-retention
[8]: https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#restart-the-agent
[9]: https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-status-and-information
[10]: https://docs.microsoft.com/en-us/office365/troubleshoot/miscellaneous/reports-show-anonymous-user-name#resolution
[11]: https://docs.microsoft.com/en-us/office365/troubleshoot/antispam/sender-rewriting-scheme
[12]: https://www.rapdev.io/#Get-in-touch
[13]: mailto:support@rapdev.io
[14]: https://www.datadoghq.com/blog/rapdev-microsoft-365-datadog-marketplace/