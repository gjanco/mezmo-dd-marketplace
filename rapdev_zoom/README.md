# RapDev Zoom Integration

## Overview

The Zoom Integration has the capability of monitoring Meetings, Rooms, Users, Network Statistics, and Geolocation Overviews to provide an optimal experience for your employees, no matter where they are located around the world. The integration comes pre-built with four fully customizable dashboards that bring the most crucial information to the surface. Additionally, we've designed our visuals to be deliverable without changes to C-Level Executives, Managers, Tech Leads, Engineers, and much more!

### Monitors

1. Zoom Room Has Problem
2. Zoom Room's Component Has A Problem 

### Dashboards

1. RapDev Zoom Meetings Overview
2. RapDev Zoom Rooms Dashboard
3. RapDev Zoom Meeting Quality
4. RapDev Zoom User Details
5. RapDev Zoom Geo Overview

### Pricing
##### *Volume pricing is only available upon request through a private offer*
| Units | Discount % | Cost/Unit |
|---|---|---|
| 1 - 2499 | 0% | $1 |
| 2500 - 4999 | 25% | $0.75 |
| 5000 + | Variable | Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for more information |
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

## Setup

Follow the step-by-step instructions below to install and configure this check for an Agent running on a host. 

### Prerequisites

The following items are all required for this integration to run as intended:
  - You must have the Datadog Agent installed and running.
  - Access to the server running the Datadog Agent and modify the configurations.
  - The Zoom account you are ingesting data for is NOT a free account.


### Installation

```
*Linux*
sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_zoom==5.2.0

*Powershell*
& "$env:ProgramFiles\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_zoom==5.2.0

*Command Prompt*
"%PROGRAMFILES%\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_zoom==5.2.0
``` 

### Configuration
1. Start by navigating to the [Zoom Marketplace][1] to generate an `API Key` and `API Secret` to authenticate to the Zoom API. 

2. Once there, click on `Develop` in the upper right hand-corner and then select `Build App`. If prompted, please sign in.

3. If you don't already have `JWT` enabled under the JWT section, click on `Create`. Otherwise, select `View Here`.

4. You should see an `API Key` and an `API Secret` on the page. You will need to copy and paste both these values accordingly into your agent's zoom configuration file `conf.d/rapdev_zoom.d/conf.yaml`. 
Finish the configuration by filling in your Zoom Account name. See below for an example:
   
   ```
   init_config: 
   
   instances:
     - base_api_url: "https://api.zoom.us/v2/"
       api_key: <YOUR_API_KEY>
       api_secret: <YOUR_API_SECRET>
       account_name: <YOUR_ACCOUNT_NAME>

       # Set to true to collect only rooms metrics
       room_only_mode: False

       collect_usernames: True
       collect_participant_details: True

       # Only collect metrics on specific users (not required)
       users_to_track:
         - "bob_smith@myorg.com"
         - "jane_doe@myorg.com"
         - "my_user@myorg2.com"
   ```
   
5. [Restart the Agent][2].

#### Sub Account Data Ingestion

When pulling data in for Zoom sub-accounts, you have two options:

1. (Recommended) Log in to your sub-account using the owner email and generate an API key and secret for each sub-account (see steps above for how-to).
Using your credentials, define an instance for each account in your `conf.yaml`. With this approach, each Zoom account has their own rate limit.
See the example below for a correct minimal configuration for this setup (`master_api_mode` defaults to `False` so you are not required to include it here):

    ```
    init_config: 
   
    instances:
      - base_api_url: "https://api.zoom.us/v2/"
        api_key: <YOUR_API_KEY>
        api_secret: <YOUR_API_SECRET>
        account_name: <YOUR_ACCOUNT_NAME>

      - base_api_url: "https://api.zoom.us/v2/"
        api_key: <YOUR_API_KEY2>
        api_secret: <YOUR_API_SECRET2>
        account_name: <YOUR_ACCOUNT_NAME2>
    ```

2. Use the master account API credentials to access your sub-accounts. **Note**: This contributes towards the rate limit of the main account. It is only suggested that
you use this approach if you don't have a limit on your Zoom API. To run in this mode, set the `master_api_mode` in the `conf.yaml` to `True`. The configuration for
this would look similar to the following example:

    ```
    init_config: 
   
    instances:
      - base_api_url: "https://api.zoom.us/v2/"
        api_key: <YOUR_API_KEY>
        api_secret: <YOUR_API_SECRET>
        account_name: <YOUR_ACCOUNT_NAME>
        master_api_mode: True
    ```

### Validation

1. [Run the Agent's status subcommand][3] and look for `rapdev_zoom` under the Checks section.

    Alternatively, detailed information is available about the integration using the following command:
    
    ```
    *Linux*
    sudo -u dd-agent datadog-agent check rapdev_zoom
    
    *Powershell*
    & "$env:ProgramFiles\Datadog\Datadog Agent\bin\agent.exe" check rapdev_zoom

    *Command Prompt*
    "%PROGRAMFILES%\Datadog\Datadog Agent\bin\agent.exe" check rapdev_zoom
    ```


## Support
For support or feature requests, contact RapDev.io through the following channels:

- Support: datadog-engineering@rapdev.io
- Sales: sales@rapdev.io
- Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
- Phone: 855-857-0222

### Pricing
##### *Volume pricing is only available upon request through a private offer*
| Units | Discount % | Cost/Unit |
|---|---|---|
| 1 - 2499 | 0% | $1 |
| 2500 - 4999 | 25% | $0.75 |
| 5000 + | Variable | Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for more information |
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note](mailto:datadog-engineering@rapdev.io), and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here][4] to purchase this application.

[1]: https://marketplace.zoom.us/
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[3]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[4]: https://app.datadoghq.com/marketplace/app/rapdev-zoom/pricing
