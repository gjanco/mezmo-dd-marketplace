try:
    from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
except ImportError:
    from checks import AgentCheck

from datetime import datetime, timezone

from six.moves.urllib.parse import quote

from .constants import Constants, Tables
from .stats import StatsDo

from requests.exceptions import HTTPError # Import exceptions
from json import JSONDecodeError

class ServicenowCheck(AgentCheck):
    def __init__(self, *args, **kwargs):
        super(ServicenowCheck, self).__init__(*args, **kwargs)
        self.log.debug("INFO: ServicenowCheck.__init__() --> initializing")
        self.instance_name = self.instance.get("instance_name")
        self.collect_statsdo = is_affirmative(
            self.instance.get("collect_statsdo", True)
        )
        self.collect_itsm_metrics = is_affirmative(
            self.instance.get("collect_itsm_metrics", False)
        )
        self.opt_fields = self.instance.get('opt_fields', [])
        
        self.base_url = 'https://' + \
            str(self.instance_name) + '.service-now.com'

        if self.collect_statsdo:
            self.stats_url = self.base_url + "/stats.do"
            self.stats_title = (
                self.instance.get(
                    "stats_title") or Constants.DEFAULT_STATS_TITLE
            )
            self.statsdo_url = self.base_url + Constants.STATSDO_PATH

        if self.collect_itsm_metrics:
            self.assignment_group_names = self.instance.get(
                "assignment_groups", False)
            self.table_api_url = self.base_url + Constants.TABLE_API_BASE_PATH
            self.agg_api_url = self.base_url + Constants.AGG_API_BASE_PATH
            self.encoded_query = ""
            self.open_incident_states = self.instance.get("incident_open_states", [1, 2, 3])
            self.closed_incident_states = self.instance.get("incident_closed_states", [6, 7, 8])
            self.time_format = self.instance.get("time_format", Constants.SNC_TIME_FORMAT)
        self.check_initializations.append(self.validate_config)

    def check(self, instance):
        base_tags = Constants.REQUIRED_TAGS
        base_tags = base_tags + ["instance_name:" + self.instance_name]
        self.gauge("datadog.marketplace.rapdev.servicenow", 1.0, tags=base_tags)

        if self.collect_statsdo:
            self.check_statsdo()

        if self.collect_itsm_metrics:
            connected = self.check_itsm_connection()
            if connected:
                try:
                    self.check_itsm(instance)
                    self.service_check(
                        "{}.itsm_check_online".format(Constants.METRIC_PREFIX),
                        self.OK,
                        tags=base_tags
                    )
                    self.get_inc_this_year()
                except Exception as e:
                    self.log.error("unknown exception running itsm check\n"
                                   + repr(e)
                                   )
                    self.service_check(
                        "{}.itsm_check_online".format(Constants.METRIC_PREFIX),
                        self.CRITICAL,
                        tags=base_tags
                    )

    def validate_config(self):
        """
        check for a valid config, e.g. at least one check,
        basic auth creds if itsm check enabled
        """
        if not self.instance_name:
            self.log.warning(
                'ServicenowCheck.validate_config() --> no instance name in config')
            raise ConfigurationError(Constants.ERROR_NO_INSTANCE)

        if not self.collect_itsm_metrics and not self.collect_statsdo:
            self.log.warning(
                'ServicenowCheck.validate_config() --> At least one service check must be provided')
            raise ConfigurationError(Constants.ERROR_AT_LEAST_ONE_CHECK)

        if not self.collect_itsm_metrics:
            return


    def check_itsm_connection(self):
        """
        attempt to get one incident from the table api
        to see if the itsm check can run
        """

        base_tags = Constants.REQUIRED_TAGS
        base_tags = base_tags + ["instance_name:" + self.instance_name]

        connected = False
        single_incident_url = self.table_api_url + "/incident?sysparm_limit=1"
        try:
            response = self.http.get(single_incident_url,extra_headers=Constants.TABLE_API_HEADERS)
            if response.status_code != 200:
                raise Exception(response.status_code)
        except Exception as e:
            self.log.warning(
                "ServicenowCheck.check_itsm_connection() --> Non 200 request returned from incident api - itsm check will not run + \n " + repr(e))
            self.service_check(
                "{}.table_api_connection".format(
                    Constants.METRIC_PREFIX
                ),
                self.CRITICAL,
                tags=base_tags
            )
        else:
            self.service_check(
                "{}.table_api_connection".format(
                    Constants.METRIC_PREFIX
                ),
                self.OK,
                tags=base_tags
            )
            connected = True
        finally:
            self.gauge_http_response(response)

        return connected

    def gauge_http_response(self, response):
        """
        gauge http responses from Requests.Response object
        """
        base_tags = Constants.REQUIRED_TAGS
        base_tags = base_tags + ["instance_name:" + self.instance_name]
        endpoint = response.url
        endpoint = endpoint[endpoint.find(".com/") + 4:endpoint.find("?")]

        metric_tags = base_tags + ["endpoint:" + endpoint,
                                   "status_code:" + str(response.status_code)
                                  ]
        time_elapsed = response.elapsed.total_seconds()
        self.gauge(
            "{}.http_response".format(
                Constants.METRIC_PREFIX,
                response.status_code or 0
            ),
            1,
            tags=metric_tags
        )
        self.gauge(
            "{}.http_response_time".format(
                Constants.METRIC_PREFIX,
            ),
            time_elapsed,
            tags=metric_tags
        )

    def check_itsm(self, instance):
        base_tags = Constants.REQUIRED_TAGS
        base_tags = base_tags + ["instance_name:" + self.instance_name]
        encoded_query = self.set_encoded_query()
        inc_url = self.table_api_url + "/incident"
        if encoded_query:
            inc_url = inc_url + "?sysparm_query=" + encoded_query + "&sysparm_display_value=all"

        """
        get all the incidents we will work with this check
        essential to the check so kick back to
        check() if it fails
        """
        try:
            resp = self.http.get(inc_url,extra_headers=Constants.TABLE_API_HEADERS)

            resp.raise_for_status()

        except HTTPError as e:
            self.log.error(
                "failed to get incidents - itsm check cannot continue" + repr(e))
            self.service_check(
                "{}.table_api_connection".format(Constants.METRIC_PREFIX),
                self.CRITICAL,
                tags=base_tags
            )
            raise Exception(e)
        finally:
            self.gauge_http_response(resp)

        data = resp.json()
        incidents = data["result"]
        self.log.debug(
            "Servicenowcheck.check_itsm() --> "
            + str(len(incidents))
            + " incidents returned from encoded query"
        )

        incident_store = {}

        # hold glide records
        ag_cache = {0: None}
        user_cache = self.build_gr_cache(
            Tables.SYS_USER,
            "sys_id",
            Constants.FIELDS_USER
        )

        user_cache[0] = None

        location_cache = self.build_gr_cache(
            Tables.CMN_LOCATION,
            "sys_id",
            Constants.FIELDS_LOCATION
        )

        location_cache[0] = None

        task_sla_cache = self.build_gr_cache(
            Tables.TASK_SLA,
            "task",
            Constants.FIELDS_TASK_SLA
        )
        task_sla_cache[0] = None

        sla_name_cache = self.build_gr_cache(
            Tables.CONTRACT_SLA,
            "sys_id",
            Constants.FIELDS_CONTRACT_SLA
        )
        sla_name_cache = {0: None}

        for incident in incidents:
            try:
                if incident["assignment_group"]:
                    assignment_group_id = incident["assignment_group"]["value"]
                else:
                    assignment_group_id = 0

                if incident["caller_id"]["value"]:
                    caller_id = incident["caller_id"]["value"]
                else:
                    caller_id = 0

                if incident["location"]["value"]:
                    location_id = incident["location"]["value"]
                else:
                    location_id = 0

                if incident["assigned_to"]["value"]:
                    assigned_to_id = incident["assigned_to"]["value"]
                else:
                    assigned_to_id = 0

                if self.opt_fields:
                    opt_tags = []
                    for field in self.opt_fields:
                        field_name = field
                        if incident[field]:
                            field_value = incident[field]["value"]
                        else:
                             field_value = ''
                        opt_tag = field_name + ":" + field_value
                        if opt_tag not in opt_tags:
                            opt_tags.append(opt_tag)

                priority = "p" + incident["priority"]["value"]
                sys_created_on = incident["sys_created_on"]["display_value"]
                incident_id = incident["sys_id"]["value"]
                incident_state = incident["state"]["value"]           
                now = datetime.now()
                sco_date = datetime.strptime(
                    sys_created_on,
                    self.time_format
                ).replace(tzinfo=timezone.utc)
                time_delta = now - sco_date
                time_delta_seconds = time_delta.total_seconds() / 3600
                caller_is_vip = "false"
                incident_sla_breached = 0
                assignment_group = incident["assignment_group"]["display_value"]

                if not assignment_group:
                    assignment_group_name = "none"
                else:
                    assignment_group_name = assignment_group

                if assignment_group_name not in incident_store:
                    incident_store[assignment_group_name] = {}
                    incident_store[assignment_group_name][priority] = {}
                    incident_store[assignment_group_name][priority][incident_state] = {
                        "vip": 0,
                        "breached": {},
                        "total": 0,
                    }
                elif priority not in incident_store[assignment_group_name]:
                    incident_store[assignment_group_name][priority] = {}
                    incident_store[assignment_group_name][priority][incident_state] = {
                        "vip": 0,
                        "breached": {},
                        "total": 0,
                    }
                elif incident_state not in incident_store[assignment_group_name][priority]:
                    incident_store[assignment_group_name][priority][incident_state] = {
                        "vip": 0,
                        "breached": {},
                        "total": 0
                    }

                self.log.info(
                    "ServicenowCheck.check_itsm() --> processing slas")

                if task_sla_cache.get(incident_id, False):
                    sla = task_sla_cache[incident_id]

                    if sla["sla"]:
                        sla_id = sla["sla"]["value"]
                    else:
                        sla_id = 0

                    sla_stage = sla["stage"]
                    sla_end_time = sla["end_time"]
                    sla_start_time = sla["start_time"]
                    sla_complete_time = 0

                    if sla_end_time:
                        sla_start_time_fmt = datetime.strptime(
                            sla_start_time,
                            self.time_format
                        )
                        sla_end_time_fmt = datetime.strptime(
                            sla_end_time,
                            self.time_format
                        )
                        sla_complete_time = sla_end_time_fmt - sla_start_time_fmt
                        sla_complete_time = sla_complete_time.total_seconds() / 3600

                    sla_def = self.get_or_update_cache(
                        sla_id,
                        "contract_sla",
                        sla_name_cache
                    )

                    sla_name = sla_def.get("name", "undefined")
                    sla_target = sla_def.get("target", "undefined")

                    sla_tags = base_tags + [
                        "servicenow_assignment_group:" + assignment_group_name,
                        "servicenow_priority:" + priority,
                        "sla_name:" + sla_name,
                        "sla_incident_number:" + incident["number"]["value"],
                        "sla_target:" + sla_target,
                        "sla_stage:" + sla_stage,
                    ]

                    if sla["stage"] == "in_progress":
                        sla_percentage = sla["percentage"]
                        if float(sla_percentage) > 100:
                            sla_percentage = 100
                        self.gauge(
                            "rapdev.servicenow.sla", sla_percentage, tags=sla_tags
                        )

                    if sla_complete_time:
                        self.gauge(
                            "rapdev.servicenow.sla_elapsed_time",
                            sla_complete_time,
                            tags=sla_tags,
                        )

                    if sla["stage"] == "in_progress" and sla["has_breached"] == "true":
                        # CHANGE
                        some_value = incident_store[assignment_group_name][priority][incident_state]["breached"]
                        if sla_name not in some_value:
                            incident_store[assignment_group_name][priority][incident_state]["breached"][
                                sla_target
                            ] = {"total": 0}

                        incident_store[assignment_group_name][priority][incident_state]["breached"][
                            sla_target
                        ]["total"] += 1

                caller = self.get_or_update_cache(
                    caller_id,
                    "sys_user",
                    user_cache
                )

                if caller:
                    caller_name = caller["name"]
                else:
                    caller_name = "none"

                # update open inc totals
                if int(incident_state) in self.open_incident_states:
                    if caller and caller["vip"] == "true":
                        incident_store[assignment_group_name][priority][incident_state]["vip"] += 1

                    if incident_sla_breached > 0:
                        incident_store[assignment_group_name][priority][incident_state][
                            "breached"
                        ] += incident_sla_breached

                    incident_store[assignment_group_name][priority][incident_state]["total"] += 1

                assigned_to = self.get_or_update_cache(
                    assigned_to_id,
                    "sys_user",
                    user_cache
                )

                if assigned_to:
                    assigned_to_name = assigned_to["name"]
                else:
                    assigned_to = "none"

                location = self.get_or_update_cache(
                    location_id,
                    "cmn_location",
                    location_cache
                )

                if location:
                    location_name = location["name"]
                else:
                    location_name = "none"

                inc_opened = int(incident_state) in self.open_incident_states

                # prepare individual incident metric
                if self.opt_fields:
                    incident_tags = opt_tags + base_tags + [
                    "servicenow_assignment_group:" + assignment_group_name,
                    "servicenow_priority:" + incident["priority"]["value"],
                    "incident_number:" + incident["number"]["value"],
                    "caller:" + caller_name,
                    "description:" + incident["short_description"]["value"],
                    "opened:" + incident["sys_created_on"]["display_value"],
                    "assigned_to:" + assigned_to_name,
                    "location:" + location_name,
                    "state:" + incident_state,
                    "open:" + str(inc_opened)
                ]
                else:
                    incident_tags = base_tags + [
                        "servicenow_assignment_group:" + assignment_group_name,
                        "servicenow_priority:" + incident["priority"]["value"],
                        "incident_number:" + incident["number"]["value"],
                        "caller:" + caller_name,
                        "description:" + incident["short_description"]["value"],
                        "opened:" + incident["sys_created_on"]["display_value"],
                        "assigned_to:" + assigned_to_name,
                        "location:" + location_name,
                        "state:" + incident_state,
                        "open:" + str(inc_opened)
                    ]
                # closed incidents
                if int(incident_state) not in self.open_incident_states:
                    if not incident["closed_at"]["display_value"]:
                        continue

                    incident_close_time = incident["closed_at"]["display_value"]
                    incident_open_time = incident["sys_created_on"]["display_value"]
                    incident_open_time_fmt = datetime.strptime(
                        incident_open_time,
                        self.time_format
                    ).replace(tzinfo=timezone.utc)
                    incident_close_time_fmt = datetime.strptime(
                        incident_close_time,
                        self.time_format
                    ).replace(tzinfo=timezone.utc)
                    incident_time_to_close = (
                        incident_close_time_fmt - incident_open_time_fmt
                    ).total_seconds()

                    # seconds --> hours
                    incident_time_to_close = incident_time_to_close / 3600

                    self.gauge(
                        "rapdev.servicenow.incident_resolution_time",
                        incident_time_to_close,
                        tags=incident_tags,
                    )

                self.gauge(
                    "rapdev.servicenow.incident",
                    time_delta_seconds,
                    tags=incident_tags)

            except Exception as e:
                self.log.error("Unknown error occurred processing incident payload"
                               + incident_id
                               + "incident metrics will not be processed"
                               + repr(e)
                               )
                continue


        # Print Totals
        for ag in incident_store:
            for priority in incident_store[ag]:
                for state in incident_store[ag][priority]:
                    accumulation_tags = base_tags + [
                        "servicenow_assignment_group:" + ag,
                        "servicenow_priority:" + priority,
                        "servicenow_state:" + state
                    ]

                    num_vip = incident_store[ag][priority][state]["vip"]
                    num_total = incident_store[ag][priority][state]["total"]

                    self.gauge(
                        "rapdev.servicenow.vip_count", num_vip, accumulation_tags
                    )

                    self.gauge(
                        "rapdev.servicenow.incident_count", num_total, tags=accumulation_tags
                    )

                for target in incident_store[ag][priority][state]["breached"]:
                    breach_tags = accumulation_tags
                    breach_tags.append("sla_target:" + target)
                    num_breached = incident_store[ag][priority][state]["breached"][target][
                        "total"
                    ]
                    try:
                        self.gauge(
                            "rapdev.servicenow.incident_breached",
                            num_breached,
                            accumulation_tags,
                        )
                    except Exception as e:
                        self.log.error("unable to gauge breach " + repr(e))

    def set_encoded_query(self):
        """
        1.) all -open- incidents
        2.) all -closed- incidents -closed- or -resolved- in the last
            30 days
        """
        closed_encoded_query = Constants.QUERY_CLOSED_OR_RESOLVED_LAST_30
        ag_encoded_query = ""
        state_ec = "stateIN"
        open_states = self.open_incident_states

        for x in range (len(open_states)):
            state_ec = state_ec + str(open_states[x])
            if x != len(open_states) -1:
                state_ec = state_ec + ","

        if self.assignment_group_names:
            for ag in self.assignment_group_names:
                encoded_ag = quote(ag)
                if ag_encoded_query:
                 ag_encoded_query = ag_encoded_query + "%5EOR" + \
                    "assignment_group.name%3D" + encoded_ag
                else:
                    ag_encoded_query = "assignment_group.name%3D" + encoded_ag

        open_encoded_query = state_ec
        if ag_encoded_query:
            open_encoded_query = open_encoded_query + "^" + ag_encoded_query
            closed_encoded_query = closed_encoded_query + "^" + ag_encoded_query

        encoded_query = open_encoded_query + "^NQ" + closed_encoded_query
       

        return encoded_query

    def build_gr_cache(self, table, key, fields):
        cache = {}
        url = (
            self.table_api_url
            + "/"
            + table
        )

        if fields:
            url = url + "?sysparm_fields=" + fields

        resp = self.http.get(url,extra_headers=Constants.TABLE_API_HEADERS)

        self.gauge_http_response(resp)
        resp.raise_for_status()

        records = resp.json()["result"]

        if not len(records):
            self.log.warn("ServicenowCheck.build_gr_cache() -->"
                          + " no results returned for " + table
            )
            return {}

        for record in records:
            record_key = record.pop(key)
            if hasattr(record_key, "get") and record_key.get("value", False):
                record_key = record_key.get("value")

            cache[record_key] = record

        self.log.debug("ServicenowCheck.build_gr_cache() --> Cache set for "
                       + table
                       +"\n"
                       + str(cache)
        )
        return cache


    def sanatize_90p(self, value):
        split = value.split(":")
        return (
            int(split[0]) * 86400 * 1000
            + int(split[1]) * 60 * 1000
            + float(split[2]) * 1000
        )

    def get_inc_this_year(self):
        base_tags = Constants.REQUIRED_TAGS
        base_tags = base_tags + ["instance_name:" + self.instance_name]
        try:
            response = self.http.get(
                self.agg_api_url + Constants.YEAR_SLUG,
                headers=Constants.TABLE_API_HEADERS  
            )

            response.raise_for_status()

            resp = response.json()

            result = resp.get("result")
          
        except (HTTPError, JSONDecodeError) as e:
            self.log.error(
                "failed to get incidents for current year" + repr(e))
            raise Exception(e)

        if not result:
            return
        
 
        
        stats = result.get("stats")

        if not stats:
            return
        
        count = stats.get("count") 

        if count:
          self.gauge(
              "rapdev.servicenow.incident_total_year",
              count, tags=base_tags)
    
    def now_request_single_record(self, table, id):
        """
        request a single record from the /now/table api
        and return the response
        """

        base_tags = Constants.REQUIRED_TAGS
        base_tags = base_tags + ["instance_name:" + self.instance_name]

        try:
            url = self.base_url + Constants.TABLE_API_BASE_PATH + "/" + table + "/" + id
            resp = self.http.get(url,extra_headers=Constants.TABLE_API_HEADERS)

            resp.raise_for_status()

            return resp

        except HTTPError as e:
            self.log.warning(
                "Servicenowcheck.now_request_single_record() -->" +
                "HTTPError getting " + table +
                "from ServiceNow" + repr(e) + "\n" + id
            )
            self.service_check("{}.table_api_connection".format(
                Constants.METRIC_PREFIX), self.CRITICAL, tags=base_tags)
            raise Exception(e)

        finally:
            self.gauge_http_response(resp)

    def get_or_update_cache(self, sys_id, table, cache):
        if sys_id not in cache:
            resp = self.now_request_single_record(table, sys_id)
            record = resp.json()["result"]
            cache[sys_id] = record

        return cache[sys_id]

    def check_statsdo(self):
        base_tags = Constants.REQUIRED_TAGS
        base_tags = base_tags + ["instance_name:" + self.instance_name]
        try:
            response = self.http.get(
                self.stats_url, headers=Constants.STATSDO_HEADERS)
            if response.status_code != 200:
                raise HTTPError(
                    {"code": response.status_code, "response": response}
                )

        except HTTPError as e:
            self.log.warning(
                "Servicenowcheck.check_statsdo() -->" +
                "HTTP error getting /stats.do  - check cannot continue"
            )
            self.service_check(
                "rapdev.servicenow.statsdo_connection",
                self.CRITICAL,
                tags=base_tags
            )
            return
        except Exception as e:
            self.log.error("Unknown exception checking statsdo " + repr(e) +
                           "check cannot continue"
                           )
            return

        statsdo = StatsDo(response.text)
        statsdo.set_properties_from_soup(statsdo.soup, [], "body", "", "")
        if statsdo.title != self.stats_title:
            self.service_check(
                "rapdev.servicenow.statsdo_connection", self.CRITICAL)
            return

        self.service_check("rapdev.servicenow.statsdo_connection", self.OK)
        self.gauge(
            "rapdev.servicenow.stats.trans_time",
            # time between sending the request and parse of the headers
            response.elapsed.total_seconds(),
            tags=base_tags,
        )

        for metric in statsdo.metrics:
            try:
                float(metric["value"])
            except ValueError:
                continue

            try:
                self.gauge(
                    metric["name"],
                    metric["value"],
                    tags=metric["tags"]
                )
            except Exception as e:
                self.log.warning(
                    "error gauging metric "
                    + metric["name"]
                    + ":"
                    + metric["value"]
                    + "\n"
                    + repr(e)
                )
