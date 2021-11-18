import pytest


@pytest.fixture(scope="session")
def dd_environment():
    yield


INIT_CONFIG = {
    "username": "api",
    "password": "scadadogapi1Pass",
    "host": "http://127.0.0.1",
    "port": 57412,
    "config_api_url": "/config/v1/project/",
    "eventlog_api_url": "/config/v1/event_log",
    "logging_endpoint": "https://http-intake.logs.datadoghq.com/v1/input/",
    "kepserver_tag_filters": ["/channels/*", "/channels/Channel1/*"],
    "opcua_host": "opc.tcp://127.0.0.1:49320",
}


@pytest.fixture
def instance():
    return INIT_CONFIG.copy()
