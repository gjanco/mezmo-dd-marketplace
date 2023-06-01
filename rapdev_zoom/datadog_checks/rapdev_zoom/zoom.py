try:
    from datadog_checks.base import AgentCheck, ConfigurationError
except ImportError:
    from checks import AgentCheck
from .helpers import *
import requests
import time
import datetime
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
import json
import jwt

REQUIRED_SETTINGS = [
    "base_api_url",
    "api_key",
    "api_secret",
    "account_name"
]
REQUIRED_TAGS = [
    "vendor:rapdev",
]
AUTHENTICATION_METHODS = [
    "jwt",
    "oauth"
]


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class ZoomCheck(AgentCheck):

    __NAMESPACE__ = "rapdev.zoom"

    def __init__(self, *args, **kwargs):
        super(ZoomCheck, self).__init__(*args, **kwargs)
        
        # Base tags/params
        self.base_api_url = self.instance.get("base_api_url", "https://api.zoom.us/v2/")
        self.account_name = self.instance.get("account_name", "")
        self.authentication_method = self.instance.get("authentication_method", "jwt")
        self.billing_metric = f"datadog.marketplace.{self.__NAMESPACE__}"

        # Initialize tags
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])

        # Zoom authentication params
        if self.authentication_method == "jwt":
            self.api_key = self.instance.get("api_key", "")
            self.api_secret = self.instance.get("api_secret", "")
        elif self.authentication_method == "oauth":
            self.account_id = self.instance.get("account_id", "")
            self.client_id = self.instance.get("client_id", "")
            self.client_secret = self.instance.get("client_secret", "")

        # Run mode params
        ## Meetings
        self.collect_participant_details = self.instance.get("collect_participant_details", True)
        self.collect_usernames = self.instance.get("collect_usernames", True)
        self.users_to_track = self.instance.get("users_to_track", [])
        
        ## Rooms
        self.room_only_mode = self.instance.get("room_only_mode", False)
        
        ## Phones
        self.enable_phone_mode = self.instance.get("enable_phone_mode", False)
        self.phone_only_mode = self.instance.get("phone_only_mode", False)
        self.enable_phone_call_logs = self.instance.get("enable_phone_call_logs", True)
        self.call_timer_ingest = self.instance.get("call_timer_ingest", 10)

        # Initialize API trackers
        self.successful_api_calls = 0
        self.failed_api_calls = 0
        self.api_rate_limits_hit = 0

    def check(self, instance):
        self.validate_config()
        self.test_api_connection()

        # Get current start time
        self.current_time = datetime.datetime.now(datetime.timezone.utc)

        # Reset tags if required
        base_tags = list(self.tags)

        # Reset API trackers at the start of every check run
        self.reset_trackers()

        if self.room_only_mode:
            self.get_rooms_metrics(base_tags)
        else:
            # We will parse phone information at this point, need to read from cache
            self.persistent = self.read_from_cache()

            if self.phone_only_mode:
                self.get_phones_metrics(base_tags)
            # Otherwise get all metrics
            else:
                self.get_users(base_tags)

                if self.enable_phone_mode:
                    self.get_phones_metrics(base_tags)

                self.get_rooms_metrics(base_tags)
                self.get_meetings(base_tags)

            # Write out the persistent cache
            self.write_to_cache()

        if self.account_name:
            # Append account name at the end of run to submit with service checks
            base_tags.append(f"zoom_account_name:{self.account_name}")

        # Send OK if the API daily limit wasn't encountered during this run 
        if self.api_rate_limits_hit == 0:
            self.service_check("can_call_api", AgentCheck.OK, tags=base_tags)

        # Submit the metrics for api failed vs successful
        self.gauge("api.successful_calls", self.successful_api_calls, tags=base_tags)
        self.gauge("api.failed_calls", self.failed_api_calls, tags=base_tags)


    def test_api_connection(self):
        self.log.debug("Attempting connection test to Zoom API URL %s.", self.base_api_url)

        # add account name if present
        base_tags = list(self.tags)
        if self.account_name:
            base_tags.append(f"zoom_account_name:{self.account_name}")

        try:
            if self.room_only_mode:
                x = self.http.get(
                        self.base_api_url + "rooms",
                        auth=BearerAuth(self.generate_token())
                    )
            elif self.phone_only_mode:
                x = self.http.get(
                    self.base_api_url + "phone/devices",
                    auth=BearerAuth(self.generate_token())
                )
            else:
                x = self.http.get(
                    self.base_api_url + "users",
                    auth=BearerAuth(self.generate_token())
                )

            x.raise_for_status()
        except Exception as e:
            self.service_check("can_connect", AgentCheck.CRITICAL, tags=base_tags)
            raise Exception(f"Cannot authenticate to ZOOM API. The check will not run: {e}")
        else:
            self.log.debug("Connection successful")
            self.service_check("can_connect", AgentCheck.OK, tags=base_tags)

    def validate_config(self):
        errors = []

        if self.authentication_method not in AUTHENTICATION_METHODS:
            errors.append("Please provide a valid authentication method.")

        if self.authentication_method == "jwt":
            if not self.api_key:
                errors.append("Your Zoom Account API Key is required for JWT.")
            if not self.api_secret:
                errors.append("Your Zoom Account API Secret is required for JWT.")
        elif self.authentication_method == "oauth":
            if not self.account_id:
                errors.append("Your Zoom Account Account ID is required for Server-To-Server oAuth.")
            if not self.client_id:
                errors.append("Your Zoom Account Client ID is required for Server-To-Server oAuth.")
            if not self.client_secret:
                errors.append("Your Zoom Account Client Secret is required for Server-To-Server oAuth.")
        
        if self.room_only_mode and self.phone_only_mode:
            errors.append("room_only_mode and phone_only_mode are set to True. Please fix this and restart the agent.")

        if errors:
            raise ConfigurationError(f"Please fix the following errors: {', '.join(errors)}")

    def generate_token(self):
        if self.authentication_method == "jwt":
            token = jwt.encode(
                {"iss": self.api_key, "exp": time.time() + 60},
                self.api_secret,
                algorithm='HS256'
            )
        
            if float(jwt.__version__.split('.')[0]) < 2:
                token = token.decode('utf-8')

        elif self.authentication_method == "oauth":
            client_auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
            post_data = {
                "grant_type": "account_credentials",
                "account_id": self.account_id
            }

            oauth_response = self.http.post(
                "https://zoom.us/oauth/token",
                auth=client_auth,
                data=post_data
            ).json()
        
            token = oauth_response.get("access_token", "")

        return token



    def call_api(self, request_path, phone_type="", next_page_token="", from_date="", to_date="", page_size=300):
        """Helper function to call the zoom api via desired query params

        :param string request_path: the path for which to append to the base api url
        :param string phone_type: if collecting phones, what type of phone (assigned or unassigned)
        :param string next_page_token: the token for the next page if pagination is required
        :param string from_date: the start date from where to begin the query range
        :param string to_date: the end date for where to end the query range
        :param integer page_size: the number of records per page the api returns
        :raises Exception: when a non-200 and non-429 (zoom rate limit code) is returned
        :return: json of the API response
        """
    
        # Only time page_size is false is on line 669 which means none of the other conditions will hit anyways
        # since we're making a single query for the user so this should be safe
        if page_size:
            request_path = f"{request_path}?page_size={page_size}"
        if phone_type:
            request_path = f"{request_path}&type={phone_type}"
        if next_page_token:
            request_path = f"{request_path}&next_page_token={next_page_token}"
        if from_date and to_date:
            request_path = f"{request_path}&from={from_date}&to={to_date}"

        while True:
            # Make Zoom API request
            results = self.http.get(
                self.base_api_url + request_path,
                auth=BearerAuth(self.generate_token())
            )

            # Grab status code
            response_code = results.status_code

            # If call is successful, return json result
            if response_code == 200:
                self.successful_api_calls += 1
                return results.json()
            # 400 is response code for not supported calls (e.g. free plan making paid plan calls)
            elif response_code == 400:
                self.failed_api_calls += 1
                self.log.warning(f"Error making API call: {results.text}")    
                return {}
            # If 429, that means we hit rate limit
            elif response_code == 429:
                self.failed_api_calls += 1
                headers = results.headers

                limit_type = headers.get("X-RateLimit-Type")

                # Need to append the account name in case the service checks fail
                api_base_tags = list(self.tags)

                if self.account_name:
                    api_base_tags.append(f"zoom_account_name:{self.account_name}")

                # If we hit the queries per second limit, sleep for a sec and retry
                if limit_type == "QPS":
                    self.log.warning("Hit Queries per Second API rate limit. Sleeping for a second then retrying...")
                    self.service_check("can_call_api", AgentCheck.WARNING, tags=api_base_tags)
                    time.sleep(1)
                    continue
                # If we hit the daily limit, return None
                elif limit_type == "Daily-limit":
                    self.api_rate_limits_hit += 1
                    self.service_check("can_call_api", AgentCheck.CRITICAL, tags=api_base_tags)
                    raise Exception("Zoom daily API limit was hit. Check will successfully run again when the limit resets at the end of the day.")
            else:
                try:
                    results.raise_for_status()
                except HTTPError as e:
                    raise HTTPError(f"Non-200 response code returned from Zoom API: {e}")
                except Exception as e:
                    raise Exception(f"Unknown exception was caught during Zoom API request: {e}")
            
    def get_users(self, base_tags):
        """Gets the users from Zoom API and sends in the active count and billing metric for each"""
        request_path = "users"

        response = self.call_api(request_path)

        while True:
            users = response.get("users", [])

            for user in users:
                metric_tags = base_tags.copy()

                user_email = user.get("email", "")
                user_timezone = user.get("timezone", "")
                user_type = user.get("type")

                if user_email:
                    metric_tags.append(f"zoom_user_email:{user_email}")
                if user_timezone:
                    metric_tags.append(f"zoom_user_timezone:{user_timezone}")

                if user_type == 1:
                    metric_tags.append("zoom_user_account_type:basic")
                elif user_type == 2:
                    metric_tags.append("zoom_user_account_type:licensed")
                elif user_type == 3:
                    metric_tags.append("zoom_user_account_type:on-prem")

                self.gauge("users.active.count", 1, tags=metric_tags)
                self.gauge(self.billing_metric, 1, tags=metric_tags, raw=True)

            page_token = response.get("next_page_token", "")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, next_page_token=page_token)

    def get_phones_metrics(self, base_tags):
        """Gets the metrics for phones and calls"""
        self.get_phone_devices(base_tags, "assigned")

        if self.enable_phone_call_logs:
            self.get_phone_sites()
            self.get_phone_call_logs(base_tags)

    def get_phone_devices(self, base_tags, assign_type):
        request_path = "phone/devices"

        response = self.call_api(request_path, phone_type=assign_type)

        while True:
            phones = response.get("devices", [])

            for phone in phones:
                metric_tags = base_tags.copy()

                phone_name = phone.get("display_name", "")
                phone_type = phone.get("device_type", "")
                phone_status = 1 if phone.get("status", "") == "online" else 2

                phone_site = phone.get("site", {})
                site_name = phone_site.get("name", "")

                # Add tags to metrics
                metric_tags.append(f"phone_name:{phone_name}")                
                metric_tags.append(f"phone_type:{phone_type}")
                metric_tags.append(f"site_name:{site_name}")

                # If we're collecting phones, submit as a metric
                self.gauge(self.billing_metric, 1, tags=metric_tags, raw=True)

                self.gauge("phone.count", 1, tags=metric_tags)
                self.gauge("phone.status", phone_status, tags=metric_tags)

            page_token = response.get("next_page_token", "")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, phone_type=assign_type, next_page_token=page_token)

    def get_phone_sites(self):
        """ Builds the map of site id's to site names to be submitted in phone call runs"""
        request_path = "/phone/sites"

        response = self.call_api(request_path, page_size=300)

        self.sites = {}

        while True:
            sites = response.get("sites", [])

            for site in sites:
                self.sites[site.get("id")] = site.get("name") 

            page_token = response.get("next_page_token", "")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, next_page_token=page_token, page_size=300)


    def get_phone_call_logs(self, base_tags):
        request_path = "phone/metrics/call_logs"
    
        parsed_call_ids = self.persistent.get('calls', {}).keys()

        # Calcuate our "stop" point in terms of old calls
        old_calls_break = False
        past_time = (self.current_time - datetime.timedelta(minutes=self.call_timer_ingest)).strftime('%Y-%m-%dT%H:%M:%SZ')

        response = self.call_api(request_path, page_size=100)
        while True:
            call_logs = response.get("call_logs", [])

            for call_log in call_logs:
                metric_tags = base_tags.copy()

                call_id = call_log.get("call_id", "")
                call_timestamp = call_log.get("date_time", "")

                # Check if call has hit our ingest threshold
                if call_timestamp < past_time:
                    self.log.info("Old calls hit, exitting out of calls ingestion...")
                    old_calls_break = True
                    break
                # Check if this call's ID is already in our cache, if so we can stop ingestion
                elif call_id in parsed_call_ids:
                    self.log.info("Hit previously parsed calls, exitting out of calls ingestion...")
                    old_calls_break = True
                    break
                # Otherwise add to cache because this is a new call
                else:
                    self.persistent['calls'][call_id] = call_timestamp

                direction = call_log.get("direction", "")
                duration = call_log.get("duration", 0)
                mos = call_log.get("mos", "")

                # Add tags to metrics
                metric_tags.append(f"call_id:{call_id}")
                metric_tags.append(f"call_direction:{direction}")

                callee = call_log.get("callee", {})
                caller = call_log.get("caller", {})

                callee_device_type = callee.get("device_type", "")
                callee_extension_number = callee.get("extension_number", "")
                callee_isp = callee.get("isp", "")
                callee_phone_number = callee.get("phone_number", "")
                callee_site_id = callee.get("site_id", "")

                if callee_site_id:
                    callee_site_name = self.sites.get(callee_site_id, "")
                    metric_tags.append(f"callee_site_name:{callee_site_name}")
                if callee_device_type:
                    metric_tags.append(f"callee_device_type:{callee_device_type}")
                if callee_extension_number:
                    metric_tags.append(f"callee_extension_number:{callee_extension_number}")
                if callee_isp:
                    metric_tags.append(f"callee_isp:{callee_isp}")
                if callee_phone_number:
                    metric_tags.append(f"callee_phone_number:{callee_phone_number}")

                caller_device_type = caller.get("device_type", "")
                caller_extension_number = caller.get("extension_number", "")
                caller_isp = caller.get("isp", "")
                caller_phone_number = caller.get("phone_number", "")
                caller_site_id = caller.get("site_id", "")

                if caller_site_id:
                    caller_site_name = self.sites.get(caller_site_id, "")
                    metric_tags.append(f"caller_site_name:{caller_site_name}")
                if caller_device_type:
                    metric_tags.append(f"caller_device_type:{caller_device_type}")
                if caller_extension_number:
                    metric_tags.append(f"caller_extension_number:{caller_extension_number}")
                if caller_isp:
                    metric_tags.append(f"caller_isp:{caller_isp}")   
                if caller_phone_number:
                    metric_tags.append(f"caller_phone_number:{caller_phone_number}")
                
                self.gauge("call.count", 1, tags=metric_tags)
                self.gauge("call.mean_opinion_score", mos, tags=metric_tags)
                self.gauge("call.duration", duration, tags=metric_tags)

            page_token = response.get("next_page_token", "")

            # First break condition is we've hit old calls
            if old_calls_break:
                break
            # Second is no more pages to parse
            elif page_token == "":
                break
            # Otherwise make new request
            else:
                response = self.call_api(request_path, next_page_token=page_token, page_size=100)
                
    def get_rooms_metrics(self, base_tags):
        """Gets the metrics for each room such as component status, names, participants, etc..."""
        request_path = "metrics/zoomrooms"

        #call to get location hierarchy
        locations_dict = self.get_rooms_locations()

        # Rooms Health counts
        critical_rooms = 0
        warning_rooms = 0
        healthy_rooms = 0

        # Rooms Status counts
        rooms_available = 0
        rooms_in_meetings = 0
        rooms_offline = 0
        rooms_under_construction = 0

        response = self.call_api(request_path)
        while True:
            rooms = response.get("zoom_rooms", [])

            for room in rooms:
                location_tags = []
                room_name = room.get("room_name", "")
                room_id = room.get("id", "")
                room_status = room.get("status", "")
                room_health = room.get("health", "")
                device_ip = room.get("device_ip", "")
                camera = room.get("camera", "")
                microphone = room.get("microphone", "")
                speaker = room.get("speaker", "")
                location_id = room.get("location_id", "")

                # If tags provided (running in sub account mode), copy those instead
                metric_tags = base_tags.copy()

                if location_id:
                    location_tags = get_room_location_tags(location_id, locations_dict)
                    for tag in location_tags:
                        metric_tags.append(tag)
                
                if room_name:
                    metric_tags.append(f"zoom_room_name:{room_name}")
                if room_id:
                    metric_tags.append(f"zoom_room_id:{room_id}")
                if device_ip:
                    metric_tags.append(f"zoom_room_device_ip:{device_ip}")
                if camera:
                    metric_tags.append(f"zoom_room_camera:{camera}")
                if microphone:
                    metric_tags.append(f"zoom_room_microphone:{microphone}")
                if speaker:
                    metric_tags.append(f"zoom_room_speaker:{speaker}")

                if self.room_only_mode:
                    self.gauge(self.billing_metric, 1, tags=metric_tags, raw=True)

                # Increment counts and send in the current health for this room
                if room_health:
                    if room_health == "critical":
                        health = 3
                        critical_rooms += 1
                    elif room_health == "warning":
                        health = 2
                        warning_rooms += 1
                    else:
                        health = 1
                        healthy_rooms += 1

                    self.gauge("room.health", health, tags=metric_tags)

                # Increment counts and send in the current status for this room
                if room_status:
                    if room_status == "Available":
                        status = 1
                        rooms_available += 1
                    elif room_status == "In Meeting":
                        status = 2
                        rooms_in_meetings += 1
                    elif room_status == "Offline":
                        status = 3
                        rooms_offline += 1
                    else:
                        status = 4
                        rooms_under_construction += 1

                    self.gauge("room.status", status, tags=metric_tags)

                room_issues = room.get("issues", [])
                component_tags = base_tags.copy() + location_tags
                self.parse_and_send_issues(room_issues, room_name, room_id, component_tags)

            page_token = response.get("next_page_token", "")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, next_page_token=page_token)

        metric_tags = base_tags.copy()

        # Send in the room health counts 
        metric_tags.append("zoom_room_health:critical")
        self.gauge("room.health.count", critical_rooms, tags=metric_tags)
        metric_tags.remove("zoom_room_health:critical")

        metric_tags.append("zoom_room_health:warning")
        self.gauge("room.health.count", warning_rooms, tags=metric_tags)
        metric_tags.remove("zoom_room_health:warning")

        metric_tags.append("zoom_room_health:healthy")
        self.gauge("room.health.count", healthy_rooms, tags=metric_tags)
        metric_tags.remove("zoom_room_health:healthy")

        # Send in the room status counts
        metric_tags.append("zoom_room_status:available")
        self.gauge("room.status.count", rooms_available, tags=metric_tags)
        metric_tags.remove("zoom_room_status:available")

        metric_tags.append("zoom_room_status:in_meetings")
        self.gauge("room.status.count", rooms_in_meetings, tags=metric_tags)
        metric_tags.remove("zoom_room_status:in_meetings")

        metric_tags.append("zoom_room_status:offline")
        self.gauge("room.status.count", rooms_offline, tags=metric_tags)
        metric_tags.remove("zoom_room_status:offline")

        metric_tags.append("zoom_room_status:under_construction")
        self.gauge("room.status.count", rooms_under_construction, tags=metric_tags)
        metric_tags.remove("zoom_room_status:under_construction")

    def get_rooms_locations(self):
        """Gets the room locations that are currently present in the account and adds them to a list"""
        locations_request_path = "rooms/locations/"
        structure_request_path = locations_request_path + "structure"

        # Get all the locations structures in use from zoom
        # this is ordered with the first index being highest (e.g. country)
        # and last index being lowest (e.g. the room itself)
        structures = self.call_api(structure_request_path).get("structures", [])

        structure_dict = {}

        # Remove "room" since thats not a location type
        try:
            structures.remove("room")
        except Exception as e:
            pass

        # Start building dict for structures 
        for structure in structures:
            structure_dict[structure] = {} 

        # Reverse structures so we know a rooms parent, and that parent, etc...
        # so we can directly just iterate later working from the bottom up
        structures.reverse()
        structure_dict["structures"] = structures

        location_response = self.call_api(locations_request_path)

        while True:
            locations = location_response.get("locations", [])

            for location in locations:
                location_id = location.get("id")
                location_name = location.get("name")
                location_parent_id = location.get("parent_location_id")
                location_type = location.get("type")

                # Set the location's id to a dict which contains the name and parent id
                structure_dict[location_type][location_id] = {
                    "name": location_name,
                    "parent_id": location_parent_id
                }

            page_token = location_response.get("next_page_token", "")
            if page_token == "":
                break
            else:
                location_response = self.call_api(locations_request_path, next_page_token=page_token)

        return structure_dict
 
    def parse_and_send_issues(self, issues, room_name, room_id, base_tags):
        """Helper function for parsing room issues"""
        room_controller_is_connected = 1
        selected_camera_is_connected = 1
        selected_mic_is_connected = 1
        selected_speaker_is_connected = 1
        is_cpu_usage_ok = 1
        is_bandwidth_ok = 1

        for issue in issues:
            if "controller disconnected" in issue.lower():
                room_controller_is_connected = 0
            elif "camera has disconnected" in issue.lower():
                selected_camera_is_connected = 0
            elif "microphone has disconnected" in issue.lower():
                selected_mic_is_connected = 0
            elif "speaker has disconnected" in issue.lower():
                selected_speaker_is_connected = 0
            elif issue == "High CPU usage is detected":
                is_cpu_usage_ok = 0
            elif issue == "Low bandwidth network is detected":
                is_bandwidth_ok = 0

        metric_tags = base_tags.copy()
        metric_tags.append(f"zoom_room_name:{room_name}")
        metric_tags.append(f"zoom_room_id:{room_id}")

        metric_tags.append("zoom_room_component:controller")
        self.gauge("room.component.status", room_controller_is_connected, tags=metric_tags)
        metric_tags.remove("zoom_room_component:controller")

        metric_tags.append("zoom_room_component:camera")
        self.gauge("room.component.status", selected_camera_is_connected, tags=metric_tags)
        metric_tags.remove("zoom_room_component:camera")

        metric_tags.append("zoom_room_component:microphone")
        self.gauge("room.component.status", selected_mic_is_connected, tags=metric_tags)
        metric_tags.remove("zoom_room_component:microphone")

        metric_tags.append("zoom_room_component:speaker")
        self.gauge("room.component.status", selected_speaker_is_connected, tags=metric_tags)
        metric_tags.remove("zoom_room_component:speaker")

        metric_tags.append("zoom_room_component:cpu")
        self.gauge("room.component.status", is_cpu_usage_ok, tags=metric_tags)
        metric_tags.remove("zoom_room_component:cpu")

        metric_tags.append("zoom_room_component:bandwidth")
        self.gauge("room.component.status", is_bandwidth_ok, tags=metric_tags)
        metric_tags.remove("zoom_room_component:bandwidth")

    def get_meetings(self, base_tags):
        """Gets all the current meetings with the participants and calls the QOS function on each"""
        request_path = "metrics/meetings"
        
        todays_date = str(datetime.date.today())
        response = self.call_api(request_path, from_date=todays_date, to_date=todays_date)

        while True:
            meetings = response.get("meetings", [])

            for meeting in meetings:
                host_name = meeting.get("host", "")
                meeting_id = meeting.get("id", "")
                
                metric_tags = base_tags.copy()
                
                metric_tags.append(f"zoom_meeting_id:{meeting_id}")

                if self.collect_usernames:
                    metric_tags.append(f"zoom_meeting_host:{host_name}")

                # Get the QOS metrics for every particpant in the meeting
                try:
                    self.get_meeting_qos(meeting_id, metric_tags)
                except Exception as e:
                    self.log.error(f"Get Meeting QOS FAILED. Caught exception: {e}")

                # Send in a count for this meeting 
                self.gauge("meetings.count", 1, tags=metric_tags)

                # Send in the number of participants on this meeting
                self.gauge("meetings.participants", meeting.get("participants"), tags=metric_tags)

            page_token = response.get("next_page_token", "")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, next_page_token=page_token, from_date=todays_date, to_date=todays_date)

    def get_meeting_qos(self, meeting_id, base_tags):
        """Gets the QOS for each participant in the current meeting"""
        request_path = f"metrics/meetings/{meeting_id}/participants/qos"
        
        response = self.call_api(request_path, page_size=10)

        # Base tags provided here should already have meeting id and host (if ingesting)
        base_metric_tags = base_tags.copy()
        
        # Audio input/output counts
        audio_input_bitrate = 0
        audio_input_avg_loss = 0.0
        audio_input_jitter = 0
        audio_input_latency = 0
        audio_input_max_loss = 0.0
        audio_output_bitrate = 0
        audio_output_avg_loss = 0.0
        audio_output_jitter = 0
        audio_output_latency = 0
        audio_output_max_loss = 0.0

        # Video input/output counts
        video_input_bitrate = 0
        video_input_avg_loss = 0.0
        video_input_jitter = 0
        video_input_latency = 0
        video_input_max_loss = 0.0
        video_output_bitrate = 0
        video_output_avg_loss = 0.0
        video_output_jitter = 0
        video_output_latency = 0
        video_output_max_loss = 0.0

        # Record counts
        valid_audio_input_records = 0
        valid_audio_output_records = 0
        valid_video_input_records = 0
        valid_video_output_records = 0

        while True:
            participants = response.get("participants", [])

            for participant in participants:
                metric_tags = base_metric_tags.copy()

                leave_time = participant.get("leave_time", "")

                if participant and leave_time == "":
                    user_email = None
                    # Check if we want to collect individual user metrics
                    if self.collect_participant_details:
                        user_location = participant.get("location", "")
                        user_name = participant.get("user_name", "")
                        domain = participant.get("domain", "")
                        ip_address = participant.get("ip_address", "")
                        data_center = participant.get("data_center", "")
                        network_type = participant.get("network_type", "")
                        user_id = participant.get("id", "")

                        # Only need users email if the users_to_track list is set
                        if self.users_to_track and user_id:
                            user_request_path = f"users/{user_id}"                       
                            
                            # noinspection PyTypeChecker
                            user_response = self.call_api(user_request_path, page_size=None)
                            user_email = user_response.get("email", "")

                            if user_email:
                                metric_tags.append(f"zoom_user_email:{user_email}")

                        if user_location:
                            country = get_country(user_location)
                            metric_tags.append(f"zoom_user_location:{user_location}")
                            metric_tags.append(f"zoom_user_country:{country}")

                        metric_tags.append(f"zoom_user_domain:{domain}")
                        metric_tags.append(f"zoom_user_ip:{ip_address}")
                        metric_tags.append(f"zoom_user_data_center:{data_center}")
                        metric_tags.append(f"zoom_user_network_type:{network_type}")

                        if self.collect_usernames:
                            metric_tags.append(f"zoom_user_name:{user_name}")

                    if (self.users_to_track and user_email in self.users_to_track) or (not self.users_to_track):
                        self.gauge("users.in_meetings.count", 1, tags=metric_tags)

                    recent_user_qos = participant.get("user_qos", [])
                    if recent_user_qos:
                        recent_user_qos = recent_user_qos[-1]
                        audio_input = recent_user_qos.get("audio_input", {})
                        audio_output = recent_user_qos.get("audio_output", {})
                        video_input = recent_user_qos.get("video_input", {})
                        video_output = recent_user_qos.get("video_output", {})
                        cpu_usage = recent_user_qos.get("cpu_usage", {})
                        
                        if check_for_metrics(audio_input):
                            valid_audio_input_records += 1

                            audio_input_bitrate += parse_kbps(audio_input.get("bitrate", ""))
                            audio_input_avg_loss += percentage_to_float(audio_input.get("avg_loss", ""))
                            audio_input_jitter += parse_milliseconds(audio_input.get("jitter", ""))
                            audio_input_latency += parse_milliseconds(audio_input.get("latency", ""))
                            audio_input_max_loss += percentage_to_float(audio_input.get("max_loss", ""))

                            if self.collect_participant_details:
                                if (self.users_to_track and user_email in self.users_to_track) or \
                                        (not self.users_to_track):
                                    metric_tags.append("zoom_user_qos_audio:input")
                                    self.parse_and_submit_user_qos(audio_input, metric_tags)
                                    metric_tags.remove("zoom_user_qos_audio:input")

                        if check_for_metrics(audio_output):
                            valid_audio_output_records += 1

                            audio_output_bitrate += parse_kbps(audio_output.get("bitrate", ""))
                            audio_output_avg_loss += percentage_to_float(audio_output.get("avg_loss", ""))
                            audio_output_jitter += parse_milliseconds(audio_output.get("jitter", ""))
                            audio_output_latency += parse_milliseconds(audio_output.get("latency", ""))
                            audio_output_max_loss += percentage_to_float(audio_output.get("max_loss", ""))

                            if self.collect_participant_details:
                                if (self.users_to_track and user_email in self.users_to_track) or\
                                        (not self.users_to_track):
                                    metric_tags.append("zoom_user_qos_audio:output")
                                    self.parse_and_submit_user_qos(audio_output, metric_tags)
                                    metric_tags.remove("zoom_user_qos_audio:output")

                        if check_for_metrics(video_input):
                            valid_video_input_records += 1

                            video_input_bitrate += parse_kbps(video_input.get("bitrate", ""))
                            video_input_avg_loss += percentage_to_float(video_input.get("avg_loss", ""))
                            video_input_jitter += parse_milliseconds(video_input.get("jitter", ""))
                            video_input_latency += parse_milliseconds(video_input.get("latency", ""))
                            video_input_max_loss += percentage_to_float(video_input.get("max_loss", ""))

                            if self.collect_participant_details:
                                if (self.users_to_track and user_email in self.users_to_track) or \
                                        (not self.users_to_track):
                                    metric_tags.append("zoom_user_qos_video:input")
                                    self.parse_and_submit_user_qos(video_input, metric_tags)
                                    metric_tags.remove("zoom_user_qos_video:input")

                        if check_for_metrics(video_output):
                            valid_video_output_records += 1

                            video_output_bitrate += parse_kbps(video_output.get("bitrate", ""))
                            video_output_avg_loss += percentage_to_float(video_output.get("avg_loss", ""))
                            video_output_jitter += parse_milliseconds(video_output.get("jitter", ""))
                            video_output_latency += parse_milliseconds(video_output.get("latency", ""))
                            video_output_max_loss += percentage_to_float(video_output.get("max_loss", ""))

                            if self.collect_participant_details:
                                if (self.users_to_track and user_email in self.users_to_track) or \
                                        (not self.users_to_track):
                                    metric_tags.append("zoom_user_qos_video:output")
                                    self.parse_and_submit_user_qos(video_output, metric_tags)
                                    metric_tags.remove("zoom_user_qos_video:output")

                        if check_for_cpu_metrics(cpu_usage):
                            system_max_cpu_usage_value = percentage_to_float(cpu_usage.get("system_max_cpu_usage", ""))
                            zoom_avg_cpu_usage_value = percentage_to_float(cpu_usage.get("zoom_avg_cpu_usage", ""))
                            zoom_max_cpu_usage_value = percentage_to_float(cpu_usage.get("zoom_max_cpu_usage", ""))
                            zoom_min_cpu_usage_value = percentage_to_float(cpu_usage.get("zoom_min_cpu_usage", ""))

                            if self.collect_participant_details:
                                if (self.users_to_track and user_email in self.users_to_track) or \
                                        (not self.users_to_track):
                                    metric_tags.append("zoom_user_qos_cpu:usage")
                                    self.gauge("user.qos.cpu.system_max_usage",
                                               system_max_cpu_usage_value,
                                               tags=metric_tags)
                                    self.gauge("user.qos.cpu.avg_usage",
                                               zoom_avg_cpu_usage_value,
                                               tags=metric_tags)
                                    self.gauge("user.qos.cpu.max_usage",
                                               zoom_max_cpu_usage_value,
                                               tags=metric_tags)
                                    self.gauge("user.qos.cpu.min_usage",
                                               zoom_min_cpu_usage_value,
                                               tags=metric_tags)
                                    metric_tags.remove("zoom_user_qos_cpu:usage")

            page_token = response.get("next_page_token", "")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, next_page_token=page_token, page_size=10)

        if valid_audio_input_records > 0:
            avg_audio_input_avg_loss = calculate_average(audio_input_avg_loss, valid_audio_input_records)
            avg_audio_input_jitter = calculate_average(audio_input_jitter, valid_audio_input_records)
            avg_audio_input_latency = calculate_average(audio_input_latency, valid_audio_input_records)
            avg_audio_input_max_loss = calculate_average(audio_input_max_loss, valid_audio_input_records)
            base_metric_tags.append("zoom_meeting_qos_audio:input")
            self.gauge("meeting.qos.bitrate", audio_input_bitrate, tags=base_metric_tags)
            self.gauge("meeting.qos.average_loss", avg_audio_input_avg_loss, tags=base_metric_tags)
            self.gauge("meeting.qos.jitter", avg_audio_input_jitter, tags=base_metric_tags)
            self.gauge("meeting.qos.latency", avg_audio_input_latency, tags=base_metric_tags)
            self.gauge("meeting.qos.max_loss", avg_audio_input_max_loss, tags=base_metric_tags)
            base_metric_tags.remove("zoom_meeting_qos_audio:input")

        if valid_audio_output_records > 0:
            avg_audio_output_avg_loss = calculate_average(audio_output_avg_loss, valid_audio_output_records)
            avg_audio_output_jitter = calculate_average(audio_output_jitter, valid_audio_output_records)
            avg_audio_output_latency = calculate_average(audio_output_latency, valid_audio_output_records)
            avg_audio_output_max_loss = calculate_average(audio_output_max_loss, valid_audio_output_records)
            base_metric_tags.append("zoom_meeting_qos_audio:output")
            self.gauge("meeting.qos.bitrate", audio_output_bitrate, tags=base_metric_tags)
            self.gauge("meeting.qos.average_loss", avg_audio_output_avg_loss, tags=base_metric_tags)
            self.gauge("meeting.qos.jitter", avg_audio_output_jitter, tags=base_metric_tags)
            self.gauge("meeting.qos.latency", avg_audio_output_latency, tags=base_metric_tags)
            self.gauge("meeting.qos.max_loss", avg_audio_output_max_loss, tags=base_metric_tags)
            base_metric_tags.remove("zoom_meeting_qos_audio:output")

        if valid_video_input_records > 0:
            avg_video_input_avg_loss = calculate_average(video_input_avg_loss, valid_video_input_records)
            avg_video_input_jitter = calculate_average(audio_input_jitter, valid_video_input_records)
            avg_video_input_latency = calculate_average(audio_input_latency, valid_video_input_records)
            avg_video_input_max_loss = calculate_average(audio_input_max_loss, valid_video_input_records)
            base_metric_tags.append("zoom_meeting_qos_video:input")
            self.gauge("meeting.qos.bitrate", video_input_bitrate, tags=base_metric_tags)
            self.gauge("meeting.qos.average_loss", avg_video_input_avg_loss, tags=base_metric_tags)
            self.gauge("meeting.qos.jitter", avg_video_input_jitter, tags=base_metric_tags)
            self.gauge("meeting.qos.latency", avg_video_input_latency, tags=base_metric_tags)
            self.gauge("meeting.qos.max_loss", avg_video_input_max_loss, tags=base_metric_tags)
            base_metric_tags.remove("zoom_meeting_qos_video:input")

        if valid_video_output_records > 0:
            avg_video_output_avg_loss = calculate_average(video_output_avg_loss, valid_video_output_records)
            avg_video_output_jitter = calculate_average(video_output_jitter, valid_video_output_records)
            avg_video_output_latency = calculate_average(video_output_latency, valid_video_output_records)
            avg_video_output_max_loss = calculate_average(video_output_max_loss, valid_video_output_records)
            base_metric_tags.append("zoom_meeting_qos_video:output")
            self.gauge("meeting.qos.bitrate", video_output_bitrate, tags=base_metric_tags)
            self.gauge("meeting.qos.average_loss", avg_video_output_avg_loss, tags=base_metric_tags)
            self.gauge("meeting.qos.jitter", avg_video_output_jitter, tags=base_metric_tags)
            self.gauge("meeting.qos.latency", avg_video_output_latency, tags=base_metric_tags)
            self.gauge("meeting.qos.max_loss", avg_video_output_max_loss, tags=base_metric_tags)
            base_metric_tags.remove("zoom_meeting_qos_video:output")

    def parse_and_submit_user_qos(self, qos_values, metric_tags):
        """Helper function used to parse through the list of user qos and submit the correct format for each"""
        bitrate = parse_kbps(qos_values.get("bitrate", ""))
        avg_loss = percentage_to_float(qos_values.get("avg_loss", ""))
        jitter = parse_milliseconds(qos_values.get("jitter", ""))
        latency = parse_milliseconds(qos_values.get("latency", ""))
        max_loss = percentage_to_float(qos_values.get("max_loss", ""))

        if bitrate:
            self.gauge("user.qos.bitrate", bitrate, tags=metric_tags)
        if avg_loss:
            self.gauge("user.qos.average_loss", avg_loss, tags=metric_tags)
        if jitter:
            self.gauge("user.qos.jitter", jitter, tags=metric_tags)
        if latency:
            self.gauge("user.qos.latency", latency, tags=metric_tags)
        if max_loss:
            self.gauge("user.qos.max_loss", max_loss, tags=metric_tags)

    def reset_trackers(self):
        """Helper function that resets any desired values"""
        self.successful_api_calls = 0
        self.failed_api_calls = 0
        self.api_rate_limits_hit = 0

    def read_from_cache(self):
        # READ LASTEST STATE OF DICT FROM PERSISTENT STORAGE AND LOAD AS JSON
        persistent = self.read_persistent_cache('dict')
        # TRY TO LOAD CACHE AS JSON
        try:
            persistent = json.loads(persistent)
        except ValueError:
            persistent = {
                'calls': {}
            }
            self.log.error(
                f'ERROR READING PERSISTENT DICTIONARY TO JSON\nCREATING NEW DICT: {persistent}')

        return persistent

    def write_to_cache(self):
        old_call_ids = set()

        # Remove any call IDs older than today since these shouldn't show up in requests anymore
        for call_id, call_time in self.persistent.get('calls', {}).items():

            # Check if call time is older than 5 minutes of ingest period (for grace)
            if call_time < (self.current_time - datetime.timedelta(minutes=(self.call_timer_ingest + 5))).strftime('%Y-%m-%dT%H:%M:%SZ'):
                old_call_ids.add(call_id)

        for old_id in old_call_ids:
            del self.persistent['calls'][old_id]
            self.log.info(f"Dropping call_id from cache: {old_id}")

        try:
            self.write_persistent_cache('dict', json.dumps(self.persistent))
        except ValueError:
            self.log.error(
                f'ERROR WRITING DICTIONARY TO CACHE')
