# Solaris Agent
## Overview

The Solaris Agent allows you to collect and report on Solaris system metrics within Datadog. The integration supports both Solaris 10 and 11, as well as SPARC and i86pc architectures. The Solaris Agent uses the default Solaris Perl system distribution and does not require additional library dependencies, simplifying installation and compatability.

The Solaris Agent provides the host metadata required to support the Datadog Infrastructure List, enabling your organization to work with Solaris host systems similar to other supported Datadog host operating systems.

The Solaris Agent uses the same URLs and ports as the native agents. The Solaris Agent currently supports core infrastructure metrics and log tails. It does not support Agent checks, integrations, or service checks. 

### Solaris agent in infrastructure list

![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_solaris_agent/images/1.png)

![Screenshot3](https://raw.githubusercontent.com/DataDog/marketplace/master/rapdev_solaris_agent/images/3.png)

## Setup

1. Install the Solaris Agent using the Solaris Image Packaging System.
```
pkgadd -d http://rapdev-files.s3.amazonaws.com/solaris/DatadogAgent-1.1.0.pkg
```

2. Install OpenCSW curl. If you have a version of curl that supports HTTPs already on your system, determine the filesystem path to the curl binary and add it to the `/etc/datadog/agent.yml` file in the next step. It's strongly recommended to use OpenCSW curl if possible. Older versions of curl may have outdated SSL libraries.
```
pkgadd -d http://get.opencsw.org/now
/opt/csw/bin/pkgutil -U
/opt/csw/bin/pkgutil -y -i curl 
```

3. Copy `/etc/datadog/agent.yml.example` to `/etc/datadog/agent.yml` and update the Agent configuration parameters as required for installation. When using OpenCSW curl, only the parameter `api_key` needs to be updated for basic Agent functionality.
```
cp /etc/datadog/agent.yml.example /etc/datadog/agent.yml
vi /etc/datadog/agent.yml
```

3. Enable the datadog-agent service.
```
svcadm enable datadog-agent
svcadm restart datadog-agent
```

4. Verify the Solaris Agent is running.
```
ps -ef | grep datadog-agent
tail -f /var/log/datadog/agent.log
```

5. (Optional) Configure log file tails in `/etc/datadog/agent.yml`. Uncomment the `logs:` section in `/etc/datadog/agent.yml` and add configuration for each file tail.
```
# cat /etc/datadog/agent.yml
# {...}
logs:
  - type: file
    path: "/var/adm/messages"
    service: "datadog"
    source: "agent"
```

6. (Optional) Modify `/etc/logadm.conf` if the default settings for log rotation do not meet your organization requirements.
```
cat /etc/logadm.conf
# ...
/var/log/datadog/agent.log -C 10 -c -s 100m
```

## Support

For support or feature requests, contact RapDev.io through the following channels: 

 - Email: integrations@rapdev.io 
 - Chat: [RapDev.io/products](https://rapdev.io/products)
 - Phone: 855-857-0222 
 
---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:integrations@rapdev.io) and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here](https://app.datadoghq.com/marketplace/app/rapdev-solaris-agent/pricing) to purchase this application.
