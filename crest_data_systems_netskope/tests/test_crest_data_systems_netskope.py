# Copyright (C) 2023 Crest Data Systems.
# All rights reserved

import sys

import pytest

from datadog_checks.base.errors import ConfigurationError

sys.path.insert(0, "datadog_checks")


class datadog_agent:
    config = {"api_key": "test-api-key", "app_key": "test-app-key"}

    @classmethod
    def get_config(cls, key):
        return cls.config.get(key)

    @staticmethod
    def get_hostname():
        return "example.com"

    @staticmethod
    def log(*args):
        return object

    @staticmethod
    def tracemalloc_enabled():
        return False


sys.modules["datadog_agent"] = datadog_agent
from crest_data_systems_netskope import CrestDataSystemsNetskopeCheck  # noqa: E402


@pytest.mark.e2e
def test_instance_check(dd_run_check, aggregator, instance):
    with pytest.raises(ConfigurationError):
        CrestDataSystemsNetskopeCheck("crest_data_systems_netskope", {}, [instance])
