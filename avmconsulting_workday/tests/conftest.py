import pytest

INIT_CONFIG = {
    "url": "https://wd2-impl-services1.workday.com/ccx/service/alignt_tenant/Integrations",
    "password": "s1234qwerasdf",
    "user": "zaq1xsw2",
    "tenant": "1qaz2wsx",
    "site": "datadoghq.com",
    "api_key": "1q2w3e4r5t6y7u8i",
}


@pytest.fixture(scope='session')
def dd_environment():
    yield INIT_CONFIG


@pytest.fixture
def instance():
    return INIT_CONFIG.copy()
