# (C) RapDev, Inc. 2020-present
# All rights reserved
import pytest


@pytest.fixture(scope="session")
def dd_environment():
    yield


@pytest.fixture
def instance():
    return {}
