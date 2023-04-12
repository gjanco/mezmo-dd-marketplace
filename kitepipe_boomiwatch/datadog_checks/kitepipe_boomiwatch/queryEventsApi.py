# import libraries

# import local code
from .globals import __NAMESPACE__


def queryBoomiEventsApi(
    self,
    boomi_api_url,
    boomi_api_userid,
    boomi_api_token,
    startDateTime,
    endDateTime,
    boomi_account_id,
    cluster_node_id,
):

    # Calls Boomi Events API, pages over results, returns array of Events.
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
    # arr_events...    Array of Event objects just as they came from Boomi API but assembled into array.

    # Begin the log
    self.log.debug("Entered queryBoomiEventsApi.")

    # Create an array to hold the output.
    arr_events = []

    ###############################
    # QUERYING EVENTS BY DATE RANGE
    ###############################

    # Prepare the data to be used as request JSON input to Boomi Events API...
    # for all events in date range.
    apiRequest = {
        "QueryFilter": {
            "expression": {
                "argument": [startDateTime.isoformat()[0:19] + "Z", endDateTime.isoformat()[0:19] + "Z"],
                "operator": "BETWEEN",
                "property": "eventDate",
            }
        }
    }

    # Prepare URL for first page of Boomi Events API response.
    sEventsApiUrl = "{}/api/rest/v1/{}/Event/query".format(boomi_api_url, boomi_account_id)

    # Get first page of Boomi Events API response
    eventResponse = getBoomiEventsApiResponsePage(
        self, boomi_api_userid, boomi_api_token, sEventsApiUrl, apiRequest, cluster_node_id
    )

    # If we reached here, we got a first page.
    logmsg = "Total count of Events in Query Result: {}".format(eventResponse['numberOfResults'])
    self.log.info(logmsg)

    # If there are more than zero reults, append to output
    if eventResponse['numberOfResults'] > 0:
        arr_events.extend(eventResponse['result'])

        # Iterate over remaining pages, if any
        while 'queryToken' in eventResponse:
            # Get subsequent page of Boomi Events API response.
            eventResponse = getBoomiEventsApiResponsePage(
                self,
                boomi_api_userid,
                boomi_api_token,
                sEventsApiUrl + "More",
                eventResponse['queryToken'],
                cluster_node_id,
            )

            # If we reached here, we got a subsequent page.
            # If there are more than zero reults, append to output
            if eventResponse['numberOfResults'] > 0:
                arr_events.extend(eventResponse['result'])

    # Return results to caller
    return arr_events


def getBoomiEventsApiResponsePage(self, boomi_api_userid, boomi_api_token, boomi_api_url, jRequest, cluster_node_id):

    # Calls Boomi Events API and retrieves one page of results.
    # INPUTS:
    # boomi_api_userid...  User Id for Basic Auth into Boomi Platform API calls; do not prepend BOOMI_TOKEN.
    # boomi_api_token...   API token (password not supported)
    # boomi_api_url...     Full URL for making Boomi API calls,
    #                      e.g. https://api.boomi.com/api/rest/v1/<BOOMI_ACCOUNT>/Event/query
    # jRequest...          JSON request body for making API call.
    #
    # OUTPUTS:
    # response_json...     JSON response body from API call.

    # Begin the log
    self.log.debug("Entered getBoomiEventsApiResponsePage.")
    logmsg = "Boomi Events API URL: {}".format(boomi_api_url)
    self.log.debug(logmsg)
    logmsg = "Boomi Events API Request Body: {}".format(jRequest)
    self.log.debug(logmsg)

    # Perform HTTP Request.
    response_json = ""
    # Submit a metric showing that we tried to make a Boomi API call.
    self.count(__NAMESPACE__ + "boomi_api_calls_attempted", 1, tags=["boomiapicalltype:Event"])

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
Failed to get Boomi Event API response page at URL {}.
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
    logmsg = "Event Response Data:\n{}".format(response_json)
    self.log.debug(logmsg)

    # If we reached here, we have JSON returned from Boomi API call.
    # Inspect JSON contents
    if 'numberOfResults' in response_json and 'result' in response_json:
        # JSON contents are as expected.
        # Return data to caller.
        return response_json
    else:
        # JSON contents are NOT as expected
        errmsg = '''\
Boomi API Event query response JSON content was not as expected; missing 'numberOfResults' or 'result'.
Boomi Event API URL: {}
Boomi Event API Request Body: {}
Boomi Event API Response: {}\
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
