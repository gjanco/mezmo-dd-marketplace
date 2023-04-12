# import libraries

# import local code
from .globals import __NAMESPACE__


def queryAtomStatusViaApi(
    self,
    boomi_api_url,
    boomi_api_userid,
    boomi_api_token,
    boomi_account_id,
):

    # Calls Boomi Atom API, returns array of results.
    #
    # INPUTS:
    # boomi_api_url...     Base URL for making Boomi API calls, e.g. https://api.boomi.com
    # boomi_api_userid...  User Id for Basic Auth into Boomi Platform API calls; do not prepend BOOMI_TOKEN.
    # boomi_api_token...   API token (password not supported)
    # boomi_account_id...  Boomi AtomSphere Platform account ID; used in making API calls.
    # install_dir...       Where the runtime is installed.  We will grab container.id from this path.
    #                      to use this value in the API URL
    #
    # OUTPUTS:
    # arr_atoms...          Array of JSON objects coming from Boomi AtomSphere query Atom API response.

    # Begin the log
    self.log.debug("Entered queryAtomStatusViaApi.")

    # Create an array to hold the output.
    arr_atoms = []

    try:

        #########################
        # QUERY ATOM  (api call)
        #########################

        # Prepare URL.
        sAtomApiUrl = "{}/api/rest/v1/{}/Atom/query".format(boomi_api_url, boomi_account_id)

        # Get API response
        atomApiResponse = getAtomApiResponse(self, boomi_api_userid, boomi_api_token, sAtomApiUrl)

        # If we reached here, we got an API response.
        # We only process the first page of results and throw a warning if more pages exist.
        logmsg = "Total count of Atoms in Query Result: {}".format(atomApiResponse['numberOfResults'])
        self.log.info(logmsg)

        # If there are more than zero reults, append to output
        if atomApiResponse['numberOfResults'] > 0:
            arr_atoms.extend(atomApiResponse['result'])

        # If there is another page of results, throw a warning.
        if 'queryToken' in atomApiResponse:
            self.log.warning(
                "Boomi API Query Atom returned more than one page of results.  Only processing first page."
            )

    except Exception as e:

        # Something went wrong querying API.
        # Throw a warning
        msg = "Failure in queryAtomStatusViaApi.py.  Could not report any runtime online status. " + str(e)
        self.warning(msg)

    # Return results to caller
    return arr_atoms


def getAtomApiResponse(self, boomi_api_userid, boomi_api_token, boomi_api_url):

    # Calls Boomi Atom (object) API and retrieves results.
    # INPUTS:
    # boomi_api_userid...  User Id for Basic Auth into Boomi Platform API calls; do not prepend BOOMI_TOKEN.
    # boomi_api_token...   API token (password not supported)
    # boomi_api_url...     Full URL for making Boomi API calls,
    #                      e.g. https://api.boomi.com/api/rest/v1/<BOOMI_ACCOUNT>/Event/query
    #
    # OUTPUTS:
    # response_json...     JSON response body from API call.

    # Begin the log
    self.log.debug("Entered getAtomApiResponse.")
    logmsg = "Boomi Atom (object) API URL: {}".format(boomi_api_url)
    self.log.debug(logmsg)

    # Perform HTTP Request.
    response_json = ""
    # Submit a metric showing that we tried to make a Boomi API call.
    self.count(__NAMESPACE__ + "boomi_api_calls_attempted", 1, tags=["boomiapicalltype:AtomObject"])

    try:
        response = self.http.post(
            boomi_api_url,
            json={},
            headers={'Accept': 'application/json'},
            auth=("BOOMI_TOKEN." + boomi_api_userid, boomi_api_token),
        )
        response.raise_for_status()
        response_json = response.json()
    except Exception as e:
        # Failure performing HTTP request
        errmsg = '''\
Failed to query Atom (object) API response page at URL {}.
Error message was...
{}\
'''.format(
            boomi_api_url, str(e)
        )
        # Write to log
        self.log.error(errmsg)
        # Blow up this function
        raise e

    # Log some info about the response.
    logmsg = "Atom (object) Response Data:\n{}".format(response_json)
    self.log.debug(logmsg)

    # If we reached here, we have JSON returned from Boomi API call.
    # Inspect JSON contents
    if '@type' in response_json and 'result' in response_json and 'numberOfResults' in response_json:
        # JSON contents are as expected.
        # Return data to caller.
        return response_json
    else:
        # JSON contents are NOT as expected
        errmsg = '''\
Boomi Atom (object) API Query response JSON content was not as expected; missing '@type', 'result' or 'numberOfResults'.
Boomi Atom (object) API URL: {}
Boomi Atom (object) API Response: {}\
'''.format(
            boomi_api_url, response_json
        )
        # Write to log
        self.log.error(errmsg)
        # Blow up this function
        raise Exception(errmsg)
