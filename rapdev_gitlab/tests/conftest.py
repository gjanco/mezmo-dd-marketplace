
import pytest


@pytest.fixture(scope='session')
def dd_environment():
    yield


@pytest.fixture
def instance():
    instance = {
        "base_url": "http://not.a.real.url.com/",
        "user": "fake_user",
        "password": "fake_secure_password"
    }
    return instance
