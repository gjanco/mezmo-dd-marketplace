# (C) RapDev, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from typing import Any, Dict

try:
    from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
except ImportError:
    from checks import AgentCheck
import pytest
from datadog_checks.rapdev_backup import BackupCheck
from mock import patch


def test_check_invalid_configs(dd_run_check, instance):
    # Test missing access_token
    check = BackupCheck('rapdev_backup', {}, [{
        "dd_api_key": "my_key",
        "dd_app_key": "my_appkey"
    }])

    with pytest.raises(Exception):
        dd_run_check(check)

    check = BackupCheck('rapdev_backup', {}, [{
        "dd_api_key": "my_key",
        "dd_app_key": "my_appkey",
        "backup_path": "/etc/datadog-agent/"
    }])
    with pytest.raises(Exception,
                       match="datadog_checks.base.errors.ConfigurationError: " \
                             + "Detected 1 error while loading configuration model `InstanceConfig`:" + "\n" \
                             + "backup_storage_platform" + "\n" \
                             + "  field required"
                       ):
        dd_run_check(check)

    check = BackupCheck('rapdev_backup', {}, [{
        "dd_api_key": "my_key",
        "dd_app_key": "my_appkey",
        "backup_storage_platform": "AWS"
    }])
    with pytest.raises(Exception,
                       match="datadog_checks.base.errors.ConfigurationError: " \
                             + "Detected 1 error while loading configuration model `InstanceConfig`:" + "\n" \
                             + "backup_path" + "\n" \
                             + "  field required"
                       ):
        dd_run_check(check)

    with pytest.raises(Exception,
                       match="No key dd_app_key found"
                       ):
        check = BackupCheck('rapdev_backup', {}, [{
            "dd_api_key": "mykey",
            "backup_path": "/etc/datadog-agent/",
            "backup_storage_platform": "AWS"
        }])

    with pytest.raises(Exception,
                       match="No key dd_api_key found"
                       ):
        check = BackupCheck('rapdev_backup', {}, [{
            "dd_app_key": "mykey",
            "backup_path": "/etc/datadog-agent/",
            "backup_storage_platform": "AWS"
        }])

    check = BackupCheck('rapdev_backup', {"dd_app_key": "test123"}, [{
        "dd_api_key": "mykey",
        "backup_path": "/etc/datadog-agent/",
        "backup_storage_platform": "test"
    }])
    with pytest.raises(Exception,
                       match="datadog_checks.base.errors.ConfigurationError: " \
                             + "Provided storage platform is not supported: test"
                       ):
        dd_run_check(check)

    # AWS
    check = BackupCheck('rapdev_backup', {}, [{
        "dd_api_key": "my_key",
        "dd_app_key": "my_appkey",
        "backup_path": "/etc/datadog-agent/",
        "backup_storage_platform": "AWS"
    }])
    with pytest.raises(Exception,
                       match="datadog_checks.base.errors.ConfigurationError: " \
                             + "aws_access_key, aws_secret_key, and aws_s3_bucket_url " \
                             + "are all required for storing backups in AWS."
                       ):
        dd_run_check(check)

    check = BackupCheck('rapdev_backup', {}, [{
        "dd_api_key": "my_key",
        "dd_app_key": "my_appkey",
        "backup_path": "/etc/datadog-agent/",
        "backup_storage_platform": "AWS",
        "AWS_ACCESS_KEY": "test"
    }])
    with pytest.raises(Exception,
                       match="datadog_checks.base.errors.ConfigurationError: " \
                             + "aws_access_key, aws_secret_key, and aws_s3_bucket_url " \
                             + "are all required for storing backups in AWS."
                       ):
        dd_run_check(check)

        check = BackupCheck('rapdev_backup', {}, [{
            "dd_api_key": "my_key",
            "dd_app_key": "my_appkey",
            "backup_path": "/etc/datadog-agent/",
            "backup_storage_platform": "AWS",
            "AWS_ACCESS_KEY": "test",
            "AWS_SECRET_KEY": "test123"
        }])
        dd_run_check(check)

        check = BackupCheck('rapdev_backup', {}, [{
            "dd_api_key": "my_key",
            "dd_app_key": "my_appkey",
            "backup_path": "/etc/datadog-agent/",
            "backup_storage_platform": "AWS",
            "AWS_ACCESS_KEY": "test",
            "AWS_S3_BUCKET_URL": "mytest123/"
        }])
        dd_run_check(check)

    # Azure
    check = BackupCheck('rapdev_backup', {}, [{
        "dd_api_key": "my_key",
        "dd_app_key": "my_appkey",
        "backup_path": "/etc/datadog-agent/",
        "backup_storage_platform": "AZURE"
    }])
    with pytest.raises(Exception,
                       match="datadog_checks.base.errors.ConfigurationError: " \
                             + "azure_connection_string and azure_container_name are required for Azure authentication."
                       ):
        dd_run_check(check)

        check = BackupCheck('rapdev_backup', {}, [{
            "dd_api_key": "my_key",
            "dd_app_key": "my_appkey",
            "backup_path": "/etc/datadog-agent/",
            "backup_storage_platform": "AZURE",
            "AZURE_CONNECTION_STRING": "myteststring/test129039012390f"
        }])
        dd_run_check(check)

        check = BackupCheck('rapdev_backup', {}, [{
            "dd_api_key": "my_key",
            "dd_app_key": "my_appkey",
            "backup_path": "/etc/datadog-agent/",
            "backup_storage_platform": "AZURE",
            "AZURE_CONTAINER_NAME": "test129039012390f"
        }])
        dd_run_check(check)


def test_check_critical_service_checks(instance, aggregator, dd_run_check):
    check = BackupCheck('rapdev_backup', {"dd_app_key": "test321"}, [{
        "dd_api_key": "test123",
        "timestamp_format": "%Y-%m-%dT%H%M%S",
        "backup_path": "/etc/datadog-agent/",
        "backup_storage_platform": "LOCAL"
    }])
    with pytest.raises(Exception, match="Cannot authenticate to Datadog API. The check will not run"):
        dd_run_check(check)

    aggregator.assert_service_check("rapdev.backup.can_connect", status=check.CRITICAL)
