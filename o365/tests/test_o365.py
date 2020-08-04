# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from typing import Any, Dict

from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.o365 import O365Check

# def test_check(aggregator, instance):
#     # type: (AggregatorStub, Dict[str, Any]) -> None
#     check = O365Check('o365', {}, [instance])
#     check.check(instance)

#     aggregator.assert_all_metrics_covered()


def test_nothing():
    assert 1
