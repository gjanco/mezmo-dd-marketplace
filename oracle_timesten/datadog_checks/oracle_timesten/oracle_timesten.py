from typing import Any, Dict
import re
import socket
import time
from collections import OrderedDict
import requests
import json

import cx_Oracle
import os
from inspect import currentframe, getframeinfo
from enum import Enum

from datadog_checks.base import AgentCheck
try:
    from datadog_agent import get_config
except ImportError:

    def get_config(key):
        return ""

class State(Enum):
    """
    ACTIVE - The data store is currently the active master data store. Applications may update its replicated tables
    STANDBY - The data store is the standby master data store. Applications may only update its non-replicated tables.
    FAILED - The data store is a failed master data store. No updates are replicated to it.
    IDLE - The data store has not yet been assigned its role in the active standby pair. It cannot be updated by applications or replication. Every store comes up in the IDLE state
    RECOVERING - The store is in the process of synchronizing updates with the active store after a failure.
    """

    ACTIVE = 1
    STANDBY = 2
    FAILED = 3
    IDLE = 4
    RECOVERING = 5


class OracleTimestenCheck(AgentCheck):
    def check(self, instance):
        # type: (Dict[str, Any]) -> None

        # Patch in proxy configuration for requests
        proxyConfig = get_config("proxy")
        if proxyConfig:
            httpProxy = proxyConfig.get("http", None)
            httpsProxy = proxyConfig.get("https", None)

            if httpProxy:
                os.environ["http_proxy"] = httpProxy
            if httpsProxy:
                os.environ["https_proxy"] = httpsProxy

        disable_zzinternal_metrics = instance.get('disable_zzinternal_metrics')
        cf = currentframe()
        os.environ["TIMESTEN_HOME"] = instance.get("timesten_home")
        try:
            connection = cx_Oracle.connect(
                "{0}/{1}@{2}/{3}".format(
                    instance.get("username"),
                    instance.get("password"),
                    instance.get("hostname"),
                    instance.get("database"),
                )
            )

            cursor = connection.cursor()
            snapshots = cursor.arrayvar(str, 1024, 1024)
            cursor.callproc("SYS.TT_STATS.SHOW_SNAPSHOTS", (snapshots,))

            _snaps = list()
            for v in snapshots.getvalue():
                self.log.debug(v)
                try:
                    _snaps.append(int(v.strip().split(" ")[0]))
                except ValueError as e:
                    pass

            m0 = None
            m1 = None
            try:
                m0 = min(_snaps)
                m1 = max(_snaps)
            except Exception:
                rc = cursor.callfunc("SYS.TT_STATS.CAPTURE_SNAPSHOT", int, ["ALL"])
                time.sleep(15)

            rc = cursor.callfunc("SYS.TT_STATS.CAPTURE_SNAPSHOT", int, ["ALL"])
            stats = cursor.arrayvar(str, 1024, 1024)
            rc_current = rc
            self.log.debug(
                "{0} {1} {2}".format(
                    getframeinfo(cf).filename, cf.f_lineno, rc_current
                )
            )
            rc_previous = rc - 1
            self.log.debug(
                "{0} {1} {2}".format(
                    getframeinfo(cf).filename, cf.f_lineno, rc_previous
                )
            )
            cursor.callproc(
                "SYS.TT_STATS.GENERATE_REPORT_TEXT", (rc_previous, rc_current, stats)
            )

            _lines = list()
            for v in stats.getvalue():
                _lines.append(v)

            headers = {
                "Content-type": "application/json",
		"DD-API-KEY": get_config("api_key"),
            }

            active_database = instance.get("database")
            show_all_information = False
            if int(instance.get("verbose_flag")) == int("1"):
                show_all_information = True
            show_sql_information = False
            if int(instance.get("logs_flag")) == int("1"):
                show_sql_information = True

            # Send license metric
            self.gauge(
                        "datadog.marketplace.rapdev.oracle_timesten",
                        "1",
                        tags=[
                            "vendor:rapdev",
                        ],
                    ) 

            self.log.debug(
                "{0} {1} {2}".format(
                    getframeinfo(cf).filename, cf.f_lineno, instance.get("verbose")
                )
            )
            self.log.debug(
                "{0} {1} {2}".format(
                    getframeinfo(cf).filename, cf.f_lineno, instance.get("logs")
                )
            )

            self.log.debug(
                "{0} {1} {2}".format(
                    getframeinfo(cf).filename, cf.f_lineno, instance.get("username")
                )
            )
            self.log.debug(
                "{0} {1} {2}".format(
                    getframeinfo(cf).filename, cf.f_lineno, instance.get("password")
                )
            )
            self.log.debug(
                "{0} {1} {2}".format(
                    getframeinfo(cf).filename, cf.f_lineno, instance.get("hostname")
                )
            )
            self.log.debug(
                "{0} {1} {2}".format(
                    getframeinfo(cf).filename, cf.f_lineno, instance.get("database")
                )
            )

            _indexes = OrderedDict(
                [
                    ("Summary", None),
                    ("Memory Usage and Connections", None),
                    ("Load Profile", None),
                    ("Instance Efficiency Percentage (Target 100%)", None),
                    ("Statement Statistics", None),
                    ("Transaction Statistics", None),
                    ("1. SQL Sort by Executions", None),
                    ("2. SQL Sort by Preparations", None),
                    ("3. Top SQL Command Texts", None),
                    ("PL/SQL Memory Statistics", None),
                    ("Replication Statistics", None),
                    ("Parallel Replication/AWT Statistics", None),
                    ("Log Statistics", None),
                    ("Log Holds", None),
                    ("CheckPoint Statistics", None),
                    ("Cache Group Statistics", None),
                    ("Grid Statistics", None),
                    ("DB Activity Statistics", None),
                    ("Latch Statistics", None),
                    ("Lock Statistics", None),
                    ("XLA Information", None),
                    ("Configuration Parameters", None),
                ]
            )

            self.log.debug(
                "{0} {1} {2}".format(
                    getframeinfo(cf).filename, cf.f_lineno, _indexes
                )
            )

            _arrays = OrderedDict(
                [
                    ("Summary", []),
                    ("Memory Usage and Connections", []),
                    ("Load Profile", []),
                    ("Instance Efficiency Percentage (Target 100%)", []),
                    ("Statement Statistics", []),
                    ("Transaction Statistics", []),
                    ("1. SQL Sort by Executions", []),
                    ("2. SQL Sort by Preparations", []),
                    ("3. Top SQL Command Texts", []),
                    ("PL/SQL Memory Statistics", []),
                    ("Replication Statistics", []),
                    ("Parallel Replication/AWT Statistics", []),
                    ("Log Statistics", []),
                    ("Log Holds", []),
                    ("CheckPoint Statistics", []),
                    ("Cache Group Statistics", []),
                    ("Grid Statistics", []),
                    ("DB Activity Statistics", []),
                    ("Latch Statistics", []),
                    ("Lock Statistics", []),
                    ("XLA Information", []),
                    ("Configuration Parameters", []),
                ]
            )

            self.log.debug(
                "{0} {1} {2}".format(
                    getframeinfo(cf).filename, cf.f_lineno, _arrays
                )
            )

            _re = instance.get("_re")

            self.log.debug("{0} {1} {2}".format(getframeinfo(cf).filename, cf.f_lineno, _re))

            _current = 0
            _previous = 0
            _previous_key = None
            for i, _j in _indexes.items():
                if _current == 0:
                    _current = calculate_index4string(_lines, i)
                    _indexes[i] = _current
                    _previous_key = i
                else:
                    _previous = _current
                    _current = calculate_index4string(_lines, i)
                    _indexes[i] = _current
                    _arrays[_previous_key] = _lines[_previous:_current]
                    _previous_key = i

            _arrays[_previous_key] = _lines[_current:]

            for i, j in _arrays.items():
                # Summary
                if i == "Summary" and show_all_information:

                    _pattern1 = re.compile(_re["Summary 0"])
                    _pattern2 = re.compile(_re["Summary 1"])
                    _pattern3 = re.compile(_re["Summary 2"])

                    reportduration = 0
                    snapid = 0
                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern2, v):
                            snapid = re.match(_pattern2, v).group(1)
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, snapid
                                )
                            )
                        elif re.match(_pattern3, v):
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename,
                                    cf.f_lineno,
                                    reportduration,
                                )
                            )
                            reportduration = re.match(_pattern3, v).group(1)
                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                    self.gauge(
                        "rapdev.oracle_timesten.reportduration",
                        reportduration,
                        tags=[
                            "dbname:{0}".format(active_database),
                            "ttmonitor:summary",
                            "vendor:rapdev",
                        ],
                    )

                # End of Summary
                # Memory Usage and Connections
                elif i == "Memory Usage and Connections" and show_all_information:

                    _pattern1 = re.compile(_re["Memory Usage and Connections"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Memory Usage and Connections"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric1 = "rapdev.oracle_timesten.memory.{0}".format(
                                re.match(_pattern1, v).group(1).strip()
                            )
                            _endvalue = re.match(_pattern1, v).group(3).strip()

                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename,
                                    cf.f_lineno,
                                    _endvalue,
                                )
                            )

                            self.gauge(
                                _metric1,
                                _endvalue,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:memory_usage_and_connections",
                                    "vendor:rapdev",
                                ],
                            )
                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of Memory Usage and Connections
                # Load Profile
                elif i == "Load Profile" and show_all_information:

                    _pattern1 = re.compile(_re["Load Profile 0"])
                    _pattern2 = re.compile(_re["Load Profile 1"])
                    _pattern3 = re.compile(_re["Load Profile 2"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Load Profile 0"],
                        )
                    )
                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Load Profile 1"],
                        )
                    )
                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Load Profile 2"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric1 = "rapdev.oracle_timesten.{0}{1}".format(
                                "".join(
                                    re.match(_pattern1, v).group(1).strip().split(" ")
                                ),
                                "PerSec",
                            )
                            _metric2 = "rapdev.oracle_timesten.{0}{1}".format(
                                "".join(
                                    re.match(_pattern1, v).group(1).strip().split(" ")
                                ),
                                "PerTxn",
                            )
                            _persec = re.match(_pattern1, v).group(2).strip()
                            _pertrx = re.match(_pattern1, v).group(3).strip()

                            self.gauge(
                                _metric1,
                                _persec,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:load_profile",
                                    "vendor:rapdev",
                                ],
                            )

                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _persec
                                )
                            )

                            self.gauge(
                                _metric2,
                                _pertrx,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:load_profile",
                                    "vendor:rapdev",
                                ],
                            )

                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric2
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _pertrx
                                )
                            )

                        elif re.match(_pattern2, v):
                            _metric1 = "rapdev.oracle_timesten.{0}".format(
                                "".join(
                                    re.match(_pattern2, v).group(1).strip().split(" ")
                                )
                            )
                            _persec = re.match(_pattern2, v).group(2).strip()

                            self.gauge(
                                _metric1,
                                _persec,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:load_profile",
                                    "vendor:rapdev",
                                ],
                            )

                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _persec
                                )
                            )

                        elif re.match(_pattern3, v):
                            _metric = re.match(_pattern3, v).group(1).strip()
                            _metric1 = "rapdev.oracle_timesten.{0}".format(
                                "".join(_metric.split(" "))
                            )
                            _persec = re.match(_pattern3, v).group(2).strip()

                            self.gauge(
                                _metric1,
                                _persec,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:load_profile",
                                    "vendor:rapdev",
                                ],
                            )

                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _persec
                                )
                            )
                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of Load Profile
                # Instance Efficiency Percentage (Target 100%)
                elif i == "Instance Efficiency Percentage (Target 100%)":

                    _pattern1 = re.compile(
                        _re["Instance Efficiency Percentage (Target 100%)"]
                    )

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Instance Efficiency Percentage (Target 100%)"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric = "".join(
                                re.match(_pattern1, v)
                                .group(1)
                                .replace("%", "")
                                .replace("/", "")
                                .split(" ")
                            )
                            _metric1 = "rapdev.oracle_timesten.{0}{1}".format(_metric, "Perc")
                            _metric = "".join(
                                re.match(_pattern1, v)
                                .group(3)
                                .replace("%", "")
                                .replace("/", "")
                                .split(" ")
                            )
                            _metric2 = "rapdev.oracle_timesten.{0}{1}".format(_metric, "Perc")

                            _ratio1 = re.match(_pattern1, v).group(2).strip()
                            _ratio2 = re.match(_pattern1, v).group(4).strip()

                            self.gauge(
                                _metric1,
                                _ratio1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:instance_efficiency_percentage",
                                    "vendor:rapdev",
                                ],
                            )

                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _ratio1
                                )
                            )

                            self.gauge(
                                _metric2,
                                _ratio2,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:instance_efficiency_percentage",
                                    "vendor:rapdev",
                                ],
                            )

                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric2
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _ratio2
                                )
                            )
                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of Instance Efficiency Percentage (Target 100%)
                # Statement Statistics
                elif i == "Statement Statistics" and show_all_information:

                    _pattern1 = re.compile(_re["Statement Statistics"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Statement Statistics"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric1 = "rapdev.oracle_timesten.{0}".format(
                                re.match(_pattern1, v).group(1).strip()
                            )

                            if 'zzinternal' in _metric1 and disable_zzinternal_metrics:
                                continue

                            _value1 = re.match(_pattern1, v).group(2).strip()
                            _source1 = "Source:{0}".format(
                                re.match(_pattern1, v).group(4).strip()
                            )
                            _source2 = "Source:{0}".format(
                                re.match(_pattern1, v).group(5).strip()
                            )

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:statement_statistics",
                                    "vendor:rapdev",
                                    _source1,
                                    _source2,
                                ],
                            )

                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of Statement Statistics
                # Transaction Statistics
                elif i == "Transaction Statistics" and show_all_information:

                    _pattern1 = re.compile(_re["Transaction Statistics"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Transaction Statistics"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric1 = "rapdev.oracle_timesten.{0}".format(
                                re.match(_pattern1, v).group(1).strip()
                            )

                            if 'zzinternal' in _metric1 and disable_zzinternal_metrics:
                                continue

                            _value1 = re.match(_pattern1, v).group(2).strip()
                            _source1 = "Source:{0}".format(
                                re.match(_pattern1, v).group(4).strip()
                            )
                            _source2 = "Source:{0}".format(
                                re.match(_pattern1, v).group(5).strip()
                            )

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:transaction_statistics",
                                    "vendor:rapdev",
                                    _source1,
                                    _source2,
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of Transaction Statistics
                # 1. SQL Sort by Executions'
                elif i == "1. SQL Sort by Executions" and show_all_information:

                    _pattern1 = re.compile(_re["1. SQL Sort by Executions"])
                    _pattern2 = re.compile("^(.*) (ttSQLCmdCacheInfo)$")
                    _metric1 = "rapdev.oracle_timesten.{0}".format("SQL_Sort_by_Executions")
                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _value1 = re.match(_pattern1, v).group(1).strip()
                            _command_id = re.match(_pattern1, v).group(3).strip()
                            _text = re.match(_pattern1, v).group(4).strip()
                            _command1 = re.match(_pattern2, _text).group(1).strip()
                            _source1 = re.match(_pattern2, _text).group(2).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:SQL_Sort_by_Executions",
                                    "vendor:rapdev",
                                    "cmdID:{0}".format(_command_id),
                                    "cmdText:{0}".format(_command1),
                                    "Source:{0}".format(_source1),
                                ],
                            )

                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of 1. SQL Sort by Executions'
                # 2. SQL Sort by Preparations
                elif i == "2. SQL Sort by Preparations" and show_all_information:

                    _pattern1 = re.compile(_re["2. SQL Sort by Preparations"])

                    _pattern2 = re.compile("^(.*) (ttSQLCmdCacheInfo)$")

                    _metric1 = "rapdev.oracle_timesten.{0}".format("SQL_Sort_by_Preparations")
                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _value1 = re.match(_pattern1, v).group(1).strip()
                            _command_id = re.match(_pattern1, v).group(3).strip()
                            _text = re.match(_pattern1, v).group(4).strip()
                            _command1 = re.match(_pattern2, _text).group(1).strip()
                            _source1 = re.match(_pattern2, _text).group(2).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:SQL_Sort_by_Preparations",
                                    "vendor:rapdev",
                                    "cmdID:{0}".format(_command_id),
                                    "cmdText:{0}".format(_command1),
                                    "Source:{0}".format(_source1),
                                ],
                            )
                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of 2. SQL Sort by Preparations
                # 3. Top SQL Command Texts
                elif (
                    i == "3. Top SQL Command Texts"
                    and show_all_information
                    and show_sql_information
                ):

                    _pattern1 = re.compile(_re["3. Top SQL Command Texts"])

                    _metric1 = "rapdev.oracle_timesten.{0}".format("Top_SQL_Command_Texts")

                    contents = list()
                    log_entries = list()
                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):

                            _sql_id = re.match(_pattern1, v).group(1).strip()
                            _command1 = re.match(_pattern1, v).group(2).strip()

                            item = {
                                "SQLID": _sql_id,
                                "SQLText": _command1,
                                "tag1": "dbname:{0}".format(active_database),
                                "tag2": "ttmonitor:Top_SQL_Command_Texts",
                            }

                            log_entries.append(item)

                    log_entries = {
                        "ddsource": "oracletimesten",
                        "ddtags": "service:timesten,vendor:rapdev,dbname:{0}".format(
                            active_database
                        ),
                        "hostname": socket.gethostname(),
                        "message": json.dumps(log_entries, indent=2),
                    }

                    snapshots_file = {
                        "ddsource": "oracletimesten",
                        "ddtags": "service:timesten,vendor:rapdev,dbname:{0}".format(
                            active_database
                        ),
                        "hostname": socket.gethostname(),
                        "message": list("{0}\n".format(v) for v in _lines),
                    }

                    contents.append(snapshots_file)
                    contents.append(log_entries)

                    try:
                        response = requests.post(
                            instance.get("endpoint"),
                            headers=headers,
                            data=json.dumps(contents, indent=2),
                        )

                        print(response)
                    except Exception as e:
                        self.log.error("Error sending logs: {}".format(str(e)))

                # End of 3. Top SQL Command Texts
                # PL/SQL Memory Statistics
                elif i == "PL/SQL Memory Statistics" and show_all_information:

                    _pattern1 = re.compile(_re["PL/SQL Memory Statistics"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["PL/SQL Memory Statistics"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric1 = "rapdev.oracle_timesten.{0}".format(
                                re.match(_pattern1, v).group(1).strip()
                            )
                            _value1 = re.match(_pattern1, v).group(3).strip()
                            _source1 = re.match(_pattern1, v).group(5).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:pl_sql_memory_statistics",
                                    "vendor:rapdev",
                                    "Source:{0}".format(_source1),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of PL/SQL Memory Statistics
                # Replication Statistics
                elif i == "Replication Statistics":

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Replication Statistics"],
                        )
                    )

                    _pattern1 = re.compile(_re["Replication Statistics"])
                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):

                            _peer = re.match(_pattern1, v).group(11)

                            _metric1 = "rapdev.oracle_timesten.{0}".format("Log_Send_LSN(B)")
                            _value1 = re.match(_pattern1, v).group(1).strip()

                            _derived_value1 = _value1.split("/")[0]
                            _derived_value2 = _value1.split("/")[1]

                            self.gauge(
                                _metric1,
                                _derived_value2,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "peer:{0}".format(_peer),
                                    "LogFileNumber:{0}".format(_derived_value1),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename,
                                    cf.f_lineno,
                                    _derived_value1,
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename,
                                    cf.f_lineno,
                                    _derived_value2,
                                )
                            )

                            _metric1 = "rapdev.oracle_timesten.{0}".format("Log_Send_LSN(E)")
                            _value1 = re.match(_pattern1, v).group(2).strip()

                            _derived_value1 = _value1.split("/")[0]
                            _derived_value2 = _value1.split("/")[1]

                            self.gauge(
                                _metric1,
                                _derived_value2,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "peer:{0}".format(_peer),
                                    "LogFileNumber:{0}".format(_derived_value1),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename,
                                    cf.f_lineno,
                                    _derived_value1,
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename,
                                    cf.f_lineno,
                                    _derived_value2,
                                )
                            )

                            _metric1 = "rapdev.oracle_timesten.{0}".format("Log_Behind(B)")
                            _value1 = re.match(_pattern1, v).group(3).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "peer:{0}".format(_peer),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )

                            _metric1 = "rapdev.oracle_timesten.{0}".format("Log_Behind(E)")
                            _value1 = re.match(_pattern1, v).group(4).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "peer:{0}".format(_peer),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )

                            _metric1 = "rapdev.oracle_timesten.{0}".format("RPS(B)")
                            _value1 = re.match(_pattern1, v).group(5).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "peer:{0}".format(_peer),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )

                            _metric1 = "rapdev.oracle_timesten.{0}".format("RPS(E)")
                            _value1 = re.match(_pattern1, v).group(6).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "peer:{0}".format(_peer),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )

                            _metric1 = "rapdev.oracle_timesten.{0}".format("TPS(B)")
                            _value1 = re.match(_pattern1, v).group(7).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "peer:{0}".format(_peer),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )

                            _metric1 = "rapdev.oracle_timesten.{0}".format("TPS(E)")
                            _value1 = re.match(_pattern1, v).group(8).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "peer:{0}".format(_peer),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )

                            _metric1 = "rapdev.oracle_timesten.{0}".format("Latency(B)")
                            _value1 = re.match(_pattern1, v).group(9).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "peer:{0}".format(_peer),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )

                            _metric1 = "rapdev.oracle_timesten.{0}".format("Latency(E)")
                            _value1 = re.match(_pattern1, v).group(10).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "peer:{0}".format(_peer),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of Replication Statistics
                # Parallel Replication/AWT Statistics
                elif i == "Parallel Replication/AWT Statistics":

                    _pattern1 = re.compile(_re["Parallel Replication/AWT Statistics"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Parallel Replication/AWT Statistics"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric1 = "rapdev.oracle_timesten.awt.{0}".format(
                                re.match(_pattern1, v).group(1).strip()
                            )

                            if 'zzinternal' in _metric1 and disable_zzinternal_metrics:
                                continue

                            _value1 = re.match(_pattern1, v).group(2).strip()
                            _peer = re.match(_pattern1, v).group(4).strip()
                            _source1 = re.match(_pattern1, v).group(5).strip()
                            _source2 = re.match(_pattern1, v).group(6).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:replication_statistics",
                                    "vendor:rapdev",
                                    "repPeer:{0}".format(_peer),
                                    "Source:{0}".format(_source1),
                                    "Source:{0}".format(_source2),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _peer
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source2
                                )
                            )

                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of Parallel Replication/AWT Statistics
                # Log Statistics
                elif i == "Log Statistics" and show_all_information:

                    _pattern1 = re.compile(_re["Log Statistics"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Log Statistics"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric1 = "rapdev.oracle_timesten.{0}".format(
                                re.match(_pattern1, v).group(1).strip()
                            )

                            if 'zzinternal' in _metric1 and disable_zzinternal_metrics:
                                continue

                            _value1 = re.match(_pattern1, v).group(2).strip()
                            _source1 = "Source:{0}".format(
                                re.match(_pattern1, v).group(4).strip()
                            )
                            _source2 = "Source:{0}".format(
                                re.match(_pattern1, v).group(5).strip()
                            )

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:log_statistics",
                                    _source1,
                                    "vendor:rapdev",
                                    _source2,
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source2
                                )
                            )
                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of Log Statistics
                # Log Holds
                elif i == "Log Holds" and show_all_information:

                    _pattern1 = re.compile(_re["Log Holds"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename, cf.f_lineno, _re["Log Holds"]
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _text = " ".join(
                                re.match(_pattern1, v).group(1).strip().split()
                            )

                            _metric1 = "rapdev.oracle_timesten.{0}".format(
                                _text.split(" ")[0].strip()
                            )

                            if 'zzinternal' in _metric1 and disable_zzinternal_metrics:
                                continue

                            _value1 = _text.split(" ")[2].strip()
                            _desc1 = _text.split(" ")[3].strip()

                            _source1 = re.match(_pattern1, v).group(2).strip()
                            _source2 = re.match(_pattern1, v).group(3).strip()

                            _derived_value1 = _value1.split("/")[0]
                            _derived_value2 = _value1.split("/")[1]

                            self.gauge(
                                _metric1,
                                _derived_value2,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:log_holds",
                                    "vendor:rapdev",
                                    "Desc:{0}".format(_desc1),
                                    "LogFileNumber:{0}".format(_derived_value1),
                                    "Source {0}".format(_source1),
                                    "Source {0}".format(_source2),
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _desc1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source2
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename,
                                    cf.f_lineno,
                                    _derived_value1,
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename,
                                    cf.f_lineno,
                                    _derived_value2,
                                )
                            )

                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of Log Holds
                # CheckPoint Statistics
                elif i == "CheckPoint Statistics" and show_all_information:

                    _pattern1 = re.compile(_re["CheckPoint Statistics"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["CheckPoint Statistics"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric1 = "rapdev.oracle_timesten.{0}".format(
                                re.match(_pattern1, v).group(1).strip()
                            )

                            if 'zzinternal' in _metric1 and disable_zzinternal_metrics:
                                continue

                            _value1 = re.match(_pattern1, v).group(2).strip()
                            _source1 = re.match(_pattern1, v).group(4).strip()
                            _source2 = re.match(_pattern1, v).group(5).strip()

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:checkpoint_statistics",
                                    "vendor:rapdev",
                                    _source1,
                                    _source2,
                                ],
                            )

                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source2
                                )
                            )

                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of CheckPoint Statistics
                elif i == "Cache Group Statistics" and show_all_information:
                    pass

                # DB Activity Statistics
                elif i == "DB Activity Statistics":

                    _pattern1 = re.compile(_re["DB Activity Statistics"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["DB Activity Statistics"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric1 = "rapdev.oracle_timesten.{0}".format(
                                re.match(_pattern1, v).group(1).strip()
                            )

                            if 'zzinternal' in _metric1 and disable_zzinternal_metrics:
                                continue

                            _value1 = re.match(_pattern1, v).group(2).strip()
                            _source1 = "Source:{0}".format(
                                re.match(_pattern1, v).group(4).strip()
                            )
                            _source2 = "Source:{0}".format(
                                re.match(_pattern1, v).group(5).strip()
                            )

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:db_activity_statistics",
                                    "vendor:rapdev",
                                    _source1,
                                    _source2,
                                ],
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source2
                                )
                            )

                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of DB Activity Statistics
                # Lock Statistics
                elif i == "Lock Statistics" and show_all_information:

                    _pattern1 = re.compile(_re["Lock Statistics"])

                    self.log.debug(
                        "{0} {1} {2}".format(
                            getframeinfo(cf).filename,
                            cf.f_lineno,
                            _re["Lock Statistics"],
                        )
                    )

                    for v1 in j:
                        v = v1.strip()
                        if re.match(_pattern1, v):
                            _metric1 = "rapdev.oracle_timesten.{0}".format(
                                re.match(_pattern1, v).group(1).strip()
                            )

                            if 'zzinternal' in _metric1 and disable_zzinternal_metrics:
                                continue

                            _value1 = re.match(_pattern1, v).group(2).strip()
                            _source1 = "Source:{0}".format(
                                re.match(_pattern1, v).group(4).strip()
                            )
                            _source2 = "Source:{0}".format(
                                re.match(_pattern1, v).group(5).strip()
                            )

                            self.gauge(
                                _metric1,
                                _value1,
                                tags=[
                                    "dbname:{0}".format(active_database),
                                    "ttmonitor:lock_statistics",
                                    _source1,
                                    "vendor:rapdev",
                                    _source2,
                                ],
                            )

                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _metric1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _value1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source1
                                )
                            )
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, _source2
                                )
                            )

                        else:
                            self.log.debug(
                                "{0} {1} {2}".format(
                                    getframeinfo(cf).filename, cf.f_lineno, v1
                                )
                            )

                # End of Lock Statistics
                elif i == "Configuration Parameters" and show_all_information:
                    for v1 in j:
                        self.log.debug(
                            "{0} {1} {2}".format(
                                getframeinfo(cf).filename, cf.f_lineno, v1
                            )
                        )
                else:
                    for v1 in j:
                        self.log.debug(
                            "{0} {1} {2}".format(
                                getframeinfo(cf).filename, cf.f_lineno, v1
                            )
                        )

            if m0 is not None and m1 is not None:
                cursor.callproc("SYS.TT_STATS.DROP_SNAPSHOTS_RANGE", (m0, m1 - 1))
                connection.commit()

            # Send the metrics for holds on log files
            self._send_active_db_hold_total(cursor, active_database)
            self._send_active_db_hold_by_type(cursor, active_database)

            # Send replication state
            if instance.get("show_replication_state"):
                self._send_replication_state(cursor, active_database)

            cursor.close()
            connection.close()
            self.service_check("rapdev.oracle_timesten", self.OK, 
                tags=[
                    "dbname:{0}".format(active_database),
                    "vendor:rapdev",
                ],
            )
        except Exception as e:
            # Ideally we'd use a more specific message...
            self.service_check("rapdev.oracle_timesten", self.CRITICAL, message=str(e),
                tags=[
                    "dbname:{0}".format(active_database),
                    "vendor:rapdev",
                ],
            )

    def _send_active_db_hold_total(self, cursor, active_database):
        """
        Get's and sends the active database's "hold" value in megabytes.
        The "hold" fields (HOLDLFN/HOLDLFO) describe the oldest log records that replication has NOT yet sent to a peer.
        If some component of TimesTen places a "hold" on a log, it cannot delete any log records newer than the "hold"
        LFN/LFO.
        :param cursor:          a cursor to execute sql queries
        :param active_database: the active database
        :return: None
        """
        sql = """
            SELECT (writeLFN-holdLFN)*paramValue
                FROM V$BOOKMARK, V$CONFIGURATION 
                WHERE lower(paramName) = 'logfilesize'
            """

        try:
            cursor.execute(sql)

            data = cursor.fetchone()

            if data:
                self.gauge(
                    "rapdev.oracle_timesten.total_hold",
                    data[0],
                    tags=[
                        "dbname:{0}".format(active_database),
                        "ttmonitor:holds",
                        "vendor:rapdev",
                    ],
                )
            else:
                self.log.warning(
                    "No data was returned while attempting to retrieve total hold"
                )
        except Exception as e:
            self.log.error(
                "Unable to get the total hold value. Error: {}".format(str(e))
            )

    def _send_active_db_hold_by_type(self, cursor, active_database):
        """
        Sends the total amount of data in MB that each type is holding.
        This includes the two checkpoints and all replication peers.
        :param cursor:          the cursor
        :param active_database: the database to query
        :return: None
        """
        sql = """
            SELECT type, description, (b.writeLFN - h.holdLFN) * c.paramValue
                FROM V$LOG_HOLDS h, V$BOOKMARK b, V$CONFIGURATION c 
                WHERE lower(c.paramName) = 'logfilesize'
             """

        try:
            cursor.execute(sql)

            data = cursor.fetchall()

            if data:
                for row in data:
                    self.gauge(
                        "rapdev.oracle_timesten.hold.{}".format(row[0].strip().lower()),
                        row[2],
                        tags=[
                            "dbdescription:{}".format(row[1]),
                            "dbname:{0}".format(active_database),
                            "ttmonitor:holds",
                            "vendor:rapdev",
                        ],
                    )
            else:
                self.log.warning(
                    "No data was received while attempting to get hold data by type"
                )
        except Exception as e:
            self.log.error("Unable to get hold data by type. Error: {}".format(str(e)))

    def _send_replication_state(self, cursor, active_database):
        """
        Get the replication state of the active database. This will need to be mapped to values to be sent to Datadog.
        :param cursor:          the cursor
        :param active_database: the active database
        :return: None
        """
        # We have to use EXECUTE IMMEDIATE since Cursor.callproc does not handle builtin procedures well.
        sql = """
              DECLARE
                TYPE ttRepStateGet_record IS RECORD
                  (state varchar2(20));
                TYPE ttRepStateGet_table IS TABLE OF ttRepStateGet_record;
              v_ttState ttRepStateGet_table;
              BEGIN
                EXECUTE IMMEDIATE 'CALL ttRepStateGet'
                  BULK COLLECT into v_ttState;
                DBMS_OUTPUT.PUT_LINE (v_ttState(1).state);
              end;
              """

        try:
            # We have to enable output since it is disabled by default
            cursor.callproc("dbms_output.enable")
            cursor.execute(sql)

            state = None
            attempts = 3
            status = cursor.var(cx_Oracle.NUMBER)
            line = cursor.var(cx_Oracle.STRING)

            cursor.callproc("dbms_output.get_line", (line, status))

            while attempts > 0:
                if status.getvalue() == 0:  # status is 1 when no lines are in the buffer.
                    state = line.getvalue()

                    state = (
                        state if state in [_state.name for _state in State] else None
                    )

                    if state:
                        self.gauge(
                            "rapdev.oracle_timesten.replication_state",
                            State[state].value,
                            tags=[
                                "dbname:{}".format(active_database),
                                "ttmonitor:replication_state",
                                "state:{}".format(state),
                                "vendor:rapdev",
                            ],
                        )
                    else:
                        self.log.warning(
                            "Unable to retrieve the replication state. Retrieved '{}' from the output line".format(
                                state
                            )
                        )
                    # Break here since we've sent the metrics or don't know what output we are reading.
                    break
                else:
                    self.log.warning(
                        "Unable to retrieve the replication state. Attempt {} out of 3".format(
                            attempts
                        )
                    )

                attempts -= 1

            if state:
                self._send_individual_replication_state_metrics(
                    State[state], active_database
                )
        except Exception as e:
            self.log.error("Unable to get replication state. Error: {}".format(str(e)))

    def _send_individual_replication_state_metrics(
        self, current_state, active_database
    ):
        """
        Sends the current state metric as a flag (1 on, 0 off). Used in a table-like dashboard.
        :param current_state: the current replication state (State) of the active database.
        :return: None
        """
        for state in State:
            self.gauge(
                "rapdev.oracle_timesten.replication_state.{}".format(state.name),
                1 if current_state == state else 0,
                tags=[
                    "dbname:{}".format(active_database),
                    "ttmonitor:replication_state",
                    "state:{}".format(state.name),
                    "vendor:rapdev",
                ],
            )


def calculate_index4string(input_array, target_string):
    _input_array = list()
    for v in input_array:
        _input_array.append(v.lower())
    _index = None
    try:
        if target_string.lower() in _input_array:
            _index = _input_array.index(target_string.lower())
        else:
            _pattern = re.compile("^" + target_string.lower())
            for v in _input_array:
                if re.match(_pattern, v):
                    _index = _input_array.index(v.lower())
    except ValueError:
        _index = None
    return _index
