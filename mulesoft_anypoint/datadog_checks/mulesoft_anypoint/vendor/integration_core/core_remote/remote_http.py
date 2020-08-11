import json
import time
from enum import Enum

import requests

from ..core_parsing import RE_CURLY_BRACES_KEYS, RegexParser

# fmt: off
from ..core_remote.remote_base import IRemoteCaller, IRequest, JsonResponse, ResponseStatus, RetryStrategy  # isort:skip
# fmt: on


class HttpRequestType(Enum):
    POST = 1
    GET = 2


class HttpRequest(IRequest):
    def __init__(
        self,
        request_type,
        url,
        query_params=None,
        headers=None,
        data=None,
        retry_strategy=None,
    ):
        self._request_type = request_type
        self._url = url
        self._query_params = query_params
        self._headers = headers
        self._data = data
        self.retry_strategy = retry_strategy or RetryStrategy(1)

    def get_url(self):
        return self._url

    def update_headers(self, headers):
        if self._headers:
            self._headers.update(headers)
        else:
            self._headers = dict(headers)

    def get_args(self):
        return {
            "method": self._request_type.name,
            "url": self._url,
            "headers": self._headers,
            "params": self._query_params,
            "data": self._data,
        }


class HttpCaller(IRemoteCaller):
    RESPONSES = {
        401: ResponseStatus.NOT_CONNECTED,
        200: ResponseStatus.OK,
        403: ResponseStatus.LACK_OF_RIGHT,
        408: ResponseStatus.TIMEOUT,
        500: ResponseStatus.ERROR,
    }

    def __init__(self, auth=None):
        self._auth = auth
        self._regex_parser = RegexParser()

    def call(self, request):
        if self._auth:
            self._auth.add_auth_to_request(self, request)
        response = None
        for attempt in range(request.retry_strategy.attempts_num):
            try:
                http_response = requests.request(**request.get_args())
                status = (
                    HttpCaller.RESPONSES.get(http_response.status_code)
                    or ResponseStatus.ERROR
                )
                if status == ResponseStatus.ERROR:
                    raise Exception(http_response.content)
                content_type = http_response.headers.get("content-type")
                if content_type and JsonResponse.get_content_type() in content_type:
                    response_type = JsonResponse
                    data = json.loads(http_response.content)
                else:
                    raise Exception("Unsupported content type: {}".format(content_type))
                response = response_type(data, status)
                break
            except Exception as ex:
                if attempt == request.retry_strategy.attempts_num - 1:
                    message = "Cannot reach {}".format(request.get_url())
                    if request.retry_strategy.attempts_num > 1:
                        message += (
                            " after {} attempts waiting {} "
                            "seconds between each one".format(
                                request.retry_strategy.attempts_num,
                                request.retry_strategy.wait_time,
                            )
                        )
                    message += ". Exception type and message: {}, {}".format(
                        type(ex), str(ex)
                    )
                    response = JsonResponse({"error": message}, ResponseStatus.ERROR)
                else:
                    time.sleep(request.retry_strategy.wait_time)
        return response or JsonResponse({"error": "unknown"}, ResponseStatus.ERROR)

    def fill_uri_params(self, url, uri_params):
        if not uri_params:
            return url
        uri_vars = self._regex_parser.get_set(RE_CURLY_BRACES_KEYS, url)
        filled_url = url
        for uri_var in uri_vars:
            uri_param_key = uri_var[1:-1]
            uri_param_value = uri_params[uri_param_key]
            filled_url = filled_url.replace(uri_var, str(uri_param_value))
        return filled_url
