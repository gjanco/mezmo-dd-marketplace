import threading
from abc import ABCMeta, abstractmethod
from threading import Lock

import six

try:
    from queue import Empty, Queue
except ImportError:
    from Queue import Empty, Queue


@six.add_metaclass(ABCMeta)
class IPool:
    @abstractmethod
    def apply_async(self, func, args=()):
        raise NotImplementedError

    @abstractmethod
    def wait_and_close(self):
        raise NotImplementedError

    @abstractmethod
    def get_queue_size(self):
        raise NotImplementedError

    def get_active_size(self):
        raise NotImplementedError

    def get_total_size(self):
        raise NotImplementedError

    def empty(self):
        raise NotImplementedError

    def closed(self):
        raise NotImplementedError


@six.add_metaclass(ABCMeta)
class BasePool(IPool):
    def __init__(self, n_threads):
        self._n_threads = n_threads
        self._queue = Queue()
        self._lock = Lock()
        self._active_threads = 0
        self._queue_size = 0
        self._closed = False

    def apply_async(self, func, args=()):
        self._lock.acquire()
        self._queue_size += 1
        self._lock.release()
        self._queue.put([func, args])

    def wait_and_close(self):
        self._queue.join()
        self._closed = True

    def get_queue_size(self):
        return self._queue_size

    def get_active_size(self):
        return self._active_threads

    def get_total_size(self):
        return self._queue_size + self._active_threads

    def empty(self):
        return self._active_threads == 0

    def closed(self):
        return self._closed


@six.add_metaclass(ABCMeta)
class MultithreadingPool(BasePool):
    def __init__(self, n_threads, auto_close=False):
        super(MultithreadingPool, self).__init__(n_threads)
        self._threads = []
        self._auto_close = auto_close
        for _ in range(self._n_threads):
            worker = threading.Thread(target=self._start_worker)
            self._threads.append(worker)
            worker.start()

    def _start_worker(self):
        while not self._closed:
            try:
                task = self._queue.get(block=True, timeout=1)
                self._lock.acquire()
                self._active_threads += 1
                self._queue_size -= 1
                self._lock.release()

                task[0](*task[1])
                self._queue.task_done()

                self._lock.acquire()
                self._active_threads -= 1
                self._lock.release()
            except Empty:
                if self._auto_close and self._active_threads == 0:
                    self._closed = True
                    break
