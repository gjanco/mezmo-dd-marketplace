# Copyright (C) 2023 Crest Data Systems.
# All rights reserved

"""This is API client used for calling the customers API."""
import time
from typing import Generator, List, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from . import cds_netskope_constants as constants
from . import cds_netskope_utils as utils
from .cds_netskope_errors import APIError, EmptyResponseError, InvalidAPICredentialsError, SSLError

STATUS_FORCELIST = [429] + list(range(501, 600))
SUCCESSFUL_STATUSCODE = list(range(200, 299))
METHOD_WHITELIST = ["GET", "POST"]


# Error handler decorator
def handle_errors(method):
    """Handle common errors in API response."""

    def wrapper(self, *args, **kwargs):
        err = None
        err_msg = None
        try:
            res = method(self, *args, **kwargs)

            if res is None:
                raise EmptyResponseError

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
        except requests.exceptions.JSONDecodeError as ex:
            return {"message": "can't decode response to json", "error": str(ex)}

    return wrapper


# Create common session object
def get_requests_retry_session(
    retries=constants.RETRY,
    backoff_factor=constants.BACKOFF_FACTOR,
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
    session.mount("https://", adapter)

    return session


class NetskopeClient(object):
    """A Client for all API related transactions."""

    def __init__(self, host, token, log):
        """Initialize an object.

        :param host: Netskope host
        :type host: str
        :param token: Netskope API v2 token
        :type token: str
        :param log: logging object
        :type log: object
        """
        self.session = get_requests_retry_session()
        self.set_server_cert_verification(constants.VERIFY_SSL)
        self.token = token
        self.base_url = f"https://{host}".strip("/")
        self.headers = {"Authorization": f"Bearer {self.token}"}

        self.host = host
        self.log = log

    def authenticate(self, event_types: List[str], index: str) -> List[str]:
        """Validates Netskope V2 token by fetching data of provided event type.

        :param event_type: list of event types
        :type event_type: List[str]
        :param index: index
        :type index: str

        :return: list of event types that are not accessible with configured V2 token.
        :rtype: List[str]
        """
        operation = int(time.time())
        forbidden_event_types = []
        for event_type in event_types:
            url = self.generate_url(event_type, index, operation)
            response = self.session.get(url, timeout=constants.REQUEST_TIMEOUT, headers=self.headers)
            if response.status_code == 403:
                event_endpoint = constants.EVENT_DATAEXPORT_ENDPOINT.split("?")[0].format(
                    constants.ENDPOINT_MAP[event_type] if constants.ENDPOINT_MAP.get(event_type) else event_type
                )
                self.log.error(
                    f"Netskope | HOST={self.host} | MESSAGE=Authentication failed for '{event_type}'"  # noqa: G00
                    " event endpoint, received insufficient permission error. Ensure permission of endpoint"
                    f" '{event_endpoint}'."
                )
                forbidden_event_types.append(event_type)
                continue
            response.raise_for_status()
            self.log.info(
                f"Netskope | HOST={self.host} | MESSAGE=Successfully authenticated '{event_type}'"  # noqa: G00
                " event endpoint."
            )
            if constants.AUTH_SHOULD_WAIT:
                self.wait_for(response.json().get("wait_time"))
        return forbidden_event_types

    def fetch_events_data(
        self, event_type: str, index: str, from_timestamp: bool = False
    ) -> Generator[List, None, None]:
        """Fetches events data with help of Netskope iterator API.

        :param event_type: type of event to fetch from Netskope
        :type event_type: str
        :param index: Netskope iterator API index for checkpoint mechanism
        :type index: str
        :param from_timestamp: flag to indicate whether data should be fetched from fixed timestamp
            or from last checkpoint through next batch
        :type from_timestamp: bool

        :return: events data lists
        :rtype: Generator[List, None, None]
        """
        iteration_count = 1
        url = self.generate_url(event_type, index, "next")
        if from_timestamp:
            operation = int(time.time()) - constants.TIMESTAMP_OFFSET
            timestamp_url = self.generate_url(event_type, index, operation)

        while True:
            response = self.get(timestamp_url if iteration_count == 1 and from_timestamp else url)
            results = response.get("result")
            timestamp_hwm = response.get("timestamp_hwm")
            if not timestamp_hwm and not results:
                return
            yield results
            if iteration_count >= constants.MAX_ITERATIONS or self.hwm_break(timestamp_hwm):
                return

            iteration_count += 1

            self.wait_for(response.get("wait_time"))

    def generate_url(self, event_type: str, index: str, operation: Union[str, int]) -> str:
        """Generates Netskope URL.

        :param event_type: type of event to fetch from Netskope
        :type event_type: str
        :param index: Netskope iterator API index for checkpoint mechanism
        :type index: str
        :param operation: Netskope iterator API operation parameter
        :type operation: Union[str, int]

        :return: url
        :rtype: str
        """
        if constants.ENDPOINT_MAP.get(event_type):
            event_type = constants.ENDPOINT_MAP[event_type]
        url = self.base_url + constants.EVENT_DATAEXPORT_ENDPOINT.format(event_type, index, operation)
        return url

    def set_server_cert_verification(self, verify) -> None:
        """Set SSL certificate verification.

        :param verify: ssl verification flag
        :type verify: bool
        """
        self.session.verify = verify

    def wait_for(self, seconds: Union[str, float, int, None] = None) -> None:
        """Waits before making next API call.

        :param seconds: seconds to wait for
        :type seconds: Union[str, float, int, None]
        """
        wait_time = constants.MAX_WAIT_TIME
        if utils.is_float(seconds):
            wait_time = float(seconds) if float(seconds) <= constants.MAX_WAIT_TIME else wait_time
            self.log.info(
                f"Netskope | HOST={self.host} | MESSAGE=Waiting for {wait_time} seconds before next"  # noqa: G00
                " API call."
            )
        else:
            self.log.info(
                f"Netskope | HOST={self.host} | MESSAGE=Waiting for the default wait time"  # noqa: G00
                f"(={wait_time} seconds) before next API call."
            )

        time.sleep(wait_time)

    def hwm_break(self, timestamp: Union[float, int]) -> bool:
        """Returns True if timestamp is within breaking condition otherwise returns False.

        :param timestamp: response hwm (high watermark) timestamp
        :type timestamp: Union[float, int]

        :return: True is timestamp is in breaking condition
        :rtype: bool
        """
        if utils.is_float(timestamp) and time.time() - float(timestamp) <= constants.HWM_BREAKING_POINT:
            return True
        return False

    @jsonify
    @handle_errors
    def get(self, url, **kwargs):
        """Sends a GET request and returns response."""
        response = self.session.get(url, timeout=constants.REQUEST_TIMEOUT, headers=self.headers, **kwargs)
        return response

    @jsonify
    @handle_errors
    def post(self, url, **kwargs):
        """Sends a POST request and returns response."""
        return self.session.post(url, timeout=constants.REQUEST_TIMEOUT, headers=self.headers, **kwargs)
