
import pytest


@pytest.fixture(scope='session')
def dd_environment():
    yield


@pytest.fixture
def instance():
    instance = {
        "base_url": "https://api.github.com/",
        "user": "henri-hatch",
        "org": 'rapdev-io',
        "github_mode": "organization",
        "key_path": "/Users/henrihatch/Desktop/rapdev-github-datadog.2022-06-01.private-key.pem",
        "app_id": "26154513"
    }
    return instance
