## Overview

The MaxDB integration monitors data and log areas and volumes, caches, sessions, locks, and other metrics for MaxDB instances to ensure the databases are running as they should be. The integration comes with a dashboard which can be filtered by database, as well as database host. The MaxDB integration also comes with monitors for some common metrics that relate to the overall health of the database.

### Monitors
1. MaxDB Connection Check
2. MaxDB State
3. MaxDB Data Volume Usage
4. MaxDB Lock Utilization
5. MaxDB Log Area Usage

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

## Setup

### Prerequisites
1. You must have the DBM CLI utility on the server with the Datadog Agent installed. This may be specific to your version of MaxDB, so make sure the version aligns with the version of the database installed.

### Install Integration
To install the MaxDB check on your host:

1. Install the integration.
```
sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_maxdb==1.0.0
```

### Prepare the MaxDB

To query the MaxDB system tables, as well as get information such as the DB state and uptime, certain permissions must be granted to the monitoring user. For more information, see [Server Permissions](https://help.sap.com/viewer/a2b90eaeb9ab4081a73792cf467c967b/1909.002/en-US/44c00acc5bb24612e10000000a11466f.html).

1. Connect to the database and run the following command to create a user and set their password (you must have the server permission [UserMgm](https://help.sap.com/viewer/d3bbe2d506ae4964911a87bc9e14b910/1909.002/en-US/44ea1e8eedb767d6e10000000a155369.html)):

   `user_create <user>,<password>` 

2. Grant the newly created user the needed permissions:

   `user_put <user> SERVERRIGHTS=+AccessSQL,+DBInfoRead`

### Configuration
1. Edit the `rapdev_maxdb.d/conf.yaml` file, in the `conf.d/` folder at the root of your Agent's configuration directory.

```
  - hostname: "hostname@example.com"
    dbmcli: "/opt/sdb/MaxDB/bin/dbmcli"
    username: "datadog"
    password: "datadog"
    database: "DEMODB"
    uptime_enabled: false
```

2. [Restart the Datadog Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent).

### Validation

[Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-information) and look for `maxdb` under the Checks section.

Alternatively, you can get detailed information about the integration using the following command.
```
sudo ‐u dd‐agent datadog‐agent check rapdev_maxdb
```

## Uninstallation

### Agent Integration Uninstall 

1. Run the following command to remove the integration:

    - Linux: `sudo -u dd-agent datadog-agent integration remove datadog-rapdev_maxdb`

    - Windows: `“C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration remove datadog-rapdev_maxdb”`
        
2. Restart the Datadog Agent by using your OS's [Restart Command](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#restart-the-agent).

3. Run the Agent status command as described in the Validation section, and verify the integration is no longer running.

YAML Config Cleanup:
- If you plan to reinstall or need to keep the config files:
    - Navigate to your Agent's `conf.d` directory and locate the `rapdev_maxdb.d` folder to access the YAML configs. **NOTE**: These files contain sensitive information such as user/password and server info.
    
- If you plan to fully uninstall with config removal:
    - Navigate to your Agent's `conf.d` directory, and remove the `rapdev_maxdb.d` folder.

MaxDB Cleanup:
- As a best practice, remove any associated users and permissions created exclusively for this integration. For more details, reference the **Prepare the MaxDB** section.

For any questions or problems, view our Support section for ways to get in touch.

## Support

For support or feature requests, contact RapDev.io through the following channels: 

 - Email: support@rapdev.io 
 - Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
 - Phone: 855-857-0222 

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

---
Made with ❤️  in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:support@rapdev.io) and we'll build it!!*
