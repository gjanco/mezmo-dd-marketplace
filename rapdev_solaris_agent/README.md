# Solaris Agent
## Overview

The Solaris Agent allows you to collect and report on Solaris system metrics within Datadog. The integration supports both Solaris 10 and 11, as well as SPARC and i86pc architectures. The Solaris Agent uses the default Solaris Perl system distribution and does not require additional library dependencies, simplifying installation and compatability.

The Solaris Agent provides the host metadata required to support the Datadog Infrastructure List, enabling your organization to work with Solaris host systems similar to other supported Datadog host operating systems.

The Solaris Agent uses the same URLs and ports as the native agents. The Solaris Agent currently supports core infrastructure metrics and log tails. It does not support Agent checks, integrations, or service checks. 

## Setup

1. A current installation of curl is required on each Solaris Agent host system. The Solaris Agent was built and tested with curl from the [OpenCSW](https://www.opencsw.org/about/) project.
```sh
pkgadd -d http://get.opencsw.org/now
/opt/csw/bin/pkgutil -U
/opt/csw/bin/pkgutil -y -i curl
```

2. Install the Solaris Agent using the Solaris Image Packaging System. 
```sh
pkgadd -d http://rapdev-files.s3.amazonaws.com/solaris/DatadogAgent-1.2.0.pkg
```

3. If you are upgrading an existing Solaris Agent installation, first remove the current Solaris Agent package. The Solaris Agent configuration and log files will be retained.
```sh
pkgrm DatadogAgent
pkgadd -d http://rapdev-files.s3.amazonaws.com/solaris/DatadogAgent-1.2.0.pkg
```

4. Copy `/etc/datadog/agent.yml.example` to `/etc/datadog/agent.yml` and update the Solaris Agent configuration settings in the `/etc/datadog/agent.yml` file.

    ```sh
    cp /etc/datadog/agent.yml.example /etc/datadog/agent.yml
    vi /etc/datadog/agent.yml
    ```

    i. (Required) Set the `api_key` value to your Datadog's API key string.
    ```yaml
    api_key: <datadog-api-key>
    ```

    ii. (Optional) Uncomment and set the `hostname` setting if you do not want to rely on dynamic system lookup of the hostname.
    ```yaml
    hostname: your-hostname.your-domain
    ```

    iii. (Optional) Uncomment and set the `tags` setting to specify tags to include on all metrics and logs.
    ```yaml
    tags:
      - environment:dev
    #  - <TAG_KEY1>:<TAG_VALUE1>
    #  - <TAG_KEY2>:<TAG_VALUE2>
    ```

    iv. (Optional) Uncomment the `logs:` section in `/etc/datadog/agent.yml` and add a configuration for desired log tail. The `dd-agent` user requires read access to all files configured for log tails.
    ```yaml
    logs:
      - type: file
        path: /var/adm/messages
        service: datadog
        source: agent
    ```

    v. (Optional) If your Datadog instance is located in the EU instead of the US, uncomment the following settings:
    ```yaml
    dd_url: https://api.datadoghq.eu
    dd_log_url: https://http-intake.logs.datadoghq.eu
    ```

    vi. (Optional) If your host system requires a proxy to communicate with Datadog's APIs, uncomment and update the following settings:
    ```yaml
    proxy_host: my-proxy.com
    proxy_port: 3128
    proxy_user: username
    proxy_pass: password
    ```

    vii. (Optional) If the host is using an installation of curl other than `/opt/csw/bin/curl`, uncomment and update the following setting. The version of curl specified here should be current enough to support updated versions of TLS.
    ```yaml
    curl_bin: /opt/csw/bin/curl
    ```

    viii. (Optional) The Solaris Agent includes a recent version of the [CA extract](https://curl.se/docs/caextract.html) PEM file located at `/opt/datadog-agent/ssl/cacert.pem`. Change this setting to your organization's cacert.pem bundle when using an SSL traffic inspection proxy for egress internet access. The `dd-agent` user should have directory and file access permissions on the cacert.pem file as well as the parent directory to read the CA Bundle.
    ```yaml
    cacert: /etc/ssl/cacert.pem
    ```

    ix. (Optional) If there are issues with the supplied CA Bundle or the custom CA Bundle from your organization, SSL validation can be disabled by setting the following value in the configuration file. However, this setting is not recommended as it will disable SSL validation of the Datadog API hosts.
    ```yaml
    skip_ssl_validation: yes
    ```

5. Enable the datadog-agent service.
```sh
svcadm enable datadog-agent
```

6. Verify the Solaris Agent is running.
```sh
svcs datadog-agent
ps -ef | grep datadog-agent
tail -f /var/log/datadog/agent.log
```

7. If you need to restart the Solaris Agent, use the following command:
```sh
svcadm restart datadog-agent
```

8. (Optional) Modify `/etc/logadm.conf` if the default settings for log rotation do not meet your organization requirements.
```sh
cat /etc/logadm.conf
# {...}
/var/log/datadog/agent.log -C 10 -c -s 10m
```

## Support

For support or feature requests, contact RapDev.io through the following channels: 

 - Email: datadog-engineering@rapdev.io 
 - Chat: [RapDev.io/products](https://rapdev.io/products)
 - Phone: 855-857-0222 
 
---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:datadog-engineering@rapdev.io) and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here](https://app.datadoghq.com/marketplace/app/rapdev-solaris-agent/pricing) to purchase this application.
