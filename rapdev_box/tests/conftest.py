import pytest
import os


@pytest.fixture(scope='session')
def dd_environment():
    yield


@pytest.fixture
def instance():
    instance = {
        "box_url": "https://api.box.com/",
        "dd_url": "https://app.datadoghq.com",
        "dd_api_key": 'datadog_api_key',
        "enterprise_id": "enterprise_id",
        "client_id": "client_id",
        "client_secret": "client_secret",
        "tags": ["foo:bar"]
    }
    return instance

