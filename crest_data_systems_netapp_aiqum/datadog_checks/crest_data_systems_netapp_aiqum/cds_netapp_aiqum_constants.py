API_ERROR_MSG = "Something went wrong."

# API Client Constants
VERIFY_SSL = False
RETRY = 3
BACKOFF_FACTOR = 3
REQUEST_TIMEOUT = 30

INTEGRATION_PREFIX = "cds.netapp.aiqum"
AUTH_EVENT_SOURCE_TYPE = INTEGRATION_PREFIX + ".auth"
AUTH_CHECK_NAME = "can_connect"

# Logs ingestion interval
LOGS_INTERVAL = 3600  # 3600 Seconds = 1 Hour

# Chunk configuration for log events
MAX_CHUNK_SIZE = 5000000  # 5000000Bytes = 5MB
MAX_CHUNK_LENGTH = 1000
