# HP-UX Agent
## Overview

The HP-UX Agent allows you to collect and report on system metrics within Datadog. The integration supports HP-UX 11.31 on both PA-RISC and Itanium architectures. The HP-UX Agent uses the default HP-UX Perl system distribution and does not require additional library dependencies, simplifying installation and compatability.

The HP-UX Agent provides the host metadata required to support the Datadog Infrastructure List, enabling your organization to work with HP-UX host systems similar to other supported Datadog host operating systems.

The HP-UX Agent uses the same URLs and ports as the native agents. The HP-UX Agent currently supports core infrastructure metrics, process checks, and log tails. It does not support custom Agent checks, integrations, or service checks.

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

## Setup

1. Install a current version of cURL if your system does not have one available. The HP-UX Agent was built and tested with [curl-7.73.0](http://hpux.connect.org.uk/hppd/hpux/Networking/WWW/curl-7.73.0/) from the [HP-UX Porting and Archive Centre](http://hpux.connect.org.uk).

2. Download the HP-UX Agent install [package](http://rapdev-files.s3.amazonaws.com/hpux/DatadogAgent-1.5.3.tgz).
```sh
mkdir -p /tmp/datadog-agent-install
cd /tmp/datadog-agent-install
/usr/local/bin/curl -o DatadogAgent-1.5.3.tgz http://rapdev-files.s3.amazonaws.com/hpux/DatadogAgent-1.5.3.tgz 
```

3. Install the HP-UX Agent. You can run the `install.sh` script to update an existing HP-UX Agent install.
```sh
cd /tmp/datadog-agent-install
gunzip -c DatadogAgent-1.5.3.tgz | tar -xvf -
./install.sh 
```

4. Copy `/etc/datadog/agent.yaml.example` to `/etc/datadog/agent.yaml` and update the HP-UX Agent settings in the `/etc/datadog/agent.yaml` file:

    i. (Required) Set the `api_key` value to your Datadog's API key string.

    ii. (Optional) Uncomment and set the `hostname` setting if you do not want to rely on dynamic system lookup of the hostname.
    ```yaml
    hostname: your-hostname.your-domain
    ```

    iii. (Optional) Uncomment and set the `tags` setting to specify tags to include on all metrics and logs.
    ```yaml
    tags:
      - environment:production
    #  - <TAG_KEY1>:<TAG_VALUE1>
    #  - <TAG_KEY2>:<TAG_VALUE2>
    ```

    iv. (Optional) Enable log message collection. Copy `/etc/datadog/logs.yaml.example` to `/etc/datadog/logs.yaml`. Read the `/etc/datdog/logs.yaml` comments and examples for configuration options to support log collection, including the multi-line log feature.
    ```sh
    cp /etc/datadog/logs.yaml.example /etc/datadog/logs.yaml
    vi /etc/datadog/logs.yaml
    chown datadog:sys /etc/datadog/logs.yaml
    ```

    v. (Optional) Enable process checks. Copy `/etc/datadog/process.yaml.example` to `/etc/datadog/process.yaml`. Read the `/etc/datdog/process.yaml` file for comments and examples of the configuration options to support process checks.
    ```sh
    cp /etc/datadog/process.yaml.example /etc/datadog/process.yaml
    vi /etc/datadog/process.yaml
    chown datadog:sys /etc/datadog/process.yaml
    ```

    The following metrics are supported for process checks.
    | Name | Description | Included Tags |
    | --- | --- | --- |
    | system.processes.mem.vms | Process virtual memory size (bytes) | `process_name`, `process_pid` |
    | system.processes.mem.rss | Process resident memory size (bytes) | `process_name`, `process_pid` |
    | system.processes.mem.pct | Process memory usage (percent) | `process_name`, `process_pid` |
    | system.processes.cpu.pct | Process cpu usage (percent) | `process_name`, `process_pid` |
    | system.processes.number | Running process count (matching search_string) | `process_name` |

    vi. (Optional) Configure the filesystem check. Copy `/etc/datadog/filesystem.yaml.example` to `/etc/datadog/filesystem.yaml`. Read the `/etc/datdog/filesystem.yaml` file for comments and examples of the configuration options to support the filesystem check.
    ```sh
    cp /etc/datadog/filesystem.yaml.example /etc/datadog/filesystem.yaml
    vi /etc/datadog/filesystem.yaml
    chown datadog:sys /etc/datadog/filesystem.yaml
    ```

    vii. (Optional) Configure the directories (files) check. Copy `/etc/datadog/directories.yaml.example` to `/etc/datadog/directories.yaml`. Read the `/etc/datdog/directories.yaml` comments and examples for configuration options to support the directories check.
    ```sh
    cp /etc/datadog/directories.yaml.example /etc/datadog/directories.yaml
    vi /etc/datadog/directories.yaml
    chown datadog:sys /etc/datadog/directories.yaml
    ```

    The following metrics are supported for the directories check:
    | Name | Description | Included Tags |
    | --- | --- | --- |
    | system.disk.directory.exists | Directory exists on the system (exists = 1) | name |
    | system.disk.directory.files | Count of files in the directory (recursive) | name |
    | system.disk.directory.bytes | Size of the directory (recursive) in bytes | name |
    | system.disk.directory.file.bytes | File size in bytes | name |
    | system.disk.directory.file.accessed_sec_ago | File last accessed in seconds | name |
    | system.disk.directory.file.modified_sec_ago | File last modified in seconds | name |
    | system.disk.directory.file.changed_sec_ago | File last changed in seconds | name |

    viii. (Optional) If your Datadog instance is located in the EU instead of the US, uncomment the following settings:
    ```yaml
    dd_url: https://api.datadoghq.eu
    dd_log_url: https://http-intake.logs.datadoghq.eu
    ```

    ix. (Optional) If your host system requires a proxy to communicate with Datadog's APIs, uncomment and update the following settings:
    ```yaml
    proxy_host: my-proxy.com
    proxy_port: 3128
    proxy_user: username
    proxy_pass: password
    ```

    x. (Optional) If the host is using an installation of cURL that is not in the default PATH, uncomment and update the following setting in `/etc/datadog/agent.yaml`. The version of cURL defined here should be current enough to support updated versions of TLS.
    ```yaml
    curl_bin: /usr/local/bin/curl
    ```

    xi. (Optional) If the host does not have gzip available in the datadog user PATH, uncomment and update the following setting in `/etc/datadog/agent.yaml`. Metric submissions to Datadog will be compressed to improve performance when a valid gzip executable is available.
    ```yaml
    gzip_bin: /usr/contrib/bin/gzip
    ```

    xii. (Optional) The HP-UX Agent includes a recent version of the [CA extract](https://curl.se/docs/caextract.html) PEM file located at `/opt/datadog-agent/ssl/cacert.pem`. Change this setting to your organization's `cacert.pem` bundle when using an SSL traffic inspection proxy for egress internet access. The `dd-agent` user should have directory and file access permissions on the `cacert.pem` file as well as the parent directory to read the CA Bundle.
    ```yaml
    cacert: /etc/ssl/cacert.pem
    ```

    xi. (Optional) If there are issues with the supplied CA Bundle or the custom CA Bundle from your organization, SSL validation can be disabled by setting the following value in the configuration file. However, this setting is not recommended as it disables SSL validation of the Datadog API hosts.
    ```yaml
    skip_ssl_validation: yes
    ```

5. Start the HP-UX Agent.
```sh
/sbin/init.d/datadog-agent start
```

6. Verify the HP-UX Agent is running.
```sh
pgrep datadog-agent
tail -n25 -f /var/log/datadog/agent.log
```

7. The HP-UX Agent is configured to run on system boot with `/init.d/rc3.d/S999datadog-agent`. If you need to disable the HP-UX Agent on system boot, change the `ENABLED` setting in the `/etc/rc.config.d/datadog-agent` file.
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

## Uninstallation

### Agent Uninstall

Command:
- You can uninstall the HP-UX Agent by using the `uninstall.sh` script provided in the tarball package. 

```sh
mkdir -p /tmp/datadog-agent-install
cd /tmp/datadog-agent-install
/usr/local/bin/curl -o DatadogAgent-1.5.3.tgz http://rapdev-files.s3.amazonaws.com/hpux/DatadogAgent-1.5.3.tgz
gunzip -c DatadogAgent-1.5.3.tgz | tar -xvf -
./uninstall.sh
```

Config & Log Cleanup:
- Configuration files and logs are not removed. You must manually remove them from `/var/log/datadog/` and `/etc/datadog/`.

For any questions or problems, view our Support section for ways to get in touch.

## Support

For support or feature requests, contact RapDev.io through the following channels: 

 - Email: support@rapdev.io 
 - Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
 - Phone: 855-857-0222 

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.
 
---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:support@rapdev.io) and we'll build it!!*
