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

### Uninstallation
1. Remove all Datadog files associated with this integration.

2. Within Gitlab, navigate to `Admin` from the Menu and under `Overview`, click on `Users`.

3. Delete the user that was created in the installation process.

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