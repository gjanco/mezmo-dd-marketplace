# CHANGELOG - RapDev HP-UX Agent

## 1.4.1 / 2022-09-06

* [Added] support for multi-line logs.
* [Added] support for recursive directory and file (stat) checks.
* [Fixed] filesystem check defaults to local filesystems.
* [Added] filesystem check 'include_remote_filesystems' configuration option.
* [Added] 'use_mount' configuration option to use mount points instead of devices metric tags.
* [Added] multiple configuration files to simplified automated installation and configuration.
* [Added] improved error handling and reporting for metric and log submissions to Datadog.
* [Added] support for setting the Agent log level in the configuration.
* [Added] improved configuration option validation and logging.

## 1.3.2 / 2022-02-16

* [Fixed] incorrect permissions on agent.yml and agent.log during agent reinstall.

## 1.3.1 / 2022-02-14

* [Fixed] incorrect agent startup event on metadata refresh.

## 1.3.0 / 2022-02-10

* [Added] support disk configuration options for mount point and device include and exclude.
* [Added] support disk configuration options for device_tag_re and mount_point_tag_re.
* [Added] support for process checks.
* [Added] support for log tail file globs.
* [Added] uninstall script.

## 1.2.0 / 2021-06-11

* [Added] Bumped version to align with Solaris Agent version.
* [Added] Support for Datadog's gohai host infrastructure metadata.

## 1.0.1 / 2021-05-26

* [Added] Initial release