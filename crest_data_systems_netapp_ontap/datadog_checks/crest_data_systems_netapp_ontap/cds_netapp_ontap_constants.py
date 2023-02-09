# Metrics and Logs configuration
INTEGRATION_PREFIX = "cds.netapp.ontap"
AUTH_EVENT_SOURCE_TYPE = INTEGRATION_PREFIX + ".auth"
AUTH_CHECK_NAME = "can_connect"

# Logs ingestion interval
LOGS_INTERVAL = 3600

# Chunk configuration for log events
MAX_CHUNK_SIZE = 5000000  # 5000000Bytes = 5MB
MAX_CHUNK_LENGTH = 1000
