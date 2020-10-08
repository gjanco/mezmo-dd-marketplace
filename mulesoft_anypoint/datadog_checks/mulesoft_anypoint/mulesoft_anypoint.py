from datadog_checks.base import AgentCheck

from .vendor.integration_core.ilogger import ILogger

from .vendor.integration_core.integration_core import (  # isort:skip
    IntegrationCore,  # isort:skip
    get_metrics_prefix,  # isort:skip
)  # isort:skip

from .vendor.integration_core.ireporter import (  # isort:skip
    IReporter,  # isort:skip
    ReportItemType,  # isort:skip
    CheckStatus,  # isort:skip
)  # isort:skip

from .vendor.integration_core.readers.mulesoft_anypoint.reader_mulesoft_anypoint import (  # isort:skip
    ReaderMulesoftAnypoint,  # isort:skip
    BASE_PREFIX,  # isort:skip
    SERVICE_CHECK,  # isort:skip
)  # isort:skip


class ReporterDatadog(IReporter):
    def __init__(self, datadog_agent):
        self._datadog_agent = datadog_agent

    def report_metric(self, report_item):
        if report_item.report_type == ReportItemType.COUNT:
            self._datadog_agent.count(
                report_item.name, round(report_item.value, 2), tags=report_item.tags
            )
        if report_item.report_type == ReportItemType.GAUGE:
            self._datadog_agent.gauge(
                report_item.name, round(report_item.value, 2), tags=report_item.tags
            )
        if report_item.report_type == ReportItemType.SERVICE_CHECK:
            self._datadog_agent.service_check(
                report_item.name, report_item.value.value, message=report_item.message
            )


class Logger(ILogger):
    def __init__(self, datadog_agent):
        self._logger = datadog_agent.log

    def info(self, message):
        self._logger.info(message)

    def warning(self, message):
        self._logger.warning(message)

    def debug(self, message):
        self._logger.debug(message)

    def error(self, message):
        self._logger.error(message)


class MulesoftAnypointCheck(AgentCheck):
    def __init__(self, *args, **kwargs):
        AgentCheck.__init__(self, *args, **kwargs)
        self._logger = Logger(self)
        self._reporter = ReporterDatadog(self)
        instance = kwargs["instances"][0]
        instance.update(kwargs["init_config"])
        self._logger.debug("MulesoftAnypointCheck init()")
        self._reader = ReaderMulesoftAnypoint(logger=self._logger, config=instance)
        n_threads = instance["threads"]
        self._integration_core = IntegrationCore(
            self._logger, n_threads, self._reader, self._reporter
        )
        self._service_check_name = ".".join(
            [
                get_metrics_prefix(BASE_PREFIX, instance.get("app_env") or "prod"),
                SERVICE_CHECK,
            ]
        )

    def _report_service_check(self, results):
        results_log = (
            "MulesoftAnypointCheck _report_service_check(): Results list size:"
            + str(len(results))
        )
        self._logger.debug(results_log)
        for ep_result in results:
            if ep_result.value == CheckStatus.CRITICAL:
                message = "Check result {}: {}".format(
                    ep_result.value, ep_result.message
                )
                self._logger.error(message)
            message = "Reporting {} ".format(ep_result.name)
            self._logger.debug(message)
            self._reporter.report_metric(ep_result)

    def check(self, instance):
        api_filter = instance.get("api_filter") or "ALL"
        message = "MulesoftAnypointCheck check() START {}".format(api_filter)
        self._logger.debug(message)
        results = self._integration_core.execute()
        self._report_service_check(results)
        message = "MulesoftAnypointCheck check() END {}".format(api_filter)
        self._logger.debug(message)
