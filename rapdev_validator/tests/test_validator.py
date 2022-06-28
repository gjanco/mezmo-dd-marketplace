from typing import Any, Dict

from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.dev.utils import get_metadata_metrics
from datadog_checks.rapdev_validator import ValidatorCheck
import pytest
from mock import patch

def test_missing_config(instance, aggregator, dd_run_check):
    with pytest.raises(Exception, match="Please provide a list of required tag keys and values"):
        check = ValidatorCheck('rapdev_validator', {"app_key": "test321"}, [{
        "api_key": "test123"
        }])
        dd_run_check(check)
