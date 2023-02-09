"""This is API client used for calling the customers API."""
import urllib.parse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util import Retry

from .cds_netapp_aiqum_constants import BACKOFF_FACTOR, REQUEST_TIMEOUT, RETRY, VERIFY_SSL
from .cds_netapp_aiqum_errors import APIError, EmptyAPIResponseError, InvalidAPICredentialsError, SSLError

STATUS_FORCELIST = [429] + list(range(501, 600))
SUCCESSFUL_STATUSCODE = list(range(200, 299))
METHOD_WHITELIST = ["GET", "POST", "HEAD"]


# Error handler decorator
def handle_errors(method):
    """Handle common errors in API response."""

    def wrapper(self, *args, **kwargs):
        err = None
        err_msg = None
        try:
            res = method(self, *args, **kwargs)

            if res is None:
                raise EmptyAPIResponseError

            elif res.status_code == 401:
                raise InvalidAPICredentialsError

            elif res.status_code not in SUCCESSFUL_STATUSCODE:
                raise APIError(
                    "Request to API server failed. URL: {} | Status code: {} | Response: {}".format(
                        res.url, res.status_code, res.text
                    ),
                    res,
                )

            return res

        except requests.exceptions.Timeout as ex:
            err_msg = "TimeoutError: Timeout while requesting data from Platform."
            err = ex

        except requests.exceptions.SSLError as ex:
            err_msg = "SSLError: Please verify the SSL certificate for the provided configuration."
            err = ex
            raise SSLError(ex)

        except requests.exceptions.ProxyError as ex:
            err_msg = "ProxyError: Invalid Proxy credentials. Please recheck your Proxy settings."
            err = ex

        except requests.exceptions.ConnectionError as ex:
            err_msg = "ConnectionError: Error while connecting."
            err = ex

        except requests.exceptions.RequestException as ex:
            err_msg = "RequestError: Error while fetching data."
            err = ex

        raise APIError(err_msg + f" Error: {err}")

    return wrapper


# Jsonify response decorator
def jsonify(method):
    """Returns json dict of response."""

    def wrapper(self, *args, **kwargs):
        try:
            res = method(self, *args, **kwargs)
            return res.json()
        except requests.exceptions.JSONDecodeError:
            return {}

    return wrapper


# Create common session object
def get_requests_retry_session(
    retries=RETRY,
    backoff_factor=BACKOFF_FACTOR,
    status_forcelist=STATUS_FORCELIST,
    method_whitelist=METHOD_WHITELIST,
):
    """Creates and returns a session object with retry mechanism."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        method_whitelist=method_whitelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


class AIQUMAPIClient(object):
    """A Client for all API related transactions."""

    def __init__(self, domain, username, password, log):
        """Initialize an object."""
        self.session = get_requests_retry_session()
        self.session.verify = VERIFY_SSL
        self.username = username
        self.password = password
        self.base_url = domain.strip("/")

        self.log = log

    def build_url(self, endpoint, *objects):
        """Builds full url."""
        objects = [urllib.parse.quote_plus(arg, safe="") for arg in objects]

        return "{}/{}/{}".format(
            self.base_url,
            endpoint.strip("/"),
            "/".join(objects),
        ).rstrip("/")

    def set_server_cert_verification(self, verify):
        """Set SSL certificate verification."""
        self.session.verify = verify

    @jsonify
    @handle_errors
    def get(self, url, **kwargs):
        """Sends a GET request and returns response."""
        response = self.session.get(url, timeout=REQUEST_TIMEOUT, auth=(self.username, self.password), **kwargs)
        return response

    @jsonify
    @handle_errors
    def post(self, url, **kwargs):
        """Sends a POST request and returns response."""
        return self.session.post(url, timeout=REQUEST_TIMEOUT, auth=(self.username, self.password), **kwargs)
