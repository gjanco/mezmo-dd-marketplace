# import libraries

# import local code
from .globals import __NAMESPACE__


def queryBoomiAuditLogsApi(
    self,
    boomi_api_url,
    boomi_api_userid,
    boomi_api_token,
    startDateTime,
    endDateTime,
    boomi_account_id,
    cluster_node_id,
):

    # Calls Boomi AuditLogs API, pages over results, returns array of AuditLogs.
    #
    # INPUTS:
    # boomi_api_url...     Base URL for making Boomi API calls, e.g. https://api.boomi.com
    # boomi_api_userid...  User Id for Basic Auth into Boomi Platform API calls; do not prepend BOOMI_TOKEN.
    # boomi_api_token...   API token (password not supported)
    # startDateTime...     TZ-aware datetime with UTC TZ, precise to the second but not more granular than that.
    # endDateTime...       Corresponds to startDateTime.
    # boomi_account_id...  Boomi AtomSphere Platform account ID; used in making API calls.
    #
    # OUTPUTS:
    # arr_auditlogs...    Array of AuditLog objects just as they came from Boomi API but assembled into array.

    # Begin the log
    self.log.debug("Entered queryBoomiAuditLogsApi.")

    # Create an array to hold the output.
    arr_auditlogs = []

    ###################################
    # QUERYING AUDITLOGS BY DATE RANGE
    ###################################

    # Prepare the data to be used as request JSON input to Boomi AuditLogs API...
    # for all auditlogs in date range.
    apiRequest = {
        "QueryFilter": {
            "expression": {
                "argument": [startDateTime.isoformat()[0:19] + "Z", endDateTime.isoformat()[0:19] + "Z"],
                "operator": "BETWEEN",
                "property": "date",
            }
        }
    }

    # Prepare URL for first page of Boomi AuditLogs API response.
    sAuditLogsApiUrl = "{}/api/rest/v1/{}/AuditLog/query".format(boomi_api_url, boomi_account_id)

    # Get first page of Boomi AuditLogs API response
    auditlogResponse = getBoomiAuditLogsApiResponsePage(
        self, boomi_api_userid, boomi_api_token, sAuditLogsApiUrl, apiRequest, cluster_node_id
    )

    # If we reached here, we got a first page.
    logmsg = "Total count of AuditLogs in Query Result: {}".format(auditlogResponse['numberOfResults'])
    self.log.info(logmsg)

    # If there are more than zero reults, append to output
    if auditlogResponse['numberOfResults'] > 0:
        arr_auditlogs.extend(auditlogResponse['result'])

        # Iterate over remaining pages, if any
        while 'queryToken' in auditlogResponse:
            # Get subsequent page of Boomi AuditLogs API response.
            auditlogResponse = getBoomiAuditLogsApiResponsePage(
                self,
                boomi_api_userid,
                boomi_api_token,
                sAuditLogsApiUrl + "More",
                auditlogResponse['queryToken'],
                cluster_node_id,
            )

            # If we reached here, we got a subsequent page.
            # If there are more than zero reults, append to output
            if auditlogResponse['numberOfResults'] > 0:
                arr_auditlogs.extend(auditlogResponse['result'])

    # Return results to caller
    return arr_auditlogs


def getBoomiAuditLogsApiResponsePage(self, boomi_api_userid, boomi_api_token, boomi_api_url, jRequest, cluster_node_id):

    # Calls Boomi AuditLogs API and retrieves one page of results.
    # INPUTS:
    # self...              Reference to Datadog AgentCheck object that ultimately launched this.
    # boomi_api_userid...  User Id for Basic Auth into Boomi Platform API calls; do not prepend BOOMI_TOKEN.
    # boomi_api_token...   API token (password not supported)
    # boomi_api_url...     Full URL for making Boomi API calls,
    #                      e.g. https://api.boomi.com/api/rest/v1/<BOOMI_ACCOUNT>/AuditLog/query
    # jRequest...          JSON request body for making API call.
    #
    # OUTPUTS:
    # response_json...     JSON response body from API call.

    # Begin the log
    self.log.debug("Entered getBoomiAuditLogsApiResponsePage.")
    logmsg = "Boomi AuditLogs API URL: {}".format(boomi_api_url)
    self.log.debug(logmsg)
    logmsg = "Boomi AuditLogs API Request Body: {}".format(jRequest)
    self.log.debug(logmsg)

    # Perform HTTP Request.
    response_json = ""
    # Submit a metric showing that we tried to make a Boomi API call.
    self.count(__NAMESPACE__ + "boomi_api_calls_attempted", 1, tags=["boomiapicalltype:AuditLog"])

    try:
        response = self.http.post(
            boomi_api_url,
            json=jRequest,
            headers={'Accept': 'application/json'},
            auth=("BOOMI_TOKEN." + boomi_api_userid, boomi_api_token),
        )
        response.raise_for_status()
        response_json = response.json()
    except Exception as e:
        # Failure performing HTTP request
        errmsg = '''\
Failed to get Boomi AuditLog API response page at URL {}.
POSTed body was...
{}
Error message was...
{}\
'''.format(
            boomi_api_url, jRequest, str(e)
        )
        # Write to log
        self.log.error(errmsg)
        # Blow up this execution
        self.service_check(
            __NAMESPACE__ + "completed",
            self.CRITICAL,
            tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
        )
        raise Exception(errmsg)

    # Log some info about the response.
    logmsg = "AuditLog Response Data:\n{}".format(response_json)
    self.log.debug(logmsg)

    # If we reached here, we have JSON returned from Boomi API call.
    # Inspect JSON contents
    if 'numberOfResults' in response_json:
        # JSON contents are as expected.
        # Return data to caller.
        return response_json
    else:
        # JSON contents are NOT as expected
        errmsg = '''\
Boomi API AuditLog query response JSON content was not as expected; missing 'numberOfResults'.
Boomi AuditLog API URL: {}
Boomi AuditLog API Request Body: {}
Boomi AuditLog API Response: {}\
'''.format(
            boomi_api_url, jRequest, response_json
        )
        # Write to log
        self.log.error(errmsg)
        # Blow up this execution
        self.service_check(
            __NAMESPACE__ + "completed",
            self.CRITICAL,
            tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
        )
        raise Exception(errmsg)
