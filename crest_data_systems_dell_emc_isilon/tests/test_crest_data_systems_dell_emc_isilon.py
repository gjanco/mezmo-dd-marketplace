from typing import Any, Dict

from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.crest_data_systems_dell_emc_isilon import CrestDataSystemsDellEmcIsilonCheck
from datadog_checks.dev.utils import get_metadata_metrics


def test_check(aggregator, instance):
    # type: (AggregatorStub, Dict[str, Any]) -> None
    check = CrestDataSystemsDellEmcIsilonCheck("crest_data_systems_dell_emc_isilon", {}, [instance])
    check.check(instance)

    aggregator.assert_all_metrics_covered()
    aggregator.assert_metrics_using_metadata(get_metadata_metrics())
