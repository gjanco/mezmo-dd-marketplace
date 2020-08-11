from abc import ABCMeta, abstractmethod

import six

from ..core_remote.remote_base import ResponseStatus, RetryStrategy
from ..core_remote.remote_http import HttpRequest, HttpRequestType


@six.add_metaclass(ABCMeta)
class IAuth:
    @abstractmethod
    def connect(self, caller):
        raise NotImplementedError

    @abstractmethod
    def add_auth_to_request(self, caller, request):
        raise NotImplementedError

    @abstractmethod
    def connected(self):
        raise NotImplementedError


class AuthConnectionError(Exception):
    def __init__(self, response, message):
        self.response = response
        super(AuthConnectionError, self).__init__(message)


class BearerAuth(IAuth):
    def __init__(self, url, client_id, client_secret, attempts_num=3, wait_time=2):
        self._access_token = None
        self._auth_header = None
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }
        self._connect_request = HttpRequest(
            request_type=HttpRequestType.POST,
            url=url,
            data=data,
            retry_strategy=RetryStrategy(attempts_num, wait_time),
        )

    def connect(self, caller):
        response = caller.call(self._connect_request)
        if response.status() != ResponseStatus.OK:
            self._auth_header = None
            raise AuthConnectionError(
                response,
                "Cannot generate bearer auth. Response status: {}".format(
                    response.status().name
                ),
            )
        self._access_token = response.get_data()["access_token"]
        self._auth_header = {"Authorization": "Bearer " + self._access_token}

    def connected(self):
        return self._auth_header is not None

    def get_access_token(self):
        return self._access_token

    def add_auth_to_request(self, caller, request):
        if request == self._connect_request:
            return
        if not self._auth_header:
            self.connect(caller)
        request.update_headers(self._auth_header)
