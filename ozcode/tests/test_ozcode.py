# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

from typing import Any, Dict

from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.dev.utils import get_metadata_metrics
from datadog_checks.dev import get_here
from datadog_checks.base import ensure_bytes
from datadog_checks.ozcode import OzcodeCheck

import pytest
import mock
import json
import os

customtag = "custom:tag"

instance = {
  'tags': [customtag],
  'ssl_verify': False,
}
  
METRICS = [
  "datadog.marketplace.ozcode.agent"
]

HERE = get_here()

class MockFailedResponse(Exception):
    pass

class MockResponse:
    def __init__(self, text):
        j = json.loads(text)
        self.text = json.dumps(j["body"])
        self._json = j["body"]
        self.status_code = j["status_code"]

    @property
    def content(self):
        return ensure_bytes(self.text)

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code == 500:
            raise MockFailedResponse("request failed")

def mock_get_factory(fixture_group):
    def mock_get(url, *args, **kwargs):
        split_url = url.split('/')
        path = split_url[-1]
        f_name = os.path.join(HERE, 'fixtures', fixture_group, "{}.json".format(path))
        with open(f_name, 'r') as f:
            text_data = f.read()
            return MockResponse(text_data)

    return mock_get

@pytest.mark.integration
@pytest.mark.usefixtures('dd_environment')
def test_check(aggregator):
    # type: (AggregatorStub, Dict[str, Any]) -> None
    check = OzcodeCheck('ozcode', {}, [instance])
    
    with mock.patch('requests.get', side_effect=mock_get_factory('ok'), autospec=True):
        check.check(instance)    
        # the check should send Ok
        aggregator.assert_service_check('ozcode.agent.can_connect', OzcodeCheck.OK)

    with mock.patch('requests.get', side_effect=mock_get_factory('fail'), autospec=True):
        check.check(instance)    
        # the check should send Critical
        aggregator.assert_service_check('ozcode.agent.can_connect', OzcodeCheck.CRITICAL)

    for metric in METRICS:
        aggregator.assert_metric(metric)
        aggregator.assert_metric_has_tag(metric, customtag)
