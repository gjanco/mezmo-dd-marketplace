# RapDev GitHub Integration

## Overview
This integration collects and reports GitHub metrics to Datadog through
different endpoints in the GitHub API. The following varieties
of metrics are submitted:
+ Organization/Enterprise Stats
+ Repository Metrics
+ Self-hosted and Installed Runners
+ GitHub Workflow Monitoring

### Dashboards
This integration provides an out-of-the-box dashboard called
**RapDev GitHub Dashboard**.
This dashboard populates as data is submitted to Datadog over time and includes
environment variables to further narrow down a search
on a specific repo or author.

## Setup

### Prerequisites
You must have the Datadog Agent installed on a host. You also
must be able to connect to that host and be able to edit the files
so as to configure the Agent and YAML Integration Configs.  Refer to [these instructions](https://docs.datadoghq.com/getting_started/agent/) to install the Datadog Agent.

### Installation

Run the following commands to install the integration:

```
## Linux ##
`sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_github==1.0.0`

## Windows ##
`"%ProgramFiles%\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_github==1.0.0` 
```

1. In GitHub, navigate to the [Developer Settings Page](https://github.com/settings/apps). If prompted, login and navigate to **Settings** > **Developer Settings** > **Github Apps**. 

2. Click **New GitHub App** and set the following fields accordingly:
    - Set `GitHub App Name` to a name of your choice.
    - `Homepage URL` to `http://127.0.0.1`.
    - Uncheck `Active` under `Webhook`.

3. Under the **Permissions** section, set the following permissions:
    - <b>Repository Permissions:</b> set `Actions`, `Issues`, `Metadata`, and `Pull Requests`, to `Read Only`.
    - <b>Organization Permissions:</b> set `Administration`, `Members`, and `Self-hosted Runners` to `Read Only`.

4. Finally, set `Where can this GitHub App be installed?` to `Any account` and click **Create GitHub App**. Once created, GitHub should redirect you to the App settings. Save the App ID in a secure place as this is used in the configuration file.

5. Scroll down to the `Private Keys` section and click **Generate a private key**. It should automatically save the `.pem` file. If you'd like, you can move this to somewhere more secure.

6. Click `Install App` on the left hand side and select `Install` for the organization you'd like to monitor. Ensure `All Repositories` is selected and select `Install`. Repeat this step for any additional organizations you'd like to monitor.

    This should redirect you to the App installation on your org. Within the web address bar, save the 8-digit number at the end of the URL to a secure location.

7. Find where the `conf.d/rapdev_github.d/conf.yaml.example` [configuration file](https://docs.datadoghq.com/agent/guide/agent-configuration-files/?tab=agentv6v7#agent-configuration-directory) is located, remove the `.example` from the file name, and open the file to set the following:
    - `user`: The name of the authenticated user.
    - `org`: The name of your organization or enterprise.
    - `github_mode`: Either `organization` or `enterprise`, depending on which you are on.
    - `key_path`: The path to your `.pem` file that was generated in Step 9.
    - `org_app_id`: The 8-digit ID that was on the end of the URL from Step 13.
    - `gh_app_id`: The 6-digit App ID generated in Step 8.
    - `repo_list`: A list of repositories on your organization or enterprise that the integration should look at. If this is left blank, it goes through all repos (<b>Note</b>: This may increase time between updates by approximately one minute for every 40 repos).

8. Once configured, [start the Datadog Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7) and begin using the integration.

## Uninstallation

### Agent Integration Uninstall 

1. Run the following command to remove the integration:

    - Linux: `sudo -u dd-agent datadog-agent integration remove datadog-rapdev_github`

    - Windows: `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-rapdev_github”`
        
2. Restart the Datadog Agent by using your OS's [Restart Command](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#restart-the-agent).

3. Run the Agent status command as described in the Validation section, and verify the integration is no longer running.

YAML Config Cleanup:
- If you plan to reinstall or need to keep the config files:
    - Navigate to your Agent's `conf.d` directory and locate the `rapdev_github.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as API tokens.
    
- If you plan to fully uninstall with config removal:
    - Navigate to your Agent's `conf.d` directory, and remove the `rapdev_github.d` folder.

Github Cleanup:
- As a best practice, remove any associated API keys and apps created exclusively for this integration. For more details, reference the Installation section.

For any questions or problems, view our Support section for ways to get in touch.

## Support
For support or feature requests, contact RapDev.io through the following channels:
- Support: support@rapdev.io
- Sales: sales@rapdev.io
- Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
- Phone: 855-857-0222

### Pricing

Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

---
Made with ❤️ in Boston
*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a 
[note](mailto:support@rapdev.io), and we'll build it!!*
