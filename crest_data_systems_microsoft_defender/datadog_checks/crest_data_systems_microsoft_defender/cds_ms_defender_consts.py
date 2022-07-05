"""Constants"""
LOGS_PREFIX = "ms.defender.endpoint"
INTEGRATION_PREFIX = "cds." + LOGS_PREFIX
VULNS_ENDPOINT_NAME = "vulns"
MACHINE_ENDPOINT_NAME = "endpoints"
ALERT_ENDPOINT_NAME = "alerts"
INCIDENT_ENDPOINT_NAME = "incidents"
INVESTIGATION_ENDPOINT_NAME = "investigations"
# Source Types
CHECKPOINT_SOURCE_TYPE = LOGS_PREFIX + ".checkpoint"
VULNS_SOURCE_TYPE = LOGS_PREFIX + ".vulnerabilities"
MACHINE_REFS_SOURCE_TYPE = VULNS_SOURCE_TYPE + ".endpoint_refs"
VULNS_MACHINE_SOFTWARE_SOURCE_TYPE = LOGS_PREFIX + ".endpoint-software.vulns"
MACHINES_SOURCE_TYPE = LOGS_PREFIX + ".endpoints"
MACHINES_VULNS_SOURCE_TYPE = MACHINES_SOURCE_TYPE + ".vulns"
MISSING_KBS_SOURCE_TYPE = MACHINES_SOURCE_TYPE + ".missing_kbs"
SOFTWARE_VULNS_SOURCE_TYPE = LOGS_PREFIX + ".software.vulns"
SOFTWARE_DISTS_SOURCE_TYPE = LOGS_PREFIX + ".software.distributions"
ALERTS_SOURCE_TYPE = LOGS_PREFIX + ".alerts"
INCIDENT_SOURCE_TYPE = LOGS_PREFIX + ".incidents"
INVESTIGATION_SOURCE_TYPE = LOGS_PREFIX + ".investigations"
# Extra Constants
MAX_URL_LENGTH = 2000

# Logs Constants
LOG_PREFIX = "ms-defender-"
MAX_CHUNK_SIZE = 5000000  # 5000000Bytes = 5MB
MAX_CHUNK_LENGTH = 1000

# API Constants
BASE_URL = "https://api.securitycenter.microsoft.com"
BASE_URL_FOR_DEFENDER = "https://api.security.microsoft.com"

EXPOSURE_LEVEL = "/api/exposureScore"

# Vulnerability APIs
LIST_VULN_ENDPOINT = "/api/vulnerabilities"
LIST_VULN_FILTER_FIELD = "updatedOn"
LIST_DEVICES_BY_VULNERABILITY = "/api/vulnerabilities/{}/machineReferences"
LIST_VULN_BY_MACHINE_AND_SOFTWARE = "/api/vulnerabilities/machinesVulnerabilities"

# Machine APIs
LIST_MACHINE_ENDPOINT = "/api/machines"
LIST_MACHINE_FILTER_FIELD = "lastSeen"
LIST_MISSING_KBS = "/api/machines/{}/getmissingkbs"
LIST_ENDPOINT_VULNS = "/api/machines/{}/vulnerabilities"

# Software APIs
LIST_SOFTWARE_ENDPOINT = "/api/Software"
LIST_SOFTWARE_VULNS = "/api/Software/{}/vulnerabilities"
LIST_SOFTWARE_DISTRIBUTIONS = "/api/Software/{}/distributions"

# Alert APIs
LIST_ALERT_ENDPOINT = "/api/alerts"
LIST_ALERT_FILTER_FIELD = "lastUpdateTime"

# Incidents APIs
LIST_INCIDENT_ENDPOINT = "/api/incidents"
LIST_INCIDENT_FILTER_FIELD = "lastUpdateTime"

# investigation APIs
LIST_INVEST_ENDPOINT = "/api/investigations"
LIST_INVEST_FILTER_FIELD = "startTime"
