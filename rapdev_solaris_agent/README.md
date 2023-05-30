# Solaris Agent
## Overview

The Solaris Agent allows you to collect and report on Solaris system metrics within Datadog. The integration supports both Solaris 10 and 11, as well as SPARC and i86pc architectures. The Solaris Agent uses the default Solaris Perl system distribution and does not require additional library dependencies, simplifying installation and compatability.

The Solaris Agent provides the host metadata required to support the Datadog Infrastructure List, enabling your organization to work with Solaris host systems similar to other supported Datadog host operating systems.

The Solaris Agent uses the same URLs and ports as the native agents. The Solaris Agent supports core infrastructure metrics, process checks, and log tails. It does not support integrations or service checks. 

### Pricing
Interested in using multiple RapDev integrations? Contact [sales@rapdev.io](mailto:sales@rapdev.io) for packaged pricing offers.

## Setup

1. Install a current version of cURL if your system does not have one available. The Solaris Agent was built and tested with cURL from the [OpenCSW](https://www.opencsw.org/about/) project.
```sh
pkgadd -d http://get.opencsw.org/now
/opt/csw/bin/pkgutil -U
/opt/csw/bin/pkgutil -y -i curl
```

2. Install the Solaris Agent using the Solaris Image Packaging System. 
```sh
pkgadd -d http://rapdev-files.s3.amazonaws.com/solaris/DatadogAgent-1.5.6.pkg
```

3. If you are upgrading an existing Solaris Agent installation, first remove the current Solaris Agent package. The Solaris Agent configuration and log files will be retained.
```sh
pkgrm DatadogAgent
pkgadd -d http://rapdev-files.s3.amazonaws.com/solaris/DatadogAgent-1.5.6.pkg
```

4. Copy `/etc/datadog/agent.yaml.example` to `/etc/datadog/agent.yaml` and update the Solaris Agent configuration settings in the `/etc/datadog/agent.yaml` file.

    ```sh
    cp /etc/datadog/agent.yaml.example /etc/datadog/agent.yaml
    vi /etc/datadog/agent.yaml
    chown datadog:sys /etc/datadog/agent.yaml
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

    v. (Optional) Enable process checks. Copy `/etc/datadog/process.yaml.example` to `/etc/datadog/process.yaml`. Read the `/etc/datdog/process.yaml` comments and examples for configuration options to support process checks.
    ```sh
    cp /etc/datadog/process.yaml.example /etc/datadog/process.yaml
    vi /etc/datadog/process.yaml
    chown datadog:sys /etc/datadog/process.yaml
    ```

    The following metrics are supported for process checks:
    | Name | Description | Included Tags |
    | --- | --- | --- |
    | system.processes.mem.vms | Process virtual memory size (bytes) | process_name, process_pid |
    | system.processes.mem.rss | Process resident memory size (bytes) | process_name, process_pid |
    | system.processes.mem.pct | Process memory usage (percent) | process_name, process_pid |
    | system.processes.cpu.pct | Process cpu usage (percent) | process_name, process_pid |
    | system.processes.threads | Process lightweight process count (threads) | process_name, process_pid |
    | system.processes.number | Running process count (matching search_string) | process_name |

    vi. (Optional) Configure the filesystem check. Copy `/etc/datadog/filesystem.yaml.example` to `/etc/datadog/filesystem.yaml`. Read the `/etc/datdog/filesystem.yaml` comments and examples for configuration options to support the filesystem check.
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

    viii. (Optional) If your Datadog instance is located in the EU instead of the US, uncomment the following settings in `/etc/datadog/agent.yaml`:
    ```yaml
    dd_url: https://api.datadoghq.eu
    dd_log_url: https://http-intake.logs.datadoghq.eu
    ```

    ix. (Optional) If your host system requires a proxy to communicate with Datadog's APIs, uncomment and update the following settings in `/etc/datadog/agent.yaml`:
    ```yaml
    proxy_host: my-proxy.com
    proxy_port: 3128
    proxy_user: username
    proxy_pass: password
    ```

    x. (Optional) If the host is using an installation of cURL that is not in the default PATH, uncomment and update the following setting in `/etc/datadog/agent.yaml`. The version of cURL defined here should be current enough to support updated versions of TLS.
    ```yaml
    curl_bin: /opt/csw/bin/curl
    ```

    xi. (Optional) If the host does not have gzip available in the datadog user PATH, uncomment and update the following setting in `/etc/datadog/agent.yaml`. Metric submissions to Datadog will be compressed to improve performance when a valid gzip executable is available.
    ```yaml
    gzip_bin: /opt/csw/bin/gzip
    ```

    xii. (Optional) The Solaris Agent includes a recent version of the [CA extract](https://curl.se/docs/caextract.html) PEM file located at `/opt/datadog-agent/ssl/cacert.pem`. Change this setting to your organization's `cacert.pem` bundle when using an SSL traffic inspection proxy for egress internet access. The `datadog` user should have directory and file read access permission on the `cacert.pem` file as well as the parent directory to read the CA Bundle.
    ```yaml
    cacert: /etc/ssl/cacert.pem
    ```

    xiii. (Optional) If there are issues with the supplied CA Bundle or the custom CA Bundle from your organization, SSL validation can be disabled by setting the following value in the main configuration file. However, this setting is not recommended because it disables SSL validation of the Datadog API hosts.
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
pgrep datadog-agent
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

## Uninstallation

### Agent Uninstall

Command:
- Remove the Agent using the Solaris Packaging system: `pkgrm DatadogAgent`

Config & Log Cleanup:
- Configuration files and logs are not removed. You must remove them manually from `/var/log/datadog/` and `/etc/datadog/`.

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
