# (C) RapDev, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import csv
import json
import traceback
from datetime import date, datetime, timedelta, timezone

# from typing import Any
from random import choice
from string import ascii_letters

import requests

# from datadog_agent import get_config
from datadog_checks.base import AgentCheck
from dateutil.parser import parse

REQUIRED_TAGS = [
    "vendor:rapdev",
]

REQUIRED_SETTINGS = [
    "tenant_id",
    "client_id",
    "client_secret",
]

class O365Check(AgentCheck):
    def check(self, instance):
        self.metric_prefix = "rapdev.o365"
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.metric_prefix)
        self.service_check_name = "{}.status".format(self.metric_prefix)

        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.today = datetime.now(tz=timezone.utc).date()
        self.events_token = {}
        self.reports_token = {}
        self.synthetics_token = {}
        self.synthetic_email_api_key = "KIcolOzDSn2tdHppEnCmF5bVbAGSHDiN43eWkcWR"
        self.tags.append("{}:{}".format("tenant_id", self.instance.get("tenant_id", None)))

        ###########################################################################################
        ## Microsoft 365 Graph Authorization
        ###########################################################################################
        self.do_check("Reports.Authorization", "set_reports_token", instance)

        ###########################################################################################
        ## Microsoft 365 Active Users, Groups, & Activations
        ###########################################################################################
        self.do_check("Reports.ActiveUsers", "report_active_users", instance)
        self.do_check("Reports.Activations", "report_activations", instance)
        self.do_check("Reports.GroupsActivity", "report_groups_activity", instance)

        ###########################################################################################
        ## Microsoft 365 Outlook
        ###########################################################################################
        if self.instance.get("enable_outlook", True):
            self.do_check(
                "Reports.Outlook.Activity", "report_outlook_activity", instance
            )
            self.do_check("Reports.Outlook.Devices", "report_outlook_devices", instance)
            self.do_check(
                "Reports.Outlook.MailboxUsage", "report_outlook_usage", instance
            )
        else:
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Outlook.Activity")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Outlook.Devices")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Outlook.Usage")],
            )

        ###########################################################################################
        ## Microsoft 365 OneDrive
        ###########################################################################################
        if self.instance.get("enable_onedrive", True):
            self.do_check(
                "Reports.OneDrive.Activity", "report_onedrive_activity", instance
            )
            self.do_check("Reports.OneDrive.Usage", "report_onedrive_usage", instance)
        else:
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.OneDrive.Activity")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.OneDrive.Usage")],
            )

        ###########################################################################################
        ## Microsoft 365 SharePoint
        ###########################################################################################
        if self.instance.get("enable_sharepoint", True):
            self.do_check(
                "Reports.SharePoint.Activity", "report_sharepoint_activity", instance
            )
            self.do_check(
                "Reports.SharePoint.Usage", "report_sharepoint_usage", instance
            )
        else:
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.SharePoint.Activity")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.SharePoint.Usage")],
            )

        ###########################################################################################
        ## Microsoft 365 Skype For Business
        ###########################################################################################
        if self.instance.get("enable_skype", True):
            self.do_check("Reports.Skype.Activity", "report_skype_activity", instance)
            self.do_check("Reports.Skype.Devices", "report_skype_devices", instance)
            self.do_check(
                "Reports.Skype.Organizer.Sessions",
                "report_skype_organizer_sessions",
                instance,
            )
            self.do_check(
                "Reports.Skype.Organizer.Users",
                "report_skype_organizer_users",
                instance,
            )
            self.do_check(
                "Reports.Skype.Organizer.Minutes",
                "report_skype_organizer_minutes",
                instance,
            )
            self.do_check(
                "Reports.Skype.Participant.Sessions",
                "report_skype_participant_sessions",
                instance,
            )
            self.do_check(
                "Reports.Skype.Participant.Users",
                "report_skype_participant_users",
                instance,
            )
            self.do_check(
                "Reports.Skype.Participant.Minutes",
                "report_skype_participant_minutes",
                instance,
            )
            self.do_check(
                "Reports.Skype.PeerToPeer.Sessions",
                "report_skype_p2p_sessions",
                instance,
            )
            self.do_check(
                "Reports.Skype.PeerToPeer.Users", "report_skype_p2p_users", instance
            )
            self.do_check(
                "Reports.Skype.PeerToPeer.Minutes", "report_skype_p2p_minutes", instance
            )
        else:
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Skype.Activity")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Skype.Devices")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags
                + ["service:{}".format("Reports.Skype.Organizer.Sessions")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Skype.Organizer.Users")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags
                + ["service:{}".format("Reports.Skype.Organizer.Minutes")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags
                + ["service:{}".format("Reports.Skype.Participant.Sessions")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags
                + ["service:{}".format("Reports.Skype.Participant.Users")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags
                + ["service:{}".format("Reports.Skype.Participant.Minutes")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags
                + ["service:{}".format("Reports.Skype.PeerToPeer.Sessions")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags
                + ["service:{}".format("Reports.Skype.PeerToPeer.Users")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags
                + ["service:{}".format("Reports.Skype.PeerToPeer.Minutes")],
            )

        ###########################################################################################
        ## Microsoft 365 Teams
        ###########################################################################################
        if self.instance.get("enable_teams", True):
            self.do_check("Reports.Teams.Activity", "report_teams_activity", instance)
            self.do_check("Reports.Teams.Devices", "report_teams_devices", instance)
        else:
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Teams.Activity")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Teams.Devices")],
            )

        ###########################################################################################
        ## Microsoft 365 Yammer
        ###########################################################################################
        if self.instance.get("enable_yammer", True):
            self.do_check("Reports.Yammer.Activity", "report_yammer_activity", instance)
            self.do_check("Reports.Yammer.Devices", "report_yammer_devices", instance)
            self.do_check("Reports.Yammer.Groups", "report_yammer_groups", instance)
        else:
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Yammer.Activity")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Yammer.Devices")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Reports.Yammer.Groups")],
            )

        ###########################################################################################
        ## Microsoft 365 Synthetics
        ###########################################################################################
        if self.instance.get("enable_synthetics", True):
            self.do_check("Synthetics.Authorization", "set_synthetics_token", instance)
            self.do_check(
                "Synthetics.Outlook.Calendar",
                "get_calendar_synthetic_metrics",
                instance,
            )
            self.do_check(
                "Synthetics.OneDrive.File", "get_onedrive_synthetic_metrics", instance
            )
            self.do_check(
                "Synthetics.Teams.Chat", "get_teams_synthetic_metrics", instance
            )
        else:
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Synthetics.Authorization")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Synthetics.Outlook.Calendar")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Synthetics.OneDrive.File")],
            )
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Synthetics.Teams.Chat")],
            )

        ###########################################################################################
        ## Email Synthetics
        ###########################################################################################
        if self.instance.get("enable_synthetic_email", True):
            self.do_check("Synthetics.Email", "get_email_synthetic_metrics", instance)
        else:
            self.service_check(
                self.service_check_name,
                AgentCheck.UNKNOWN,
                tags=self.tags + ["service:{}".format("Synthetics.Email")],
            )

        return

    def do_check(self, service, check, instance):
        check_tags = ["{}:{}".format("service", service)]
        check_func = getattr(self, check)
        try:
            check_func(instance)
        except Exception as e:
            m = "[{}]: {}".format(service, e)
            self.log.error(m)
            self.log.error(traceback.format_exc())
            self.service_check(
                self.service_check_name,
                AgentCheck.CRITICAL,
                message=m,
                tags=self.tags + check_tags,
            )
        else:
            self.service_check(
                self.service_check_name, AgentCheck.OK, tags=self.tags + check_tags
            )
        return

    def parse_present(self, value):
        if not value:
            return float(0)
        else:
            return float(1)

    def parse_float(self, value):
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
        """ csvRowToMetrics:

            Convert Microsoft Graph API Reports (csv) to datadog metrics.
        """

        metric_tags = tags.copy()

        # Extract row columns as metric tags
        for column, tag_key in tag_fields.items():
            tag_val = row.get(column, None)
            metric_tags.append("{}:{}".format(tag_key, tag_val))

        # Extract row colums as metrics
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

            # Send Metric
            send_metric = getattr(self, metric_type)
            send_metric(metric_name, metric_value, tags=metric_tags + append_tags)
        return

    def get_synthetic_http_metric(
        self, metric_pre, verb, url, headers, proxies, data, tags
    ):
        metric_tags = tags.copy()

        try:
            r = requests.request(
                verb.upper(), url=url, headers=headers, proxies=proxies, data=data
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

    def set_reports_token(self, instance):
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
        proxies = self.get_instance_proxy(instance, url)
        r = requests.post(url, data=data, proxies=proxies)
        r.raise_for_status()


        self.reports_token = r.json()
        return

    def set_synthetics_token(self, instance):
        tenant_id = self.instance.get("tenant_id")
        client_id = self.instance.get("client_id")
        client_secret = self.instance.get("client_secret")
        username = self.instance.get("username")
        password = self.instance.get("password")

        url = "https://login.microsoftonline.com/{}/oauth2/token".format(tenant_id)
        scopes = [
            "Calendars.ReadWrite",
            "Files.ReadWrite" "Group.ReadWrite.All",
            "ChannelMessage.Send",
            "Channel.Create",
            "Channel.Delete",
            "Team.ReadBasic.All",
            "Directory.ReadWrite.All",
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

        r = requests.post(url, data=form_data)
        r.raise_for_status()

        self.synthetics_token = r.json()
        return

    ###############################################################################################
    ## Microsoft 365 Active Users, Groups & Activations
    ###############################################################################################
    def report_active_users(self, instance, period="d7"):
        """ Office 365 Active Users report
            https://docs.microsoft.com/en-us/graph/api/resources/office-365-active-users-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getOffice365ActiveUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        app_fields = [
            "Exchange",
            "OneDrive",
            "SharePoint",
            "Skype for Business",
            "Yammer",
            "Teams",
        ]
        tag_fields = {
            "User Principal Name": "upn",
            "Display Name": "display_name",
        }
        row_fields = []

        for name in app_fields:
            prefix = self.metric_prefix
            formatted_name = name.lower().replace(" ", "_")

            row_fields.append(
                {
                    "column_name": "Has {} License".format(name),
                    "metric_name": "{}.activeuser.{}.license".format(
                        prefix, formatted_name
                    ),
                    "metric_type": "gauge",
                    "parser_func": "parse_boolean",
                    "append_tags": ["o365_app:{}".format(name)],
                }
            )

            row_fields.append(
                {
                    "column_name": "{} License Assign Date".format(name),
                    "metric_name": "{}.activeuser.{}.license_assign.time".format(
                        prefix, formatted_name
                    ),
                    "metric_type": "gauge",
                    "parser_func": "parse_elapsed_days",
                    "append_tags": ["o365_app:{}".format(name)],
                }
            )

            row_fields.append(
                {
                    "column_name": "{} Last Activity Date".format(name),
                    "metric_name": "{}.activeuser.{}.last_active.time".format(
                        prefix, formatted_name
                    ),
                    "metric_type": "gauge",
                    "parser_func": "parse_elapsed_days",
                    "append_tags": ["o365_app:{}".format(name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Billing Metric """
                billing_tags = [
                    "{}:{}".format("user", row.get("User Principal Name", None))
                ]
                self.gauge(self.billing_metric, 1.0, tags=self.tags + billing_tags)

                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags,
                )
        return

    def report_activations(self, instance):
        """ Office 365 activation report
            https://docs.microsoft.com/en-us/graph/api/resources/office-365-activations-reports?view=graph-rest-1.0
        """

        url = (
            "https://graph.microsoft.com/v1.0/reports/getOffice365ActivationsUserDetail"
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        app_fields = ["Windows", "Mac", "Windows 10 Mobile", "iOS", "Android"]
        tag_fields = {
            "User Principal Name": "upn",
            "Display Name": "display_name",
            "Product Type": "product_type",
            "Activated On Shared Computer": "activated_on_shared_computer",
        }
        row_fields = [
            {
                "column_name": "Last Activated Date",
                "metric_name": "{}.activations.last_activated.time".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            }
        ]

        for name in app_fields:
            row_fields.append(
                {
                    "column_name": "{}".format(name),
                    "metric_name": "{}.activations".format(prefix),
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["o365_client:{}".format(name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags,
                )
        return

    def report_groups_activity(self, instance, period="d7"):
        """ Office 365 Groups activity report
            https://docs.microsoft.com/en-us/graph/api/resources/office-365-groups-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getOffice365GroupsActivityDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "Group Display Name": "group_display_name",
            "Owner Principal Name": "owner",
            "Owner Principal Name": "upn",
            "Group Type": "type",
            "Group Id": "group_id",
        }
        row_fields = [
            {
                "column_name": "Member Count",
                "metric_name": "{}.group.members".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "External Member Count",
                "metric_name": "{}.group.external_members".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Exchange Received Email Count",
                "metric_name": "{}.group.{}.received_emails".format(prefix, "exchange"),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["{}:{}".format("o365_app", "exchange")],
            },
            {
                "column_name": "Exchange Mailbox Total Item Count",
                "metric_name": "{}.group.{}.mailbox_total_items".format(
                    prefix, "exchange"
                ),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["{}:{}".format("o365_app", "exchange")],
            },
            {
                "column_name": "Exchange Mailbox Storage Used (Byte)",
                "metric_name": "{}.group.{}.mailbox_storage".format(prefix, "exchange"),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["{}:{}".format("o365_app", "exchange")],
            },
            {
                "column_name": "SharePoint Active File Count",
                "metric_name": "{}.group.{}.active_files".format(prefix, "sharepoint"),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["{}:{}".format("o365_app", "sharepoint")],
            },
            {
                "column_name": "SharePoint Total File Count",
                "metric_name": "{}.group.{}.total_files".format(prefix, "sharepoint"),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["{}:{}".format("o365_app", "sharepoint")],
            },
            {
                "column_name": "SharePoint Site Storage Used (Byte)",
                "metric_name": "{}.group.{}.site_storage".format(prefix, "sharepoint"),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["{}:{}".format("o365_app", "sharepoint")],
            },
            {
                "column_name": "Yammer Posted Message Count",
                "metric_name": "{}.group.{}.posted_messages".format(prefix, "yammer"),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["{}:{}".format("o365_app", "yammer")],
            },
            {
                "column_name": "Yammer Read Message Count",
                "metric_name": "{}.group.{}.read_messages".format(prefix, "yammer"),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["{}:{}".format("o365_app", "yammer")],
            },
            {
                "column_name": "Yammer Liked Message Count",
                "metric_name": "{}.group.{}.liked_messages".format(prefix, "yammer"),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
                "append_tags": ["{}:{}".format("o365_app", "yammer")],
            },
        ]

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags,
                )
        return

    ###############################################################################################
    ## Microsoft 365 Teams
    ###############################################################################################
    def report_teams_devices(self, instance, period="d7"):
        """ Teams device usage report
            https://docs.microsoft.com/en-us/graph/api/resources/microsoft-teams-device-usage-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getTeamsDeviceUsageUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        app_fields = ["Web", "Windows Phone", "Android Phone", "iOS", "Mac", "Windows"]
        tag_fields = {
            "User Principal Name": "upn",
        }
        row_fields = [
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.teams.device.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            }
        ]

        for name in app_fields:
            row_fields.append(
                {
                    "column_name": "Used {}".format(name),
                    "metric_name": "{}.teams.device".format(prefix),
                    "metric_type": "gauge",
                    "parser_func": "parse_boolean",
                    "append_tags": ["device:{}".format(name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:teams"],
                )
        return

    def report_teams_activity(self, instance, period="d7"):
        """ Teams user activity report
            https://docs.microsoft.com/en-us/graph/api/resources/microsoft-teams-user-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getTeamsUserActivityUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "User Principal Name": "upn",
        }
        row_fields = [
            {
                "column_name": "Team Chat Message Count",
                "metric_name": "{}.teams.activity.team_chat_messages".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Private Chat Message Count",
                "metric_name": "{}.teams.activity.private_chat_messages".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Call Count",
                "metric_name": "{}.teams.activity.calls".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Meeting Count",
                "metric_name": "{}.teams.activity.meetings".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.teams.activity.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:teams"],
                )
        return

    ###############################################################################################
    ## Microsoft 365 Outlook
    ###############################################################################################
    def report_outlook_activity(self, instance, period="d7"):
        """ Email activity report
            https://docs.microsoft.com/en-us/graph/api/resources/email-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getEmailActivityUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "User Principal Name": "upn",
            "Display Name": "display_name",
        }
        row_fields = [
            {
                "column_name": "Read Count",
                "metric_name": "{}.outlook.activity.reads".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Send Count",
                "metric_name": "{}.outlook.activity.sends".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Receive Count",
                "metric_name": "{}.outlook.activity.receives".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.outlook.activity.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:outlook"],
                )
        return

    def report_outlook_devices(self, instance, period="d7"):
        """ Email app usage report
            https://docs.microsoft.com/en-us/graph/api/resources/email-app-usage-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getEmailAppUsageUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        app_fields = [
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
        tag_fields = {
            "User Principal Name": "upn",
            "Display Name": "display_name",
        }
        row_fields = [
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.outlook.device.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            }
        ]

        for name in app_fields:
            row_fields.append(
                {
                    "column_name": "{}".format(name),
                    "metric_name": "{}.outlook.device".format(prefix),
                    "metric_type": "gauge",
                    "parser_func": "parse_present",
                    "append_tags": ["device:{}".format(name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:outlook"],
                )
        return

    def report_outlook_usage(self, instance, period="d7"):
        """ Mailbox usage report
            https://docs.microsoft.com/en-us/graph/api/resources/mailbox-usage-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getMailboxUsageDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "User Principal Name": "upn",
            "Display Name": "display_name",
        }
        row_fields = [
            {
                "column_name": "Item Count",
                "metric_name": "{}.outlook.usage.items".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Storage Used (Byte)",
                "metric_name": "{}.outlook.usage.storage_used".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Deleted Item Count",
                "metric_name": "{}.outlook.usage.deleted_items".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Deleted Item Size (Byte)",
                "metric_name": "{}.outlook.usage.deleted_size".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Issue Warning Quota (Byte)",
                "metric_name": "{}.outlook.usage.issue_warning_quota".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Prohibit Send Quota (Byte)",
                "metric_name": "{}.outlook.usage.prohibit_send_quota".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Prohibit Send/Receive Quota (Byte)",
                "metric_name": "{}.outlook.usage.prohibit_send_receive_quota".format(
                    prefix
                ),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.outlook.usage.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]
        ## Need computed metrics for overages on quotas ?? ##

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:outlook"],
                )
        return

    ###############################################################################################
    ## Microsoft 365 OneDrive
    ###############################################################################################
    def report_onedrive_activity(self, instance, period="d7"):
        """ OneDrive activity report
            https://docs.microsoft.com/en-us/graph/api/resources/onedrive-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getOneDriveActivityUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "User Principal Name": "upn",
        }
        row_fields = [
            {
                "column_name": "Viewed Or Edited File Count",
                "metric_name": "{}.onedrive.activity.viewed_or_edited_files".format(
                    prefix
                ),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Synced File Count",
                "metric_name": "{}.onedrive.activity.synced_files".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Shared Internally File Count",
                "metric_name": "{}.onedrive.activity.internal_shared_files".format(
                    prefix
                ),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Shared Externally File Count",
                "metric_name": "{}.onedrive.activity.external_shared_files".format(
                    prefix
                ),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.onedrive.activity.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:onedrive"],
                )
        return

    def report_onedrive_usage(self, instance, period="d7"):
        """ OneDrive usage report
            https://docs.microsoft.com/en-us/graph/api/resources/onedrive-usage-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getOneDriveUsageAccountDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "User Principal Name": "upn",
            "Display Name": "display_name",
            "Owner Display Name": "owner_display_name",
            "Owner Principal Name": "owner_principal_name",
            "Site URL": "onedrive",
        }
        row_fields = [
            {
                "column_name": "File Count",
                "metric_name": "{}.onedrive.usage.files".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Active File Count",
                "metric_name": "{}.onedrive.usage.active_files".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Storage Used (Byte)",
                "metric_name": "{}.onedrive.usage.storage_used".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Storage Allocated (Byte)",
                "metric_name": "{}.onedrive.usage.storage_allocated".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.onedrive.usage.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:onedrive"],
                )
        return

    ###############################################################################################
    ## Microsoft 365 SharePoint
    ###############################################################################################
    def report_sharepoint_activity(self, instance, period="d7"):
        """ SharePoint activity report
            https://docs.microsoft.com/en-us/graph/api/resources/sharepoint-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSharePointActivityUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "User Principal Name": "upn",
        }
        row_fields = [
            {
                "column_name": "Viewed Or Edited File Count",
                "metric_name": "{}.sharepoint.activity.viewed`_or_edited_files".format(
                    prefix
                ),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Synced File Count",
                "metric_name": "{}.sharepoint.activity.synced_files".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Shared Internally File Count",
                "metric_name": "{}.sharepoint.activity.internal_shared_files".format(
                    prefix
                ),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Shared Externally File Count",
                "metric_name": "{}.sharepoint.activity.external_shared_files".format(
                    prefix
                ),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Visited Page Count",
                "metric_name": "{}.sharepoint.activity.visited_pages".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.sharepoint.activity.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:sharepoint"],
                )
        return

    def report_sharepoint_usage(self, instance, period="d7"):
        """ SharePoint site usage report
            https://docs.microsoft.com/en-us/graph/api/resources/sharepoint-site-usage-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSharePointSiteUsageDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "User Principal Name": "upn",
            "Display Name": "display_name",
            "Owner Display Name": "owner_display_name",
            "Owner Principal Name": "owner_principal_name",
            "Site Id": "site_id",
            "Site URL": "site_url",
            "Root Web Template": "root_web_template",
        }
        row_fields = [
            {
                "column_name": "File Count",
                "metric_name": "{}.sharepoint.usage.files".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Active File Count",
                "metric_name": "{}.sharepoint.usage.active_files".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Storage Used (Byte)",
                "metric_name": "{}.sharepoint.usage.storage_used".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Storage Allocated (Byte)",
                "metric_name": "{}.sharepoint.usage.storage_allocated".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Page View Count",
                "metric_name": "{}.sharepoint.usage.page_views".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Visited Page Count",
                "metric_name": "{}.sharepoint.usage.visited_pages".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.sharepoint.usage.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:sharepoint"],
                )
        return

    ###############################################################################################
    ## Microsoft 365 Skype For Business
    ###############################################################################################
    def report_skype_activity(self, instance, period="d7"):
        """ Skype For Business activity report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessActivityUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "User Principal Name": "upn",
        }
        met_fields = [
            "Total Peer-to-peer Session Count",
            "Total Participated Conference Count",
            "Total Organized Conference Count",
            "Peer-to-peer IM Count",
            "Peer-to-peer Audio Count",
            "Peer-to-peer Audio Minutes",
            "Peer-to-peer Video Count",
            "Peer-to-peer Video Minutes",
            "Peer-to-peer App Sharing Count",
            "Peer-to-peer File Transfer Count",
            "Organized Conference IM Count",
            "Organized Conference Audio/Video Count",
            "Organized Conference Audio/Video Minutes",
            "Organized Conference App Sharing Count",
            "Organized Conference Web Count",
            "Organized Conference Dial-in/out 3rd Party Count",
            "Organized Conference Dial-in/out Microsoft Count",
            "Organized Conference Dial-in Microsoft Minutes",
            "Organized Conference Dial-out Microsoft Minutes",
            "Participated Conference IM Count",
            "Participated Conference Audio/Video Count",
            "Participated Conference Audio/Video Minutes",
            "Participated Conference App Sharing Count",
            "Participated Conference Web Count",
            "Participated Conference Dial-in/out 3rd Party Count",
        ]
        row_fields = [
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.skype.activity.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            }
        ]

        for name in met_fields:
            terminus = name.split(" ")[-1]
            row_fields.append(
                {
                    "column_name": name,
                    "metric_name": "{}.skype.activity.{}".format(
                        prefix, terminus.lower()
                    ),
                    "default_val": 0.0,
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["{}:{}".format("skype_type", name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    def report_skype_devices(self, instance, period="d7"):
        """ Skype For Business device usage report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-device-usage-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessDeviceUsageUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        app_fields = ["Windows", "Windows Phone", "Android Phone", "iPhone", "iPad"]
        tag_fields = {
            "User Principal Name": "upn",
        }
        row_fields = [
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.skype.device.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            }
        ]

        for name in app_fields:
            row_fields.append(
                {
                    "column_name": "{}".format(name),
                    "metric_name": "{}.skype.device".format(prefix),
                    "metric_type": "gauge",
                    "parser_func": "parse_boolean",
                    "append_tags": ["device:{}".format(name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    def report_skype_organizer_sessions(self, instance, period="d7"):
        """ Skype For Business organizer activity report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-organizer-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessOrganizerActivityCounts(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {}
        met_fields = [
            "IM",
            "Audio/Video",
            "App Sharing",
            "Web",
            "Dial-in/out 3rd Party",
            "Dian-in/out Microsoft",
        ]
        row_fields = []

        for name in met_fields:
            row_fields.append(
                {
                    "column_name": name,
                    "metric_name": "{}.skype.organizer.sessions".format(prefix),
                    "default_val": 0.0,
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["{}:{}".format("skype_type", name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    def report_skype_organizer_users(self, instance, period="d7"):
        """ Skype For Business organizer activity user report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-organizer-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessOrganizerActivityUserCounts(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {}
        met_fields = [
            "IM",
            "Audio/Video",
            "App Sharing",
            "Web",
            "Dial-in/out 3rd Party",
            "Dian-in/out Microsoft",
        ]
        row_fields = []

        for name in met_fields:
            row_fields.append(
                {
                    "column_name": name,
                    "metric_name": "{}.skype.organizer.users".format(prefix),
                    "default_val": 0.0,
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["{}:{}".format("skype_type", name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    def report_skype_organizer_minutes(self, instance, period="d7"):
        """ Skype For Business organizer activity minutes report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-organizer-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessOrganizerActivityMinuteCounts(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {}
        met_fields = [
            "Audio/Video",
            "Dial-in Microsoft",
            "Dian-out Microsoft",
        ]
        row_fields = []

        for name in met_fields:
            row_fields.append(
                {
                    "column_name": name,
                    "metric_name": "{}.skype.organizer.minutes".format(prefix),
                    "default_val": 0.0,
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["{}:{}".format("skype_type", name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    def report_skype_participant_sessions(self, instance, period="d7"):
        """ Skype For Business participant activity report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-participant-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessParticipantActivityCounts(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {}
        met_fields = [
            "IM",
            "Audio/Video",
            "App Sharing",
            "Web",
            "Dial-in/out 3rd Party",
        ]
        row_fields = []

        for name in met_fields:
            row_fields.append(
                {
                    "column_name": name,
                    "metric_name": "{}.skype.participant.sessions".format(prefix),
                    "default_val": 0.0,
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["{}:{}".format("skype_type", name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    def report_skype_participant_users(self, instance, period="d7"):
        """ Skype For Business Participant activity user report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-participant-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessParticipantActivityUserCounts(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {}
        met_fields = [
            "IM",
            "Audio/Video",
            "App Sharing",
            "Web",
            "Dial-in/out 3rd Party",
        ]
        row_fields = []

        for name in met_fields:
            row_fields.append(
                {
                    "column_name": name,
                    "metric_name": "{}.skype.participant.users".format(prefix),
                    "default_val": 0.0,
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["{}:{}".format("skype_type", name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    def report_skype_participant_minutes(self, instance, period="d7"):
        """ Skype For Business participant activity minutes report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-participant-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessParticipantActivityMinuteCounts(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {}
        met_fields = ["Audio/Video"]
        row_fields = []

        for name in met_fields:
            row_fields.append(
                {
                    "column_name": name,
                    "metric_name": "{}.skype.participant.minutes".format(prefix),
                    "default_val": 0.0,
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["{}:{}".format("skype_type", name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    def report_skype_p2p_sessions(self, instance, period="d7"):
        """ Skype For Business peer-to-peer activity report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-peer-to-peer-activity?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessPeerToPeerActivityCounts(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {}
        met_fields = [
            "IM",
            "Audio",
            "Video",
            "App Sharing",
            "File Transfer",
        ]
        row_fields = []

        for name in met_fields:
            row_fields.append(
                {
                    "column_name": name,
                    "metric_name": "{}.skype.p2p.sessions".format(prefix),
                    "default_val": 0.0,
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["{}:{}".format("skype_type", name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    def report_skype_p2p_users(self, instance, period="d7"):
        """ Skype For Business peer-to-peer activity user report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-peer-to-peer-activity?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessPeerToPeerActivityUserCounts(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {}
        met_fields = [
            "IM",
            "Audio",
            "Video",
            "App Sharing",
            "File Transfer",
        ]
        row_fields = []

        for name in met_fields:
            row_fields.append(
                {
                    "column_name": name,
                    "metric_name": "{}.skype.p2p.users".format(prefix),
                    "default_val": 0.0,
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["{}:{}".format("skype_type", name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    def report_skype_p2p_minutes(self, instance, period="d7"):
        """ Skype For Business peer-to-peer activity minutes report
            https://docs.microsoft.com/en-us/graph/api/resources/skype-for-business-peer-to-peer-activity?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getSkypeForBusinessPeerToPeerActivityMinuteCounts(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {}
        met_fields = [
            "Audio",
            "Video",
        ]
        row_fields = []

        for name in met_fields:
            row_fields.append(
                {
                    "column_name": name,
                    "metric_name": "{}.skype.p2p.minutes".format(prefix),
                    "default_val": 0.0,
                    "metric_type": "gauge",
                    "parser_func": "parse_float",
                    "append_tags": ["{}:{}".format("skype_type", name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:skype"],
                )
        return

    ###############################################################################################
    ## Microsoft 365 Yammer
    ###############################################################################################
    def report_yammer_activity(self, instance, period="d7"):
        """ Yammer activity report
            https://docs.microsoft.com/en-us/graph/api/resources/yammer-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getYammerActivityUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "User Principal Name": "upn",
            "Display Name": "display_name",
            "User State": "user_state",
        }
        row_fields = [
            {
                "column_name": "Posted Count",
                "metric_name": "{}.yammer.activity.posted".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Read Count",
                "metric_name": "{}.yammer.activity.reads".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Liked Count",
                "metric_name": "{}.yammer.activity.likes".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.yammer.activity.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "State Change Date",
                "metric_name": "{}.yammer.activity.state_changed".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:yammer"],
                )
        return

    def report_yammer_devices(self, instance, period="d7"):
        """ Yammer device usage report
            https://docs.microsoft.com/en-us/graph/api/resources/yammer-device-usage-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getYammerDeviceUsageUserDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        app_fields = [
            "Web",
            "Windows Phone",
            "Android Phone",
            "iPhone",
            "iPad",
            "Others",
        ]
        tag_fields = {
            "User Principal Name": "upn",
            "Display Name": "display_name",
            "User State": "user_state",
        }
        row_fields = [
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.yammer.device.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
            {
                "column_name": "State Change Date",
                "metric_name": "{}.yammer.device.state_changed".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        for name in app_fields:
            row_fields.append(
                {
                    "column_name": "{}".format(name),
                    "metric_name": "{}.yammer.device".format(prefix),
                    "metric_type": "gauge",
                    "parser_func": "parse_present",
                    "append_tags": ["device:{}".format(name)],
                }
            )

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:yammer"],
                )
        return

    def report_yammer_groups(self, instance, period="d7"):
        """ Yammer groups activity report
            https://docs.microsoft.com/en-us/graph/api/resources/yammer-groups-activity-reports?view=graph-rest-1.0
        """

        url = "https://graph.microsoft.com/v1.0/reports/getYammerGroupsActivityDetail(period='{}')".format(
            period
        )
        token = self.reports_token.get("access_token", None)
        headers = {"Authorization": "Bearer {}".format(token)}
        proxies = self.get_instance_proxy(instance, url)

        prefix = self.metric_prefix
        tag_fields = {
            "Owner Principal Name": "owner_principal_name",
            "Owner Principal Name": "upn",
            "Group Display Name": "group_display_name",
            "Group Display Name": "display_name",
            "Group Type": "group_type",
            "Office 365 Connected": "office_365_connected",
        }
        row_fields = [
            {
                "column_name": "Member Count",
                "metric_name": "{}.yammer.group.members".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Posted Count",
                "metric_name": "{}.yammer.group.posts".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Read Count",
                "metric_name": "{}.yammer.group.reads".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Liked Count",
                "metric_name": "{}.yammer.group.likes".format(prefix),
                "default_val": 0.0,
                "metric_type": "gauge",
                "parser_func": "parse_float",
            },
            {
                "column_name": "Last Activity Date",
                "metric_name": "{}.yammer.group.last_activity".format(prefix),
                "metric_type": "gauge",
                "parser_func": "parse_elapsed_days",
            },
        ]

        with requests.get(url, headers=headers, proxies=proxies, stream=True) as r:
            r.raise_for_status()
            lines = (line.decode("utf-8") for line in r.iter_lines())
            for row in csv.DictReader(lines):
                """ Metrics """
                self.csv_row_to_metrics(
                    row=row,
                    tag_fields=tag_fields,
                    row_fields=row_fields,
                    tags=self.tags + ["o365_app:yammer"],
                )
        return

    ###############################################################################################
    ## Synthetics :: Email
    ###############################################################################################
    def get_email_synthetic_metrics(self, instance):
        checkin_url = "https://email.synth-rapdev.io/checkin"
        metrics_url = "https://email.synth-rapdev.io/metrics"
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.synthetic_email_api_key,
        }

        prefix = self.metric_prefix
        email_address = self.instance.get("email_address")

        """ /checkin """
        proxies = self.get_instance_proxy(instance, checkin_url)
        res = requests.post(
            checkin_url,
            headers=headers,
            json={
                "emailAddress": email_address,
                "checkVersion": self.check_version,
            },
            proxies=proxies,
        )
        res.raise_for_status()

        """ /metrics """
        proxies = self.get_instance_proxy(instance, metrics_url)
        res = requests.post(
            metrics_url,
            headers=headers,
            json={"emailAddress": email_address},
            proxies=proxies,
        )
        res.raise_for_status()

        metrics = res.json()

        for metric in metrics:
            metric_tags = self.tags.copy()
            metric_tags.append("{}:{}".format("email", metric.get("emailAddress")))
            metric_tags.append("{}:{}".format("mailbox", metric.get("emailAddress")))
            metric_tags.append("{}:{}".format("cloud", "aws"))
            metric_tags.append("{}:{}".format("region", metric.get("sourceRegion")))

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
    def get_calendar_synthetic_metrics(self, instance):
        metric_prefix = "{}.synthetic".format(self.metric_prefix)
        token = self.synthetics_token.get("access_token", None)
        graph_url = "https://graph.microsoft.com/v1.0"

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
        proxies = self.get_instance_proxy(instance, url)
        res = self.get_synthetic_http_metric(
            metric_prefix,
            "GET",
            url,
            headers,
            proxies,
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

            proxies = self.get_instance_proxy(instance, url)
            res = self.get_synthetic_http_metric(
                metric_prefix,
                "POST",
                url,
                headers,
                proxies,
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

                proxies = self.get_instance_proxy(instance, url)
                res = self.get_synthetic_http_metric(
                    metric_prefix,
                    "PATCH",
                    url,
                    headers,
                    proxies,
                    json.dumps(data, default=str),
                    metric_tags + ["operation:update"],
                )

                """ [Delete] calendar event"""
                url = "{}/users/{}/calendar/events/{}".format(
                    graph_url, username, event_id
                )
                proxies = self.get_instance_proxy(instance, url)
                res = self.get_synthetic_http_metric(
                    metric_prefix,
                    "DELETE",
                    url,
                    headers,
                    proxies,
                    json.dumps(data, default=str),
                    metric_tags + ["operation:delete"],
                )
        return

    ###############################################################################################
    ## Synthetics :: OneDrive
    ###############################################################################################
    def get_onedrive_synthetic_metrics(self, instance):
        metric_prefix = "{}.synthetic".format(self.metric_prefix)
        token = self.synthetics_token.get("access_token", None)
        graph_url = "https://graph.microsoft.com/v1.0"
        username = self.instance.get("username")

        metric_tags = self.tags.copy()
        metric_tags.append("upn:{}".format(username))
        metric_tags.append("o365_app:{}".format("OneDrive"))

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token),
        }

        """ [Read] User's OneDrive """
        url = "{}/users/{}/drive".format(graph_url, username)
        proxies = self.get_instance_proxy(instance, url)
        res = self.get_synthetic_http_metric(
            metric_prefix,
            "GET",
            url,
            headers,
            proxies,
            None,
            metric_tags + ["operation:read"],
        )

        if res:
            drive_id = res.get("id")
            drive_dt = datetime.now(tz=timezone.utc)
            drive_ts = int(drive_dt.replace(tzinfo=timezone.utc).timestamp())

            """ Random 4MB file content (supported Graph API non-stream max) """
            content = "".join([choice(ascii_letters) for i in range(4000000)])
            metric_tags.append("file_size:{}".format(len(content)))

            """ [Create] OneDrive item (upload) """
            url = "{}/users/{}/drive/root:/ddagent-synthetic/dd-agent-{}.txt:/content".format(
                graph_url, username, drive_ts
            )
            proxies = self.get_instance_proxy(instance, url)
            res = self.get_synthetic_http_metric(
                metric_prefix,
                "PUT",
                url,
                headers,
                proxies,
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

                proxies = self.get_instance_proxy(instance, url)
                res = self.get_synthetic_http_metric(
                    metric_prefix,
                    "PATCH",
                    url,
                    headers,
                    proxies,
                    json.dumps(data, default=str),
                    metric_tags + ["operation:update"],
                )

                """ [Delete] OneDrive item """
                url = "{}/users/{}/drive/items/{}".format(
                    graph_url, username, drive_item_id
                )
                proxies = self.get_instance_proxy(instance, url)
                res = self.get_synthetic_http_metric(
                    metric_prefix,
                    "DELETE",
                    url,
                    headers,
                    proxies,
                    None,
                    metric_tags + ["operation:delete"],
                )
        return

    ###############################################################################################
    ## Synthetics :: Teams
    ###############################################################################################
    def get_teams_synthetic_metrics(self, instance):
        metric_prefix = "{}.synthetic".format(self.metric_prefix)
        token = self.synthetics_token.get("access_token", None)
        graph_url = "https://graph.microsoft.com/v1.0"
        username = self.instance.get("username")

        metric_tags = self.tags.copy()
        metric_tags.append("upn:{}".format(username))
        metric_tags.append("o365_app:{}".format("teams"))

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token),
        }

        """ [Read] User's joined teams """
        url = "{}/me/joinedTeams".format(graph_url)
        proxies = self.get_instance_proxy(instance, url)
        res = requests.get(url, headers=headers, proxies=proxies)
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
            proxies = self.get_instance_proxy(instance, url)
            res = self.get_synthetic_http_metric(
                metric_prefix,
                "GET",
                url,
                headers,
                proxies,
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
                proxies = self.get_instance_proxy(instance, url)
                res = self.get_synthetic_http_metric(
                    metric_prefix,
                    "POST",
                    url,
                    headers,
                    proxies,
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
                    proxies = self.get_instance_proxy(instance, url)
                    res = self.get_synthetic_http_metric(
                        metric_prefix,
                        "POST",
                        url,
                        headers,
                        proxies,
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
