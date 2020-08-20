# Oracle TimesTen

## Overview

[![Oracle TimesTen Datadog Integration](https://raw.githubusercontent.com/DataDog/marketplace/master/oracle_timesten/images/video.png)](https://www.youtube.com/watch?v=W0Sko27hxrA)

The Oracle TimesTen integration enables you to monitor your TimesTen in-memory databases. This integration covers over 200 metrics and provides details about your top queries, database status, execution times, and much more.

Below are some screenshots of the dashboard that is included with the integration.

![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/oracle_timesten/images/1.png)

![Screenshot2](https://raw.githubusercontent.com/DataDog/marketplace/master/oracle_timesten/images/2.png)

![Screenshot3](https://raw.githubusercontent.com/DataDog/marketplace/master/oracle_timesten/images/3.png)

![Screenshot4](https://raw.githubusercontent.com/DataDog/marketplace/master/oracle_timesten/images/4.png)
 
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
sudo ‐u dd‐agent datadog‐agent integration install --third-party datadog-oracle_timesten==1.0.1`
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
  
  See the [sample oracle_timesten.d/conf.yaml][3] for all available configuration options.

2. [Restart the Datadog Agent][4].

### Validation

[Run the Agent's status subcommand][5] and look for `oracle_timesten` under the Checks section.

Alternatively, you can get detailed information about the integration using the following command.
```
sudo ‐u dd‐agent datadog‐agent check oracle_timesten
```

## Pricing

$500 per Oracle TimesTen database

## Support

For support or feature requests please contact RapDev.io through the following channels: 

 - Email: integrations@rapdev.io 
 - Chat: [RapDev.io/products](https://rapdev.io/products)
 - Phone: 855-857-0222 

Made with ❤️  in Boston

---

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:integrations@rapdev.io) and we'll build it!!*
