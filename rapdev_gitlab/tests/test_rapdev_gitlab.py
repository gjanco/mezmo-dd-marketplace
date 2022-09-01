

from typing import Any, Callable, Dict

from datadog_checks.base import AgentCheck
from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.rapdev_gitlab import RapdevGitlabCheck

import pytest
import mock
import requests

def test_init(instance):
    check = RapdevGitlabCheck('rapdev_gitlab', {}, [instance])
    assert check.instance.get('base_url') == 'http://not.a.real.url.com/'
    assert check.instance.get('user') == 'fake_user'
    assert check.instance.get('password') == 'fake_secure_password'

@pytest.mark.integration
def test_call_api_get_failure(aggregator, instance):
    check = RapdevGitlabCheck('rapdev_gitlab', {}, [instance])
    with mock.patch('requests.get', side_effect=requests.exceptions.HTTPError('An HTTP Error'), autospec=True):
        with pytest.raises(Exception) as failure:
            check.call_api("fail")
            assert failure.value.args[0] == 'There was an issue'

        aggregator.assert_service_check('rapdev.gitlab.can_connect', RapdevGitlabCheck.CRITICAL)
