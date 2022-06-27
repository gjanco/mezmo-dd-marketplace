import os

import pytest

from datadog_checks.dev import docker_run, get_docker_hostname, get_here

from .constants import Config

URL = "http://{}:8000".format(get_docker_hostname())
STATS_TITLE = "Servlet statistics"
config = Config.STATSDO_AND_ITSM.copy()
config['url'] = URL

@pytest.fixture(scope="session")
def dd_environment():
    compose_file = os.path.join(get_here(), "docker-compose.yml")
    with docker_run(
        compose_file, 
        endpoints=[URL]
    ):
        yield config

@pytest.fixture
def instance():
    return config.copy()
