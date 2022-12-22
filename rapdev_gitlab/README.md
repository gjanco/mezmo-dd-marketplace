# RapDev GitLab Integration

## Overview
GitLab is a DevOps software package that combines the ability to develop, secure, and operate software in a single application. This integration collects and reports the following GitLab metrics through different endpoints in the GitLab API:
+ Project metrics
+ Sidekiq stats
+ Instance metrics
+ Installed runners
+ Total and open issues

### Dashboards
This integration provides an out-of-the-box dashboard called **RapDev GitLab Dashboard** which displays data submitted to Datadog over time, and includes environment variables to further narrow down a search on a specific project or host.

## Setup

### Prerequisites
You must have the Datadog Agent installed on a host. You also must be able to connect to that host and be able to edit the files so as to configure the Agent and YAML Integration Configs. Refer to [these instructions][1] to install the Datadog Agent.

### Installation

Run the following commands to install the integration:

For Linux:
`sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_gitlab==1.0.0`

For Windows:
`"%ProgramFiles%\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_gitlab==1.0.0`

1. In GitLab, login under an authenticated account with administrator privileges.

2. Navigate to `Admin` from the Menu in the top left corner.

3. Under `Overview`, click on `Users` and create a new user.

4. Fill out the required fields with Administrator access level and is not an external user. An email alias may be used but you will need to access the email invitation to create a new password. 

5. Reset and create a new password with the email that is sent.

6. Within the Datadog yaml file, set the `base_url` to your organization's url and set the username and password to the ones for the user created earlier from step 4.

## Uninstallation

### Agent Integration Uninstall 

1. Run the following command to remove the integration:

    - Linux: `sudo -u dd-agent datadog-agent integration remove datadog-rapdev_gitlab`

    - Windows: `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-rapdev_gitlab”`
        
2. Restart the Datadog Agent by using your OS's [Restart Command](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#restart-the-agent).

3. Run the Agent status command as described in the Validation section, and verify the integration is no longer running.

YAML Config Cleanup:
- If you plan to reinstall or need to keep the config files:
    - Navigate to your Agent's `conf.d` directory and locate the `rapdev_gitlab.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as API tokens.
    
- If you plan to fully uninstall with config removal:
    - Navigate to your Agent's `conf.d` directory, and remove the `rapdev_gitlab.d ` folder.

Gitlab Cleanup:
- As a best practice, remove any associated users and passwords created exclusively for this integration. for more details, reference the Installation section.

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
[note][2], and we'll build it!!*

[1]: https://docs.datadoghq.com/getting_started/agent/
[2]: mailto:support@rapdev.io
