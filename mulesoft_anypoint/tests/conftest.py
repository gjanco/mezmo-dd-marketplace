import os

import pytest

from datadog_checks.dev import docker_run, get_docker_hostname, get_here

from .docker.common import load_endpoints

from datadog_checks.mulesoft_anypoint.vendor.integration_core.ilogger import (  # isort:skip
    ILogger,  # isort:skip
)  # isort:skip

from .docker.conn_mock import (  # isort:skip
    INIT_CONFIG,  # isort:skip
    INSTANCE,  # isort:skip
    INSTANCE2,  # isort:skip
    INSTANCE3,  # isort:skip
    INSTANCE4,  # isort:skip
)  # isort:skip

from datadog_checks.mulesoft_anypoint.vendor.integration_core.core_parsing import (  # isort:skip
    RegexParser,  # isort:skip
)  # isort:skip
from datadog_checks.mulesoft_anypoint.vendor.integration_core.core_threading import (  # isort:skip
    MultithreadingPool,  # isort:skip
)  # isort:skip

from datadog_checks.mulesoft_anypoint.vendor.integration_core.ireporter import (  # isort:skip
    IReporter,  # isort:skip
    ReportItem,  # isort:skip
    ReportItemType,  # isort:skip
    CheckStatus,  # isort:skip
)  # isort:skip

from datadog_checks.mulesoft_anypoint.vendor.integration_core.readers.mulesoft_anypoint.reader_mulesoft_anypoint import (  # isort:skip # noqa
    ReaderMulesoftAnypoint,  # isort:skip
)  # isort:skip


@pytest.fixture(scope="session")
def dd_environment():
    compose_file = os.path.join(get_here(), "docker/docker-compose.yml")
    base_url = INIT_CONFIG["hosts"]["anypoint"].format(get_docker_hostname()) + "/"
    endpoints = load_endpoints(os.path.join(get_here(), "docker/apis"))
    with docker_run(
        compose_file,
        build=True,
        endpoints=[base_url + endpoint for endpoint in endpoints],
    ):
        yield INSTANCE


@pytest.fixture
def init_config():
    return INIT_CONFIG.copy()


@pytest.fixture
def instance():
    return INSTANCE.copy()


@pytest.fixture
def instance2():
    return INSTANCE2.copy()


@pytest.fixture
def instance3():
    return INSTANCE3.copy()


@pytest.fixture
def instance4():
    return INSTANCE4.copy()


@pytest.fixture
def configured_init_config():
    init_config_copy = INIT_CONFIG.copy()
    init_config_copy["hosts"]["anypoint"] = init_config_copy["hosts"][
        "anypoint"
    ].format(get_docker_hostname())
    init_config_copy["hosts"]["object_store_v2"] = init_config_copy["hosts"][
        "object_store_v2"
    ].format(get_docker_hostname())
    init_config_copy["hosts"]["object_store_v2_stats"] = init_config_copy["hosts"][
        "object_store_v2_stats"
    ].format(get_docker_hostname())
    init_config_copy["hosts"]["mule_server"] = init_config_copy["hosts"][
        "mule_server"
    ].format(get_docker_hostname())
    init_config_copy["hosts"]["oauth_provider"] = init_config_copy["hosts"][
        "oauth_provider"
    ].format(get_docker_hostname())
    return init_config_copy


@pytest.fixture
def configured_init_config_no_license(configured_init_config):
    init_config_copy = configured_init_config.copy()
    init_config_copy["api_key"] = "000"
    return init_config_copy


@pytest.fixture(scope="function")
def reader_mulesoft_anypoint(fake_logger, configured_init_config, instance):
    instance.update(configured_init_config)
    return ReaderMulesoftAnypoint(logger=fake_logger, config=instance)


class FakeLogger(ILogger):
    def info(self, message):
        pass

    def warning(self, message):
        pass

    def debug(self, message):
        pass

    def error(self, message):
        pass


class FakeReporter(IReporter):
    def report_metric(self, report_item):
        pass


@pytest.fixture(scope="function")
def fake_logger():
    return FakeLogger()


@pytest.fixture(scope="function")
def fake_reporter():
    return FakeReporter()


@pytest.fixture(scope="module")
def check_ok():
    return ReportItem(
        name="test.ioconnect.mulesoft.anypoint.can_connect",
        report_type=ReportItemType.SERVICE_CHECK,
        value=CheckStatus.OK,
        message="",
    )


@pytest.fixture(scope="module")
def check_critical():
    return ReportItem(
        name="test.ioconnect.mulesoft.anypoint.can_connect",
        report_type=ReportItemType.SERVICE_CHECK,
        value=CheckStatus.CRITICAL,
        message="",
    )


@pytest.fixture(scope="module")
def license_ok():
    return ReportItem(
        name="test.ioconnect.mulesoft.anypoint.license_valid",
        report_type=ReportItemType.SERVICE_CHECK,
        value=CheckStatus.OK,
        message="",
    )


@pytest.fixture(scope="module")
def license_critical():
    return ReportItem(
        name="test.ioconnect.mulesoft.anypoint.license_valid",
        report_type=ReportItemType.SERVICE_CHECK,
        value=CheckStatus.CRITICAL,
        message="",
    )


@pytest.fixture(scope="session")
def url_with_rep_params():
    return "https://some-url/with{a}/{a}/{b}repeated{c}/parameters{d}"


@pytest.fixture(scope="session")
def url_with_unq_params():
    return "https://some-url/with{a}/{b}unique{c}/parameters{d}"


@pytest.fixture(scope="session")
def abcd_cb_keys():
    return ["{a}", "{b}", "{c}", "{d}"]


@pytest.fixture(scope="session")
def json_root_object():
    return {
        "a": "b",
        "c": {"d": "e", "f": "g"},
        "h": ["i", "j"],
        "k": [{"kk": "l"}, {"kk": "m"}],
        "n": [{"kn": "o"}, {"kn": "o"}],
    }


@pytest.fixture(scope="session")
def json_root_list(json_root_object):
    return [
        json_root_object,
        json_root_object,
        json_root_object,
        json_root_object,
        {"a": "p"},
    ]


@pytest.fixture(scope="module")
def fake_expr():
    return "fake_expr"


@pytest.fixture(scope="module")
def regex_parser():
    return RegexParser()


# THREADING FIXTURES
@pytest.fixture(scope="function")
def multithreading_pool_4():
    return MultithreadingPool(4)


@pytest.fixture(scope="session")
def auth_resp():
    return {
        "access_token": "00000000-0000-0000-0000-000000000000",
        "token_type": "bearer",
    }


@pytest.fixture(scope="session")
def ok_resp():
    return {"data": "ok_default"}


@pytest.fixture(scope="module")
def test_url():
    return "http://localhost:8000/test_url"


# INTEGRATION CORE FIXTURES
@pytest.fixture(scope="session")
def base_prefix():
    return "base.prefix"


@pytest.fixture(scope="session")
def dev_env():
    return "DEV"


@pytest.fixture(scope="session")
def prod_env():
    return "PROD"


@pytest.fixture(scope="session")
def test_path():
    return "path"


@pytest.fixture(scope="session")
def integration_core():
    return "integration_core"


@pytest.fixture(scope="session")
def test_utils():
    return "test_utils"


@pytest.fixture(scope="module")
def endpoint():
    return {
        "url": "/test/endpoint",
        "host_key": "object_store_v2",
        "headers": {"env_id": "env_id", "org_id": "org_id"},
        "ep_name": "endpoint1",
        "query_params": {
            "qp1": "%prev",
            "qp2": "&literal",
            "qp3": "env_id",
            "qp4": "{pk1}",
            "qp5": "{pk2}",
        },
        "paging": {
            "type": "offset",
            "list_root": "$.data",
            "limit": 25,
            "param_limit": "limit",
            "param": "offset",
        },
    }


@pytest.fixture(scope="module")
def endpoint2():
    return {
        "url": "/test/endpoint/{param1}/{param2}",
        "uri_params": {"param1": "{pk1}", "param2": "env_id"},
        "paging": {
            "type": "page_token",
            "list_root": "$.values",
            "param": "nextPageToken",
            "next_page": "$.nextPageToken",
        },
        "excluded_base_tags": ["env_id"],
    }


@pytest.fixture(scope="module")
def endpoint3():
    return {
        "url": "/test/endpoint3",
        "headers": {"env_id": "env_id", "org_id": "org_id"},
    }


@pytest.fixture(scope="module")
def parent_data():
    return {"pk1": "pv1", "pk2": "pv2"}


@pytest.fixture(scope="module")
def json_data():
    return {"data": [{"dk1": "dv11", "dk2": "dv12"}, {"dk1": "dv21", "dk2": "dv22"}]}


@pytest.fixture(scope="module")
def selector():
    return {
        "tags_expr_str": {"tk1": "{pk1}", "tk2": "$.data.[*].dk1", "tk3": "literal"}
    }


@pytest.fixture(scope="module")
def test_list():
    return [1, 2, 3, 4]


@pytest.fixture(scope="module")
def tags_expr_values():
    return {"tk1": "pv1", "tk2": ["dv11", "dv21"], "tk3": "literal"}
