import datetime
import json
from xml.sax.saxutils import escape

import lxml.etree as ET
import pytz
from dateutil import tz
from dateutil.parser import parse
from requests.exceptions import ConnectionError, HTTPError, InvalidURL, Timeout

from datadog_checks.base import AgentCheck, ConfigurationError

from .const import EVENT_TYPES, STATES, XML_NODES


class WorkdayCheck(AgentCheck):
    check_delay = 0
    persistent_cache_key = "workday_saved_integrations"

    def __init__(self, name, init_config, instances):
        super(WorkdayCheck, self).__init__(name, init_config, instances)
        self._url = self.instance.get('url', '')
        self.user = self.instance.get('user', '')
        self.last_invoke_date = datetime.datetime.now(tz=tz.tzlocal())
        self.tenant = self.instance.get('tenant', '')
        self.password = self.instance.get('password', '')
        self._tags = self.instance.get('tags', [])
        self.integrations = []
        self.integrations_dict = {}
        self._min_collection_interval = self.instance.get('min_collection_interval', 600)
        self._headers = {'Content-Type': 'application/soap+xml'}
        if not self._url:
            raise ConfigurationError('Configuration error, Workday url is required.')
        if not self.tenant or not self.password or not self.user:
            raise ConfigurationError('Configuration error, Workday user, password and tenant credentials are required.')
        self.check_initializations.append(self.integrations_load)

    def sendlogs(self, log):
        api_key = self.instance.get("api_key")
        datadog_site = self.instance.get("site", "datadoghq.com")
        headers = {
            'Content-Type': 'application/json',
            'DD-API-KEY': api_key,
        }
        try:
            self.http.post('https://http-intake.logs.%s/v1/input' % datadog_site, headers=headers, json=log)
        except Exception:
            pass

    def check(self, _):
        try:
            integration_event_response = self.getEvents(
                "", "999", "1", self._min_collection_interval + self.check_delay
            )
        except Timeout as e:
            self.service_check(
                "avmconsulting.workday.can_connect",
                self.CRITICAL,
                tags=self._tags + ["workday_tenant:" + self.tenant],
                message="Request timeout: {}, {}".format(self._url, e),
            )
            Errmsg = "avmconsulting_workday: {},{}".format(self._url, e)
            self.log.error(Errmsg)
            return
        except (HTTPError, InvalidURL, ConnectionError) as e:
            self.service_check(
                "avmconsulting.workday.can_connect",
                self.CRITICAL,
                tags=self._tags + ["workday_tenant:" + self.tenant],
                message="Request failed: {}, {}".format(self._url, e),
            )
            Errmsg = "avmconsulting_workday: {},{}".format(self._url, e)
            self.log.error(Errmsg)
            return
        content = ET.XML(integration_event_response.content)
        content = namespace_strip(content).getroot()
        try:
            str(content.find(XML_NODES['Integration_Events_Response']).text)
            self.service_check(
                "avmconsulting.workday.can_connect", self.OK, tags=self._tags + ["workday_tenant:" + self.tenant]
            )
            self.check_delay = 0
            self.last_invoke_date = datetime.datetime.now(tz=tz.tzlocal()) - datetime.timedelta(
                seconds=(self._min_collection_interval / 2)
            )
        except Exception:
            self.service_check(
                "avmconsulting.workday.can_connect",
                self.CRITICAL,
                tags=self._tags + ["workday_tenant:" + self.tenant],
                message="Maintenance",
            )
            Errmsg = "avmconsulting_workday:MAINTENANCE {}".format(self._url)
            self.log.error(Errmsg)
            return
        events = content.findall(XML_NODES['Integration_Event'])
        events.reverse()
        for event in events:
            try:
                str(event.find(XML_NODES['Integration_System_ID']).text)
            except Exception:
                continue
            integration_full = str(
                event.find(XML_NODES['Integration_System_Reference']).find(XML_NODES['Integration_System_ID']).text
            )
            state = str(event.find(XML_NODES['Integration_Status']).text)
            integration = self.splitter(integration_full)
            event_id = str(event.find(XML_NODES['Integration_Event_ID']).text)
            event_type = "Other"
            for key in EVENT_TYPES:
                if key in event_id:
                    event_type = EVENT_TYPES[key]
            init_date_str = str(event.find(XML_NODES['Initiated_DateTime']).text)
            init_date = parse(init_date_str)
            if not (state in STATES) or (
                (integration in self.integrations_dict)
                and (parse(self.integrations_dict[integration]["date"]) >= init_date)
            ):
                continue
            completed_date = parse(event.find(XML_NODES['Completed_DateTime']).text)
            self.count(
                "avmconsulting.workday.total_jobs",
                1,
                tags=self._tags
                + ["workday.integration_name:" + integration, "workday_tenant:" + self.tenant, "type:" + event_type],
            )
            self.count(
                "datadog.marketplace.avmconsulting.workday",
                1,
                tags=self._tags
                + [
                    "workday_tenant:" + self.tenant,
                    "job_id:" + event_id,
                ],
            )
            if STATES[state] > STATES['CompletedWithWarnings']:
                self.count(
                    "avmconsulting.workday.failed_jobs",
                    1,
                    tags=self._tags
                    + [
                        "workday.integration_name:" + integration,
                        "workday_tenant:" + self.tenant,
                        "type:" + event_type,
                    ],
                )
            self.histogram(
                "avmconsulting.workday.duration",
                (completed_date - init_date).seconds,
                tags=self._tags
                + ["workday.integration_name:" + integration, "workday_tenant:" + self.tenant, "type:" + event_type],
            )
            logs = event.findall(XML_NODES['Logs'])
            if len(logs) > 0:
                jsonlogs = []
                for log in logs:
                    timestamp = init_date.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    severity = str(log.find(XML_NODES['Message_Severity_Level']).text)
                    message = str(log.find(XML_NODES['Message_Summary']).text).replace('"', '')
                    jsonlogs.append(
                        {
                            'timestamp': timestamp,
                            'level': severity,
                            'ddtags': 'workday.integration_name:%s,source:workday,type:%s'
                            % (integration.lower(), event_type),
                            'event_id': event_id,
                            'message': message,
                            'workday_tenant': self.tenant,
                        }
                    )
                del logs
                self.sendlogs(jsonlogs)
            self.integrations_dict.update(
                {integration: {"state": state, "date": init_date_str, "new": True, "type": event_type}}
            )
        del events
        clear(content)
        self.integrations_unload()

    def splitter(self, item, symbol="/", position=0):
        return item.split(symbol)[position]

    def integrations_unload(self):
        self.cleanOld()
        self.write_persistent_cache(self.persistent_cache_key, json.dumps(self.integrations_dict))
        for integration, info in self.integrations_dict.items():
            if info["state"] in STATES and info["new"]:
                self.service_check(
                    "avmconsulting.workday.integration.state",
                    STATES[info["state"]],
                    tags=self._tags
                    + [
                        "workday.integration_name:" + integration,
                        "workday_tenant:" + self.tenant,
                        "type" + info["type"],
                    ],
                    message=info["state"] if info["state"] != "Completed" else None,
                )

    def cleanOld(self):
        try:
            for integration in list(self.integrations_dict):
                if (
                    parse(self.integrations_dict[integration]["date"]) + datetime.timedelta(days=10)
                ) < datetime.datetime.now():
                    del self.integrations_dict[integration]
        except Exception:
            pass

    def integrations_load(self):
        try:
            persistent_cache = self.read_persistent_cache(self.persistent_cache_key)
            self.integrations_dict = json.loads(persistent_cache)
        except Exception:
            pass

    def getSecurity(self):
        security = """
    xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
        <env:Header>
        <wsse:Security env:mustUnderstand="1">
            <wsse:UsernameToken>
                <wsse:Username>%s@%s</wsse:Username>
                <wsse:Password
                    Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">%s</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </env:Header>
"""
        return security % (self.user, self.tenant, escape(self.password))

    def getEvents(self, WDintegration="", Count="1", Page="1", Interval=15):
        Request_Criteria = ""
        if WDintegration != "":
            Request_Criteria = """
<wd:Integration_System_Reference><wd:ID wd:type="Integration_System_ID">{}/wd:ID></wd:Integration_System_Reference>
            """.format(
                WDintegration
            )
        else:
            timezone = datetime.datetime.now(tz=tz.tzlocal()).strftime("%z")
            timezone = timezone[:3] + ":" + timezone[3:]
            dateReq = (self.last_invoke_date - datetime.timedelta(seconds=Interval)).strftime(
                "%Y-%m-%dT%H:%M:%S"
            ) + timezone
            Request_Criteria = """
<wd:Sent_After>{}</wd:Sent_After>
            """.format(
                dateReq
            )
        data = """
<env:Envelope
    xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
                        %s
           <env:Body>
        <wd:Get_Integration_Events_Request wd:version="v35.2" xmlns:wd="urn:com.workday/bsvc">
<wd:Request_Criteria>
%s
</wd:Request_Criteria>
<wd:Response_Filter>
                <wd:Page>%s</wd:Page>
                <wd:Count>%s</wd:Count>
            </wd:Response_Filter>
        </wd:Get_Integration_Events_Request>
    </env:Body>
</env:Envelope>
"""
        data = data % (self.getSecurity(), Request_Criteria, Page, Count)
        r = self.http.post(self._url, headers=self._headers, data=data)
        r.raise_for_status()
        return r


def namespace_strip(xmldoc):
    xslt = '''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" indent="no"/>

<xsl:template match="/|comment()|processing-instruction()">
    <xsl:copy>
      <xsl:apply-templates/>
    </xsl:copy>
</xsl:template>

<xsl:template match="*">
    <xsl:element name="{local-name()}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
</xsl:template>

<xsl:template match="@*">
    <xsl:attribute name="{local-name()}">
      <xsl:value-of select="."/>
    </xsl:attribute>
</xsl:template>
</xsl:stylesheet>
'''
    xslt_doc = ET.XML(xslt)
    transform = ET.XSLT(xslt_doc)
    result = transform(xmldoc)
    clear(xmldoc)
    return result


def clear(content):
    for elem in content:
        elem.clear()
    for ancestor in elem.xpath('ancestor-or-self::*'):
        while ancestor.getprevious() is not None:
            del ancestor.getparent()[0]
    del content
