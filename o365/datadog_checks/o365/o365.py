# (C) RapDev, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import os, io, csv, json, traceback
import requests as rq # SKIP_HTTP_VALIDATION

from .sharepy import SharePointSession
from urllib.parse import urlparse
from collections import deque
from datetime import date, datetime, timedelta, timezone
from random import choice
from string import ascii_letters
from datadog_checks.base import AgentCheck
from dateutil.parser import parse
from datadog_checks.base import AgentCheck

try:
    from datadog_agent import get_config
except ImportError:
    def get_config(key):
        return ""

REQ_TIMEOUT   = 30
MAX_FILE_SIZE = 4000000

REQUIRED_TAGS = [
    "vendor:rapdev",
]

REQUIRED_SETTINGS = [
    "tenant_id",
    "client_id",
    "client_secret",
]

REPORTS = {
    "Activations": {
        "Reports.Activations.ActivationCounts": "ActivationsActivationCounts",
        "Reports.Activations.UserCounts": "ActivationsUserCounts",
    },
    "GroupsActivity": {
        "Reports.GroupsActivity.ActivityCounts": "GroupsActivityActivityCounts",
        "Reports.GroupsActivity.GroupCounts": "GroupsActivityGroupCounts",
        "Reports.GroupsActivity.Storage": "GroupsActivityStorage",
        "Reports.GroupsActivity.FileCounts": "GroupsActivityFileCounts",
    },
    "Outlook": {
        "Reports.OutlookActivity.ActivityCounts": "OutlookActivityActivityCounts",
        "Reports.OutlookActivity.UserCounts": "OutlookActivityUserCounts",
        "Reports.OutlookAppUsage.UserCounts": "OutlookAppUsageAppsUserCounts",
        "Reports.OutlookAppUsage.VersionsUserCounts": "OutlookAppUsageVersionsUserCounts",
        "Reports.OutlookMailboxUsage.Detail": "OutlookMailboxUsageDetail",
        "Reports.OutlookMailboxUsage.MailboxCounts": "OutlookMailboxUsageMailboxCounts",
        "Reports.OutlookMailboxUsage.QuotaStatusMailboxCounts": "OutlookMailboxUsageQuotaStatusMailboxCounts",
        "Reports.OutlookMailboxUsage.Storage": "OutlookMailboxUsageStorage",        
    },
    "Teams": {
        "Reports.TeamsDeviceUsage.UserCounts": "TeamsDeviceUsageUserCounts",
        "Reports.TeamsUserActivity.UserCounts": "TeamsUserActivityUserCounts",
    },
    "OneDrive": {
        "Reports.OneDriveActivity.UserCounts": "OneDriveActivityUserCounts",
        "Reports.OneDriveActivity.FileCounts": "OneDriveActivityFileCounts",
        "Reports.OneDriveUsage.AccountCounts": "OneDriveUsageAccountCounts",
        "Reports.OneDriveUsage.FileCounts": "OneDriveUsageFileCounts",
        "Reports.OneDriveUsageAccountDetail": "OneDriveUsageAccountDetail",
    },
    "SharePoint": {
        "Reports.SharePointActivity.FileCounts": "SharePointActivityFileCounts",
        "Reports.SharePointActivity.UserCounts": "SharePointActivityUserCounts",
        "Reports.SharePointActivity.Pages": "SharePointActivityPages",
        "Reports.SharePointUsageFileCounts": "SharePointUsageFileCounts",
        "Reports.SharePointUsageSiteCounts": "SharePointUsageSiteCounts",
        "Reports.SharePointUsagePages": "SharePointUsagePages",
        "Reports.SharePointUsageDetail": "SharePointUsageDetail",
    },
    "Yammer": {
        "Reports.YammerActivity.ActivityCounts": "YammerActivityActivityCounts",
        "Reports.YammerActivity.UserCounts": "YammerActivityUserCounts",
        "Reports.YammerDeviceUsage.UserCounts": "YammerDeviceUsageUserCounts",
        "Reports.YammerGroupsActivity.GroupCounts": "YammerGroupsActivityGroupCounts",
        "Reports.YammerGroupsACtivity.ActivityCounts": "YammerGroupsActivityActivityCounts",
    },
    "Skype": {
        "Reports.SkypeActivity.ActivityCounts": "SkypeActivityActivityCounts",
        "Reports.SkypeActivity.UserCounts": "SkypeActivityUserCounts",
        "Reports.SkypeDeviceUsage.UserCounts": "SkypeDeviceUsageUserCounts",
        "Reports.SkypeOrganizerActivity.ActivityCounts": "SkypeOrganizerActivityActivityCounts",
        "Reports.SkypeOrganizerActivity.UserCounts": "SkypeOrganizerActivityUserCounts",
        "Reports.SkypeOrganizerActivity.MinuteCounts": "SkypeOrganizerActivityMinuteCounts",
        "Reports.SkypeParticipantActivity.ActivityCounts": "SkypeParticipantActivityActivityCounts",
        "Reports.SkypeParticipantActivity.UserCounts": "SkypeParticipantActivityUserCounts",
        "Reports.SkypeParticipantActivity.MinuteCounts": "SkypeParticipantActivityMinuteCounts",
        "Reports.SkypePeerToPeerActivity.ActivityCounts": "SkypePeerToPeerActivityActivityCounts",
        "Reports.SkypePeerToPeerActivity.UserCounts": "SkypePeerToPeerActivityUserCounts",
        "Reports.SkypePeerToPeerActivity.MinuteCounts": "SkypePeerToPeerActivityMinuteCounts",        
    },
}

SHAREPOINT_PERF_METRICS = [
    "IisLatency",
    "spRequestDuration",
    "QueryCount",
    "QueryDuration",
    "CPUDuration",
    # "ClaimsAuthenticationTime",
    # "ClaimsAuthenticationTimeType",
    "Network-WindowScaleOption",
    "Network-PacketRetransmitCount",
    "Network-SmoothedRoundTripTime",
]

class O365Check(AgentCheck):
    def check(self, instance):
        self.metric_prefix = "rapdev.o365"
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.metric_prefix)
        self.service_check_name = "{}.status".format(self.metric_prefix)
        self.today = datetime.now(tz=timezone.utc).date()
        self.reports_token = {}
        self.synthetics_token = {}
        self.management_token = {}
        self.report_refresh_column = "\ufeffReport Refresh Date"
        self.synthetic_email_api_key = "KIcolOzDSn2tdHppEnCmF5bVbAGSHDiN43eWkcWR"
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.tags.append("{}:{}".format("tenant_id", self.instance.get("tenant_id")))

        self.set_proxies()

        enabled = self.instance.get("enable_synthetics", True)
        self.do_check("Synthetics.Authorization", "set_synthetics_token", enabled)
        self.do_check("Synthetics.Outlook.Calendar", "get_calendar_synthetic_metrics", enabled)
        self.do_check("Synthetics.OneDrive.File", "get_onedrive_synthetic_metrics", enabled)
        self.do_check("Synthetics.Teams.Chat", "get_teams_synthetic_metrics", enabled)
        self.do_check("Synthetics.SharePoint.Site", "get_sharepoint_synthetic_metrics", enabled)

        self.do_check("Reports.Authorization", "set_reports_token")
        self.do_check("Reports.ActiveUsers.ServiceUserCounts", "ActiveUsersServiceUserCounts")

        if self.instance.get("probe_mode", True):
            self.log.info("instance configured in probe mode; reports skipped")
            return

        self.do_check("Reports.ActiveUsers.UserCounts", "ActiveUsersUserCounts")

        enabled = self.instance.get("enable_activations", True)
        for report_name, report_func in REPORTS["Activations"].items():
            self.do_check(report_name, report_func, enabled)

        enabled = self.instance.get("enable_groups", True)
        for report_name, report_func in REPORTS["GroupsActivity"].items():
            self.do_check(report_name, report_func, enabled)

        enabled = self.instance.get("enable_outlook", True)
        for report_name, report_func in REPORTS["Outlook"].items():
            self.do_check(report_name, report_func, enabled)

        enabled = self.instance.get("enable_teams", True)
        for report_name, report_func in REPORTS["Teams"].items():
            self.do_check(report_name, report_func, enabled)

        enabled = self.instance.get("enable_onedrive", True)
        for report_name, report_func in REPORTS["OneDrive"].items():
            self.do_check(report_name, report_func, enabled)

        enabled = self.instance.get("enable_sharepoint", True)
        for report_name, report_func in REPORTS["SharePoint"].items():
            self.do_check(report_name, report_func, enabled)

        enabled = self.instance.get("enable_yammer", True)
        for report_name, report_func in REPORTS["Yammer"].items():
            self.do_check(report_name, report_func, enabled)

        enabled = self.instance.get("enable_skype", True)
        for report_name, report_func in REPORTS["Skype"].items():
            self.do_check(report_name, report_func, enabled)

        enabled = self.instance.get("enable_synthetic_email", True)
        self.do_check("Synthetics.Email", "get_email_synthetic_metrics", enabled)

        enabled = self.instance.get("enable_incidents", True)
        self.do_check("Messages.Authorization", "set_management_token", enabled)
        self.do_check("Messages.Incidents", "get_servicecomms_incidents", enabled)

        return

    def set_proxies(self):
        proxy_config = get_config("proxy")
        if proxy_config:
            http_proxy = proxy_config.get("http", None)
            https_proxy = proxy_config.get("https", None)

            if http_proxy:
                os.environ["http_proxy"] = http_proxy
            if https_proxy:
                os.environ["https_proxy"] = https_proxy
        return

    def do_check(self, check, function, enabled=True):
        check_tags = self.tags.copy()
        check_tags.append("{}:{}".format("check", check))

        if not enabled:
            self.service_check(self.service_check_name, AgentCheck.UNKNOWN, tags=check_tags)
            return

        check_func = getattr(self, function)
        try:
            check_func()
        except Exception as e:
            m = "[{}]: {}".format(check, e)
            self.log.error(m)
            self.log.error(traceback.format_exc())
            self.service_check(self.service_check_name, AgentCheck.CRITICAL, message=m, tags=check_tags)
        else:
            self.service_check(self.service_check_name, AgentCheck.OK, tags=check_tags )
        return

    def parse_present(self, value):
        if not value:
            return float(0)
        else:
            return float(1)

    def parse_float(self, value):
        if not value:
            return float(0)
        try:
            parsed_value = float(value)
        except ValueError:
            return float(0)
        return parsed_value

    def parse_boolean(self, value):
        if not value:
            return float(0)

        if value == True:
            return float(1)
        elif value.lower() == "true":
            return float(1)
        elif value.lower() == "yes":
            return float(1)
        elif value.lower() == "1":
            return float(1)
        else:
            return float(0)

    def parse_elapsed_days(self, value):
        if not self.today:
            self.today = datetime.now(tz=timezone.utc).date()
        
        try:
            parsed_value = parse(value)
        except ValueError:
            return float(-1)
        except TypeError:
            return float(-1)

        dt = self.today - parsed_value.date()
        return float(dt.days)   

    def csv_row_to_metrics(self, row=None, tag_fields={}, row_fields=[], tags={}):
        metric_tags = tags.copy()

        for column, tag_key in tag_fields.items():
            tag_val = row.get(column, None)
            metric_tags.append("{}:{}".format(tag_key, tag_val))

        for definition in row_fields:
            column_name = definition.get("column_name")
            metric_name = definition.get("metric_name")
            metric_type = definition.get("metric_type")
            default_val = definition.get("default_val", None)
            parser_func = definition.get("parser_func")
            append_tags = definition.get("append_tags", [])

            column_value = row.get(column_name, default_val)
            parse_method = getattr(self, parser_func)
            metric_value = parse_method(column_value)

            send_metric = getattr(self, metric_type)
            send_metric(metric_name, metric_value, tags=metric_tags + append_tags)
        return

    def daily_report_to_metrics(self, url, headers, row_fields, tag_fields, tags):
        with rq.get(url, headers=headers, stream=True, timeout=REQ_TIMEOUT) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())

            # latest daily report date
            latest_date = "1900-01-01"
            rows = []
            for row in csv.DictReader(lines):
                rows.append(row)
                report_date = row.get("Report Date")
                if  report_date > latest_date:
                    latest_date = report_date

            for row in rows:
                if row.get("Report Date") < latest_date:
                    continue

                metric_tags = tags.copy()
                for column, tag_key in tag_fields.items():
                    tag_val = row.get(column, None)
                    metric_tags.append("{}:{}".format(tag_key, tag_val))

                for definition in row_fields:
                    column_name = definition.get("column_name")
                    metric_name = definition.get("metric_name")
                    metric_type = definition.get("metric_type")
                    default_val = definition.get("default_val", None)
                    parser_func = definition.get("parser_func")
                    append_tags = definition.get("append_tags", [])

                    column_value = row.get(column_name, default_val)
                    parse_method = getattr(self, parser_func)
                    metric_value = parse_method(column_value)

                    # Ignore column tags on refresh metrics
                    if metric_name.endswith('.refresh'):
                        metric_tags = tags.copy()

                    send_metric = getattr(self, metric_type)
                    send_metric(metric_name, metric_value, tags=metric_tags + append_tags)

    def period_report_to_metrics(self, url, headers, row_fields, tag_fields, agg_fields, tags):
        aggregates = {}

        with rq.get(url, headers=headers, stream=True, timeout=REQ_TIMEOUT) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())

            for row in csv.DictReader(lines):
                for definition in agg_fields:
                    column_name = definition.get("column_name")
                    metric_name = definition.get("metric_name")
                    metric_type = definition.get("metric_type")
                    default_val = definition.get("default_val", None)
                    parser_func = definition.get("parser_func")
                    append_tags = definition.get("append_tags", [])

                    column_value = row.get(column_name, default_val)
                    parse_method = getattr(self, parser_func)
                    metric_value = parse_method(column_value)

                    if not column_name in aggregates:
                        aggregates[column_name] = 0
                    aggregates[column_name] = aggregates[column_name] + metric_value

                for definition in row_fields:
                    column_name = definition.get("column_name")
                    metric_name = definition.get("metric_name")
                    metric_type = definition.get("metric_type")
                    default_val = definition.get("default_val", None)
                    parser_func = definition.get("parser_func")
                    append_tags = definition.get("append_tags", [])

                    column_value = row.get(column_name, default_val)
                    parse_method = getattr(self, parser_func)
                    metric_value = parse_method(column_value)

                    metric_tags = tags.copy()
                    # ignore column tags on refresh metrics
                    if not metric_name.endswith('.refresh'):
                        for column, tag_key in tag_fields.items():
                            tag_val = row.get(column, None)
                            metric_tags.append("{}:{}".format(tag_key, tag_val))
                    
                    send_metric = getattr(self, metric_type)
                    send_metric(metric_name, metric_value, tags=metric_tags + append_tags)
            
            # Send aggregate metrics
            for definition in agg_fields:
                column_name = definition.get("column_name")
                metric_name = definition.get("metric_name")
                metric_type = definition.get("metric_type")
                default_val = definition.get("default_val", None)
                parser_func = definition.get("parser_func")
                append_tags = definition.get("append_tags", [])

                metric_tags = tags.copy()
                send_metric = getattr(self, metric_type)
                send_metric(metric_name, aggregates.setdefault(column_name, -1.0), tags=metric_tags + append_tags)

    def daily_report_to_metrics_topn(self, url, headers, row_fields, tag_fields, tags, topn):
        with rq.get(url, headers=headers, stream=True, timeout=REQ_TIMEOUT) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())

            # latest daily report date
            latest_date = "1900-01-01"
            rows = []
            for row in csv.DictReader(lines):
                rows.append(row)
                report_date = row.get("Report Date")
                if  report_date > latest_date:
                    latest_date = report_date

            metric_lists = {}
            for row in rows:
                if row.get("Report Date") < latest_date:
                    continue

                metric_tags = tags.copy()
                for column, tag_key in tag_fields.items():
                    tag_val = row.get(column, None)
                    metric_tags.append("{}:{}".format(tag_key, tag_val))

                for definition in row_fields:
                    column_name = definition.get("column_name")
                    metric_name = definition.get("metric_name")
                    metric_type = definition.get("metric_type")
                    default_val = definition.get("default_val", None)
                    parser_func = definition.get("parser_func")
                    append_tags = definition.get("append_tags", [])

                    column_value = row.get(column_name, default_val)
                    parse_method = getattr(self, parser_func)
                    metric_value = parse_method(column_value)

                    # Ignore column tags on refresh metrics
                    if metric_name.endswith('.refresh'):
                        metric_tags = tags.copy()

                    metric_lists.setdefault(metric_name, []).append((metric_type, 
                        metric_value, metric_tags + append_tags))

                for metric_name in metric_lists.keys():
                    top = sorted(metric_lists[metric_name], key = lambda x: x[1], reverse=True)[:topn]

                    for m in top:
                        (metric_type, metric_value, tags) = m
                        send_metric = getattr(self, metric_type)
                        send_metric(metric_name, metric_value, tags=tags)

    def period_report_to_metrics_topn(self, url, headers, row_fields, tag_fields, tags, topn):
        aggregates   = {}
        metric_lists = {}
        with rq.get(url, headers=headers, stream=True, timeout=REQ_TIMEOUT) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())

            for row in csv.DictReader(lines):
                for definition in row_fields:
                    column_name = definition.get("column_name")
                    metric_name = definition.get("metric_name")
                    metric_type = definition.get("metric_type")
                    default_val = definition.get("default_val", None)
                    parser_func = definition.get("parser_func")
                    append_tags = definition.get("append_tags", [])

                    column_value = row.get(column_name, default_val)
                    parse_method = getattr(self, parser_func)
                    metric_value = parse_method(column_value)

                    metric_tags = tags.copy()
                    if not metric_name.endswith('.refresh'):
                        for column, tag_key in tag_fields.items():
                            tag_val = row.get(column, None)
                            metric_tags.append("{}:{}".format(tag_key, tag_val))

                    metric_lists.setdefault(metric_name, []).append((metric_type, 
                        metric_value, metric_tags + append_tags))
                    
        for metric_name in metric_lists.keys():
            top = sorted(metric_lists[metric_name], key = lambda x: x[1], reverse=True)[:topn]

            for m in top:
                (metric_type, metric_value, metric_tags) = m
                send_metric = getattr(self, metric_type)
                send_metric(metric_name, metric_value, tags=metric_tags)

    def get_synthetic_http_metric(self, metric_pre, verb, url, headers, data, tags):
        metric_tags = tags.copy()

        try:
            r = rq.request(
                verb.upper(), url=url, headers=headers, data=data, timeout=REQ_TIMEOUT
            )
        except Exception as e:
            self.gauge("{}.response".format(metric_pre), float(0), tags=metric_tags)
            raise e

        elapsed_dt = r.elapsed
        elapsed_ms = int(elapsed_dt.microseconds / 1000) + int(
            elapsed_dt.seconds * 1000
        )
        metric_tags.append("{}:{}".format("status_code", r.status_code))
        self.gauge(
            "{}.response.time".format(metric_pre), float(elapsed_ms), tags=metric_tags
        )

        try:
            r.raise_for_status()
        except Exception as e:
            raise e
        finally:
            self.gauge("{}.response".format(metric_pre), float(1), tags=metric_tags)

        if r.text:
            return r.json()
        else:
            return {}

    def set_reports_token(self):
        tenant_id = self.instance.get("tenant_id", None)
        client_id = self.instance.get("client_id", None)
        client_secret = self.instance.get("client_secret", None)

        url = "https://login.microsoftonline.com/{}/oauth2/v2.0/token".format(tenant_id)
        data = {
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        r = rq.post(url, data=data, timeout=REQ_TIMEOUT)
        r.raise_for_status()
        self.reports_token = r.json()
        return

    def set_synthetics_token(self):
        tenant_id = self.instance.get("tenant_id")
        client_id = self.instance.get("client_id")
        client_secret = self.instance.get("client_secret")
        username = self.instance.get("username")
        password = self.instance.get("password")

        url = "https://login.microsoftonline.com/{}/oauth2/token".format(tenant_id)
        scopes = [
            "AllSites.Read",
            "Calendars.ReadWrite",
            "ChannelMessage.Send",
            "Channel.ReadBasic.All",
            "Files.ReadWrite",
            "Team.ReadBasic.All",
        ]
        form_data = {
            "resource": "https://graph.microsoft.com",
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password,
            "scope": " ".join(scopes),
        }

        r = rq.post(url, data=form_data, timeout=REQ_TIMEOUT)
        r.raise_for_status()

        self.synthetics_token = r.json()
        return

    def set_management_token(self):
        tenant_id = self.instance.get("tenant_id", None)
        client_id = self.instance.get("client_id", None)
        client_secret = self.instance.get("client_secret", None)
        
        url = "https://login.microsoftonline.com/{}/oauth2/v2.0/token".format(tenant_id)
        data = {
            "scope": "https://manage.office.com/.default",
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        r = rq.post(url, data=data, timeout=REQ_TIMEOUT)
        r.raise_for_status()
        self.management_token = r.json()
        return

    ##########################################################################################
    ## Reports.ActiveUsers
    ##########################################################################################
    def ActiveUsersUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "activeusers.users")
        report_path     = "v1.0/reports/getOffice365ActiveUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Office 365",
            "Exchange",
            "OneDrive",
            "SharePoint",
            "Skype For Businesss",
            "Yammer",
            "Teams",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["product:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def ActiveUsersServiceUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "activeusers.serviceusers")
        report_path     = "v1.0/reports/getOffice365ServicesUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}
        probe_mode      = self.instance.get("probe_mode", True)

        tag_fields = {}
        col_fields = [
            "Office 365",
            "Exchange",
            "OneDrive",
            "SharePoint",
            "Skype For Businesss",
            "Yammer",
            "Teams",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{} Active".format(name),
                "metric_name": "{}.active".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["product:{}".format(name)]
            })

            row_fields.append({
                "column_name": "{} Inactive".format(name),
                "metric_name": "{}.inactive".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["product:{}".format(name)]
            })

        highmark = 0.0
        with rq.get(report_url, headers=report_headers, stream=True, timeout=REQ_TIMEOUT) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())

            for row in csv.DictReader(lines):
                for name in col_fields:
                    usercount = self.parse_float(row.get("{} Active".format(name), 0.0))
                    if usercount > highmark:
                        highmark = usercount

                if not probe_mode:
                    self.csv_row_to_metrics(
                        row=row,
                        tag_fields=tag_fields,
                        row_fields=row_fields,
                        tags=self.tags,
                    )

        # tag_metric is single unit count
        for i in range(1, int(highmark) + 1):
            user_tags = self.tags.copy()
            user_tags.append("user:user{}".format(i))
            self.gauge(self.billing_metric, 1.0, tags=user_tags)
        return


    ##########################################################################################
    ## Reports.Activations
    ##########################################################################################
    def ActivationsActivationCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "activations.devices")
        report_path     = "v1.0/reports/getOffice365ActivationCounts"
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {
            "Product Type": "product",
        }
        col_fields = [
            "Windows",
            "Mac",
            "Android",
            "iOS",
            "Windows 10 Mobile",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["device:{}".format(name)]
            })

        self.period_report_to_metrics(report_url, report_headers, row_fields, tag_fields, [], self.tags)
        return

    def ActivationsUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "activations.users")
        report_path     = "v1.0/reports/getOffice365ActivationsUserCounts"
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {
            "Product Type": "product",
        }
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "Assigned",
                "metric_name": "{}.assigned".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Activated",
                "metric_name": "{}.activated".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Shared Computer Activation",
                "metric_name": "{}.shared".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
        ]

        self.period_report_to_metrics(report_url, report_headers, row_fields, tag_fields, [], self.tags)
        return

    ##########################################################################################
    ## Reports.GroupsActivity
    ##########################################################################################
    def GroupsActivityActivityCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "groups.activity")
        report_path     = "v1.0/reports/getOffice365GroupsActivityCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Exchange Emails Received",
            "Yammer Messages Posted",
            "Yammer Messages Read",
            "Yammer Messages Liked",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return  

    def GroupsActivityGroupCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "groups")
        report_path     = "v1.0/reports/getOffice365GroupsActivityGroupCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "Total",
                "metric_name": "{}.total".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Active",
                "metric_name": "{}.active".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            }
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def GroupsActivityStorage(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "groups.storage")
        report_path     = "v1.0/reports/getOffice365GroupsActivityStorage(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "Mailbox Storage Used (Byte)",
                "metric_name": "{}.mailbox.used".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Site Storage Used (Byte)",
                "metric_name": "{}.site.used".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            }
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def GroupsActivityFileCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "groups.files")
        report_path     = "v1.0/reports/getOffice365GroupsActivityFileCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "Total",
                "metric_name": "{}.total".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Active",
                "metric_name": "{}.active".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            }
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.OutlookMailboxUsage (TopN)
    ##########################################################################################
    def OutlookMailboxUsageDetail(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "outlook.mailbox.detail")
        report_path     = "v1.0/reports/getMailboxUsageDetail(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {
            "User Principal Name": "upn",
            "Display Name": "display_name"
        }
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",  
            },
            {
                "column_name": "Storage Used (Byte)",
                "metric_name": "{}.storage.used".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Deleted Item Size (Byte)",
                "metric_name": "{}.deleted.used".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            }
        ]

        topN = self.instance.get("outlook_mailbox_topn", 0)
        if topN != 0:
            self.period_report_to_metrics_topn(report_url, report_headers, row_fields, tag_fields, 
                self.tags, topN )
        return

    ##########################################################################################
    ## Reports.OutlookActivity
    ##########################################################################################
    def OutlookActivityActivityCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "outlook.activity")
        report_path     = "v1.0/reports/getEmailActivityCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Send",
            "Receive",
            "Read",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def OutlookActivityUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "outlook.activity.users")
        report_path     = "v1.0/reports/getEmailActivityUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Send",
            "Receive",
            "Read",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.OutlookAppUsage
    ##########################################################################################
    def OutlookAppUsageAppsUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "outlook.app.users")
        report_path     = "v1.0/reports/getEmailAppUsageUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Mail For Mac",
            "Outlook For Mac",
            "Outlook For Windows",
            "Outlook For Mobile",
            "Other For Mobile",
            "Outlook For Web",
            "POP3 App",
            "IMAP4 App",
            "SMTP App",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["email_app:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def OutlookAppUsageVersionsUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "outlook.version.users")
        report_path     = "v1.0/reports/getEmailAppUsageVersionsUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Outlook 2016",
            "Outlook 2013",
            "Outlook 2010",
            "Outlook 2007",
            "Undetermined",
            "Outlook M365",
            "Outlook 2019",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["version:{}".format(name)]
            })

        self.period_report_to_metrics(report_url, report_headers, row_fields, tag_fields, [], self.tags)
        return

    ##########################################################################################
    ## Reports.OutlookMailboxUsage
    ##########################################################################################
    def OutlookMailboxUsageMailboxCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "outlook.mailbox")
        report_path     = "v1.0/reports/getMailboxUsageMailboxCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "Total",
                "metric_name": "{}.total".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Active",
                "metric_name": "{}.active".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            }
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def OutlookMailboxUsageQuotaStatusMailboxCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "outlook.mailbox.quota")
        report_path     = "v1.0/reports/getMailboxUsageQuotaStatusMailboxCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Under Limit",
            "Warning Issued",
            "Send Prohibited",
            "Send/Receive Prohibited",
            "Indeterminate",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["category:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def OutlookMailboxUsageStorage(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "outlook.mailbox.storage")
        report_path     = "v1.0/reports/getMailboxUsageStorage(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "Storage Used (Byte)",
                "metric_name": "{}.used".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.TeamsDeviceUsage
    ##########################################################################################
    def TeamsDeviceUsageUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "teams.device.users")
        report_path     = "v1.0/reports/getTeamsDeviceUsageUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Web",
            "Windows Phone",
            "Android Phone",
            "iOS",
            "Mac",
            "Windows",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["device:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.TeamsUserActivity
    ##########################################################################################
    def TeamsUserActivityUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "teams.activity.users")
        report_path     = "v1.0/reports/getTeamsUserActivityUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Team Chat Messages",
            "Private Chat Messages",
            "Calls",
            "Meetings",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.OneDriveActivity
    ##########################################################################################
    def OneDriveActivityUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "onedrive.activity.users")
        report_path     = "v1.0/reports/getOneDriveActivityUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Viewed Or Edited",
            "Synced",
            "Shared Internally",
            "Shared Externally",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def OneDriveActivityFileCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "onedrive.activity.files")
        report_path     = "v1.0/reports/getOneDriveActivityFileCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Viewed Or Edited",
            "Synced",
            "Shared Internally",
            "Shared Externally",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.OneDriveUsage
    ##########################################################################################
    def OneDriveUsageAccountCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "onedrive.sites")
        report_path     = "v1.0/reports/getOneDriveUsageAccountCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {
            "Site Type": "site_type",
        }
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "Total",
                "metric_name": "{}.total".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Active",
                "metric_name": "{}.active".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            }
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return   

    def OneDriveUsageFileCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "onedrive.files")
        report_path     = "v1.0/reports/getOneDriveUsageFileCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {
            "Site Type": "site_type",
        }
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "Total",
                "metric_name": "{}.total".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Active",
                "metric_name": "{}.active".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            }
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return  

    def OneDriveUsageStorage(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "onedrive.storage")
        report_path     = "v1.0/reports/getOneDriveUsageStorage(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {
            "Site Type": "site_type",
        }
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "Storage Used (Byte)",
                "metric_name": "{}.used".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.OneDriveUsageAccountDetail
    ##########################################################################################
    # 2021-03-22 (reuben@rapdev.io) - Adding support for aggregated allocation from OneDriveUsageAccountDetail 
    def OneDriveUsageAccountDetail(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "onedrive")
        report_path     = "v1.0/reports/getOneDriveUsageAccountDetail(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.storage.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]
        agg_fields = [
            {
                "column_name": "{}".format("Storage Used (Byte)"),
                "metric_name": "{}.storage.used".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "{}".format("Storage Allocated (Byte)"),
                "metric_name": "{}.storage.allocated".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
        ]

        self.period_report_to_metrics(report_url, report_headers, row_fields, tag_fields, agg_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.SharePointActivity
    ##########################################################################################
    def SharePointActivityFileCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "sharepoint.activity.files")
        report_path     = "v1.0/reports/getSharePointActivityFileCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Viewed Or Edited",
            "Synced",
            "Shared Internally",
            "Shared Externally",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SharePointActivityUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "sharepoint.activity.users")
        report_path     = "v1.0/reports/getSharePointActivityUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Visited Page",
            "Viewed Or Edited",
            "Synced",
            "Shared Internally",
            "Shared Externally",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SharePointActivityPages(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "sharepoint.activity.pages")
        report_path     = "v1.0/reports/getSharePointActivityPages(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "Visited Page Count",
                "metric_name": "{}.visits".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.SharePointUsage
    ##########################################################################################
    # 2021-03-22 (reuben@rapdev.io) - Adding support for aggregated allocation from SiteUsageDetail 
    def SharePointUsageDetail(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "sharepoint")
        report_path     = "v1.0/reports/getSharePointSiteUsageDetail(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {
            "Site Type": "site_type",
        }
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.storage.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]
        agg_fields = [
            {
                "column_name": "{}".format("Storage Used (Byte)"),
                "metric_name": "{}.storage.used".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "{}".format("Storage Allocated (Byte)"),
                "metric_name": "{}.storage.allocated".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
        ]

        self.period_report_to_metrics(report_url, report_headers, row_fields, tag_fields, agg_fields, self.tags)
        return

    def SharePointUsageFileCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "sharepoint.files")
        report_path     = "v1.0/reports/getSharePointSiteUsageFileCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {
            "Site Type": "site_type",
        }
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "{}".format("Total"),
                "metric_name": "{}.total".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "{}".format("Active"),
                "metric_name": "{}.active".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SharePointUsageSiteCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "sharepoint.sites")
        report_path     = "v1.0/reports/getSharePointSiteUsageSiteCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {
            "Site Type": "site_type",
        }
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "{}".format("Total"),
                "metric_name": "{}.total".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "{}".format("Active"),
                "metric_name": "{}.active".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SharePointUsagePages(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "sharepoint.pages")
        report_path     = "v1.0/reports/getSharePointSiteUsagePages(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {
            "Site Type": "site_type",
        }
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "{}".format("Page View Count"),
                "metric_name": "{}.views".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.YammerActivity
    ##########################################################################################
    def YammerActivityActivityCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "yammer.activity")
        report_path     = "v1.0/reports/getYammerActivityCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Liked",
            "Posted",
            "Read",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def YammerActivityUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "yammer.activity.users")
        report_path     = "v1.0/reports/getYammerActivityUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Liked",
            "Posted",
            "Read",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.YammerDeviceUsage
    ##########################################################################################
    def YammerDeviceUsageUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "yammer.device.users")
        report_path     = "v1.0/reports/getYammerDeviceUsageUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Web",
            "Windows Phone",
            "Android Phone",
            "iPhone",
            "iPad",
            "Other",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["device:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.YammerGroupsActivity
    ##########################################################################################
    def YammerGroupsActivityGroupCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "yammer.groups")
        report_path     = "v1.0/reports/getYammerDeviceUsageUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = []
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "{}".format("Total"),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "{}".format("Active"),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            }
        ]

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def YammerGroupsActivityActivityCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "yammer.activity.groups")
        report_path     = "v1.0/reports/getYammerGroupsActivityCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Liked",
            "Posted",
            "Read",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.SkypeActivity
    ##########################################################################################
    def SkypeActivityActivityCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity")
        report_path     = "v1.0/reports/getSkypeForBusinessActivityCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Peer-to-peer",
            "Organized",
            "Participated",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })


        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SkypeActivityUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity.users")
        report_path     = "v1.0/reports/getSkypeForBusinessActivityUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Peer-to-peer",
            "Organized",
            "Participated",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })


        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.SkypeDeviceUsage
    ##########################################################################################
    def SkypeDeviceUsageUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.device.users")
        report_path     = "v1.0/reports/getSkypeForBusinessDeviceUsageUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Windows",
            "Windows Phone",
            "Android Phone",
            "iPhone",
            "iPad",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["device:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.SkypeOrganizerActivity
    ##########################################################################################
    def SkypeOrganizerActivityActivityCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity.organizer")
        report_path     = "v1.0/reports/getSkypeForBusinessOrganizerActivityCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "IM",
            "Audio/Video",
            "App Sharing",
            "Web",
            "Dial-in/out 3rd Party",
            "Dial-in/out Microsoft",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SkypeOrganizerActivityUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity.organizer.users")
        report_path     = "v1.0/reports/getSkypeForBusinessOrganizerActivityUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "IM",
            "Audio/Video",
            "App Sharing",
            "Web",
            "Dial-in/out 3rd Party",
            "Dial-in/out Microsoft",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SkypeOrganizerActivityMinuteCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity.organizer.minutes")
        report_path     = "v1.0/reports/getSkypeForBusinessOrganizerActivityMinuteCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Audio/Video",
            "Dial-in Microsoft",
            "Dial-out Microsoft",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.SkypeParticipantActivity
    ##########################################################################################
    def SkypeParticipantActivityActivityCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity.participant")
        report_path     = "v1.0/reports/getSkypeForBusinessParticipantActivityCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "IM",
            "Audio/Video",
            "App Sharing",
            "Web",
            "Dial-in/out 3rd Party",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SkypeParticipantActivityUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity.participant.users")
        report_path     = "v1.0/reports/getSkypeForBusinessParticipantActivityUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "IM",
            "Audio/Video",
            "App Sharing",
            "Web",
            "Dial-in/out 3rd Party",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SkypeParticipantActivityMinuteCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity.participant.minutes")
        report_path     = "v1.0/reports/getSkypeForBusinessParticipantActivityMinuteCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Audio/Video",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ##########################################################################################
    ## Reports.SkypePeerToPeerActivity
    ##########################################################################################
    def SkypePeerToPeerActivityActivityCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity.p2p")
        report_path     = "v1.0/reports/getSkypeForBusinessPeerToPeerActivityCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "IM",
            "Audio",
            "Video",
            "App Sharing",
            "File Transfer",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SkypePeerToPeerActivityUserCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity.p2p.users")
        report_path     = "v1.0/reports/getSkypeForBusinessPeerToPeerActivityUserCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "IM",
            "Audio",
            "Video",
            "App Sharing",
            "File Transfer",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    def SkypePeerToPeerActivityMinuteCounts(self, period="d7"):
        report_prefix   = "{}.{}".format(self.metric_prefix, "skype.activity.p2p.minutes")
        report_path     = "v1.0/reports/getSkypeForBusinessPeerToPeerActivityMinuteCounts(period='{}')".format(period)
        report_host     = self.instance.get("graph_url", "https://graph.microsoft.com")
        report_url      = "{}/{}".format(report_host, report_path)
        report_token    = self.reports_token.get("access_token", None)
        report_headers  = {"Authorization": "Bearer {}".format(report_token)}

        tag_fields = {}
        col_fields = [
            "Audio",
            "Video",
        ]
        row_fields = [
            {
                "column_name": self.report_refresh_column,
                "metric_name": "{}.refresh".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in col_fields:
            row_fields.append({
                "column_name": "{}".format(name),
                "metric_name": "{}".format(report_prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["activity:{}".format(name)]
            })

        self.daily_report_to_metrics(report_url, report_headers, row_fields, tag_fields, self.tags)
        return

    ###############################################################################################
    ## Synthetics :: Email
    ###############################################################################################
    def get_email_synthetic_metrics(self):
        checkin_url = "https://email.synth-rapdev.io/checkin"
        metrics_url = "https://email.synth-rapdev.io/metrics"
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.synthetic_email_api_key,
        }

        prefix = self.metric_prefix
        email_address = self.instance.get("email_address")

        """ /checkin """
        res = rq.post(
            checkin_url,
            headers=headers,
            json={
                "emailAddress": email_address,
                "checkVersion": self.check_version,
            },
            timeout=REQ_TIMEOUT,
        )
        res.raise_for_status()

        """ /metrics """
        res = rq.post(
            metrics_url,
            headers=headers,
            json={"emailAddress": email_address},
            timeout=REQ_TIMEOUT,
        )
        res.raise_for_status()

        metrics = res.json()

        for metric in metrics:
            metric_tags = self.tags.copy()
            metric_tags.append("{}:{}".format("email", metric.get("emailAddress")))
            metric_tags.append("{}:{}".format("mailbox", metric.get("emailAddress")))
            metric_tags.append("{}:{}".format("cloud", "aws"))
            metric_tags.append("{}:{}".format("region", metric.get("sourceRegion")))
            metric_tags.append("{}:{}".format("o365_app", "outlook"))

            bounce_type = metric.get("bounceType", None)
            bounce_sub_type = metric.get("bounceSubType", None)
            ms_roundtrip = float(metric.get("msRoundTrip", 0))
            hop_count = float(metric.get("hopCount", 0))
            elapsed_last_sent = float(metric.get("elapsedLastSent", 0))
            elapsed_last_seen = float(metric.get("elapsedLastVisible", 0))

            self.gauge(
                "{}.synthetic.email.last_sent".format(prefix),
                elapsed_last_sent,
                tags=metric_tags,
            )
            self.gauge(
                "{}.synthetic.email.last_seen".format(prefix),
                elapsed_last_seen,
                tags=metric_tags,
            )

            if bounce_sub_type:
                metric_tags.append("{}:{}".format("bounce_type", bounce_sub_type))
                self.gauge(
                    "{}.synthetic.email.bounced".format(prefix),
                    float(1),
                    tags=metric_tags,
                )
            else:
                self.gauge(
                    "{}.synthetic.email.bounced".format(prefix),
                    float(0),
                    tags=metric_tags,
                )
                self.gauge(
                    "{}.synthetic.email.rtt".format(prefix),
                    ms_roundtrip,
                    tags=metric_tags,
                )
                self.gauge(
                    "{}.synthetic.email.hops".format(prefix),
                    hop_count,
                    tags=metric_tags,
                )
        return

    ###############################################################################################
    ## Synthetics :: Calendar
    ###############################################################################################
    def get_calendar_synthetic_metrics(self):
        metric_prefix = "{}.synthetic".format(self.metric_prefix)
        token = self.synthetics_token.get("access_token", None)
        graph_host = self.instance.get("graph_url", "https://graph.microsoft.com")
        graph_path = "v1.0"
        graph_url  = "{}/{}".format(graph_host, graph_path)

        username = self.instance.get("username")

        metric_tags = self.tags.copy()
        metric_tags.append("upn:{}".format(username))
        metric_tags.append("o365_app:{}".format("Calendar"))

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token),
        }

        """ [Read] Calendar """
        url = "{}/users/{}/calendar".format(graph_url, username)
        res = self.get_synthetic_http_metric(
            metric_prefix,
            "GET",
            url,
            headers,
            None,
            metric_tags + ["operation:read"],
        )

        if res:
            calendar_id = res.get("id")
            calendar_dt = datetime.now(tz=timezone.utc)

            """ [Create] calendar event """
            url = "{}/users/{}/calendar/events".format(graph_url, username)
            data = {
                "subject": "Synthetic Test",
                "body": {
                    "contentType": "HTML",
                    "content": "Synthetic Event created on {}".format(
                        calendar_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    ),
                },
                "start": {
                    "dateTime": calendar_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": (calendar_dt + timedelta(hours=1)).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    ),
                    "timeZone": "UTC",
                },
                "location": {"displayName": "Boston",},
                "attendees": [
                    {
                        "emailAddress": {
                            "address": username,
                            "name": "Synthetic Calendar Attendee",
                        },
                        "type": "required",
                    }
                ],
            }

            res = self.get_synthetic_http_metric(
                metric_prefix,
                "POST",
                url,
                headers,
                json.dumps(data, default=str),
                metric_tags + ["operation:create"],
            )
            event_id = res.get("id", None)

            if event_id:
                """ [Update] calendar event """
                url = "{}/users/{}/calendar/events/{}".format(
                    graph_url, username, event_id
                )
                data = {
                    "subject": "Synthetic Test (Updated)",
                    "body": {
                        "contentType": "HTML",
                        "content": "Synthetic Event created (updated) on {}".format(
                            calendar_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                        ),
                    },
                }

                res = self.get_synthetic_http_metric(
                    metric_prefix,
                    "PATCH",
                    url,
                    headers,
                    json.dumps(data, default=str),
                    metric_tags + ["operation:update"],
                )

                """ [Delete] calendar event"""
                url = "{}/users/{}/calendar/events/{}".format(
                    graph_url, username, event_id
                )
                res = self.get_synthetic_http_metric(
                    metric_prefix,
                    "DELETE",
                    url,
                    headers,
                    json.dumps(data, default=str),
                    metric_tags + ["operation:delete"],
                )
        return

    ###############################################################################################
    ## Synthetics :: OneDrive
    ###############################################################################################
    def get_onedrive_synthetic_metrics(self):
        metric_prefix = "{}.synthetic".format(self.metric_prefix)
        token = self.synthetics_token.get("access_token", None)
        username = self.instance.get("username")
        graph_host = self.instance.get("graph_url", "https://graph.microsoft.com")
        graph_path = "v1.0"
        graph_url  = "{}/{}".format(graph_host, graph_path)

        metric_tags = self.tags.copy()
        metric_tags.append("upn:{}".format(username))
        metric_tags.append("o365_app:{}".format("OneDrive"))

        file_size = self.instance.get("onedrive_file_size", MAX_FILE_SIZE)
        if file_size > MAX_FILE_SIZE:
            file_size = MAX_FILE_SIZE

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token),
        }

        """ [Read] User's OneDrive """
        url = "{}/users/{}/drive".format(graph_url, username)
        res = self.get_synthetic_http_metric(
            metric_prefix,
            "GET",
            url,
            headers,
            None,
            metric_tags + ["operation:read"],
        )

        if res:
            drive_id = res.get("id")
            drive_dt = datetime.now(tz=timezone.utc)
            drive_ts = int(drive_dt.replace(tzinfo=timezone.utc).timestamp())

            """ Random 4MB file content (supported Graph API non-stream max) """
            content = "".join([choice(ascii_letters) for i in range(file_size)])
            metric_tags.append("file_size:{}".format(len(content)))

            """ [Create] OneDrive item (upload) """
            url = "{}/users/{}/drive/root:/ddagent-synthetic/dd-agent-{}.txt:/content".format(
                graph_url, username, drive_ts
            )
            res = self.get_synthetic_http_metric(
                metric_prefix,
                "PUT",
                url,
                headers,
                content,
                metric_tags + ["operation:create"],
            )

            if res:
                drive_item_id = res.get("id", None)

                """ [Update] OneDrive item (rename) """
                url = "{}/users/{}/drive/items/{}".format(
                    graph_url, username, drive_item_id
                )
                data = {"name": "{}-modified.txt".format(drive_ts)}

                res = self.get_synthetic_http_metric(
                    metric_prefix,
                    "PATCH",
                    url,
                    headers,
                    json.dumps(data, default=str),
                    metric_tags + ["operation:update"],
                )

                """ [Delete] OneDrive item """
                url = "{}/users/{}/drive/items/{}".format(
                    graph_url, username, drive_item_id
                )
                res = self.get_synthetic_http_metric(
                    metric_prefix,
                    "DELETE",
                    url,
                    headers,
                    None,
                    metric_tags + ["operation:delete"],
                )
        return

    ###############################################################################################
    ## Synthetics :: Teams
    ###############################################################################################
    def get_teams_synthetic_metrics(self):
        metric_prefix = "{}.synthetic".format(self.metric_prefix)
        token = self.synthetics_token.get("access_token", None)
        username = self.instance.get("username")
        graph_host = self.instance.get("graph_url", "https://graph.microsoft.com")
        graph_path = "v1.0"
        graph_url  = "{}/{}".format(graph_host, graph_path)

        metric_tags = self.tags.copy()
        metric_tags.append("upn:{}".format(username))
        metric_tags.append("o365_app:{}".format("teams"))

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token),
        }

        """ [Read] User's joined teams """
        url = "{}/me/joinedTeams".format(graph_url)
        res = rq.get(url, headers=headers, timeout=REQ_TIMEOUT)
        res.raise_for_status()

        team_id = None
        channel_id = None
        if res:
            for team in res.json().get("value", []):
                if team.get("displayName") == "dd-agent-synthetic":
                    team_id = team.get("id")

        if team_id:
            """ [Read] List Teams' channels """
            url = "{}/teams/{}/channels".format(graph_url, team_id)
            res = self.get_synthetic_http_metric(
                metric_prefix,
                "GET",
                url,
                headers,
                None,
                metric_tags + ["operation:read"],
            )

            if res:
                for channel in res.get("value", []):
                    if channel.get("displayName") == "General":
                        channel_id = channel.get("id")

            if channel_id:
                channel_dt = datetime.now(tz=timezone.utc)

                """ [Create] Channel message """
                url = "{}/teams/{}/channels/{}/messages".format(
                    graph_url, team_id, channel_id
                )
                data = {
                    "body": {
                        "content": "Synthetic Message Posted On {}".format(
                            channel_dt.isoformat()
                        )
                    }
                }
                res = self.get_synthetic_http_metric(
                    metric_prefix,
                    "POST",
                    url,
                    headers,
                    json.dumps(data, default=str),
                    metric_tags + ["operation:create"],
                )

                message_id = None
                if res:
                    message_id = res.get("id", None)

                if message_id:
                    """ [Update] Channel message """
                    url = "{}/teams/{}/channels/{}/messages/{}/replies".format(
                        graph_url, team_id, channel_id, message_id
                    )
                    data = {"body": {"content": "Synthetic Message Reply",}}
                    res = self.get_synthetic_http_metric(
                        metric_prefix,
                        "POST",
                        url,
                        headers,
                        json.dumps(data, default=str),
                        metric_tags + ["operation:update"],
                    )
                else:
                    raise Exception(
                        "Missing expected return value of 'message_id' from channel post"
                    )
            else:
                raise Exception("Unable to find channel: 'General'")
        else:
            raise Exception("Unable to find team: 'dd-agent-synthetic'")
        return

    ###############################################################################################
    ## Synthetics :: SharePoint
    ###############################################################################################
    def get_sharepoint_synthetic_metrics(self):
        metric_prefix = "{}.synthetic".format(self.metric_prefix)
        username = self.instance.get("username")
        password = self.instance.get("password")

        sites = self.instance.get("sharepoint_sites", [])
        for site in sites:
            parsed_url  = urlparse(site)
            parsed_host = parsed_url.hostname
            s = SharePointSession(parsed_host, username, password, None)
            r = s.get(site)

            metric_tags = self.tags.copy()
            metric_tags.append("o365_app:{}".format("sharepoint"))
            metric_tags.append("operation:read")
            metric_tags.append("site:{}".format(site))

            elapsed_dt = r.elapsed
            elapsed_ms = int(elapsed_dt.microseconds / 1000) + int(elapsed_dt.seconds * 1000)
            metric_tags.append("{}:{}".format("status_code", r.status_code))
            self.gauge("{}.response.time".format(metric_prefix), float(elapsed_ms), 
                tags=metric_tags)

            try:
                r.raise_for_status()
            except Exception as e:
                raise e
            finally:
                self.gauge("{}.response".format(metric_prefix), float(1), tags=metric_tags)

            perf = r.json().get("perf", None)
            if not perf:
                self.log.warn("missing expected 'perf' property on SharePoint site response")
                continue

            perf_tags = self.tags.copy()
            perf_tags.append("o365_app:{}".format("sharepoint"))
            perf_tags.append("site:{}".format(site))

            # SharePoint Site performance metrics
            for metric in SHAREPOINT_PERF_METRICS:
                value = perf.get(metric, None)

                if value:
                    self.gauge(
                        "{}.{}".format(metric_prefix, metric.replace("-", "_")),
                        float(value), 
                        tags=perf_tags,
                    )
            ## ClaimsAuthenticationTime
            vtime = perf.get("ClaimsAuthenticationTime", None)
            vtype = perf.get("ClaimsAuthenticationTimeType", None)
            if vtime:
                self.gauge(
                    "{}.{}".format(metric_prefix, "ClaimsAuthenticationTime"),
                    float(vtime), 
                    tags=perf_tags+["type:{}".format(vtype)],
                )
        return

    ###############################################################################################
    ## Office 365 Service Communications - Incident Messages
    ###############################################################################################
    def get_servicecomms_incidents(self):
        token = self.management_token.get("access_token", None)
        tenant_id       = self.instance.get("tenant_id", None)
        manage_host     = self.instance.get("manage_url", "https://manage.office.com")
        manage_path     = "api/v1.0/{}/ServiceComms/Messages".format(tenant_id)
        manage_headers  = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token),
        }
        url = "{}/{}".format(manage_host, manage_path)
        res = rq.get(url, headers=manage_headers, timeout=REQ_TIMEOUT)
        res.raise_for_status()
        values = res.json().get("value")

        now = datetime.now(tz=timezone.utc)
        interval = float(self.instance.get("min_collection_interval", 300.0))
        for incident in [v for v in values if v.get("MessageType") == "Incident"]:
            incidentId = incident.get("Id")
            impactDescription = incident.get("ImpactDescription")

            tags = self.tags.copy()
            tags.append("{}:{}".format("App", "O365"))
            tags.append("{}:{}".format("Workload", incident.get("Workload")))
            tags.append("{}:{}".format("Feature", incident.get("Feature")))
            tags.append("{}:{}".format("Status", incident.get("Status")))
            tags.append("{}:{}".format("Classification", incident.get("Classification")))

            for message in incident.get("Messages", []):
                messageDT = parse(message.get("PublishedTime"))
                elapsed = now - messageDT

                if elapsed.total_seconds() < (interval + 10.0):
                    self.event({
                        "timestamp": messageDT.timestamp(),
                        "msg_title": "[{}] {}".format(incidentId, impactDescription),
                        "msg_text": message.get("MessageText"), 
                        "aggregation_key": incidentId,
                        "source_type_name": "o365",
                        "tags": tags,
                    })
        return
