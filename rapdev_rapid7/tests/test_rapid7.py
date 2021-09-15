import pytest

from typing import Any, Dict
from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.dev.utils import get_metadata_metrics
from datadog_checks.rapdev_rapid7 import Rapid7Check


def test_check(aggregator):
    instance = {}
    check = Rapid7Check('rapdev_rapid7', {}, [instance])
    with pytest.raises(Exception,  match="Non-200 response code returned from"):
        check.check(instance)
    aggregator.assert_all_metrics_covered()
    aggregator.assert_metrics_using_metadata(get_metadata_metrics())
