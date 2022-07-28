
import pytest


@pytest.fixture(scope='session')
def dd_environment():
    yield


@pytest.fixture
def instance():
    instance = {
        "base_url": "https://api.github.com/",
        "org": 'rapdev-io',
        "github_mode": "organization",
        "key_path": "/Users/henrihatch/Desktop/rapdev-github-datadog.2022-06-01.private-key.pem",
        "org_app_id": 12345678,
        "gh_app_id": 123456
    }
    return instance
