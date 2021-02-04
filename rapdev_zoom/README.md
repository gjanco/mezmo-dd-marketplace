# RapDev Zoom Integration

## Overview

The Zoom Integration has the capability of monitoring Meetings, Rooms, Users, Network Statistics, and Geolocation Overviews to provide an optimal experience for your employees, no matter where they are located around the world. The integration comes pre-built with four fully customizable dashboards that bring the most crucial information to the surface. Additionally, we've designed our visuals to be deliverable without changes to C-Level Executives, Managers, Tech Leads, Engineers, and much more!

### Meetings Overview
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_zoom/images/meetings.png)

### Zoom Rooms Dashboard
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_zoom/images/rooms.png)

### Meeting Quality Overview
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_zoom/images/meeting_quality.png)

### User Details Dashboard
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_zoom/images/user_details.png)

### Geolocation Overview
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_zoom/images/geo.png)

### Monitors

1. Zoom Room Has Problem
2. Zoom Room's Component Has A Problem 

### Dashboards

1. RapDev Zoom Meetings Overview
2. RapDev Zoom Rooms Dashboard
3. RapDev Zoom Meeting Quality
4. RapDev Zoom User Details
5. RapDev Zoom Geo Overview

## Setup

Follow the step-by-step instructions below to install and configure this check for an Agent running on a host. 

### Prerequisites

You must have the Datadog Agent installed and running. Additionally, you need to be able to connect to the server with the Datadog Agent installed.

### Installation

```
sudo ‐u dd‐agent datadog‐agent integration install --third-party datadog-rapdev_zoom==2.0.0
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
       min_collection_interval: 60
       account_name: <YOUR_ACCOUNT_NAME>
       collect_plan_usage: False      # requires admin creds
       collect_accounts: False        # requires admin creds
       collect_im_metrics: False
       collect_top_25_issues: False
       collect_participant_details: True   # send metrics for every user rather than averaging them per meeting
       collect_usernames: True             # Collect user-level info, such as user's name, location, etc...
       users_to_track:                     # Only pull in QOS metrics for these emails
         - "bob_smith@myorg.com"
         - "jane_doe@myorg.com"
         - "my_user@myorg2.com"
   ```
   
5. [Restart the Agent][2].

### Validation

1. [Run the Agent's status subcommand][3] and look for `rapdev_zoom` under the Checks section.

    Alternatively, you can get detailed information about the integration using the following command.
    
    ```
    sudo ‐u dd‐agent datadog‐agent check rapdev_zoom
    ```


## Support
For support or feature requests, contact RapDev.io through the following channels:

- Support: integrations@rapdev.io
- Sales: sales@rapdev.io
- Chat: RapDev.io/products
- Phone: 855-857-0222

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note](mailto:integrations@rapdev.io), and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here][4] to purchase this application.

[1]: https://marketplace.zoom.us/
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[3]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[4]: https://app.datadoghq.com/marketplace/app/rapdev-zoom/pricing
