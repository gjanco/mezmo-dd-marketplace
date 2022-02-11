# HP-UX Agent
## Overview

The HP-UX Agent allows you to collect and report on system metrics within Datadog. The integration supports HP-UX 11.31 on both PA-RISC and Itanium architectures. The HP-UX Agent uses the default HP-UX Perl system distribution and does not require additional library dependencies, simplifying installation and compatability.

The HP-UX Agent provides the host metadata required to support the Datadog Infrastructure List, enabling your organization to work with HP-UX host systems similar to other supported Datadog host operating systems.

The HP-UX Agent uses the same URLs and ports as the native agents. The HP-UX Agent currently supports core infrastructure metrics, process checks, and log tails. It does not support Agent checks, integrations, or service checks.  

## Setup

1. A current installation of curl is required on each HP-UX Agent host. The HP-UX Agent was built and tested with [curl-7.73.0](http://hpux.connect.org.uk/hppd/hpux/Networking/WWW/curl-7.73.0/) from the [HP-UX Porting and Archive Centre](http://hpux.connect.org.uk).

2. Download the HP-UX Agent install [package](http://rapdev-files.s3.amazonaws.com/hpux/DatadogAgent-1.3.0.tgz).
```sh
cd /tmp
/usr/local/bin/curl -o DatadogAgent-1.3.0.tgz http://rapdev-files.s3.amazonaws.com/hpux/DatadogAgent-1.3.0.tgz 
```

3. Ensure that every HP-UX Agent host has a current installation of Gzip. The HP-UX Agent was built and tested with `gzip v1.3.5`, and defaults to `/usr/contrib/bin/gzip`.

4. Install the HP-UX Agent. You can run the `install.sh` script to update an existing HP-UX Agent install.
```sh
cd /tmp
gunzip -c DatadogAgent-1.3.0.tgz | tar -xvf -
cd /tmp/datadog-agent-install
./install.sh 
```

5. Copy `/etc/datadog/agent.yml.example` to `/etc/datadog/agent.yml` and update the HP-UX Agent settings in the `/etc/datadog/agent.yml` file:

    i. (Required) Set the `api_key` value to your Datadog's API key string.

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
        path: /var/adm/syslog/*
        service: datadog
        source: agent
    ```

    Standard filesystem path globs are supported.

    v. (Optional) Uncomment the `processes:` section in `/etc/datadog/agent.yml` and add a configuration for desired process checks.
    ```yaml
    processes:
     - name: ssh
       search_string: (ssh|sshd)

     - name: apache
       search_string: apache
    ```

    The following metrics are supported for process checks.
    | Name | Description | Included Tags |
    | --- | --- | --- |
    | system.processes.mem.vms | Process virtual memory size (bytes) | `process_name`, `process_pid` |
    | system.processes.mem.rss | Process resident memory size (bytes) | `process_name`, `process_pid` |
    | system.processes.mem.pct | Process memory usage (percent) | `process_name`, `process_pid` |
    | system.processes.cpu.pct | Process cpu usage (percent) | `process_name`, `process_pid` |
    | system.processes.number | Running process count (matching search_string) | `process_name` |

    vi. (Optional) Add your desired configurations in `/etc/datadog/agent.yml` for include, exclude, and tags to apply on filesystems. See the example `agent.yml` for specific configuration options. See `/etc/datadog/agent.yml.example` for all filesystem configuration options and examples.
    ```yaml
    mount_point_tag_re:
      /home: role:home
      /tmp: role:temp,disk_size:large
    ```  

    vii. (Optional) If your Datadog instance is located in the EU instead of the US, uncomment the following settings:
    ```yaml
    dd_url: https://api.datadoghq.eu
    dd_log_url: https://http-intake.logs.datadoghq.eu
    ```

    viii. (Optional) If your host system requires a proxy to communicate with Datadog's APIs, uncomment and update the following settings:
    ```yaml
    proxy_host: my-proxy.com
    proxy_port: 3128
    proxy_user: username
    proxy_pass: password
    ```

    ix. (Optional) If the host is using an installation of cURL other than `/usr/local/bin/curl`, uncomment and update the following setting. The version of cURL specified here should be current enough to support updated versions of TLS.
    ```yaml
    curl_bin: /usr/local/bin/curl
    ```

    x. (Optional) The HP-UX Agent includes a recent version of the [CA extract](https://curl.se/docs/caextract.html) PEM file located at `/opt/datadog-agent/ssl/cacert.pem`. Change this setting to your organization's `cacert.pem` bundle when using an SSL traffic inspection proxy for egress internet access. The `dd-agent` user should have directory and file access permissions on the `cacert.pem` file as well as the parent directory to read the CA Bundle.
    ```yaml
    cacert: /etc/ssl/cacert.pem
    ```

    xi. (Optional) If there are issues with the supplied CA Bundle or the custom CA Bundle from your organization, SSL validation can be disabled by setting the following value in the configuration file. However, this setting is not recommended as it disables SSL validation of the Datadog API hosts.
    ```yaml
    skip_ssl_validation: yes
    ```

    xii. (Optional) If Gzip is not available on your HP-UX system, disable log compression. However, this setting is not recommended as it degrades performance for log tail message intake.
    ```yaml
    compress_logs: no
    ```

6. Start the HP-UX Agent.
```sh
/sbin/init.d/datadog-agent start
```

7. Verify the HP-UX Agent is running.
```sh
ps -ef | grep datadog-agent
tail -n25 -f /var/log/datadog/agent.log
```

8. The HP-UX Agent is configured to run on system boot with `/init.d/rc3.d/S999datadog-agent`. If you need to disable the HP-UX Agent on system boot, change the `ENABLED` setting in the `/etc/rc.config.d/datadog-agent` file.
```
ENABLED=0 # <-- disables the agent from running at boot
USERNAME="datadog"
LOGLEVEL="INFO"
```

9. If you need to start, stop or restart the HP-UX agent, use the following commands:
```sh
/sbin/init.d/datadog-agent stop
/sbin/init.d/datadog-agent start
```

10. The HP-UX Agent log is located at `/var/log/datadog/agent.log`. Since base HP-UX does not come with logrotate, add a logrotate or cron job configuration to your host(s) to prevent disk starvation from the HP-UX Agent logs.

11. The HP-UX Agent can be uninstalled using the `uninstall.sh` script provided in the tarball package. Configuration files and logs are not removed and must be removed manually from `/var/log/datadog/` and `/etc/datadog/`.
```sh
cd /tmp/datadog-agent-install
./uninstall.sh
```

## Support

For support or feature requests, contact RapDev.io through the following channels: 

 - Email: datadog-engineering@rapdev.io 
 - Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
 - Phone: 855-857-0222 
 
---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:datadog-engineering@rapdev.io) and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here](https://app.datadoghq.com/marketplace/app/rapdev-hpux-agent/pricing) to purchase this application.
