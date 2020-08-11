from abc import ABCMeta, abstractmethod
from enum import Enum

import six


@six.add_metaclass(ABCMeta)
class IRemoteCaller:
    @staticmethod
    @abstractmethod
    def call(request):
        raise NotImplementedError


class RetryStrategy:
    def __init__(self, attempts_num=1, wait_time=2):
        self.attempts_num = attempts_num
        self.wait_time = wait_time


@six.add_metaclass(ABCMeta)
class IRequest:
    @abstractmethod
    def get_args(self):
        raise NotImplementedError


@six.add_metaclass(ABCMeta)
class IResponse:
    @abstractmethod
    def get_data(self):
        raise NotImplementedError

    @abstractmethod
    def status(self):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_content_type():
        raise NotImplementedError


class ResponseStatus(Enum):
    NOT_CONNECTED = 1
    OK = 2
    LACK_OF_RIGHT = 3
    TIMEOUT = 4
    ERROR = 5


# pylint: disable=W0223
@six.add_metaclass(ABCMeta)
class BaseResponse(IResponse):
    def __init__(self, status):
        self._status = status

    def status(self):
        return self._status


class JsonResponse(BaseResponse):
    @staticmethod
    def get_content_type():
        return "application/json"

    def __init__(self, data, status):
        super(JsonResponse, self).__init__(status)
        self._data = data

    def get_data(self):
        return self._data
