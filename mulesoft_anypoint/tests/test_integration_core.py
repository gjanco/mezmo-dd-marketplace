import os

import pytest

# fmt: off
from datadog_checks.mulesoft_anypoint.vendor.integration_core.integration_core import (  # isort:skip
    get_abs_path, get_metrics_prefix, load_config  # isort:skip
)  # isort:skip
# fmt: on


@pytest.mark.unit
def test_get_metrics_prefix(base_prefix, dev_env, prod_env):
    prefix = get_metrics_prefix(base_prefix, dev_env)
    assert prefix == ".".join([dev_env.lower(), base_prefix])
    prefix = get_metrics_prefix(base_prefix, prod_env)
    assert prefix == base_prefix
    prefix = get_metrics_prefix(base_prefix, None)
    assert prefix == base_prefix


@pytest.mark.unit
def test_get_abs_path(integration_core, test_path):
    root_path = os.path.dirname(os.path.abspath(test_path))
    abs_path = get_abs_path(test_path)
    expected_path = os.path.join(
        root_path,
        "datadog_checks",
        "mulesoft_anypoint",
        "vendor",
        integration_core,
        test_path,
    )
    assert abs_path.lower() == expected_path.lower()


@pytest.mark.unit
def test_load_config(test_path, test_utils):
    root_path = os.path.dirname(os.path.abspath(test_path))
    test_utils = os.path.join(root_path, "tests", test_utils)
    configs = load_config(test_utils, None)
    assert len(configs) == 2
    assert "test1" in configs[0]
    assert "etest1" in configs[1]
    configs = load_config(test_utils, "test_config")
    assert len(configs) == 1
    assert "test1" in configs[0]
