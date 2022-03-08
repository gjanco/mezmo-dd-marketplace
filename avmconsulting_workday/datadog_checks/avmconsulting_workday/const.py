XML_NODES = {
    'Integration_Events_Response': ".//Get_Integration_Events_Response",
    'Integration_Event': ".//Integration_Event",
    'Integration_System_ID': ".//ID[@type='Integration_System_ID']",
    'Integration_System_Reference': ".//Integration_System_Reference",
    'Integration_Status': ".//ID[@type='Background_Process_Instance_Status_ID']",
    'Integration_Event_ID': ".//ID[@type='Background_Process_Instance_ID']",
    'Initiated_DateTime': ".//Initiated_DateTime",
    'Completed_DateTime': ".//Completed_DateTime",
    'Logs': ".//Background_Process_Message_Data",
    'Message_Severity_Level': ".//ID[@type='Message_Severity_Level']",
    'Message_Summary': ".//Message_Summary",
}
STATES = {
    'Completed': 0,
    'CompletedWithWarnings': 1,
    'CompletedWithErrors': 2,
    'Failed': 2,
}
LOG_SEVERITY = {
    'INFO': 20,
    'WARN': 30,
    'ERROR': 40,
}
EVENT_TYPES = {
    'INTEGRATION_ENTERPRISE_EVENT': 'ENTERPRISE',
    'INTEGRATION_ESB_INVOCATION': 'ESB',
}
