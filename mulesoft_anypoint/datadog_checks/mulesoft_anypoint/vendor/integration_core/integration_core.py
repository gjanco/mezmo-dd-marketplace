import json
import os

from . import __path__
from .core_threading import MultithreadingPool

try:
    from queue import Empty, Queue
except ImportError:
    from Queue import Empty, Queue


def get_metrics_prefix(base_prefix, env=None):
    metric_prefix = base_prefix
    if env and env.lower() != "prod":
        metric_prefix = ".".join([env.lower(), metric_prefix])
    return metric_prefix


def get_abs_path(path):
    return os.path.join(
        os.path.dirname(os.path.abspath(__path__[0])),
        "integration_core",
        path,
    )


def load_config(base_path, config_filter=None):
    config_list = []
    for config in os.listdir(base_path):
        ext = ".json"
        if config.endswith(ext) and (
            not config_filter or config[: -len(ext)] in config_filter
        ):
            with open(os.path.join(base_path, config)) as json_file:
                config_list.append(json.load(json_file))
    return config_list


class IntegrationCore:
    def __init__(self, logger, n_threads, reader, reporter):
        self._n_threads = n_threads
        self._logger = logger
        self._reader = reader
        self._reporter = reporter
        self._reader.set_add_to_queue_callback(self.add_to_queue_callback)
        self._queue = Queue()
        self._exec_finished = False

    def add_to_queue_callback(self, metric):
        self._queue.put(metric)

    def _report_metric(self, metric):
        self._reporter.report_metric(metric)
        self._queue.task_done()

    def _queue_consumer(self, pool):
        while not self._exec_finished or not self._queue.empty():
            try:
                metric = self._queue.get(block=True, timeout=1)
                pool.apply_async(self._report_metric, [metric])
            except Empty:
                pass

    def execute(self):
        self._exec_finished = False
        pool = MultithreadingPool(self._n_threads)
        MultithreadingPool(1, auto_close=True).apply_async(self._queue_consumer, [pool])
        self._reader.execute()
        results = self._reader.get_results()
        self._exec_finished = True
        self._queue.join()
        pool.wait_and_close()
        return results
