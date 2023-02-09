# (C) Datadog, Inc. 2022-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import sys
from unittest.mock import MagicMock

import pytest

from datadog_checks.base import AgentCheck

sys.path.insert(0, "datadog_checks")
sys.modules["datadog_agent"] = MagicMock(name="datadog_agent")
from crest_data_systems_netapp_aiqum import CrestDataSystemsNetappAiqumCheck  # noqa: E402


@pytest.mark.e2e
def test_instance_check(dd_run_check, aggregator, instance):
    check = CrestDataSystemsNetappAiqumCheck("crest_data_systems_netapp_aiqum", {}, [instance])

    assert isinstance(check, AgentCheck)
