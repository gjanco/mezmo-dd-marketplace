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
    # boomi_api_url...     Base URL for making Boomi API calls,
    #                      e.g. https://api.boomi.com
    # boomi_api_userid...  User Id for Basic Auth into Boomi Platform
    #                      API calls; do not prepend BOOMI_TOKEN.
    # boomi_api_token...   API token (password not supported)
    # boomi_account_id...  Boomi AtomSphere Platform account ID; used in
    #                      making API calls.
    # install_dir...       Where the runtime is installed.  We will grab
    #                      container.id from this path.
    #                      to use this value in the API URL
    #
    # OUTPUTS:
    # arr_atoms...         Array of JSON objects coming from Boomi AtomSphere
    #                      query Atom API response.

    # Begin the log
    self.log.debug("Entered queryAtomStatusViaApi.")

    # Create an array to hold the output.
    arr_atoms = []

    try:

        #########################
        # QUERY ATOM  (api call)
        #########################

        # Prepare URL.
        sAtomApiUrl = boomi_api_url + "/api/rest/v1/"
        sAtomApiUrl += boomi_account_id + "/Atom/query"

        # Get API response
        ar1 = boomi_api_userid
        ar2 = boomi_api_token
        atomApiResponse = getAtomApiResponse(self, ar1, ar2, sAtomApiUrl)

        # If we reached here, we got an API response.
        # We only process the first page of results and throw a warning
        # if more pages exist.
        logmsg = "Total count of Atoms in Query Result: "
        logmsg += str(atomApiResponse['numberOfResults'])
        self.log.info(logmsg)

        # If there are more than zero reults, append to output
        if atomApiResponse['numberOfResults'] > 0:
            arr_atoms.extend(atomApiResponse['result'])

        # If there is another page of results, throw a warning.
        if 'queryToken' in atomApiResponse:
            st = "Boomi API Query Atom returned more than one page of "
            st += "results.  Only processing first page."
            self.log.warning(st)

    except Exception as e:

        # Something went wrong querying API.
        # Throw a warning
        msg = "Failure in queryAtomStatusViaApi.py.  "
        msg += "Could not report any runtime online status. " + str(e)
        self.warning(msg)

    # Return results to caller
    return arr_atoms


def getAtomApiResponse(self, boomi_api_userid, boomi_api_token, boomi_api_url):

    # Calls Boomi Atom (object) API and retrieves results.
    # INPUTS:
    # boomi_api_userid...  User Id for Basic Auth into Boomi Platform API
    #                      calls; do not prepend BOOMI_TOKEN.
    # boomi_api_token...   API token (password not supported)
    # boomi_api_url...     Full URL for making Boomi API calls,
    #                      e.g. https://api.boomi.com/api/rest/v1/
    #                      <BOOMI_ACCOUNT>/Event/query
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
    st = __NAMESPACE__ + "boomi_api_calls_attempted"
    self.count(st, 1, tags=["boomiapicalltype:AtomObject"])

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
    tf = '@type' in response_json
    tf = tf and 'result' in response_json
    tf = tf and 'numberOfResults' in response_json
    if tf:
        # JSON contents are as expected.
        # Return data to caller.
        return response_json
    else:
        # JSON contents are NOT as expected
        errmsg = '''\
Boomi Atom (object) API Query response JSON content was not as expected.
Missing '@type', 'result' or 'numberOfResults'.
Boomi Atom (object) API URL: {}
Boomi Atom (object) API Response: {}\
'''.format(
            boomi_api_url, response_json
        )
        # Write to log
        self.log.error(errmsg)
        # Blow up this function
        raise Exception(errmsg)
