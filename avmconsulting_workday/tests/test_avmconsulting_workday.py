import os

import mock
import pytest

from datadog_checks.avmconsulting_workday import WorkdayCheck
from datadog_checks.base import ensure_bytes
from datadog_checks.dev import get_here
from datadog_checks.dev.utils import get_metadata_metrics

HERE = get_here()


class MockFailedResponse(Exception):
    pass


class MockResponse:
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code

    @property
    def content(self):
        return ensure_bytes(self.text)

    def raise_for_status(self):
        if self.status_code == 500:
            raise MockFailedResponse("request failed")


def mock_get_factory(param, status):
    def mock_get(*args, **kwargs):
        f_name = os.path.join(HERE, 'events', "{}".format(param))
        with open(f_name, 'r') as f:
            text_data = f.read()
            return MockResponse(text_data, status)

    return mock_get


@pytest.mark.unit
def test_check(aggregator, instance):
    check = WorkdayCheck('avmconsulting_workday', {}, [instance])
    check.check(instance)
    aggregator.assert_service_check('avmconsulting.workday.can_connect', WorkdayCheck.CRITICAL)
    with mock.patch('requests.post', side_effect=mock_get_factory("response", 200), autospec=True):
        check.check(instance)
        aggregator.assert_service_check('avmconsulting.workday.can_connect', WorkdayCheck.OK)
    aggregator.assert_all_metrics_covered()
    aggregator.assert_metrics_using_metadata(get_metadata_metrics())
