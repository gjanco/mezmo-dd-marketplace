# Unless explicitly stated otherwise all files in this repository are licensed under the BSD-3-Clause License.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2015-Present Datadog, Inc
# flake8: noqa

from typing import Optional

# API settings
_api_key = None  # type: Optional[str]
_application_key = None  # type: Optional[str]
_api_version = "v1"
_api_host = None  # type: Optional[str]
_host_name = None  # type: Optional[str]
_hostname_from_config = True
_cacert = True

# HTTP(S) settings
_proxies = None
_timeout = 60
_max_timeouts = 3
_max_retries = 3
_backoff_period = 300
_mute = True
_return_raw_response = False

# Resources
from .hosts import Host, Hosts
