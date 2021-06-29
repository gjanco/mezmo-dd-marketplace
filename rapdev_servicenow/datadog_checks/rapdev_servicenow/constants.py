class Constants:
    DEFAULT_STATS_TITLE = "Servlet statistics"
    ERROR_NO_INSTANCE = "Instance name is required"
    ERROR_AT_LEAST_ONE_CHECK = "At least one check must be configured"
    TABLE_API_BASE_PATH = "/api/now/table"
    STATSDO_PATH = "/stats.do"
    SNC_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    TABLE_API_HEADERS = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    STATSDO_HEADERS = {
        "User-Agent": "datadog-agent",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br",
    }
    METRIC_PREFIX = "rapdev.servicenow"
    REQUIRED_TAGS = [
        "vendor:rapdev"
    ]
    FIELDS_USER = "name%2Cvip%2Csys_id"
    FIELDS_LOCATION = "name%2Csys_id"
    FIELDS_TASK_SLA= "stage%2Cend_time%2Cstart_time%2Csla%2Ctask%2Cpercentage%2Chas_breached"
    FIELDS_CONTRACT_SLA = "target%2Cname%2Csys_id"
    QUERY_CLOSED_OR_RESOLVED_LAST_30 = "closed_at>=javascript:gs.beginningOfLast30Days()^ORresolved_at>=javascript:gs.beginningOfLast30Days()"

class Tables:
    SYS_USER = "sys_user"
    CMN_LOCATION = "cmn_location"
    TASK_SLA = "task_sla"
    CONTRACT_SLA = "contract_sla"
