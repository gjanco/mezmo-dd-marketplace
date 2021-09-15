# (C) RapDev, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from typing import Any, Dict

from datadog_checks.base.stubs.aggregator import AggregatorStub
from datadog_checks.dev.utils import get_metadata_metrics
from datadog_checks.rapdev_sophos import SophosCheck
import pytest
from mock import patch

def get_config(self, key):
    return "fake_api_key"

@patch.object(SophosCheck, "get_config", get_config)
def test_non_200_from_api(aggregator, instance):
   # type: (AggregatorStub, Dict[str, Any]) -> None
   check = SophosCheck('rapdev_sophos', {}, [{
       "base_api_url": "https://api.central.sophos.com"
   }])

   with pytest.raises(Exception, match="Non-200 response code returned from Sophos API"):
    check.check(instance)
