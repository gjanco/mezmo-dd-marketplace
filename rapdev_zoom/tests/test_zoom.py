# (C) RapDev, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from typing import Any, Dict

from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.dev.utils import get_metadata_metrics
from datadog_checks.rapdev_zoom import ZoomCheck

#def test_check(aggregator, instance):
#    # type: (AggregatorStub, Dict[str, Any]) -> None
#    check = ZoomCheck('rapdev_zoom', {}, [instance])
#    check.check(instance)

#    aggregator.assert_all_metrics_covered()
#    aggregator.assert_metrics_using_metadata(get_metadata_metrics())

def test_nothing():
    assert 1
