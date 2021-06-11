# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc
"""
Datadogpy is a collection of Datadog Python tools.
It contains:
* datadog.api: a Python client for Datadog REST API.
"""
# stdlib
import logging
import os
import os.path
from typing import Any, List, Optional

# datadog
from . import api
from .util.compat import iteritems, NullHandler, text
from .util.hostname import get_hostname
from .version import __version__  # noqa

# Loggers
logging.getLogger("datadog.api").addHandler(NullHandler())


def initialize(
    api_key=None,  # type: Optional[str]
    app_key=None,  # type: Optional[str]
    host_name=None,  # type: Optional[str]
    api_host=None,  # type: Optional[str]
    return_raw_response=False,  # type: bool
    hostname_from_config=True,  # type: bool
    **kwargs  # type: Any
):
    # type: (...) -> None
    """
    Initialize and configure Datadog.api

    :param api_key: Datadog API key
    :type api_key: string

    :param app_key: Datadog application key
    :type app_key: string

    :param host_name: Set a specific hostname
    :type host_name: string

    :param proxies: Proxy to use to connect to Datadog API;
                    for example, 'proxies': {'http': "http:<user>:<pass>@<ip>:<port>/"}
    :type proxies: dictionary mapping protocol to the URL of the proxy.

    :param api_host: Datadog API endpoint
    :type api_host: url

    :param cacert: Path to local certificate file used to verify SSL \
        certificates. Can also be set to True (default) to use the systems \
        certificate store, or False to skip SSL verification
    :type cacert: path or boolean

    :param mute: Mute any ApiError or ClientError before they escape \
        from datadog.api.HTTPClient (default: True).
    :type mute: boolean

    :param return_raw_response: Whether or not to return the raw response object in addition \
        to the decoded response content (default: False)
    :type return_raw_response: boolean

    :param hostname_from_config: Set the hostname from the Datadog agent config (agent 5). Will be deprecated
    :type hostname_from_config: boolean
    """
    # API configuration
    api._api_key = api_key or api._api_key or os.environ.get("DATADOG_API_KEY", os.environ.get("DD_API_KEY"))
    api._application_key = (
        app_key or api._application_key or os.environ.get("DATADOG_APP_KEY", os.environ.get("DD_APP_KEY"))
    )
    api._hostname_from_config = hostname_from_config
    api._host_name = host_name or api._host_name or get_hostname(hostname_from_config)
    api._api_host = api_host or api._api_host or os.environ.get("DATADOG_HOST", "https://api.datadoghq.com")
    api._return_raw_response = return_raw_response

    # HTTP client and API options
    for key, value in iteritems(kwargs):
        attribute = "_{}".format(key)
        setattr(api, attribute, value)
