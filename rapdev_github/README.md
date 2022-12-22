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

For Linux:
`sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_github==1.0.0`

For Windows:
`"%ProgramFiles%\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_github==1.0.0` 

1. In GitHub, login under an authenticated user and navigate to your organization or enterprise's `Settings`.

2. Within `Devloper Settings`, select `GitHub Apps`.

3. Click `New GitHub App`.

4. Set `GitHub App Name` to anything, `Homepage URL` to `http://127.0.0.1`, and uncheck `Active` under `Webhook`.

5. For Repository Permissions, set `Actions`, `Issues`, `Metadata`, and `Pull Requests`, to `Read Only`.

6. For Organization Permissions, set `Administration`, `Members`, and `Self-hosted Runners` to `Read Only`.

7. Finally, set `Where can this GitHub App be installed?` to `Only this account` and press `Create GitHub App`.

8. Once created, GitHub should redirect you to the App settings. From here, save the App ID in a secure place as it will be used in the configuration file.

9. Within `Private Keys`, select `Generate a private key`. Save the generated .pem file and the path to a secure location.

10. Click `Install App` and select `Install` for your organization.

11. Ensure `All Repositories` is selected and select `Install`.

12. This should redirect you to the App installation on your org. Within the web address bar, save the 8-digit number at the end of the URL to a secure location.

13. Find where the configuration file is located (usually in `/etc/datadog-agent/conf.d/rapdev_github.d/conf.yaml.example` on Mac and Linux), remove the `.example`, and open the file.

14. Replace `user` with an authenticated user, `org` to the name of your organization or enterprise, `github_mode` to either `organization` or `enterprise` depending on which you are on, and `key_path` to the path to your .pem file that was generated in step 9. The `org_app_id` should be set to the 8-digit ID that was on the end of the URL from step 13, and `gh_app_id` should be set to the 6-digit App ID generated in step 8.

15. `repo_list` is a list of repositories on your organization or enterprise that allow the integration to only look at a set amount of repos. If this is left blank, it will go through all repos (Note: This may increase time between updates by approximately a minute for every 40 repos).

16. Once configured, start the Datadog Agent and begin using the integration.

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
