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

REQUIRED_SETTINGS = [
    "base_api_url",
    "api_key",
    "api_secret",
    "account_name"
]
REQUIRED_TAGS = [
    "vendor:rapdev",
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
        self.base_api_url = self.instance.get("base_api_url")
        self.account_name = self.instance.get("account_name")
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.__NAMESPACE__)

        # Initialize tags
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.tags.append("zoom_api:{}".format(self.base_api_url))

        # Zoom authentication params
        self.api_key = self.instance.get("api_key")
        self.api_secret = self.instance.get("api_secret")

        # Run mode params
        self.collect_participant_details = self.instance.get("collect_participant_details", True)
        self.collect_usernames = self.instance.get("collect_usernames", True)
        self.users_to_track = self.instance.get("users_to_track", [])
        self.room_only_mode = self.instance.get("room_only_mode", False)
        
        # Master API flags
        self.is_sub_account = self.instance.get("is_sub_account", False)
        self.master_api_mode = self.instance.get("master_api_mode", False)

        # Initialize API trackers
        self.successful_api_calls = 0
        self.failed_api_calls = 0
        self.api_rate_limits_hit = 0

    def check(self, instance):
        self.validate_config()
        self.test_api_connection()

        # Append master account name at start of every run (in case it was removed)
        base_tags = list(self.tags)

        if self.is_sub_account:
            base_tags.append("zoom_account_name:{}_sub-account".format(self.account_name))
        else:
            base_tags.append("zoom_account_name:{}".format(self.account_name))

        # Reset API trackers at the start of every check run
        self.reset_trackers()

        # Check if we only care about rooms metrics
        if self.room_only_mode:
            self.get_rooms_metrics(base_tags)
        # Otherwise get all metrics
        else:
            self.get_users(base_tags)
            self.get_rooms_metrics(base_tags)
            self.get_meetings(base_tags)

        # Send OK if the API daily limit wasn't encountered during this run 
        if self.api_rate_limits_hit == 0:
            self.service_check("can_call_api", AgentCheck.OK, tags=base_tags)

        # Submit the metrics for api failed vs successful
        self.gauge("api.successful_calls", self.successful_api_calls, tags=base_tags)
        self.gauge("api.failed_calls", self.failed_api_calls, tags=base_tags)

        # Check if we should poll for sub-accounts, this will only run if we are running
        # the integration using credentials from the master account
        if self.master_api_mode:
            # Get all sub accounts via API
            sub_accounts = self.get_sub_accounts()

            for sub_account_name, sub_account_id in sub_accounts.items():
                # Reset trackers for each "sub-account" so we have API metrics for each
                self.reset_trackers()

                # Recopy list of tags
                sub_account_tags = list(self.tags)

                # Add the zoom sub-account name as a tag for all the metrics
                sub_account_tags.append("zoom_account_name:{}_sub-account".format(sub_account_name))

                if self.room_only_mode:
                    self.get_rooms_metrics(sub_account_tags, account_id=sub_account_id)
                else:
                    self.get_users(sub_account_tags, account_id=sub_account_id)
                    self.get_rooms_metrics(sub_account_tags, account_id=sub_account_id)
                    self.get_meetings(sub_account_tags, account_id=sub_account_id)

                # Send OK if the API daily limit wasn't encountered during this run 
                if self.api_rate_limits_hit == 0:
                    self.service_check("can_call_api", AgentCheck.OK, tags=sub_account_tags)

                self.gauge("api.successful_calls", self.successful_api_calls, tags=sub_account_tags)
                self.gauge("api.failed_calls", self.failed_api_calls, tags=sub_account_tags)

    def test_api_connection(self):
        self.log.debug("Attempting connection test to Zoom API URL %s.", self.base_api_url)

        try:
            x = self.http.get(self.base_api_url + "rooms",
                              auth=BearerAuth(generate_token(self.api_key, self.api_secret)))
            x.raise_for_status()
        except Exception as e:
            self.service_check("can_connect", AgentCheck.CRITICAL, tags=self.tags)
            raise Exception("Cannot authenticate to ZOOM API. The check will not run: {}".format(e))
        else:
            self.log.debug("Connection successful")
            self.service_check("can_connect", AgentCheck.OK, tags=self.tags)

    def validate_config(self):
        if not self.base_api_url:
            raise ConfigurationError("The zoom API url is required.")
        if not self.api_key:
            raise ConfigurationError("Your Zoom Account API Key is required.")
        if not self.api_secret:
            raise ConfigurationError("Your Zoom Account API Secret is required..")
        if not self.account_name:
            raise ConfigurationError("An account name is required.")

    def call_api(self, request_path, next_page_token="", from_date="", to_date="", page_size=300):
        """Helper function to call the zoom api via desired query params

        :param string request_path: the path for which to append to the base api url
        :param string next_page_token: the token for the next page if pagination is required
        :param string from_date: the start date from where to begin the query range
        :param string to_date: the end date for where to end the query range
        :param integer page_size: the number of records per page the api returns
        :raises Exception: when a non-200 and non-429 (zoom rate limit code) is returned
        :return: json of the API response
        """
        if page_size:
            request_path = request_path + "?page_size={}".format(page_size)

        if next_page_token:
            request_path = request_path + "&next_page_token={}".format(next_page_token)

        if from_date and to_date and page_size:
            request_path = request_path + "&from={}".format(from_date)
            request_path = request_path + "&to={}".format(to_date)
        elif from_date and to_date and not page_size:
            request_path = request_path + "?from={}".format(from_date)
            request_path = request_path + "&to={}".format(to_date)

        while True:
            # Make Zoom API request
            results = self.http.get(
                self.base_api_url + request_path,
                auth=BearerAuth(generate_token(self.api_key, self.api_secret))
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
                self.log.warning("Error making API call: {}".format(results.text))    
                return {}
            # If 429, that means we hit rate limit
            elif response_code == 429:
                self.failed_api_calls += 1
                headers = results.headers

                limit_type = headers.get("X-RateLimit-Type")

                # Need to append the account name in case the service checks fail
                api_base_tags = list(self.tags)
                if self.is_sub_account:
                    api_base_tags.append("zoom_account_name:{}_sub-account".format(self.account_name))
                else:
                    api_base_tags.append("zoom_account_name:{}".format(self.account_name))

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
                    raise HTTPError("Non-200 response code returned from Zoom API: {}".format(e))
                except Exception as e:
                    raise Exception("Unknown exception was caught during Zoom API request: {}".format(e))
            
    def get_users(self, base_tags, account_id=None):
        """Gets the users from Zoom API and sends in the active count and billing metric for each"""
        if account_id:
            request_path = "accounts/{}/users".format(account_id)
        else:
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
                    metric_tags.append("zoom_user_email:{}".format(user_email))
                if user_timezone:
                    metric_tags.append("zoom_user_timezone:{}".format(user_timezone))

                if user_type == 1:
                    metric_tags.append("zoom_user_account_type:basic")
                elif user_type == 2:
                    metric_tags.append("zoom_user_account_type:licensed")
                elif user_type == 3:
                    metric_tags.append("zoom_user_account_type:on-prem")

                self.gauge("users.active.count", 1, tags=metric_tags)

                if not self.room_only_mode:
                    self.gauge(self.billing_metric, 1, tags=metric_tags, raw=True)

            page_token = response.get("next_page_token", "")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, next_page_token=page_token)

    def get_rooms_metrics(self, base_tags, account_id=None):
        """Gets the metrics for each room such as component status, names, participants, etc..."""
        if account_id:
            request_path = "accounts/{}/metrics/zoomrooms".format(account_id)
        else:
            request_path = "metrics/zoomrooms"

        #call to get location hierarchy
        if account_id:
            locations_request_path = "accounts/{}/rooms/locations/".format(account_id)
        else:
            locations_request_path = "rooms/locations/"

        response = self.call_api(request_path)
        location_response = self.call_api(locations_request_path)
        locations = []
        while True:
            locations += location_response.get("locations", [])
            page_token = response.get("next_page_token", "")

            if page_token == "":
                break
            else:
                location_response = self.call_api(locations_request_path, next_page_token=page_token)

        # Rooms Health counts
        critical_rooms = 0
        warning_rooms = 0
        healthy_rooms = 0

        # Rooms Status counts
        rooms_available = 0
        rooms_in_meetings = 0
        rooms_offline = 0
        rooms_under_construction = 0

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
                    location_tags = get_room_location_tags(location_id, locations)
                    for tag in location_tags:
                        metric_tags.append(tag)
                
                if room_name:
                    metric_tags.append("zoom_room_name:{}".format(room_name))
                if room_id:
                    metric_tags.append("zoom_room_id:{}".format(room_id))
                if device_ip:
                    metric_tags.append("zoom_room_device_ip:{}".format(device_ip))
                if camera:
                    metric_tags.append("zoom_room_camera:{}".format(camera))
                if microphone:
                    metric_tags.append("zoom_room_microphone:{}".format(microphone))
                if speaker:
                    metric_tags.append("zoom_room_speaker:{}".format(speaker))

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
        metric_tags.append("zoom_room_name:{}".format(room_name))
        metric_tags.append("zoom_room_id:{}".format(room_id))

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

    def get_meetings(self, base_tags, account_id=None):
        """Gets all the current meetings with the participants and calls the QOS function on each"""
        if account_id:
            request_path = "accounts/{}/metrics/meetings".format(account_id)
        else:
            request_path = "metrics/meetings"
        
        todays_date = str(datetime.date.today())
        response = self.call_api(request_path, next_page_token="", from_date=todays_date, to_date=todays_date)

        while True:
            meetings = response.get("meetings", [])

            for meeting in meetings:
                host_name = meeting.get("host", "")
                meeting_id = meeting.get("id", "")
                
                metric_tags = base_tags.copy()
                
                metric_tags.append("zoom_meeting_id:{}".format(meeting_id))

                if self.collect_usernames:
                    metric_tags.append("zoom_meeting_host:{}".format(host_name))

                # Get the QOS metrics for every particpant in the meeting
                try:
                    self.get_meeting_qos(meeting_id, host_name, metric_tags, account_id=account_id)
                except Exception as e:
                    self.log.error("Get Meeting QOS FAILED. Caught exception: {}".format(e))

                # Send in a count for this meeting 
                self.gauge("meetings.count", 1, tags=metric_tags)

                # Send in the number of participants on this meeting
                self.gauge("meetings.participants", meeting.get("participants"), tags=metric_tags)

            page_token = response.get("next_page_token", "")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, next_page_token=page_token, from_date=todays_date, to_date=todays_date)

    def get_meeting_qos(self, meeting_id, host_name, base_tags, account_id=None):
        """Gets the QOS for each participant in the current meeting"""
        if account_id:
            request_path = "accounts/{}/metrics/meetings/{}/participants/qos".format(account_id, meeting_id)
        else:
            request_path = "metrics/meetings/{}/participants/qos".format(meeting_id)
        
        response = self.call_api(request_path, next_page_token="", from_date="", to_date="", page_size=10)

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
                            if account_id:
                                user_request_path = "accounts/{}/users/{}".format(account_id, user_id)
                            else:
                                user_request_path = "users/{}".format(user_id)                            
                            
                            # noinspection PyTypeChecker
                            user_response = self.call_api(user_request_path, next_page_token="", from_date="", to_date="", page_size=None)
                            user_email = user_response.get("email", "")

                            if user_email:
                                metric_tags.append("zoom_user_email:{}".format(user_email))

                        if user_location:
                            country = get_country(user_location)
                            metric_tags.append("zoom_user_location:{}".format(user_location))
                            metric_tags.append("zoom_user_country:{}".format(country))
                        if domain:
                            metric_tags.append("zoom_user_domain:{}".format(domain))
                        if ip_address:
                            metric_tags.append("zoom_user_ip:{}".format(ip_address))
                        if data_center:
                            metric_tags.append("zoom_user_data_center:{}".format(data_center))
                        if network_type:
                            metric_tags.append("zoom_user_network_type:{}".format(network_type))
                        if self.collect_usernames:
                            metric_tags.append("zoom_user_name:{}".format(user_name))

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
                response = self.call_api(request_path, next_page_token=page_token, from_date="", to_date="", page_size=10)

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

    def get_sub_accounts(self):
        """Gets the sub accounts from Zoom API and returns the IDs as a list"""
        request_path = "accounts/"
        response = self.call_api(request_path)

        account_ids = {}

        while True:
            accounts = response.get("accounts", [])

            for account in accounts:
                metric_tags = self.tags.copy()

                account_id = account.get("id", "")
                account_name = account.get("account_name", "")
                account_owner = account.get("owner_email", "")
                account_type = account.get("account_type", "")
                account_seats = account.get("seats", 0)

                # Only add account if it's not free, free accounts have minimal API access
                if account_type != "free":
                    account_ids[account_name] = account_id

                if account_name:
                    metric_tags.append("zoom_account_name:{}_sub-account".format(account_name))
                if account_owner:
                    metric_tags.append("zoom_sub_account_owner:{}".format(account_owner))
                if account_type:
                    metric_tags.append("zoom_sub_account_type:{}".format(account_type))
                if account_seats:
                    metric_tags.append("zoom_sub_account_seats:{}".format(account_seats))

                self.gauge("sub_accounts.count", 1, tags=metric_tags)

            page_token = response.get("next_page_token", "")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, next_page_token=page_token)
        
        return account_ids

    def reset_trackers(self):
        """Helper function that resets any desired values"""
        self.successful_api_calls = 0
        self.failed_api_calls = 0
        self.api_rate_limits_hit = 0

