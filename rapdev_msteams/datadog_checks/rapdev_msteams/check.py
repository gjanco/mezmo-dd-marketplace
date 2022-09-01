# (C) Datadog, Inc. 2022-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import json, traceback, re

from typing import Any
from dateutil.parser import parse
from datetime import datetime, timedelta, timezone
from datadog_checks.base import AgentCheck
from requests.exceptions import ConnectionError, HTTPError, InvalidURL, Timeout

REQUIRED_TAGS = [
    "vendor:rapdev",
]

DEFAULTS = {
    "EXPIRE_WINDOW": 180,
    "RENEWAL_WINDOW": 90,
    "MSGRAPH_BASEURL": "https://graph.microsoft.com",
    "NOTIFICATIONS_BASEURL": "https://msgraph-subscriptions-notifications.synth-rapdev.io",
}

MEDIA_NETWORK_FIELDS = [
    "linkspeed", 
    "wifiSignalStrength", 
    "wifiBatteryCharge", 
    "sentQualityEventRatio",
    "receivedQualityEventRatio",
    "delayEventRatio",
    "bandwidthLowEventRatio",
]

MEDIA_DEVICE_FIELDS = [
    "sentSignalLevel",
    "receivedSignalLevel",
    "sentNoiseLevel",
    "receivedNoiseLevel",
    "initialSignalLevelRootMeanSquare",
    "cpuInsufficentEventRatio",
    "renderNotFunctioningEventRatio",
    "captureNotFunctioningEventRatio",
    "deviceGlitchEventRatio",
    "lowSpeechToNoiseEventRatio",
    "lowSpeechLevelEventRatio",
    "deviceClippingEventRatio",
    "howlingEventCount",
    "renderZeroVolumeEventRatio",
    "renderMuteEventRatio",
    "micGlitchRate",
    "speakerGlitchRate",
]

MEDIA_STREAM_FIELDS = [
    "averageAudioDegradation",
    "averageJitter",
    "maxJitter",
    "averagePacketLossRate",
    "maxPacketLossRate",
    "averageRatioOfConcealedSamples",
    "maxRatioOfConcealedSamples",
    "averageRoundTripTime",
    "maxRoundTripTime",
    "packetUtilization",
    "averageBandwidthEstimate",
    "wasMediaBypassed",
    "postForwardErrorCorrectionPacketLossRate",
    "averageVideoFrameLossPercentage",
    "averageReceivedFrameRate",
    "lowFrameRateRatio",
    "averageVideoPacketLossRate",
    "averageVideoFrameRate",
    "lowVideoProcessingCapabilityRatio",
    "averageAudioNetworkJitter",
    "maxAudioNetworkJitter",
]

class MSTeamsCheck(AgentCheck):

    def __init__(self, name, init_config, instances):
        super(MSTeamsCheck, self).__init__(name, init_config, instances)

        self.metric_prefix = "rapdev.msteams"
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.metric_prefix)
        self.service_check_name = "{}.status".format(self.metric_prefix)
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.tags.append("{}:{}".format("tenant_id", self.instance.get("tenant_id")))

        self.msgraph_baseurl = self.instance.get("msgraph_baseurl", 
            DEFAULTS["MSGRAPH_BASEURL"])
        self.notifications_baseurl = self.instance.get("notifications_baseurl", 
            DEFAULTS["NOTIFICATIONS_BASEURL"])
        self.renewal_window = self.instance.get("renewal_window", 
            DEFAULTS["RENEWAL_WINDOW"])
        self.expire_window = self.instance.get("expire_window", 
            DEFAULTS["EXPIRE_WINDOW"])

        self.subscription = {}
        self.msgraph_token = {}
        self.resources = {}
        self.processed = []
        return

    def check(self, _):
        self.do_service_check("MicrosoftGraph.Authorization", "set_msgraph_token", True)
        self.do_service_check("MicrosoftGraph.Subscription", "renew_subscription", True)
        self.do_service_check("Notifications.Resources.Fetch", "fetch_resources", True)
        self.do_service_check("MicrosoftGraph.CallRecords", "process_resources", True)
        self.do_service_check("Notifications.Resources.Update", "update_resources", True)
        return

    def do_service_check(self, check, function, enabled=True):
        """ Agent.service_check() wrapper. """
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
            self.service_check(self.service_check_name, AgentCheck.CRITICAL, message=m, 
                tags=check_tags)
        else:
            self.service_check(self.service_check_name, AgentCheck.OK, tags=check_tags )
        return

    def check_http_response(self, res):
        try:
            res.raise_for_status()
        except HTTPError as e:
            m = "HTTP response error: {}".format(res.text)
            self.log.error(m)
            raise e
        except Exception as e:
            raise e
        return

    def set_msgraph_token(self):
        """ Fetch Microsoft Login oauth2 token scoped for msgraph. """
        tenant_id = self.instance.get("tenant_id", None)
        client_id = self.instance.get("client_id", None)
        client_secret = self.instance.get("client_secret", None)

        url = "https://login.microsoftonline.com/{}/oauth2/v2.0/token".format(tenant_id)
        data = {
            "scope": "{}/.default".format(self.msgraph_baseurl),
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        res = self.http.post(url, data=data)
        res.raise_for_status()
        self.msgraph_token = res.json()
        return

    def subscription_expires_in(self, minutes):
        """ Check if subscription expires in time window (minutes). """
        iso_utc_now = datetime.strftime(datetime.utcnow(), "%Y-%m-%dT%H:%M:%S.%fZ")
        iso_expires = self.subscription.get("expirationDateTime", iso_utc_now)
        dto_expires = parse(iso_expires)
        dto_current = parse(iso_utc_now) # laziness
        if (dto_expires - dto_current) < timedelta(minutes=minutes):
            return True
        return False

    def set_subscription(self, subscription_id):
        """ Set subscription from MSGraph API. """
        if not subscription_id:
            self.subscription = {}
            return

        access_token = self.msgraph_token.get("access_token", "")
        url = "{}/v1.0/subscriptions/{}".format(self.msgraph_baseurl, subscription_id)
        headers = {
            "Authorization": "Bearer {}".format(access_token),
        }

        try:
            res = self.http.get(url, extra_headers=headers)
            res.raise_for_status()
        except HTTPError as e:
            if e.response.status_code == 404:
                return None
            m = "HTTP response error: {}".format(res.text)
            self.log.error(m)
            raise e
        except Exception as e:
            raise e

        self.subscription = res.json()
        return

    def create_subscription(self, minutes):
        """ Create and set subscription from MSGraph API. """
        dto_utc_now = datetime.now(timezone.utc)
        dto_expires = dto_utc_now + timedelta(minutes=minutes)
        access_token = self.msgraph_token.get("access_token", "")
        tenant_id = self.instance.get("tenant_id", None)

        url = "{}/v1.0/subscriptions".format(self.msgraph_baseurl)
        data = {
            "changeType": "created",
            "notificationUrl": "{}/notifications".format(self.notifications_baseurl),
            "resource": "/communications/callRecords",
            "expirationDateTime": datetime.strftime(dto_expires, "%Y-%m-%dT%H:%M:%SZ"),
            "clientState": "rapdev_msteams-v{}".format(self.check_version),
            "latestSupportedTlsVersion": "v1_2"
        }
        headers = {
            "Authorization": "Bearer {}".format(access_token),
        }
        res = self.http.post(url, json=data, extra_headers=headers)
        self.check_http_response(res)

        self.subscription = res.json()
        cache_key = "{}".format(tenant_id)
        self.write_persistent_cache(cache_key, self.subscription.get("id"))
        return

    def update_subscription(self, minutes):
        """ Update and set subscription from MSGraph API. """
        dto_utc_now = datetime.now(timezone.utc)
        dto_expires = dto_utc_now + timedelta(minutes=minutes)
        access_token = self.msgraph_token.get("access_token", "")
        tenant_id = self.instance.get("tenant_id", None)
        subscription_id = self.subscription.get("id")

        url = "{}/v1.0/subscriptions/{}".format(self.msgraph_baseurl, subscription_id)
        data = {
            "expirationDateTime": datetime.strftime(dto_expires, "%Y-%m-%dT%H:%M:%S.%fZ"),
        }
        headers = {
            "Authorization": "Bearer {}".format(access_token),
        }
        res = self.http.patch(url, json=data, extra_headers=headers)
        self.check_http_response(res)

        self.subscription = res.json()
        cache_key = "{}".format(tenant_id)
        self.write_persistent_cache(cache_key, self.subscription.get("id"))
        return
        
    def renew_subscription(self):
        """ Create or update MSGraph API subscription. """
        tenant_id = self.instance.get("tenant_id", None)

        cache_key = "{}".format(tenant_id)
        subscription_id = self.read_persistent_cache(cache_key)

        self.set_subscription(subscription_id)
        if self.subscription:
            if self.subscription_expires_in(self.renewal_window):
                self.update_subscription(self.expire_window)
        else:
            self.create_subscription(self.expire_window)
        return

    def fetch_resources(self):
        """ Fetch unprocessed subscription notifications (resources). """
        tenant_id = self.instance.get("tenant_id", None)

        url = "{}/resources?processed=false".format(self.notifications_baseurl)
        data = {
            "tenantId": tenant_id,
            "subscriptionId": self.subscription.get("id"),
            "resourceType": "#microsoft.graph.callrecord",
            "checkVersion": self.check_version,
        }

        try:
            res = self.http.post(url, json=data)
        except Exception as e:
            raise e
        self.check_http_response(res)
        self.resources = res.json()
        return

    def process_resources(self):
        """ Generate metrics for unprocessed notification resources (callRecords) """
        processed_recource_ids = []
        for r in self.resources["resources"]:
            if not self.received_on_ok(r):
                # TODO: submit error metric for bad submission window to DD
                #   - Mark this as processed after metric is submitted? Fixed time could put them back into window?
                #   - Tagged individually with record id, just record as error until fall out?
                continue

            detail = self.get_call_record_detail(r)

            call_tags = self.tags.copy()
            call_tags.append("{}:{}".format("call_id", detail.get("id", "")))
            call_tags.append("{}:{}".format("call_type", detail.get("type", "")))
            for m in detail.get("modalities", []):
                call_tags.append("{}:{}".format("call_modalities", m))

            # add organizer identity tags and startDateTime to label calls
            call_tags.append("{}:{}".format("call_start", detail.get("startDateTime", "")))
            identity = detail.get("organizer", None)
            if identity:
                call_tags = self.get_identity_tags("call_organizer", identity, call_tags)

            self.submit_call_metrics(detail, call_tags)
            self.processed.append(r["id"])
        return

    def update_resources(self):
        """ Update processed notification resources """       
        url = "{}/resources".format(self.notifications_baseurl)
        data = {
            "tenantId": self.instance.get("tenant_id", ""),
            "subscriptionId": self.subscription.get("id"),
            "resourceType": "#microsoft.graph.callrecord",
            "checkVersion": self.check_version,
            "processedResourceIds": list(set(self.processed)),
        }

        try:
            res = self.http.put(url, json=data)
        except Exception as e:
            raise e
        self.check_http_response(res)
        self.processed = []
        return

    def get_call_record_detail(self, r={}):
        if not r:
            m = "empty resource provided to method: '{}'".format("get_call_record_detail")
            self.log.error(m)
            return {}

        access_token = self.msgraph_token.get("access_token", "")
        url = "{}/v1.0/communications/callRecords/{}?$expand=sessions($expand=segments)".format(
            self.msgraph_baseurl, r["id"])
        headers = {
            "Authorization": "Bearer {}".format(access_token),
        }

        try:
            res = self.http.get(url, extra_headers=headers)
            res.raise_for_status()
        except Exception as e:
            raise e
        self.check_http_response(res)
        detail = res.json()
        next_link = detail.get("sessions@odata.nextLink", None)

        # follow truncated call record sessions
        while next_link:
            try:
                res = self.http.get(url, extra_headers=headers)
                res.raise_for_status()
            except Exception as e:
                raise e
            self.check_http_response(res)

            next_detail = res.json()
            detail["sessions"] = detail["sessions"] + next_detail["sessions"]
            next_link = next_detail.get("sessions@odata.nextLink", None)
        return detail
    
    def received_on_ok(self, r={}, past_seconds=3600, future_seconds=-600):
        received_on = r.get("receivedOn", None)
        if not received_on:
            m = "missing field '{}' on resource record: {}".format("received_on", 
                json.dumps(r, default=str))
            self.log.error(m)
            return False

        now = datetime.now(timezone.utc)
        rec = parse(received_on)
        dts = (now - rec).total_seconds()

        if dts > past_seconds or dts < future_seconds:
            m = "timestamp exceeds maximum submit window for resource {} ({}s)".format(
                r.get("resourceData", {}).get("id", ""), dts)
            self.log.error("{}; check system time configuration".format(m))
            return False
        return True

    def get_identity_tags(self, prefix="user", identity={}, base_tags=[]):
        tags = base_tags.copy()

        if not identity:
            m = "empty identity field on resource"
            self.log.error(m)
            return tags

        k = "user"
        if not identity.get(k, None):
            k = "guest"
        if not identity.get(k, None):
            k = "phone"

        if not identity.get(k, None):
            m = "empty user and guest fields on identity field: {}".format(
                json.dumps(identity, default=str))
            self.log.error(m)
            return tags

        tags.append("{}_{}:{}".format(prefix, "id", identity.get(k, {}).get("id", "")))
        tags.append("{}_{}:{}".format(prefix, "name", identity.get(k, {}).get("displayName", "")))
        tags.append("{}_{}:{}".format(prefix, "tenant", identity.get(k, {}).get("tenantId", "")))
        return tags

    def get_ua_tags(self, user_agent={}, base_tags=[]):
        tags = base_tags.copy()

        if not user_agent:
            m = "empty user_agent field on resource"
            self.log.error(m)
            return tags

        for k in ["appVersion", "platform", "productFamily"]:
            value = user_agent.get(k, "unknown")
            tags.append("{}:{}".format(k.lower(), value))
        return tags

    def get_duration(self, start, end):
        if not start:
            start = "2000-01-01T00:00:00"
        if not end:
            end = "2000-01-01T00:00:00"

        sdt = parse(start)
        edt = parse(end)
        duration = (edt - sdt).total_seconds()
        return float(duration)

    def get_ptseconds(self, pts="PT0S"):
        """ dangerously assuming seconds only! """
        match = re.search('PT(.+?)S', pts)
        if not match:
            return float(0)
        return float(match.group(1))

    def submit_call_metrics(self, r={}, base_tags=[]):
        m_prefix = "{}.{}".format(self.metric_prefix, "call")
        if not r:
            m = "empty resource provided to method: '{}'".format("submit_call_metrics")
            self.log.error(m)
            return

        tags = base_tags.copy()

        # call.organizer
        organizer = r.get("organizer", {})
        if not organizer:
            m = "empty or unset resource in callRecord: '{}'".format("organizer")
            self.log.debug(m)
        else:
            m_name = "{}.{}".format(m_prefix, "organizer")
            m_tags = self.get_identity_tags("user", organizer, tags)
            self.gauge(m_name, 1.0, m_tags)

        # call.participant(s)
        participants = r.get("participants", [])
        if not participants:
            m = "empty or unset resource in callRecord: '{}'".format("participants")
            self.log.debug(m)
        for p in participants:
            m_name = "{}.{}".format(m_prefix, "participant")
            m_tags = self.get_identity_tags("user", p, tags)
            self.gauge(m_name, 1.0, m_tags)

        # call.duration
        #   failureInfo condition check (what does that look like)
        sdt = r.get("startDateTime", None)
        edt = r.get("endDateTime", None)
        m_name = "{}.{}".format(m_prefix, "duration")
        self.gauge(m_name, self.get_duration(sdt, edt), tags)

        ## call.participants
        m_name = "{}.{}".format(m_prefix, "participants")
        self.gauge(m_name, float(len(participants)), tags)

        ## billing_metric
        m_name = self.billing_metric
        m_tags = self.tags.copy()
        for i in range(len(participants)):
            m_tag_value = "{}_{}".format(r.get("id", ""), i)
            m_tags.append("{}:{}".format("meeting_participant", m_tag_value))
        self.gauge(m_name, float(1), m_tags)

        # -> sessions
        for session in r.get("sessions", []):
            self.submit_session_metrics(session, tags)
        return

    def submit_session_metrics(self, s={}, base_tags=[]):
        m_prefix = "{}.{}".format(self.metric_prefix, "session")

        tags = base_tags.copy()
        tags.append("{}:{}".format("session_id", s.get("id", "")))

        for m in s.get("modalities", []):
            tags.append("{}:{}".format("session_modalities", m))

        ## caller and callee identity tags on session (and descendants)
        for k in ["caller", "callee"]:
            identity = s.get(k, {}).get("identity", None)
            if identity:
                tags = self.get_identity_tags("session_user", identity, tags)
            else:
                m = "empty or unset resource in session: '{}.identity'".format(k)
                self.log.debug(m)

        # session.caller, session.callee; callee.identity will be unset on group calls
        # callee network info is likely to be Microsoft relays
        for k in ["caller", "callee"]:
            endpoint = s.get(k, None)
            if endpoint:
                m_name = "{}.{}".format(m_prefix, k)
                m_tags = tags.copy()

                identity = endpoint.get("identity", None)
                if identity:
                    m_tags = self.get_identity_tags("user", identity, tags)

                user_agent = endpoint.get("userAgent", None)
                if user_agent:
                    m_tags = self.get_ua_tags(user_agent, m_tags)
                
                self.gauge(m_name, 1.0, m_tags)
                continue

            m = "empty or unset resource in callRecord: '{}.{}'".format("session", k)
            self.log.debug(m)

        # session.duration
        m_name = "{}.{}".format(m_prefix, "duration")
        sdt = s.get("startDateTime", None)
        edt = s.get("endDateTime", None)
        self.gauge(m_name, self.get_duration(sdt, edt), tags)

        # -> segments
        for segment in s.get("segments", []):
            self.submit_segment_metrics(segment, tags)
        return

    def submit_segment_metrics(self, s={}, base_tags=[]):
        m_prefix = "{}.{}".format(self.metric_prefix, "segment")

        tags = base_tags.copy()
        tags.append("{}:{}".format("segment_id", s.get("id", "")))

        # segment.duration
        m_name = "{}.{}".format(m_prefix, "duration")
        sdt = s.get("startDateTime", None)
        edt = s.get("endDateTime", None)
        self.gauge(m_name, self.get_duration(sdt, edt), tags)

        # -> media
        for media in s.get("media", []):
            self.submit_media_metrics(media, tags)
        return

    def submit_media_metrics(self, m={}, base_tags=[]):
        m_prefix = "{}.{}".format(self.metric_prefix, "media")

        tags = base_tags.copy()
        tags.append("{}:{}".format("label", m.get("label", ""))) # media type
        tags.append("{}:{}".format("device_type", m.get("label", ""))) # media type

        # media network metrics
        for k in ["caller", "callee"]:
            endpoint_tags = tags.copy()
            endpoint_tags.append("{}:{}".format("endpoint", k))

            network = m.get("{}Network".format(k), {})

            for f in MEDIA_NETWORK_FIELDS:
                m_tags = endpoint_tags.copy()
                proto = network.get("networkTransportProtocol", "uknown")
                if proto:
                    m_tags.append("{}:{}".format("protocol", proto))
                m_name = "{}.{}".format(m_prefix, f.lower())
                m_data = network.get(f, None)
                if m_data:
                    self.gauge(m_name, float(m_data), m_tags)

            device = m.get("{}Device".format(k), {})
            if device:
                m_tags = endpoint_tags.copy()

                value = device.get("captureDeviceName", None)
                if not value:
                    value = "unknown"
                m_tags.append("{}:{}".format("capture_device_name", value))

                value = device.get("captureDeviceDriver", None)
                if not value:
                    value = "unknown"
                m_tags.append("{}:{}".format("capture_device_driver", value)) 

                value = device.get("renderDeviceName", None)
                if not value:
                    value = "unknown"
                m_tags.append("{}:{}".format("render_device_name", value))  

                value = device.get("renderDeviceDriver", None)
                if not value:
                    value = "unknown"
                m_tags.append("{}:{}".format("render_device_driver", value)) 

                m_name = "{}.{}".format(m_prefix, "device")
                self.gauge(m_name, float(1.0), m_tags)

                for f in MEDIA_DEVICE_FIELDS:
                    m_name = "{}.{}".format(m_prefix, f.lower())
                    m_data = device.get(f, None)
                    if m_data:
                        self.gauge(m_name, float(m_data), m_tags)

        # -> streams
        for stream in m.get("streams", []):
            self.submit_stream_metrics(stream, tags)
        return

    def submit_stream_metrics(self, s={}, base_tags=[]):
        m_prefix = "{}.{}".format(self.metric_prefix, "stream")

        tags = base_tags.copy()
        tags.append("{}:{}".format("stream_id", s.get("stream_id", ""))) 
        tags.append("{}:{}".format("direction", s.get("streamDirection", "")))  
        tags.append("{}:{}".format("audio_codec", s.get("audioCodec", "unknown")))
        tags.append("{}:{}".format("video_codec", s.get("videoCodec", "unknown")))

        # stream representation
        self.gauge(m_prefix, float(1.0), tags)

        for f in MEDIA_STREAM_FIELDS:
            m_name = "{}.{}".format(m_prefix, f.lower())
            m_data = s.get(f, None)
            if m_data:
                # if a PT{float}S value, extract seconds value
                if str(m_data).startswith("PT"):
                    m_data = self.get_ptseconds(m_data)
                self.gauge(m_name, float(m_data), tags)
        return
