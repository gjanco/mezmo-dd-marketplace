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
6. RapDev Zoom Phones Overview

### Pricing
##### *Volume pricing is only available upon request through a private offer*
| Units | Discount % | Cost/Unit |
|---|---|---|
| 1 - 2499 | 0% | $1 |
| 2500 - 4999 | 25% | $0.75 |
| 5000 + | Variable | Contact [sales@rapdev.io](mailto:sales@rapdev.io) for more information |
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

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
sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_zoom==6.0.0

*Powershell*
& "$env:ProgramFiles\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_zoom==6.0.0

*Command Prompt*
"%PROGRAMFILES%\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_zoom==6.0.0
``` 

### Configuration
1. Start by navigating to the [Zoom Marketplace][1] to generate the authentication parameters for the integration. 

2. Once there, click on `Develop` in the upper right hand-corner and then select `Build App`. If prompted, please sign in.

3. You can authenticate via `Server-to-Server OAuth` (recommended) or `JWT`: 
  - <b>Server-To-Server OAuth</b>: 
    1. Click `Create` under the `Server-to-Server OAuth` section. Begin by copying the 3 values under `App Credentials` into the Datadog Zoom configuration file and select `Continue`.
    2. Enter the information for your app including `App Name` (such as Datadog Zoom integration), `Company Name`, your `Name`, and `Email`, and hit `Continue`. 
    3. On the `Scopes` page, provide all `*:read:admin` permissions and hit `Continue`.
    4. Finally, activate the application and your authentication setup should be good to go!
  - <b>JWT</b>: If you don't already have `JWT` enabled under the JWT section, click `Create`. Otherwise, select `View Here`. You should see an `API Key` and an `API Secret` on the page.
  

You will need to copy and paste both the values from above accordingly into your Agent's Zoom configuration file `conf.d/rapdev_zoom.d/conf.yaml`. 

See the following for an example of each authentication type (there are many more parameters available in the configuration YAML file):
   
   ```
   init_config: 
   
   instances:
    ## This is an example oAuth configuration
     - account_id: <ACCOUNT_ID>
       client_id: <CLIENT_ID>
       client_secret: <CLIENT_SECRET>
       authentication_type: "oauth"
       account_name: <ACCOUNT_NAME_TAG>

    ## This is an example JWT Configuration
     - api_key: <YOUR_API_KEY>
       api_secret: <YOUR_API_SECRET>
       account_name: <YOUR_ACCOUNT_NAME>
   ```
   
4. [Restart the Agent][2].

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

## Uninstallation

### Agent Integration Uninstall 

1. Run the following command to remove the integration:

    - Linux: `sudo -u dd-agent datadog-agent integration remove datadog-rapdev_zoom`

    - Windows: `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-rapdev_zoom”`
        
2. Restart the Datadog Agent by using your OS's [Restart Command](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#restart-the-agent).

3. Run the Agent status command as described in the Validation section, and verify the integration is no longer running.

YAML Config Cleanup:
- If you plan to reinstall or need to keep the config files:
    - Navigate to your Agent's `conf.d` directory and locate the `rapdev_zoom.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as API keys.
    
- If you plan to fully uninstall with config removal:
    - Navigate to your Agent's `conf.d` directory, and remove the `rapdev_zoom.d` folder.

Zoom Cleanup:
- As a best practice, remove any associated API keys, apps or secrets created exclusively for this integration. For more details, reference the Configuration section.

For any questions or problems, view our Support section for ways to get in touch.

## Support
For support or feature requests, contact RapDev.io through the following channels:

- Support: support@rapdev.io
- Sales: sales@rapdev.io
- Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
- Phone: 855-857-0222

### Pricing
##### *Volume pricing is only available upon request through a private offer*
| Units | Discount % | Cost/Unit |
|---|---|---|
| 1 - 2499 | 0% | $1 |
| 2500 - 4999 | 25% | $0.75 |
| 5000 + | Variable | Contact [sales@rapdev.io](mailto:sales@rapdev.io) for more information |
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note](mailto:support@rapdev.io), and we'll build it!!*

[1]: https://marketplace.zoom.us/
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[3]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information

