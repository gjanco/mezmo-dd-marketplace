from datetime import datetime, timedelta
from operator import itemgetter

try:
    from datadog_checks.base import AgentCheck, ConfigurationError
except ImportError:
    from checks import AgentCheck, ConfigurationError

from . import cds_ms_defender_consts as consts
from . import cds_ms_defender_utils as Utils


class CrestDataSystemsMicrosoftDefenderCheck(AgentCheck):

    # This will be the prefix of every metric and service check the integration sends
    __NAMESPACE__ = consts.INTEGRATION_PREFIX

    def __init__(self, name, init_config, instances):
        super(CrestDataSystemsMicrosoftDefenderCheck, self).__init__(name, init_config, instances)
        self.headers = {}
        self.checkpoints = {}
        self.configuration = {}
        self.endpoint_vulns = []
        self.checkpoints_from_logs = {}
        self.endpoints = []
        self.log_index = "main"

    def check(self, _):
        self.cur_date_time = datetime.utcnow()
        self.cur_date_time_str = self.cur_date_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.authentication()
        self.set_configurations()

        # Dashboards
        self.endpoints_dashboard()
        self.ingest_marketplace_metric()
        self.vulnerability_overview_dashboard()
        self.incidents_dashboard()
        self.investigation_dashboard()
        self.software_vulnerabilities_dashboard()
        self.alerts_dashboard()

        # Checkpoint
        self.checkpoints_from_logs = {}
        self.endpoint_vulns = []
        self.ingest_checkpoint_log()

    # Endpoints Dashboard

    def endpoints_dashboard(self):
        """
        Ingest metrics or logs for Endpoints Dashboard
        """
        try:
            endpoints = self.get_endpoints()
            if not endpoints:
                self.checkpoints.update({consts.MACHINE_ENDPOINT_NAME: self.cur_date_time_str})
                return
            endpoints = self.sorted_data(endpoints, consts.LIST_MACHINE_FILTER_FIELD)
            self.endpoints = endpoints
            Utils.ingest_logs(
                self,
                consts.MACHINES_SOURCE_TYPE,
                endpoints,
                timestamp_field=consts.LIST_MACHINE_FILTER_FIELD,
                fn_to_evaluate_event=self.modify_endpoint_event,
            )
            missing_kb_url = consts.BASE_URL + consts.LIST_MISSING_KBS
            missing_kbs, kb_date_time = Utils.make_rest_call_by_id(
                self,
                endpoints,
                consts.MACHINE_ENDPOINT_NAME,
                "id",
                consts.LIST_MACHINE_FILTER_FIELD,
                missing_kb_url,
                name_field="computerDnsName",
                headers=self.headers,
            )
            self.checkpoints.update(kb_date_time)
            missing_kb_list = []
            metric_name = "missing_kbs"
            for endpoint_id_name, list_missing_kb in missing_kbs.items():
                endpoint_id, endpoint_name = endpoint_id_name.split("||")
                metric_tags = ["endpoint_id:%s" % endpoint_id, "endpoint_name:%s" % endpoint_name]
                Utils.ingest_metric(self, metric_name, len(list_missing_kb), metric_tags)
                for missing_kb in list_missing_kb:
                    missing_kb.update({"endpoint-id": endpoint_id, "endpoint-name": endpoint_name})
                    missing_kb_list.append(missing_kb)
            self.missing_kbs_for_endpoint(missing_kb_list)
        except Exception as e:
            self.log.error("Could not collect data of endpoints")
            self.log.exception(e)

    def modify_endpoint_event(self, event):
        """
        Returns modified event and tags of Endpoint log
        """
        event["endpoint-risk"] = event.get("riskScore")
        event["endpoint-seen-time"] = self.get_epoch_time(event["lastSeen"])
        event["endpoint-health-status"] = event.get("healthStatus")
        event["endpoint-id"] = event.get("id")
        event["endpoint-name"] = event.get("computerDnsName")
        return event, []

    def missing_kbs_for_endpoint(self, missing_kbs):
        """
        Ingest logs of Missing KBs for Endpoint
        """
        Utils.ingest_logs(
            self, consts.MISSING_KBS_SOURCE_TYPE, missing_kbs, fn_to_evaluate_event=self.modify_missing_kbs_event
        )

    def modify_missing_kbs_event(self, event):
        """
        Returns modified event and tags of Missing KBs log
        """
        event["missing-kb-id"] = event["id"]
        event["products-names"] = ",".join(event.get("productsNames", []))
        return event, []

    def get_endpoints(self):
        """
        Fetch and Returns the endpoints from Defender API
        """
        endpoints = []
        endpoint_url = "{}{}?%s".format(consts.BASE_URL, consts.LIST_MACHINE_ENDPOINT)
        try:
            param = self._get_params(consts.MACHINE_ENDPOINT_NAME, consts.LIST_MACHINE_FILTER_FIELD)
            endpoint_url = endpoint_url % param
            response = Utils.make_rest_call(self, endpoint_url, headers=self.headers)
            endpoints = response.json().get("value", [])
        except Exception as e:
            self.log.error("Could not get endpoints. URL: '%s'", endpoint_url)
            self.log.exception(e)
        return endpoints

    # Vulnerability Overview Dashboard

    def vulnerability_overview_dashboard(self):
        """
        Ingest metrics or logs for Vulnerability Dashboard
        """
        self.vulns_widgets()
        self.organization_exposure_level()

    # Vulnerability Methods
    def organization_exposure_level(self):
        """
        Ingest metric value of Organization Exposure Level
        """
        metric_name = "organization_exposure_level"
        try:
            url = consts.BASE_URL + consts.EXPOSURE_LEVEL
            response = Utils.make_rest_call(self, url, headers=self.headers)
            exposure_level = response.json().get("score") or 0
            Utils.ingest_metric(self, metric_name, exposure_level, [])
        except Exception as e:
            self.log.error("Could not get Organization Exposure Level. Reason: %s", e)
            self.log.exception(e)

    def vulns_widgets(self):
        """
        Ingest vulnerabilities for widgets
        """
        try:
            vulnerabilities = []
            vulnerabilities.extend(self.get_vulnerabilities(Utils.VulnerabilitySeverity.Critical))
            vulnerabilities.extend(self.get_vulnerabilities(Utils.VulnerabilitySeverity.High))
            vulnerabilities.extend(self.get_vulnerabilities(Utils.VulnerabilitySeverity.Medium))
            vulnerabilities.extend(self.get_vulnerabilities(Utils.VulnerabilitySeverity.Low))
            vulnerabilities = self.sorted_data(vulnerabilities, consts.LIST_VULN_FILTER_FIELD)
            Utils.ingest_logs(
                self,
                consts.VULNS_SOURCE_TYPE,
                vulnerabilities,
                timestamp_field=consts.LIST_VULN_FILTER_FIELD,
                fn_to_evaluate_event=self.modify_vuln_event,
            )
            exposed_vulnerabilities = self.get_exposed_vulnerabilities(vulnerabilities)
            if exposed_vulnerabilities:
                self.vulnerabilities_by_machine_and_software(exposed_vulnerabilities)
            url = consts.BASE_URL + consts.LIST_DEVICES_BY_VULNERABILITY
            machine_refs, date_time = Utils.make_rest_call_by_id(
                self,
                exposed_vulnerabilities,
                consts.VULNS_ENDPOINT_NAME,
                "id",
                consts.LIST_VULN_FILTER_FIELD,
                url,
                name_field="name",
                headers=self.headers,
            )
            self.checkpoints.update(date_time)
            machine_ref_list = []
            for vuln_id_name, list_machine_ref in machine_refs.items():
                vuln_id, vuln_name = vuln_id_name.split("||")
                for machine_ref in list_machine_ref:
                    machine_ref.update({"vulnerability-id": vuln_id, "vulnerability-name": vuln_name})
                    machine_ref_list.append(machine_ref)
            if machine_ref_list:
                Utils.ingest_logs(self, consts.MACHINE_REFS_SOURCE_TYPE, machine_ref_list)
        except Exception as e:
            self.log.error("Could not collect data of vulnerabilities")
            self.log.exception(e)

    def vulnerabilities_by_machine_and_software(self, vulnerabilities):
        """
        Ingest logs for Vulnerabilities by Machine and Software
        """
        vuln_ids = list(map(itemgetter('id'), vulnerabilities))
        urls = self.get_url_for_endpoint_vulns(vuln_ids)
        endpoint_software_vulns = []
        for url in urls:
            try:
                response = Utils.make_rest_call(self, url, headers=self.headers)
                endpoint_software_vulns.extend(response.json().get("value", []))
            except Exception as e:
                self.log.error("Could not get ednpoint vulns. URL: '%s'", url)
                self.log.exception(e)
        if endpoint_software_vulns:
            Utils.ingest_logs(
                self,
                consts.VULNS_MACHINE_SOFTWARE_SOURCE_TYPE,
                endpoint_software_vulns,
                fn_to_evaluate_event=self.modify_vulns_by_endpoint_and_software,
            )

    def modify_vulns_by_endpoint_and_software(self, event):
        """
        Returns modified event and tags of vulnerability log
        """
        machine_id = event.get("machineId")
        event["endpoint-id"] = machine_id
        event["endpoint-name"] = next(
            filter(lambda endpoint: endpoint.get("id") == machine_id, self.endpoints), {}
        ).get("computerDnsName", machine_id)
        event["vulnerability-id"] = event.get("cveId", "")
        product_vendor = event.get("productVendor", "")
        product_name = event.get("productName", "")
        if product_vendor and product_vendor:
            event["software-id"] = "%s-_-%s" % (product_vendor, product_name)
        else:
            event["software-id"] = "N/A"
        event["software-version"] = event.get("productVersion") or "N/A"
        event["vuln-severity"] = event.get("severity") or "N/A"
        return event, []

    def get_url_for_endpoint_vulns(self, vuln_ids):
        """
        Returns the list of URL for Endpoint Vulnerability
        """
        urls = []
        machine_vulns_url = "%s%s?$filter=cveId+in+('{}')" % (consts.BASE_URL, consts.LIST_VULN_BY_MACHINE_AND_SOFTWARE)
        url = machine_vulns_url.format("', '".join(vuln_ids))
        urls = [url]
        if len(url) > consts.MAX_URL_LENGTH:
            urls = []
            previous_index = 0
            for index, _ in enumerate(vuln_ids):
                modified_url = machine_vulns_url.format("', '".join(vuln_ids[previous_index : index + 1]))
                if len(modified_url) > consts.MAX_URL_LENGTH:
                    urls.append(machine_vulns_url.format("', '".join(vuln_ids[previous_index:index])))
                    previous_index = index
                    modified_url = machine_vulns_url.format("', '".join(vuln_ids[previous_index : index + 1]))
            urls.append(modified_url)
        return urls

    def get_exposed_vulnerabilities(self, vulnerabilities):
        """
        Returns the vulnerabilities if it exposed the machines
        """
        return list(filter(lambda vulnerability: vulnerability.get("exposedMachines", 0) > 0, vulnerabilities))

    def modify_vuln_event(self, event):
        """
        Returns modified event and tags of vulnerability log
        """
        event["vulnerability-id"] = event.get("id")
        event["vuln-severity"] = event.get("severity")
        return event, []

    def get_vulnerabilities(self, severity=None):
        """
        Fetch and Returns the vulnerabilities from Defender API
        """
        vulnerabilities = []
        vuln_url = "{}{}?%s".format(consts.BASE_URL, consts.LIST_VULN_ENDPOINT)
        try:
            param = self._get_params(consts.VULNS_ENDPOINT_NAME, consts.LIST_VULN_FILTER_FIELD)
            if severity and severity in dir(Utils.VulnerabilitySeverity):
                param += self.add_severity_filter(severity)
            vuln_url = vuln_url % param
            response = Utils.make_rest_call(self, vuln_url, headers=self.headers)
            vulnerabilities = response.json().get("value", [])
        except Exception as e:
            self.log.error("Could not get vulnerabilities. URL: '%s'", vuln_url)
            self.log.exception(e)
        return vulnerabilities

    def add_severity_filter(self, severity):
        """Returns the severity filter string"""
        return "+and+severity+eq+%s" % severity

    # Software Vulnerabilities Dashboard

    def software_vulnerabilities_dashboard(self):
        """
        Ingest metrics or logs for Software Vulnerabilities Dashboard
        """
        softwares = self.get_softwares()
        if not softwares:
            return
        software_vulns = {}
        software_distributions = {}
        for software in softwares:
            software_id = software.get("id")

            # For Software Vulnerebilities

            url = consts.BASE_URL + consts.LIST_SOFTWARE_VULNS.format(software_id)
            try:
                response = Utils.make_rest_call(self, url, headers=self.headers, handle_429=True)
                software_vulns.update({software_id: response.json().get("value", [])})
            except Exception as e:
                self.log.error("Could not get vulnerabilities of '%s' id for 'softwares'", software_id)
                self.log.exception(e)

            # For Software Distributions

            url = consts.BASE_URL + consts.LIST_SOFTWARE_DISTRIBUTIONS.format(software_id)
            try:
                response = Utils.make_rest_call(self, url, headers=self.headers, handle_429=True)
                software_distributions.update({software_id: response.json().get("value", [])})
            except Exception as e:
                self.log.error("Could not get distributions of '%s' id for 'softwares'", software_id)
                self.log.exception(e)
        try:
            self.vulnerabilities_by_software(software_vulns)
            self.software_with_version_details(software_distributions)
            self.software_distributions(software_distributions)
        except Exception as e:
            self.log.error("Could not collect data of Software Distributions")
            self.log.exception(e)

    # Software Vulnerabilities
    def vulnerabilities_by_software(self, software_vulns_dict):
        """
        Ingest logs of Vulnerabilities by Software
        """
        vulnerabilities = []
        for software_id, software_vulns in software_vulns_dict.items():
            for software_vuln in software_vulns:
                software_vuln.update({"software-id": software_id})
                software_vuln.update({"vulnerability-id": software_vuln.get("id")})
                vulnerabilities.append(software_vuln)
        Utils.ingest_logs(
            self,
            consts.SOFTWARE_VULNS_SOURCE_TYPE,
            vulnerabilities,
            fn_to_evaluate_event=self.modify_software_vuln_event,
        )

    def modify_software_vuln_event(self, event):
        """
        Returns modified event and tags of software vulnerability log
        """
        event['vuln-severity'] = event["severity"]
        return event, []

    # Software Distributions

    def software_with_version_details(self, software_distributions):
        """
        Ingest metrics for Software Installations and Vulnerabilities
        """
        metric_name = "software_version_vulnerabilities"
        metric_name_install = "software_version_installations"
        for soft_id, version_arr in software_distributions.items():
            for version in version_arr:
                soft_version = version.get("version")
                metric_tags = ["software_id:%s" % soft_id, "software_version:%s" % soft_version]
                no_of_vuln = version.get("vulnerabilities")
                installations = version.get("installations")
                Utils.ingest_metric(self, metric_name, no_of_vuln, metric_tags)
                Utils.ingest_metric(self, metric_name_install, installations, metric_tags)

    def software_distributions(self, software_distributions):
        """
        Ingest logs for Software Distributions
        """
        distributions = []
        for software_id, software_dists in software_distributions.items():
            for software_dist in software_dists:
                software_dist.update({"software-id": software_id})
                distributions.append(software_dist)
        Utils.ingest_logs(self, consts.SOFTWARE_DISTS_SOURCE_TYPE, distributions)

    def get_softwares(self):
        """
        Fetch and Returns softwares from Defender API
        """
        softwares = []
        software_url = consts.BASE_URL + consts.LIST_SOFTWARE_ENDPOINT
        try:
            response = Utils.make_rest_call(self, software_url, headers=self.headers)
            softwares = response.json().get("value", [])
        except Exception as e:
            self.log.error("Could not get softwares. URL: '%s'", software_url)
            self.log.exception(e)
        return softwares

    # Investigation Dashboard

    def get_investigations(self):
        """
        Fetch and Returns investigations from Defender API
        """
        investigations = []
        investigation_url = "{}{}?%s".format(consts.BASE_URL, consts.LIST_INVEST_ENDPOINT)
        try:
            param = self._get_params(consts.INVESTIGATION_ENDPOINT_NAME, consts.LIST_INVEST_FILTER_FIELD)
            investigation_url = investigation_url % param
            response = Utils.make_rest_call(self, investigation_url, headers=self.headers)
            investigations = response.json().get("value", [])
        except Exception as e:
            self.log.error("Could not get investigations. URL: '%s'", investigation_url)
            self.log.exception(e)
        return investigations

    def investigation_dashboard(self):
        """
        Ingest metrics or logs for Investigations Dashboard
        """
        try:
            investigations = self.get_investigations()
            if not investigations:
                self.checkpoints.update({consts.INVESTIGATION_ENDPOINT_NAME: self.cur_date_time_str})
                return
            Utils.ingest_logs(
                self,
                consts.INVESTIGATION_SOURCE_TYPE,
                investigations,
                timestamp_field=consts.LIST_INVEST_FILTER_FIELD,
                fn_to_evaluate_event=self.modify_invest_event,
            )
            self.checkpoints.update({consts.INVESTIGATION_ENDPOINT_NAME: self.cur_date_time_str})
        except Exception as e:
            self.log.error("Could not collect data of Investigations")
            self.log.exception(e)

    def modify_invest_event(self, event):
        """
        Returns modified event and tags of investigation log
        """
        event["investigation-id"] = event.get("id")
        event["investigation-status"] = event.get("state") or "N/A"
        return event, []

    # Incidents Dashboard

    def incidents_dashboard(self):
        """
        Ingest metrics or logs for Incidents Dashboard
        """
        try:
            incidents = self.get_incidents()
            if not incidents:
                self.checkpoints.update({consts.INCIDENT_ENDPOINT_NAME: self.cur_date_time_str})
                return
            Utils.ingest_logs(
                self,
                consts.INCIDENT_SOURCE_TYPE,
                incidents,
                timestamp_field=consts.LIST_INCIDENT_FILTER_FIELD,
                fn_to_evaluate_event=self.modify_incident_event,
            )
            self.checkpoints.update({consts.INCIDENT_ENDPOINT_NAME: self.cur_date_time_str})
        except Exception as e:
            self.log.error("Could not collect data of Incidents")
            self.log.exception(e)

    def modify_incident_event(self, event):
        """
        Returns modified event and tags of incident log
        """
        event["incident-id"] = event.get("id")
        event["incident-severity"] = event["severity"]
        event["incident-update-time"] = self.get_epoch_time(event["lastUpdateTime"])
        event["incident-status"] = event["status"]
        return event, []

    def get_incidents(self):
        """
        Fetch and Returns incidents from Defender API
        """
        incidents = []
        incident_url = "{}{}?%s".format(consts.BASE_URL_FOR_DEFENDER, consts.LIST_INCIDENT_ENDPOINT)
        try:
            param = self._get_params(consts.INCIDENT_ENDPOINT_NAME, consts.LIST_INCIDENT_FILTER_FIELD)
            incident_url = incident_url % param
            response = Utils.make_rest_call(self, incident_url, headers=self.headers_for_defender)
            incidents = response.json().get("value", [])
        except Exception as e:
            self.log.error("Could not get incidents. URL: '%s'", incident_url)
            self.log.exception(e)
        return incidents

    # Alerts Dashboard

    def alerts_dashboard(self):
        """
        Ingest metrics or logs for Alerts Dashboard
        """
        try:
            alerts = self.get_alerts()
            if not alerts:
                self.checkpoints.update({consts.ALERT_ENDPOINT_NAME: self.cur_date_time_str})
                return
            Utils.ingest_logs(
                self,
                consts.ALERTS_SOURCE_TYPE,
                alerts,
                timestamp_field=consts.LIST_ALERT_FILTER_FIELD,
                fn_to_evaluate_event=self.modify_alert_event,
            )
            self.checkpoints.update({consts.ALERT_ENDPOINT_NAME: self.cur_date_time_str})
        except Exception as e:
            self.log.error("Could not collect data of Alerts")
            self.log.exception(e)

    def modify_alert_event(self, event):
        """
        Returns modified event and tags of alert log
        """
        event["alert-id"] = event.get("id")
        event["alert-update-time"] = self.get_epoch_time(event["lastUpdateTime"])
        event["endpoint-id"] = event.get("machineId")
        event["endpoint-name"] = event.get("computerDnsName")
        event["alert-status"] = event.get("status") or "N/A"
        event["alert-category"] = event.get("category") or "N/A"
        event["alert-severity"] = event.get("severity") or "N/A"
        return event, []

    def get_alerts(self):
        """
        Fetch and Returns alerts from Defender API
        """
        alerts = []
        alert_url = "{}{}?%s".format(consts.BASE_URL, consts.LIST_ALERT_ENDPOINT)
        try:
            param = self._get_params(consts.ALERT_ENDPOINT_NAME, consts.LIST_ALERT_FILTER_FIELD)
            alert_url = alert_url % param
            response = Utils.make_rest_call(self, alert_url, headers=self.headers)
            alerts = response.json().get("value", [])
        except Exception as e:
            self.log.error("Could not get alerts. URL: '%s'", alert_url)
            self.log.exception(e)
        return alerts

    # General Methods

    def ingest_checkpoint_log(self):
        """
        Ingest checkpoint log
        """
        if not self.checkpoints:
            return
        checkpoints = {consts.LOG_PREFIX + key: value for key, value in self.checkpoints.items()}
        Utils.ingest_logs(self, consts.CHECKPOINT_SOURCE_TYPE, [checkpoints])

    def set_configurations(self):
        """
        Set configurations for ingesting logs
        """
        api_key = self.instance.get("api_key")
        app_key = self.instance.get("app_key")
        log_index = self.instance.get("log_index")

        if api_key is None or app_key is None:
            err_message = "App Key or API Key is missing"
            self.log.error(err_message)
            raise ConfigurationError(err_message)

        self.configuration = {"appKeyAuth": app_key, "apiKeyAuth": api_key}
        self.log_index = log_index
        try:
            now = datetime.utcnow()
            past_1_hour = now - timedelta(hours=1)

            now_str = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            past_1_hour_str = past_1_hour.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            param = {'from': past_1_hour_str, 'to': now_str}
            Utils.search_log(self, log_index, "", **param)
        except Exception as e:
            self.log.error("Could not connect to Datadog, App Key or API Key or Log Index is invalid")
            self.log.exception(e)
            raise e

    def authentication(self):
        """Authenticate credentials"""
        auth_check_name = "can_connect"
        event_source_type = consts.INTEGRATION_PREFIX + ".auth"

        client_id = self.instance.get("client_id")
        client_secret = self.instance.get("client_secret")
        tenant_id = self.instance.get("tenant_id")
        min_collection_interval = self.instance.get("min_collection_interval")

        if client_id is None or client_secret is None or tenant_id is None or min_collection_interval is None:
            err_message = "Could not connect to Microsoft 365 Defender as client_id, client_secret, tenant_id"
            err_message += " or min_collection_interval are missing in configuration file."
            self.ingest_service_check_and_event_for_auth(
                auth_check_name,
                event_source_type,
                reason="Missing data in configuration file.",
            )
            self.log.error(err_message)
            raise ConfigurationError(err_message)

        url = "https://login.microsoftonline.com/%s/oauth2/token" % (tenant_id)

        payload = {
            "resource": consts.BASE_URL,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }
        payload_for_defender = payload.copy()
        payload_for_defender["resource"] = consts.BASE_URL_FOR_DEFENDER
        headers = self.headers
        headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        response = None
        try:
            response = Utils.make_rest_call(
                self,
                url,
                method="post",
                data=payload,
                headers=headers,
                do_retry=False,
            )
            response_of_defender = Utils.make_rest_call(
                self,
                url,
                method="post",
                data=payload_for_defender,
                headers=headers,
                do_retry=False,
            )
        except ConnectionError as exception:
            self.ingest_service_check_and_event_for_auth(
                auth_check_name,
                event_source_type,
                reason="Could not made request reason: %s" % str(exception),
            )
            self.log.error("Connection Error")
            self.log.exception(exception)
            raise exception
        except Exception as exception:
            self.ingest_service_check_and_event_for_auth(
                auth_check_name,
                event_source_type,
                reason="Could not made request reason: %s" % str(exception),
            )
            self.log.exception(exception)
            raise exception

        if response is None or response_of_defender is None:
            self.ingest_service_check_and_event_for_auth(
                auth_check_name,
                event_source_type,
                reason="Could not connect to Microsoft 365 Defender.",
            )
            self.log.error("Could not connect to Microsoft 365 Defender, response is None ")
            raise Exception("Could not connect to Microsoft 365 Defender, response is None")

        response_json = response.json()
        error = response_json.get("error")

        response_json_defender = response_of_defender.json()
        error_of_defender = response_json_defender.get("error")

        if error or error_of_defender:
            self.log.error("Could not make request to API. reason: %s", error or error_of_defender)
            raise Exception("Could not make request to API. reason: %s", error or error_of_defender)

        access_token = response_json.get("access_token")
        access_token_defender = response_json_defender.get("access_token")
        if access_token is None or access_token_defender is None:
            self.ingest_service_check_and_event_for_auth(
                auth_check_name,
                event_source_type,
                reason="Could not get access_token from the response.",
            )
            self.log.error("Could not get access_token from the response.")
            raise Exception("Could not get access_token from the response.")

        self.ingest_service_check_and_event_for_auth(auth_check_name, event_source_type, result=True)

        self.log.info("Authentication successful with with Microsoft 365 Defender.")
        self.headers = {
            "Authorization": "Bearer %s" % access_token,
            "Content-Type": "application/json",
        }
        self.headers_for_defender = {
            "Authorization": "Bearer %s" % access_token_defender,
            "Content-Type": "application/json",
        }
        self.access_token = access_token
        self.access_token_defender = access_token_defender

    def ingest_service_check_and_event_for_auth(self, auth_check_name, event_source_type, reason="", result=False):
        """
        Ingest Service Check and Event for authentication
        """
        if result:
            self.service_check(auth_check_name, 0, message="Authentication successful.")
            self.event(
                {
                    "source_type_name": event_source_type,
                    "msg_title": "Authentication",
                    "msg_text": "Authentication successful",
                }
            )
        else:
            self.service_check(auth_check_name, 2, message="Authentication failed.")
            self.event(
                {
                    "source_type_name": event_source_type,
                    "msg_title": "Authentication",
                    "msg_text": "Authentication failed. Reason: %s" % reason,
                }
            )

    def _get_params(self, from_endpoint, field_name):
        """
        Returns the filter string of param with given field name
        """
        is_recover = self.instance.get("is_recover", True)
        int_invoke_interval = int(self.instance.get("min_collection_interval"))
        filter_str = "$filter={}+ge+%s+and+{}+le+{}".format(field_name, field_name, self.cur_date_time_str)

        if is_recover:
            checkpoint_date_time = self.checkpoints.get(from_endpoint)
            if checkpoint_date_time:
                return filter_str % checkpoint_date_time
            self.log.info("Could not get checkpoint time from local variable for '%s' endpoint", from_endpoint)

            checkpoint_key = consts.LOG_PREFIX + from_endpoint
            if self.checkpoints_from_logs and self.checkpoints_from_logs.get(checkpoint_key):
                return filter_str % self.checkpoints_from_logs.get(checkpoint_key)

            checkpoint_from_logs = Utils.search_checkpoint_log(self, int_invoke_interval * 4)
            if checkpoint_from_logs:
                self.checkpoints_from_logs = {
                    key: value.strftime("%Y-%m-%dT%H:%M:%SZ") if isinstance(value, datetime) else value
                    for key, value in checkpoint_from_logs.items()
                }
                checkpoint_date_time_from_log = checkpoint_from_logs.get(checkpoint_key)
                if checkpoint_date_time_from_log:
                    return filter_str % checkpoint_date_time_from_log.strftime("%Y-%m-%dT%H:%M:%SZ")
            self.log.info("Could not get checkpoint time from logs for '%s' endpoint", from_endpoint)

        past_date_time = self.cur_date_time - timedelta(seconds=int_invoke_interval)
        return filter_str % past_date_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def ingest_marketplace_metric(self):
        active_endpoints = list(filter(lambda endpoint: endpoint["healthStatus"] == "Active", self.endpoints))
        metric_name = "datadog.marketplace.crest_data_systems.microsoft_defender"
        for endpoint in active_endpoints:
            endpoint_id = endpoint.get("id")
            tag = "%s_active_endpoint:%s" % (consts.INTEGRATION_PREFIX.replace(".", "_"), endpoint_id)
            self.gauge(metric_name, 1.0, tags=[tag], raw=True)

    def get_epoch_time(self, utc_date):
        """Returns Epochs for given UTC Date"""
        updated_utc_date = utc_date.split(".")
        if len(updated_utc_date) > 1:
            utc_date = updated_utc_date[0] + "." + updated_utc_date[1][:1] + updated_utc_date[1][-1]
        utc_date_obj = datetime.strptime(utc_date, '%Y-%m-%dT%H:%M:%S.%fZ')
        local_date_time = datetime.now().astimezone()
        local_timezone = local_date_time.tzinfo
        return (utc_date_obj + local_timezone.utcoffset(local_date_time)).timestamp()

    def sorted_data(self, data_list, sorting_key):
        """
        Returns the sorted list by given key
        """
        return sorted(data_list, key=lambda data: data.get(sorting_key))
