# Copyright (C) 2023 Crest Data Systems.
# All rights reserved

import pytest


@pytest.fixture(scope="session")
def dd_environment():
    yield {}


@pytest.fixture
def instance():
    return {}
