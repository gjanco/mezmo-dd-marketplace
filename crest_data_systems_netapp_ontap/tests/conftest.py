# (C) Datadog, Inc. 2022-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import pytest


@pytest.fixture(scope="session")
def dd_environment():
    yield {}


@pytest.fixture
def instance():
    return {
        "min_collection_interval": 100,
        "api_key": "some_api_key",
        "app_key": "some_app_key",
        "host": "https://10.0.0.1",
        "username": "user",
        "verify_ssl": False,
        "password": "passwd",
    }
