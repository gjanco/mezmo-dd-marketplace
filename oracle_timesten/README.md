# Oracle TimesTen

## Overview

The Oracle TimesTen integration enables you to monitor your TimesTen in-memory databases. This integration covers over 200 metrics and provides details about your top queries, database status, execution times, and much more.

The integration includes an out-of-the-box dashboard that shows an overview of your TimesTen databases' status and metrics.

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

## Setup

### Prerequisites
The Oracle TimesTen instant client and development package must be installed on the same system as the Datadog Agent and configured to connect to the TimeTen DB to be monitored.
1. Download the packages from Oracle:
```
wget https://download.oracle.com/otn_software/linux/instantclient/19600/oracle‐instantclient19.6‐basic‐19.6.0.0.0‐1.x86_64.rpm
wget https://download.oracle.com/otn_software/linux/instantclient/19600/oracle‐instantclient19.6‐devel‐19.6.0.0.0‐1.x86_64.rpm
```
2. Install the client and development packages.
```
sudo rpm ‐iUv /home/oratta/oracle‐instantclient19.6‐basic‐19.6.0.0.0‐ 1.x86_64.rpm
sudo rpm ‐iUv /home/oratta/oracle‐instantclient19.6‐devel‐19.6.0.0.0‐ 1.x86_64.rpm
```
3. Configure the client libraries on the system (NB: these paths need to be configured to match your system).
```
cd /etc/ld.so.conf.d/
sudo echo "/path/to/tt18.1.3.3.0/lib/" > oracle-timesten.conf
sudo echo "/usr/lib/oracle/19.6/client64/lib" > oracle‐instantclient.conf
sudo ldconfig
```
4.Create Oracle TimesTen users for the Datadog Agent Check using ttisql.
```
create user datadog identified by datadog;
GRANT CREATE SESSION to DATADOG;
GRANT EXECUTE ON SYS.TT_STATS TO DATADOG;
```

### Install Integration
To install the oracle_timesten check on your host:

1. Install the integration.
```
sudo ‐u dd‐agent datadog‐agent integration install --third-party datadog-oracle_timesten==1.0.1
```

### Configuration
1. Edit the `oracle_timesten.d/conf.yaml` file, in the `conf.d/` folder at the root of your Agent's configuration directory.

```
‐ database: master1:timestendirect
  username: datadog
  password: datadog
  hostname: 127.0.0.1
  verbose_flag: 1
  logs_flag: 1
  timesten_home: '/path/to/oratta/timesten/tt181'
  endpoint: https://http‐intake.logs.datadoghq.com/v1/input/
```

  See the sample `oracle_timesten.d/conf.yaml.example` provided during the integration installation for all available configuration options.

2. [Restart the Datadog Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#start-stop-and-restart-the-agent).

### Validation

[Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-information) and look for `oracle_timesten` under the Checks section.

Alternatively, you can get detailed information about the integration using the following command.
```
sudo ‐u dd‐agent datadog‐agent check oracle_timesten
```

## Support

For support or feature requests please contact RapDev.io through the following channels:

 - Email: datadog-engineering@rapdev.io
 - Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
 - Phone: 855-857-0222

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

---
Made with ❤️  in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:datadog-engineering@rapdev.io) and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here](https://app.datadoghq.com/marketplace/app/rapdev-oracle-timesten/pricing) to purchase this application.
