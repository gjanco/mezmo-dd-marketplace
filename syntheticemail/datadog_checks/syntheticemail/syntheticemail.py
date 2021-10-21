# (C) RapDev, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import json

from datadog_checks.base import AgentCheck

REQUIRED_TAGS = [
    "vendor:rapdev",
]

REQUIRED_SETTINGS = [
    "email_address",
]


class SyntheticEmailCheck(AgentCheck):
    def check(self, instance):
        self.metric_prefix = "rapdev.syntheticemail"
        self.service_check_name = "{}.status".format(self.metric_prefix)
        self.tags = REQUIRED_TAGS + instance.get("tags", [])

        self.synthetic_email_api_key = "KIcolOzDSn2tdHppEnCmF5bVbAGSHDiN43eWkcWR"

        email_address = instance.get("email_address")
        self.tags.append("email:{}".format(email_address))
        self.tags.append("mailbox:{}".format(email_address))

        self.get_email_delivery_metrics(email_address)
        return

    def do_http_request(self, verb, url, **options):
        try:
            r = self.http._request(verb.lower(), url, options)
        except Exception as e:
            message = "http request error: {}".format(e)
            self.log.error(message)
            return (e, None)

        try:
            r.raise_for_status()
        except Exception as e:
            message = "http status error: {}".format(e)
            self.log.error(message)
            return (e, r)

        return (None, r)

    def get_email_delivery_metrics(self, email_address):
        checkin_url = "https://email.synth-rapdev.io/checkin"
        metrics_url = "https://email.synth-rapdev.io/metrics"
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.synthetic_email_api_key,
        }
        content = json.dumps({
            "emailAddress": email_address,
            "checkVersion": self.check_version,
        }, default=str)

        """ billing metric """
        self.gauge("datadog.marketplace.rapdev.syntheticemail", 1.0, tags=self.tags)

        (err, res) = self.do_http_request(
            "POST", checkin_url, headers=headers, data=content
        )
        if err:
            message = "agent http checkin error: {}".format(err)
            self.service_check(
                self.service_check_name, 2, message=message, tags=self.tags
            )
            return

        (err, res) = self.do_http_request(
            "POST", metrics_url, headers=headers, data=content
        )
        if err:
            message = "agent http metrics error: {}".format(err)
            self.service_check(
                self.service_check_name, 2, message=message, tags=self.tags
            )
            return

        metrics = []
        if res:
            metrics = res.json()

        if len(metrics) == 0:
            message = "{} metrics available for email_address: {}".format(
                0, email_address
            )
            self.log.warning(message)
            self.service_check(
                self.service_check_name, 1, message=message, tags=self.tags
            )
            return

        for metric in metrics:
            metric_tags = self.tags.copy()
            metric_tags.append("{}:{}".format("cloud", "aws"))
            metric_tags.append("{}:{}".format("region", metric.get("sourceRegion")))
            metric_tags.append("{}:{}".format("probe_region", metric.get("sourceRegion")))

            bounce_type = metric.get("bounceType", None)
            bounce_sub_type = metric.get("bounceSubType", None)
            ms_roundtrip = float(metric.get("msRoundTrip", 0))
            hop_count = float(metric.get("hopCount", 0))
            elapsed_sent = float(metric.get("elapsedLastSent", 0))
            elapsed_seen = float(metric.get("elapsedLastVisible", 0))

            self.gauge(
                "{}.last_sent".format(self.metric_prefix),
                elapsed_sent,
                tags=metric_tags,
            )
            self.gauge(
                "{}.last_seen".format(self.metric_prefix),
                elapsed_seen,
                tags=metric_tags,
            )

            hop_list = metric.get("hopList", [])
            for hop in hop_list:
                hop_tags = metric_tags.copy()
                hop_tags.append("{}:{}".format("relay_host", hop.get("host", None)))
                hop_tags.append("{}:{}".format("relay_index", hop.get("index", None)))
                hop_tags.append("{}:{}".format("relay_id", hop.get("id", None)))
                hop_elapsed = float(hop.get("elapsed", 0))
                self.gauge(
                    "{}.hop.elapsed".format(self.metric_prefix),
                    hop_elapsed,
                    tags=hop_tags,
                )

            if bounce_sub_type:
                metric_tags.append("{}:{}".format("bounce_type", bounce_sub_type))
                self.gauge(
                    "{}.bounced".format(self.metric_prefix), float(1), tags=metric_tags
                )
            else:
                self.gauge(
                    "{}.bounced".format(self.metric_prefix), float(0), tags=metric_tags
                )
                self.gauge(
                    "{}.rtt".format(self.metric_prefix), ms_roundtrip, tags=metric_tags
                )
                self.gauge(
                    "{}.hops".format(self.metric_prefix), hop_count, tags=metric_tags
                )

        self.service_check(self.service_check_name, 0, tags=self.tags)
        return
