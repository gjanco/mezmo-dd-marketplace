

from typing import Any, Callable, Dict

from datadog_checks.base import AgentCheck
from datadog_checks.base.errors import CheckException, ConfigurationError

from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.dev.utils import get_metadata_metrics

from datadog_checks.rapdev_box import BoxCheck
from requests.exceptions import HTTPError


import os
import unittest
import pytest
import mock
import json
import requests

from unittest.mock import patch


def test_init(instance):
    check = BoxCheck('rapdev_box', {}, [instance])
    assert check.instance.get('box_url') == 'https://api.box.com/'
    assert check.instance.get('dd_url') == 'https://app.datadoghq.com'
    assert check.instance.get('dd_api_key') == 'datadog_api_key'
    assert check.instance.get('enterprise_id') == 'enterprise_id'
    assert check.instance.get('client_id') == 'client_id'
    assert check.instance.get('client_secret') == 'client_secret'


def test_validate_config_id(instance):
    # tests that missing client id raises Error
    with pytest.raises(ConfigurationError, match="CLIENT ID WAS NOT SUPPLIED"):
        check = BoxCheck('rapdev_box', {}, [{}])
        check.validate_config()


def test_validate_config_secret(instance):
    # tests that missing client secret raises Error
    with pytest.raises(ConfigurationError, match="CLIENT SECRET WAS NOT SUPPLIED"):
        check = BoxCheck('rapdev_box', {}, [{"client_id": "foobar"}])
        check.validate_config()


def test_validate_config_enterprise(instance):
    # tests that missing enterprise id raises Error
    with pytest.raises(ConfigurationError, match="ENTERPRISE ID WAS NOT SUPPLIED"):
        check = BoxCheck('rapdev_box', {}, [
                         {"client_id": "foobar", "client_secret": "foobar"}])
        check.validate_config()


def test_validate_config_ddapi(instance):
    # tests that missing dd api key raises Error
    with pytest.raises(ConfigurationError, match="DATADOG API KEY WAS NOT SUPPLIED"):
        check = BoxCheck('rapdev_box', {}, [
                         {"client_id": "foobar", "client_secret": "foobar", "enterprise_id": "foobar"}])
        check.validate_config()


@pytest.mark.integration
def test_call_api_get_okay(aggregator, instance):
    check = BoxCheck('rapdev_box', {}, [instance])
    with mock.patch('requests.get', autospec=True) as get:
        data = {"foo": "bar"}
        check.call_api('GET', "https://success", data)

        # the check should send Ok
        aggregator.assert_service_check('rapdev.box.can_connect', BoxCheck.OK)


@pytest.mark.integration
def test_call_api_get_fail(aggregator, instance):
    check = BoxCheck('rapdev_box', {}, [instance])
    with mock.patch('requests.get', side_effect=requests.exceptions.HTTPError('Some HTTP Error'), autospec=True) as get:
        data = {}
        with pytest.raises(CheckException) as oops:
            check.call_api('GET', "https://failure", data)
            assert oops.value.args[0] == 'Agent Check error Some HTTP Error'

        # the check should send CRITICAL
        aggregator.assert_service_check(
            'rapdev.box.can_connect', BoxCheck.CRITICAL)


@pytest.mark.integration
def test_call_api_post_okay(aggregator, instance):
    check = BoxCheck('rapdev_box', {}, [instance])
    with mock.patch('requests.get', autospec=True) as post:
        data = {"foo": "bar"}
        check.call_api('GET', "https://success", data)

        # the check should send Ok
        aggregator.assert_service_check('rapdev.box.can_connect', BoxCheck.OK)


def test_call_api_post_fail(aggregator, instance):
    check = BoxCheck('rapdev_box', {}, [instance])
    with mock.patch('requests.post', side_effect=requests.exceptions.HTTPError('Some HTTP Error'), autospec=True) as post:
        data = {}
        with pytest.raises(CheckException) as oops:
            check.call_api('POST', "https://failure", data)
            assert oops.value.args[0] == 'Agent Check error Some HTTP Error'

        # the check should send CRITICAL
        aggregator.assert_service_check(
            'rapdev.box.can_connect', BoxCheck.CRITICAL)


def test_call_api_base(aggregator, instance):
    check = BoxCheck('rapdev_box', {}, [instance])
    data = {}
    with pytest.raises(BaseException) as oops:
        check.call_api('not a valid type', "https://failure", data)
        assert oops.value.args[0] == 'UNSUPPORTED REQUEST METHOD'
        # the check should send CRITICAL
        aggregator.assert_service_check(
            'rapdev.box.can_connect', BoxCheck.CRITICAL)


def test_bearer_token_ok(aggregator, instance):
    with mock.patch('requests.post',  autospec=True) as post:
        check = BoxCheck('rapdev_box', {}, [instance])
        check.bearer_token()
        aggregator.assert_service_check('rapdev.box.got_bearer', AgentCheck.OK)
