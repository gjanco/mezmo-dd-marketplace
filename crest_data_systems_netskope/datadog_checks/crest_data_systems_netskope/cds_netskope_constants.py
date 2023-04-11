# Copyright (C) 2023 Crest Data Systems.
# All rights reserved

"""All the required global constants for Netskope Datadog Integration"""
# API Client Constants
VERIFY_SSL = True
RETRY = 3
BACKOFF_FACTOR = 3
REQUEST_TIMEOUT = 30

# Integration metrics and logs prefix
INTEGRATION_PREFIX = "cds.netskope"
AUTH_CHECK_NAME = "can_connect"
CHECKPOINT_SERVICE = "checkpoint"
HOST_TAG_NAME = "cds-netskope-instance"
BILLING_CHECKPOINT = "events"
MARKETPLACE_BILLING_METRIC = "datadog.marketplace.crest_data_systems_netskope.volume"
BILLING_PER_EVENTS = 1000000

# ServiceCheck and Events constants
NETSKOPE_CHECK_NAME = "status"

API_VAL_TAG = ["tag:datadog_keys_validation"]
API_VAL_TITLE = "Datadog api/app key validation"
API_VAL_SOURCE_TYPE = INTEGRATION_PREFIX + ".datadog_keys_validation"

CONF_VAL_TAG = ["tag:netskope_conf_validation"]
CONF_VAL_TITLE = "Netskope conf.yaml validations"
CONF_VAL_SOURCE_TYPE = INTEGRATION_PREFIX + ".netskope_conf_validation"

AUTH_TAG = ["tag:netskope_authentication"]
AUTH_TITLE = "Netskope Authentication"
AUTH_SOURCE_TYPE = INTEGRATION_PREFIX + ".netskope_authentication"

STATUS_NUMBER_TO_VALUE = {0: "SUCCESS", 1: "WARNING", 2: "ERROR"}

# Chunk configuration for logs and metrics
LOGS_MAX_CHUNK_SIZE = 5000000  # 5 MB
LOGS_MAX_CHUNK_LENGTH = 1000
METRICS_MAX_CHUNK_SIZE = 3200000  # 3.2 MB

# Netskope constants
AUTH_EVENT_TYPE = "audit"
EVENT_DATAEXPORT_ENDPOINT = "/api/v2/events/dataexport/events/{}?index={}&operation={}"
TIMESTAMP_OFFSET = 3600 * 18  # 18 Hours
CHECKPOINT_TIME_OFFSET = 3600 * 24 * 31  # 31 Days
MAX_WAIT_TIME = 5
NETSKOPE_INDEX_PREFIX = "dd.netskope"
AUTH_INDEX = NETSKOPE_INDEX_PREFIX + ".auth"
MAX_ITERATIONS = 25
AUTH_SHOULD_WAIT = False
ENDPOINT_MAP = {"connection": "page"}
HWM_BREAKING_POINT = 600  # 10 minutes

# Logs timestamp format
LOGS_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Default configurations
DEFAULT_EVENTS = ["infrastructure", "network", "connection", "audit", "application", "incident"]

# Datadog site mapping
DEFAULT_SITE = "datadoghq.com"
API_SITE = "https://api.{}"
LOGS_INTAKE_SITE = "https://http-intake.logs.{}"

# Datadog API retry constants
DD_STATUS_TO_RETRY = [408, 429, 500, 503]
DD_WAIT_FOR = 10
DD_MAX_TRIES = 3

# Datadog error messages
NO_LOG_ERROR_MESSAGE = ["invalid_argument(No valid indexes specified)"]
EMPTY_SEARCH_LOG = {"data": []}
