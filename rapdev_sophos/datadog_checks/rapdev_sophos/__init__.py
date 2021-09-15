# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from .__about__ import __version__
from .sophos import SophosCheck

__all__ = ['__version__', 'SophosCheck']
