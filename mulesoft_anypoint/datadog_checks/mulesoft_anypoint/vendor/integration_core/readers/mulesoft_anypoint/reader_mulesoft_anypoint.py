import json
import os
import platform
from datetime import datetime, timedelta
from subprocess import PIPE, Popen

import yaml

from ...core_remote.auth import AuthConnectionError, BearerAuth
from ...core_remote.remote_http import HttpCaller
from ...integration_core import get_abs_path, get_metrics_prefix
from ...ireader import IReader
from ...ireporter import CheckStatus, ReportItem, ReportItemType

BASE_PREFIX = "ioconnect.mulesoft.anypoint"
SERVICE_CHECK = "can_connect"
LICENSE_CHECK = "license_valid"
BASE_TAGS = ["env_id", "org_id"]


class ReaderMulesoftAnypoint(IReader):
    def __init__(self, logger, config=None, config_path=None):
        if config_path:
            with open(config_path) as config_file:
                self._config = yaml.load(config_file, Loader=yaml.FullLoader)
        if config:
            self._config = config
        self._debug_mode = self._config.get("debug_mode") or False
        filter__format = "API filter: {}".format(
            self._config.get("api_filter") or "all"
        )
        logger.info(filter__format)
        self._logger = logger
        min_collection_interval = self._config.get("min_collection_interval") or 15
        self._prev_execution = (
            datetime.utcnow() - timedelta(seconds=min_collection_interval)
        ).isoformat() + "Z"
        self._current_execution = datetime.utcnow().isoformat() + "Z"
        self._metric_prefix = get_metrics_prefix(
            BASE_PREFIX, self._config.get("app_env") or "prod"
        )
        self._auth = BearerAuth(
            url=self._config["hosts"].get("oauth_provider"),
            client_id=self._config.get("client_id"),
            client_secret=self._config.get("client_secret"),
            attempts_num=self._config.get("connection_attempts_num") or 3,
            wait_time=self._config.get("connection_wait_time") or 2,
        )
        self._http_caller = HttpCaller(self._auth)
        self._results = []
        self._add_to_queue_callback = None

    def set_add_to_queue_callback(self, add_to_queue_callback):
        self._add_to_queue_callback = add_to_queue_callback

    @staticmethod
    def _generate_command(*params):
        command = []
        for param in params:
            if isinstance(param, list):
                for sub_param in param:
                    command.append(sub_param)
            else:
                command.append(param)
        return command

    def _execute_jar(self):
        reader_path = get_abs_path(os.path.join("readers", "mulesoft_anypoint"))
        apis_path = os.path.join(reader_path, "apis")
        reader_jar = os.path.join(
            reader_path, "remote-metric-reader-1.0.0-jar-with-dependencies.jar"
        )
        reader_main = "com.ioconnect.datadog.DatadogApp"
        jmx_options = []
        if self._debug_mode:
            jmx_options = [
                "-Djavax.management.builder.initial=",
                "-Dcom.sun.management.jmxremote",
                "-Dcom.sun.management.jmxremote.port=8855",
                "-Dcom.sun.management.jmxremote.authenticate=false",
                "-Dcom.sun.management.jmxremote.ssl=false",
            ]
        vm_options = ["-Xmx50m"]
        app_params = [
            "--config=" + json.dumps(self._config),
            "--mprefix=" + "ioconnect.mulesoft.anypoint",
            "--dhkey=" + "anypoint",
            "--apis=" + apis_path,
            "--token=" + self._auth.get_access_token(),
            "--prevts=" + self._prev_execution,
            "--currentts=" + self._current_execution,
        ]
        if "windows" in platform.system().lower():
            app_params.append("--logdir=" + "C:\\ProgramData\\Datadog\\logs")
        else:
            app_params.append("--logdir=" + "/var/log/datadog")

        command = self._generate_command(
            "java", jmx_options, vm_options, "-cp", reader_jar, reader_main, app_params
        )

        process = Popen(command, stderr=PIPE, stdout=PIPE, shell=False)
        pid = process.pid
        jar_info = (
            "Jar execution begin:{}"
            "Process PID: {}{}"
            "apis_path: {}{}"
            "reader jar: {}{}"
            "command: {}".format(
                os.linesep,
                pid,
                os.linesep,
                apis_path,
                os.linesep,
                reader_jar,
                os.linesep,
                " ".join(command),
            )
        )
        self._logger.debug(jar_info)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            report_item = ReportItem(json_data=json.loads(line))
            value_with_tags__format = "Reporting: {} type: {} value: {} with tags: {}".format(
                report_item.name,
                report_item.report_type,
                str(report_item.value),
                str(report_item.tags),
            )
            self._logger.debug(value_with_tags__format)
            if report_item.report_type == ReportItemType.SERVICE_CHECK:
                self._results.append(report_item)
            else:
                self._add_to_queue_callback(report_item)

        output, errors = process.communicate()
        output = output.decode("utf-8")
        errors = errors.decode("utf-8")
        jar_info = (
            "Jar Execution result:{}"
            "Process PID: {}{}"
            "return code: {}{}"
            "errors: {}{}"
            "final output: {}".format(
                os.linesep,
                pid,
                os.linesep,
                process.returncode,
                os.linesep,
                errors or "no errors",
                os.linesep,
                output or "empty (already read)",
            )
        )
        self._logger.debug(jar_info)
        return process.returncode

    def get_results(self):
        return self._results

    def execute(self):
        self._logger.debug("ReaderMulesoftAnypoint execute()")
        self._current_execution = datetime.utcnow().isoformat() + "Z"
        self._results = []
        check_result = ReportItem(
            name=".".join([self._metric_prefix, SERVICE_CHECK]),
            report_type=ReportItemType.SERVICE_CHECK,
            value=CheckStatus.OK,
            message="",
        )
        license_result = ReportItem(
            name=".".join([self._metric_prefix, LICENSE_CHECK]),
            report_type=ReportItemType.SERVICE_CHECK,
            value=CheckStatus.OK,
            message="",
        )
        try:
            self._auth.connect(self._http_caller)
        except Exception as ex:
            message = str(ex)
            if isinstance(ex, AuthConnectionError):
                # pylint: disable=E1101
                message += str(ex.response.get_data())
            self._logger.error(message)
            check_result.value = CheckStatus.CRITICAL
            license_result.value = CheckStatus.CRITICAL
            check_result.message = str(ex)
            license_result.message = str(ex)
            self._results.append(check_result)
            return
        return_code = self._execute_jar()
        check_result.message = ""
        if return_code == 0:
            check_result.value = CheckStatus.OK
            license_result.value = CheckStatus.OK
        if return_code == 1:
            check_result.value = CheckStatus.CRITICAL
            message = "Failed running the Remote Metric Reader. See the log for details"
            self._logger.error(message)
            check_result.message = message
        if return_code == 2:
            check_result.value = CheckStatus.CRITICAL
            license_result.value = CheckStatus.CRITICAL
            message = "Invalid license, please reach out to support"
            self._logger.error(message)
            check_result.message = message
            license_result.message = message

        self._results.append(check_result)
        self._results.append(license_result)
        self._prev_execution = self._current_execution
