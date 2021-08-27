from typing import Any, Dict

from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.dev.utils import get_metadata_metrics
from datadog_checks.rapdev_validator import ValidatorCheck
import pytest
from mock import patch

def get_config(self, key):
    return "fake_api_key"

@patch.object(ValidatorCheck, "get_config", get_config)
def test_unauthorized_config(instance, aggregator, dd_run_check):
    with pytest.raises(Exception, match="403 Client Error: Forbidden for url: https://api.datadoghq.com/api/v1/org"):
        check = ValidatorCheck('rapdev_validator', {"app_key": "test321"}, [{
        "api_key": "test123"
        }])
        dd_run_check(check)
