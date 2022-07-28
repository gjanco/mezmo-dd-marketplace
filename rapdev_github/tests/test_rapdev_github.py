# from typing import Any, Callable, Dict
import requests.exceptions
from datadog_checks.base.errors import ConfigurationError

from datadog_checks.rapdev_github import GitHubCheck

import pytest
import mock


def test_init(instance):
    check = GitHubCheck('rapdev_github', {}, [instance])
    assert check.instance.get('base_url') == 'https://api.github.com/'
    assert check.instance.get('org') == 'rapdev-io'
    assert check.instance.get('github_mode') == 'organization'
    assert check.instance.get('key_path') == \
           '/Users/henrihatch/Desktop/rapdev-github-datadog.2022-06-01.private-key.pem'
    assert check.instance.get('org_app_id') == 12345678
    assert check.instance.get('gh_app_id') == 123456

@pytest.mark.integration
def test_call_api_get_no_key(instance):
    with pytest.raises(Exception, match="Cannot connect to API, please ensure the config is correct."):
        check = GitHubCheck('rapdev_github', {}, [instance])
        with mock.patch('requests.get', autospec=True):
            check.call_api("repos")

@pytest.mark.integration
def test_call_api_get_failure(aggregator, instance):
    check = GitHubCheck('rapdev_github', {}, [instance])
    with mock.patch('requests.get', side_effect=requests.exceptions.HTTPError('An HTTP Error'), autospec=True):
        with pytest.raises(Exception) as failure:
            check.call_api("repos")
            assert failure.value.args[0] == 'There was an issue'

        aggregator.assert_service_check('rapdev.github.can_connect', GitHubCheck.CRITICAL)