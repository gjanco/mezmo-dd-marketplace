# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
try:
    from datadog_checks.base import AgentCheck
except ImportError:
    from checks import AgentCheck


class OzcodeCheck(AgentCheck):
    def __init__(self, *args, **kwargs):
        super(OzcodeCheck, self).__init__(*args, **kwargs)
        self.metric_prefix = "ozcode.agent"
        self.base_api_url = "https://service.oz-code.com/"
        self.tags = self.instance.get("tags", [])

    def check(self, _):
        self.test_api_connection()
        self.check_local_agent()

    def check_local_agent(self):
        metric_tags = self.tags.copy()

        self.gauge("datadog.marketplace.{}".format(self.metric_prefix),
                   1,
                   tags=metric_tags)

    def test_api_connection(self):
        self.log.debug("Attempting connection test to Ozcode Server API URL %s.", self.base_api_url)

        try:
            x = self.http.get(self.base_api_url + "sign-in")
            x.raise_for_status()
            response_code = x.status_code
        except Exception as e:
            self.log.warning("Caught exception %s", e)
            self.log.warning("Cannot authenticate to Ozcode Server API. The check will not run")
            self.service_check("{}.can_connect".format(self.metric_prefix), AgentCheck.CRITICAL, tags=self.tags)
        else:
            self.log.debug("Connection successful")
            self.service_check("{}.can_connect".format(self.metric_prefix), AgentCheck.OK, tags=self.tags)
