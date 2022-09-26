## Overview
The RapDev SNMP Trap Logs package enables converting SNMP Trap messages into Datadog Logs for thousands of different
SNMP devices. We have collected as many MIB files as we could find, and have converted them to a format allowing for
the translation of SNMP traps into human-readable log messages.

This package comes with an install script to setup Logstash as an SNMP trap receiver, with the proper configurations
and MIB files to translate your messages, allowing you to alert on network events within Datadog.

For a list of all MIBs that are included with this package, [see here][4].

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

## Setup

1. On the host machine that will receive traps, run `wget https://files.rapdev.io/datadog/scripts/install_snmp_traps.sh`.
2. Ensure `DATADOG_API_KEY` is set in your environment, or provide it at install script execution time (example below).
3. Run the script: `DATADOG_API_KEY=<your_api_key> bash install_snmp_traps.sh`.
4. Enable and start the service with your operating system's service provider, for example, `service logstash start` or `systemctl start logstash.service`.

### Requirements

* Linux/UNIX type operating system (Tested on Ubuntu/CentOS/Fedora/Debian)
* `wget` installed
* Datadog API key

### Additional Configuration

- The configuration file for Logstash is set to listen on port 162 (trap receiver default). If you need to change this to a different port,
  edit the file found under `/opt/logstash/logstash-<version>/config/logstash.conf` and change the value of `port` in the `input` section.
- The configuration file for Logstash is set to listen for the community string of `public`. If you need to listen for other or additional
  community strings, edit the file found under `/opt/logstash/logstash-<version>/config/logstash.conf` and change the value of `community`.
  To replace `public`, simply replace that value. To add additional strings to listen for, append to the list: `['public', 'my_community']`.
- Due to the amount of MIB files provided, Logstash may take several minutes to start. If you wish to reduce this startup time, you may want
  to remove the MIB files that you do not need. These can be found in `/opt/logstash/yamlmibs/yamls`. For a list of all MIBs that are included
  with this package, [see here][4].
    - Exercise caution when removing MIB files, as there is a hierarchy within MIBs, and full translations may not occur if some of the base
      MIBs are removed. These include items like `IF-*`, `INET-*`, `IP-*`, and `SNMP-*`. The full list of dependencies can be found by using MIB
      browsers such as the [Observium MIB Database](https://mibs.observium.org).

### Filtering and Enriching Data in Datadog

- To create an easy filtering experience in Datadog that will include only SNMP trap messages in Datadog, the field `type` is set 
  to `snmptrap`. To filter in Datadog, use the query `@type:snmptrap`
- The use of Enrichment Tables is encouraged - the `host` field will be presented as an IP. If you desire your SNMP traps to contain a hostname,
  enrichment tables can be provided to translate IPs in the `host` field to hostnames. For more information, see [Enrichment Tables.][1].
- After setting up enrichment tables, create a facet for the field created via enrichment. We recommend `snmphost.host` as the enrichment field, as
  it is the field used in the provided dashboard to filter logs.
- For ease of visualization, it is also encouraged to use the [Message Remapper][2] functionality within Datadog. For example, if you 
  know the `ccvpEventText` field contains data you want as a log message, add that to the message remapper. Logs not containing that
  field will not be affected, and multiple remapped fields can be added over time.

## Support
For support or feature requests, contact RapDev.io through the following channels:

- Email: support@rapdev.io
- Chat: [rapdev.io][3]
- Phone: 855-857-0222

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note](mailto:support@rapdev.io), and we'll build it!!*

[1]: https://docs.datadoghq.com/logs/guide/enrichment-tables
[2]: https://docs.datadoghq.com/logs/log_configuration/processors/?tab=ui#log-message-remapper
[3]: https://www.rapdev.io/#Get-in-touch
[4]: https://files.rapdev.io/datadog/configs/mib_yamls.txt
