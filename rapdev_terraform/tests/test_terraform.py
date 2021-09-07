# (C) RapDev, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from typing import Any, Dict

try:
    from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
except ImportError:
    from checks import AgentCheck
import pytest
from datadog_checks.rapdev_terraform import TerraformCheck


def test_check_invalid_configs(dd_run_check, instance):
    # Test missing access_token
    check = TerraformCheck('rapdev_terraform', {}, [{}])

    with pytest.raises(Exception, match="datadog_checks.base.errors.ConfigurationError: Detected 1 error while " \
                                        + "loading configuration model `InstanceConfig`:" + "\n" \
                                        + "api_token" + "\n" \
                                        + "  field required"):
        dd_run_check(check)


def test_check_critical_service_checks(instance, aggregator, dd_run_check):
    check = TerraformCheck('rapdev_backup', {"app_key": "test321"}, [{
        "api_token": "test123"
    }])
    with pytest.raises(Exception, match="requests.exceptions.HTTPError: Cannot connect to the Terraform Cloud API. " \
                                        + "The check will not run correctly: 401 Client Error: Unauthorized for " \
                                        + "url: https://app.terraform.io/api/v2/account/details"):
        dd_run_check(check)

    aggregator.assert_service_check("rapdev.terraform.can_connect", status=check.CRITICAL)