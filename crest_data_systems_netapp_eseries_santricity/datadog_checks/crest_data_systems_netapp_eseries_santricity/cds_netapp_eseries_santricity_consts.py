"""Constants"""

BASE_URL = "https://{}/devmgr/v2/storage-systems"
GRAPH_ENDPOINT = "graph"
VOLUME_ENDPOINT = "analysed-volume-statistics"
DRIVE_ENDPOINT = "analysed-drive-statistics"
MEL_EVENTS_ENDPOINT = "mel-events"
FAILURES_ENDPOINT = "failures"
CONTROLLER_ENDPOINT = "analysed-controller-statistics"
INTERFACE_ENDPOINT = "analysed-interface-statistics"

LOGS_PREFIX = "netapp.eseries.santricity"
INTEGRATION_PREFIX = "cds." + LOGS_PREFIX
AUTH_EVENT_SOURCE_TYPE = INTEGRATION_PREFIX + ".auth"
AUTH_CHECK_NAME = "can_connect"
ENDPOINTS = [
    "graph",
    "analysed-volume-statistics",
    "analysed-drive-statistics",
    "analysed-controller-statistics",
    "analysed-interface-statistics",
]

GRAPH_SOURCE_TYPE = LOGS_PREFIX + ".graph"
VOLUME_SOURCE_TYPE = LOGS_PREFIX + ".volume"
DRIVE_SOURCE_TYPE = LOGS_PREFIX + ".drive"
MEL_EVENTS_SOURCE_TYPE = LOGS_PREFIX + ".mel_events"
FAILURES_SOURCE_TYPE = LOGS_PREFIX + ".failures"
CONTROLLER_SOURCE_TYPE = LOGS_PREFIX + ".controller"
INTERFACE_SOURCE_TYPE = LOGS_PREFIX + ".interface"

# Logs Constants
LOG_PREFIX = "netapp-eseries-santricity-"
MAX_CHUNK_SIZE = 5000000  # 5000000Bytes = 5MB
MAX_CHUNK_LENGTH = 1000
LOG_INGESTION_INTERVAL = 3600
