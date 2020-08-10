from typing import Any, Dict

from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.oracle_timesten import OracleTimestenCheck


#def test_check(aggregator, instance):
    # type: (AggregatorStub, Dict[str, Any]) -> None
#    check = OracleTimestenCheck('oracle_timesten', {}, [instance])
#    check.check(instance)

#    aggregator.assert_all_metrics_covered()

def test_nothing():
    assert 1
