# (C) RapDev, Inc. 2020-present
# All rights reserved
from typing import Any, Dict

from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.rapdev_maxdb import MaxDBCheck

# def test_check(aggregator, instance):
#     # type: (AggregatorStub, Dict[str, Any]) -> None
#     check = MaxDBCheck('maxdb', {}, [instance])
#     check.check(instance)

#     aggregator.assert_all_metrics_covered()


def test_nothing():
    assert 1
