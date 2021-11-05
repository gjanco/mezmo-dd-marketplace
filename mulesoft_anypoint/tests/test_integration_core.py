import os

import pytest

# fmt: off
from datadog_checks.mulesoft_anypoint.vendor.integration_core.readers.mulesoft_anypoint.reader_mulesoft_anypoint import (  # isort:skip # noqa
    ReaderMulesoftAnypoint, ExecutionResult)  # isort:skip
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
    assert ("test1" in configs[1] and "etest1" in configs[0]) or ("test1" in configs[0] and "etest1" in configs[1])
    configs = load_config(test_utils, "test_config")
    assert len(configs) == 1
    assert "test1" in configs[0]


def add_to_queue_callback(metric):
    pass


@pytest.mark.unit
@pytest.mark.usefixtures("dd_environment")
def test_reader_mulesoft_anypoint_ok(fake_logger, configured_init_config):
    reader = ReaderMulesoftAnypoint(logger=fake_logger, config=configured_init_config)
    reader.set_add_to_queue_callback(add_to_queue_callback)
    result = reader._execute_jar()
    assert ExecutionResult.OK == ExecutionResult(result)


@pytest.mark.unit
@pytest.mark.usefixtures("dd_environment")
def test_reader_mulesoft_anypoint_unexpected_error(fake_logger, configured_init_config):
    os.environ["mininterval"] = "-1"
    no_hosts_config = configured_init_config.copy()
    del no_hosts_config["hosts"]
    reader = ReaderMulesoftAnypoint(logger=fake_logger, config=no_hosts_config)
    reader.set_add_to_queue_callback(add_to_queue_callback)
    result = reader._execute_jar()
    assert ExecutionResult.UNEXPECTED_ERROR == ExecutionResult(result)
    del os.environ["mininterval"]


@pytest.mark.unit
@pytest.mark.usefixtures("dd_environment")
def test_reader_mulesoft_anypoint_customer_provisioned(fake_logger, configured_init_config):
    os.environ["mininterval"] = "-1"
    no_customer_key_config = configured_init_config.copy()
    del no_customer_key_config["customer_key"]
    reader = ReaderMulesoftAnypoint(logger=fake_logger, config=no_customer_key_config)
    reader.set_add_to_queue_callback(add_to_queue_callback)
    result = reader._execute_jar()
    assert ExecutionResult.CUSTOMER_PROVISIONED == ExecutionResult(result)
    del os.environ["mininterval"]
