# CHANGELOG - RapDev Solaris Agent

## 1.3.0 / 2021-12-09

* [Added] support disk configuration options for mount point and device include and exclude.
* [Added] support disk configuration options for device_tag_re and mount_point_tag_re.
* [Added] support for process checks.
* [Added] support log tail file globs.
* [Fixed] preinstall script user and group creation modified to avoid detection and use of LDAP based user.

## 1.2.0 / 2021-06-11

* [Added] support for new "Host Info" metadata in Datadog Infrastructure List.

## 1.1.1 / 2021-06-03

* [Fixed] reduced agent.log max file size from 100m to 10m in logadm.
* [Fixed] changed default "host_metadata_interval" to 1200 seconds.
* [Fixed] incorrect handling of "skip_ssl_validation" configuration setting.
* [Fixed] changed default dd_url to https://api.datadoghq.com.
* [Fixed] changed default user to 'dd-agent' to match Datadog agent.
* [Added] support for Certificate Authority bundle (cacert.pem).
* [Added] support for runtime parameters to configure log severity and user.

## 1.1.0 / 2021-03-16

* [Fixed] resolved issue of host-tags no populating in Datadog App.
* [Added] enabled support for log file tails.

## 1.0.0 / 2020-09-17

* [Added] Initial release.


