try:
    from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
except ImportError:
    from checks import AgentCheck
from datadog_checks.base.utils.subprocess_output import get_subprocess_output
from .helpers import *
import json
import requests
import time
import re
import datetime
from requests.auth import HTTPBasicAuth
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


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class ZoomCheck(AgentCheck):
    def __init__(self, *args, **kwargs):
        super(ZoomCheck, self).__init__(*args, **kwargs)
        self.base_api_url = self.instance.get("base_api_url")
        self.account_name = self.instance.get("account_name")
        self.api_key = self.instance.get("api_key")
        self.api_secret = self.instance.get("api_secret")
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.tags.append("zoom_api:{}".format(self.base_api_url))
        self.tags.append("zoom_account_name:{}".format(self.account_name))
        self.metric_prefix = "rapdev.zoom"
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.metric_prefix)
        self.collect_accounts = is_affirmative(self.instance.get("collect_accounts", False))
        self.collect_plan_usage = is_affirmative(self.instance.get("collect_plan_usage", False))
        self.collect_participant_details = is_affirmative(self.instance.get("collect_participant_details", True))
        self.collect_usernames = is_affirmative(self.instance.get("collect_usernames", True))
        self.collect_top_25_issues = is_affirmative(self.instance.get("collect_top_25_issues", False))
        self.collect_im_metrics = is_affirmative(self.instance.get("collect_im_metrics", False))

    def check(self, instance):
        self.validate_config()
        self.test_api_connection()
        self.get_users()
        self.get_rooms_status()
        self.get_rooms_metrics()
        self.get_meetings()

        if self.collect_accounts:
            self.get_accounts()
        if self.collect_top_25_issues:
            self.get_top_25_rooms_issues()
        if self.collect_im_metrics:
            self.get_im_metrics()

    def test_api_connection(self):
        self.log.debug("Attempting connection test to Zoom API URL %s.", self.base_api_url)

        x = self.http.get(self.base_api_url + "rooms",
                          auth=BearerAuth(generate_token(self.api_key, self.api_secret)))

        response_code = x.status_code
        if response_code == 200:
            self.log.debug("Connection successful")
            self.service_check("{}.can_connect".format(self.metric_prefix), AgentCheck.OK, tags=self.tags)
        else:
            self.log.debug("Cannot authenticate to ZOOM API. The check will not run")
            self.service_check("{}.can_connect".format(self.metric_prefix), AgentCheck.CRITICAL, tags=self.tags)

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
        request_path = request_path + "?page_size={}".format(page_size)

        if next_page_token:
            request_path = request_path + "&next_page_token={}".format(next_page_token)

        if from_date and to_date:
            request_path = request_path + "&from={}".format(from_date)
            request_path = request_path + "&to={}".format(to_date)

        results = self.http.get(
            self.base_api_url + request_path,
            auth=BearerAuth(generate_token(self.api_key, self.api_secret))
        ).json()

        return results

    def get_users(self):
        request_path = "users"
        response = self.call_api(request_path)

        user_count = get_and_except_string(response, "total_records")
        metric_tags = self.tags.copy()

        if user_count:
            self.gauge("{}.{}.registered.count".format(self.metric_prefix, request_path),
                       user_count,
                       tags=metric_tags)

        while True:
            users = get_and_except_list(response, "users")

            for user in users:
                metric_tags = self.tags.copy()

                user_email = get_and_except_string(user, "email")
                user_timezone = get_and_except_string(user, "timezone")

                if user_email:
                    metric_tags.append("zoom_user_email:{}".format(user_email))
                if user_timezone:
                    metric_tags.append("zoom_user_timezone:{}".format(user_timezone))

                self.gauge("datadog.marketplace.{}".format(self.metric_prefix),
                           1,
                           tags=metric_tags)

            page_token = get_and_except_string(response, "next_page_token")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, page_token)

    def get_accounts(self):
        request_path = "accounts"
        response = self.call_api(request_path)

        while True:
            accounts = get_and_except_list(response, "accounts")

            for account in accounts:
                metric_tags = self.tags.copy()

                account_id = get_and_except_string(account, "id")
                account_name = get_and_except_string(account, "account_name")
                owner_email = get_and_except_string(account, "owner_email")
                seats = get_and_except_string(account, "seats")

                if account_id:
                    metric_tags.append("zoom_account_id:{}".format(account_id))
                if account_name:
                    metric_tags.append("zoom_account_name:{}".format(account_name))
                if owner_email:
                    metric_tags.append("zoom_account_owner_email:{}".format(owner_email))

                if seats:
                    self.gauge("{}.account.seats".format(self.metric_prefix),
                               seats,
                               tags=metric_tags)

                if self.collect_plan_usage:
                    self.get_usage_for_account(account_id)

            page_token = get_and_except_string(response, "next_page_token")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, page_token)

    def get_usage_for_account(self, account_id):
        request_path = "accounts/{}/plans/usage".format(account_id)

        response = self.call_api(request_path)

        for plan in response:
            metric_tags = self.tags.copy()
            plan_tag = plan.split("plan_")[1]

            metric_tags.append("zoom_plan:{}".format(plan_tag))

            if plan_tag == "recording":
                free_storage = get_and_except_string(plan, "free_storage")
                free_storage_usage = get_and_except_string(plan, "free_storage_usage")
                plan_storage = get_and_except_string(plan, "plan_storage")
                plan_storage_usage = get_and_except_string(plan, "plan_storage_usage")
                plan_storage_exceed = get_and_except_string(plan, "plan_storage_exceed")

                if free_storage:
                    metric_tags.append("zoom_plan_metric:free_storage")
                    self.gauge("{}.plan.metrics".format(self.metric_prefix),
                               free_storage,
                               tags=metric_tags)
                metric_tags.remove("zoom_plan_metric:free_storage")

                if free_storage_usage:
                    metric_tags.append("zoom_plan_metric:free_storage_usage")
                    self.gauge("{}.plan.metrics".format(self.metric_prefix),
                               free_storage_usage,
                               tags=metric_tags)
                    metric_tags.remove("zoom_plan_metric:free_storage_usage")

                if plan_storage:
                    metric_tags.append("zoom_plan_metric:storage")
                    self.gauge("{}.plan.metrics".format(self.metric_prefix),
                               plan_storage,
                               tags=metric_tags)
                    metric_tags.remove("zoom_plan_metric:storage")

                if plan_storage_usage:
                    metric_tags.append("zoom_plan_metric:storage_usage")
                    self.gauge("{}.plan.metrics".format(self.metric_prefix),
                               plan_storage_usage,
                               tags=metric_tags)
                    metric_tags.remove("zoom_plan_metric:storage_usage")

                if plan_storage_exceed:
                    metric_tags.append("zoom_plan_metric:storage_exceed")
                    self.gauge("{}.plan.metrics".format(self.metric_prefix),
                               plan_storage_exceed,
                               tags=metric_tags)
                    metric_tags.remove("zoom_plan_metric:storage_exceed")
            else:
                hosts = get_and_except_string(plan, "hosts")
                usage = get_and_except_string(plan, "usage")

                if hosts:
                    metric_tags.append("zoom_plan_metric:hosts")
                    self.gauge("{}.plan.hosts".format(self.metric_prefix), hosts, tags=metric_tags)
                    metric_tags.remove("zoom_plan_metric:hosts")

                if usage:
                    metric_tags.append("zoom_plan_metric:usage")
                    self.gauge("{}.plan.usage".format(self.metric_prefix), usage, tags=metric_tags)
                    metric_tags.remove("zoom_plan_metric:usage")

    def get_rooms_status(self):
        request_path = "rooms"
        response = self.call_api(request_path)

        rooms_available = 0
        rooms_in_meetings = 0
        rooms_offline = 0
        rooms_under_construction = 0

        while True:
            rooms = get_and_except_list(response, "rooms")

            for room in rooms:
                room_name = get_and_except_string(room, "name")
                room_id = get_and_except_string(room, "id")
                status = get_and_except_string(room, "status")

                metric_tags = self.tags.copy()
                if room_name:
                    metric_tags.append("zoom_room_name:{}".format(room_name))
                if room_id:
                    metric_tags.append("zoom_room_id:{}".format(room_id))

                if status:
                    if status == "Available":
                        room_status = 1
                        rooms_available += 1
                    elif status == "InMeeting":
                        room_status = 2
                        rooms_in_meetings += 1
                    elif status == "Offline":
                        room_status = 3
                        rooms_offline += 1
                    else:
                        room_status = 4
                        rooms_under_construction += 1

                    self.gauge("{}.room.status".format(self.metric_prefix),
                               room_status,
                               tags=metric_tags)

            page_token = get_and_except_string(response, "next_page_token")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, page_token)

        metric_tags = self.tags.copy()

        metric_tags.append("zoom_room_status:available")
        self.gauge("{}.room.status.count".format(self.metric_prefix),
                   rooms_available,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_status:available")

        metric_tags.append("zoom_room_status:in_meetings")
        self.gauge("{}.room.status.count".format(self.metric_prefix),
                   rooms_in_meetings,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_status:in_meetings")

        metric_tags.append("zoom_room_status:offline")
        self.gauge("{}.room.status.count".format(self.metric_prefix),
                   rooms_offline,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_status:offline")

        metric_tags.append("zoom_room_status:under_construction")
        self.gauge("{}.room.status.count".format(self.metric_prefix),
                   rooms_under_construction,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_status:under_construction")

    def get_rooms_metrics(self):
        request_path = "metrics/zoomrooms"
        response = self.call_api(request_path)

        critical_rooms = 0
        warning_rooms = 0
        healthy_rooms = 0

        while True:
            rooms = get_and_except_list(response, "zoom_rooms")

            for room in rooms:
                room_name = get_and_except_string(room, "room_name")
                room_id = get_and_except_string(room, "id")
                room_health = get_and_except_string(room, "health")
                device_ip = get_and_except_string(room, "device_ip")
                camera = get_and_except_string(room, "camera")
                microphone = get_and_except_string(room, "microphone")
                speaker = get_and_except_string(room, "speaker")

                metric_tags = self.tags.copy()
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

                    self.gauge("{}.room.health".format(self.metric_prefix),
                               health,
                               tags=metric_tags)

                room_issues = get_and_except_list(room, "issues")

                self.parse_and_send_issues(room_issues, room_name, room_id)

            page_token = get_and_except_string(response, "next_page_token")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, page_token)

        metric_tags = self.tags.copy()

        metric_tags.append("zoom_room_health:critical")
        self.gauge("{}.room.health.count".format(self.metric_prefix),
                   critical_rooms,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_health:critical")

        metric_tags.append("zoom_room_health:warning")
        self.gauge("{}.room.health.count".format(self.metric_prefix),
                   warning_rooms,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_health:warning")

        metric_tags.append("zoom_room_health:healthy")
        self.gauge("{}.room.health.count".format(self.metric_prefix),
                   healthy_rooms,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_health:healthy")

    def parse_and_send_issues(self, issues, room_name, room_id):
        room_controller_is_connected = 1
        selected_camera_is_connected = 1
        selected_mic_is_connected = 1
        selected_speaker_is_connected = 1
        is_cpu_usage_ok = 1
        is_bandwidth_ok = 1

        for issue in issues:
            if issue == "Room Controller Disconnected":
                room_controller_is_connected = 0
            elif issue == "Selected camera has disconnected":
                selected_camera_is_connected = 0
            elif issue == "Selected microphone has disconnected":
                selected_mic_is_connected = 0
            elif issue == "Selected speaker has disconnected":
                selected_speaker_is_connected = 0
            elif issue == "High CPU usage is detected":
                is_cpu_usage_ok = 0
            elif issue == "Low bandwidth network is detected":
                is_bandwidth_ok = 0

        metric_tags = self.tags.copy()
        metric_tags.append("zoom_room_name:{}".format(room_name))
        metric_tags.append("zoom_room_id:{}".format(room_id))

        metric_tags.append("zoom_room_component:controller")
        self.gauge("{}.room.component.status".format(self.metric_prefix),
                   room_controller_is_connected,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_component:controller")

        metric_tags.append("zoom_room_component:camera")
        self.gauge("{}.room.component.status".format(self.metric_prefix),
                   selected_camera_is_connected,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_component:camera")

        metric_tags.append("zoom_room_component:microphone")
        self.gauge("{}.room.component.status".format(self.metric_prefix),
                   selected_mic_is_connected,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_component:microphone")

        metric_tags.append("zoom_room_component:speaker")
        self.gauge("{}.room.component.status".format(self.metric_prefix),
                   selected_speaker_is_connected,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_component:speaker")

        metric_tags.append("zoom_room_component:cpu")
        self.gauge("{}.room.component.status".format(self.metric_prefix),
                   is_cpu_usage_ok,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_component:cpu")

        metric_tags.append("zoom_room_component:bandwidth")
        self.gauge("{}.room.component.status".format(self.metric_prefix),
                   is_bandwidth_ok,
                   tags=metric_tags)
        metric_tags.remove("zoom_room_component:bandwidth")

    def get_meetings(self):
        request_path = "metrics/meetings"
        todays_date = str(datetime.date.today())
        response = self.call_api(request_path, "", todays_date, todays_date)

        while True:
            meetings = get_and_except_list(response, "meetings")

            for meeting in meetings:

                host_name = get_and_except_string(meeting, "host")
                meeting_id = get_and_except_string(meeting, "id")

                metric_tags = self.tags.copy()
                metric_tags.append("zoom_meeting_id:{}".format(meeting_id))

                if self.collect_usernames:
                    metric_tags.append("zoom_meeting_host:{}".format(host_name))

                try:
                    self.get_meeting_qos(meeting_id, host_name)
                except Exception:
                    self.log.info("Get Meeting QOS FAILED")

                self.gauge("{}.meetings.count".format(self.metric_prefix),
                           1,
                           tags=metric_tags)

                self.gauge("{}.meetings.participants".format(self.metric_prefix),
                           meeting["participants"],
                           tags=metric_tags)

            page_token = get_and_except_string(response, "next_page_token")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, page_token, todays_date, todays_date)

    def get_meeting_qos(self, meeting_id, host_name):
        request_path = "metrics/meetings/{}/participants/qos".format(meeting_id)
        response = self.call_api(request_path, "", "", "", 10)

        base_metric_tags = self.tags.copy()
        base_metric_tags.append("zoom_meeting_id:{}".format(meeting_id))

        if self.collect_usernames:
            base_metric_tags.append("zoom_meeting_host:{}".format(host_name))

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

        valid_audio_input_records = 0
        valid_audio_output_records = 0
        valid_video_input_records = 0
        valid_video_output_records = 0

        while True:
            participants = get_and_except_list(response, "participants")

            for participant in participants:
                metric_tags = base_metric_tags.copy()

                leave_time = get_and_except_string(participant, "leave_time")

                if participant and leave_time == "":
                    user_location = get_and_except_string(participant, "location")
                    user_name = get_and_except_string(participant, "user_name")
                    domain = get_and_except_string(participant, "domain")
                    ip_address = get_and_except_string(participant, "ip_address")
                    connection_type = get_and_except_string(participant, "connection_type")
                    data_center = get_and_except_string(participant, "data_center")
                    network_type = get_and_except_string(participant, "network_type")

                    if self.collect_participant_details:
                        if user_location:
                            country = get_country(user_location)
                            metric_tags.append("zoom_user_location:{}".format(user_location))
                            metric_tags.append("zoom_user_country:{}".format(country))
                        if domain:
                            metric_tags.append("zoom_user_domain:{}".format(domain))
                        if ip_address:
                            metric_tags.append("zoom_user_ip:{}".format(ip_address))
                        if connection_type:
                            metric_tags.append("zoom_user_connection_type:{}".format(connection_type))
                        if data_center:
                            metric_tags.append("zoom_user_data_center:{}".format(data_center))
                        if network_type:
                            metric_tags.append("zoom_user_network_type:{}".format(network_type))

                        if self.collect_usernames:
                            metric_tags.append("zoom_user_name:{}".format(user_name))

                    self.gauge("{}.users.in_meetings.count".format(self.metric_prefix),
                               1,
                               tags=metric_tags)

                    recent_user_qos = get_and_except_list(participant, "user_qos", -1)
                    audio_input = get_and_except_dict(recent_user_qos, "audio_input")
                    audio_output = get_and_except_dict(recent_user_qos, "audio_output")
                    video_input = get_and_except_dict(recent_user_qos, "video_input")
                    video_output = get_and_except_dict(recent_user_qos, "video_output")

                    if check_for_metrics(audio_input):
                        valid_audio_input_records += 1

                        audio_input_bitrate += parse_kbps(audio_input["bitrate"])
                        audio_input_avg_loss += percentage_to_float(audio_input["avg_loss"])
                        audio_input_jitter += parse_milliseconds(audio_input["jitter"])
                        audio_input_latency += parse_milliseconds(audio_input["latency"])
                        audio_input_max_loss += percentage_to_float(audio_input["max_loss"])

                        if self.collect_participant_details:
                            metric_tags.append("zoom_user_qos_audio:input")
                            self.parse_and_submit_user_qos(audio_input, metric_tags)
                            metric_tags.remove("zoom_user_qos_audio:input")

                    if check_for_metrics(audio_output):
                        valid_audio_output_records += 1

                        audio_output_bitrate += parse_kbps(audio_output["bitrate"])
                        audio_output_avg_loss += percentage_to_float(audio_output["avg_loss"])
                        audio_output_jitter += parse_milliseconds(audio_output["jitter"])
                        audio_output_latency += parse_milliseconds(audio_output["latency"])
                        audio_output_max_loss += percentage_to_float(audio_output["max_loss"])

                        if self.collect_participant_details:
                            metric_tags.append("zoom_user_qos_audio:output")
                            self.parse_and_submit_user_qos(audio_output, metric_tags)
                            metric_tags.remove("zoom_user_qos_audio:output")

                    if check_for_metrics(video_input):
                        valid_video_input_records += 1

                        video_input_bitrate += parse_kbps(video_input["bitrate"])
                        video_input_avg_loss += percentage_to_float(video_input["avg_loss"])
                        video_input_jitter += parse_milliseconds(video_input["jitter"])
                        video_input_latency += parse_milliseconds(video_input["latency"])
                        video_input_max_loss += percentage_to_float(video_input["max_loss"])

                        if self.collect_participant_details:
                            metric_tags.append("zoom_user_qos_video:input")
                            self.parse_and_submit_user_qos(video_input, metric_tags)
                            metric_tags.remove("zoom_user_qos_video:input")

                    if check_for_metrics(video_output):
                        valid_video_output_records += 1

                        video_output_bitrate += parse_kbps(video_output["bitrate"])
                        video_output_avg_loss += percentage_to_float(video_output["avg_loss"])
                        video_output_jitter += parse_milliseconds(video_output["jitter"])
                        video_output_latency += parse_milliseconds(video_output["latency"])
                        video_output_max_loss += percentage_to_float(video_output["max_loss"])

                        if self.collect_participant_details:
                            metric_tags.append("zoom_user_qos_video:output")
                            self.parse_and_submit_user_qos(video_output, metric_tags)
                            metric_tags.remove("zoom_user_qos_video:output")

            page_token = get_and_except_string(response, "next_page_token")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, page_token, "", "", 10)

        if valid_audio_input_records > 0:
            avg_audio_input_avg_loss = calculate_average(audio_input_avg_loss, valid_audio_input_records)
            avg_audio_input_jitter = calculate_average(audio_input_jitter, valid_audio_input_records)
            avg_audio_input_latency = calculate_average(audio_input_latency, valid_audio_input_records)
            avg_audio_input_max_loss = calculate_average(audio_input_max_loss, valid_audio_input_records)
            base_metric_tags.append("zoom_meeting_qos_audio:input")
            self.gauge("{}.meeting.qos.bitrate".format(self.metric_prefix),
                       audio_input_bitrate,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.average_loss".format(self.metric_prefix),
                       avg_audio_input_avg_loss,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.jitter".format(self.metric_prefix),
                       avg_audio_input_jitter,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.latency".format(self.metric_prefix),
                       avg_audio_input_latency,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.max_loss".format(self.metric_prefix),
                       avg_audio_input_max_loss,
                       tags=base_metric_tags)
            base_metric_tags.remove("zoom_meeting_qos_audio:input")

        if valid_audio_output_records > 0:
            avg_audio_output_avg_loss = calculate_average(audio_output_avg_loss, valid_audio_output_records)
            avg_audio_output_jitter = calculate_average(audio_output_jitter, valid_audio_output_records)
            avg_audio_output_latency = calculate_average(audio_output_latency, valid_audio_output_records)
            avg_audio_output_max_loss = calculate_average(audio_output_max_loss, valid_audio_output_records)
            base_metric_tags.append("zoom_meeting_qos_audio:output")
            self.gauge("{}.meeting.qos.bitrate".format(self.metric_prefix),
                       audio_output_bitrate,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.average_loss".format(self.metric_prefix),
                       avg_audio_output_avg_loss,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.jitter".format(self.metric_prefix),
                       avg_audio_output_jitter,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.latency".format(self.metric_prefix),
                       avg_audio_output_latency,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.max_loss".format(self.metric_prefix),
                       avg_audio_output_max_loss,
                       tags=base_metric_tags)
            base_metric_tags.remove("zoom_meeting_qos_audio:output")

        if valid_video_input_records > 0:
            avg_video_input_avg_loss = calculate_average(video_input_avg_loss, valid_video_input_records)
            avg_video_input_jitter = calculate_average(audio_input_jitter, valid_video_input_records)
            avg_video_input_latency = calculate_average(audio_input_latency, valid_video_input_records)
            avg_video_input_max_loss = calculate_average(audio_input_max_loss, valid_video_input_records)
            base_metric_tags.append("zoom_meeting_qos_video:input")
            self.gauge("{}.meeting.qos.bitrate".format(self.metric_prefix),
                       video_input_bitrate,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.average_loss".format(self.metric_prefix),
                       avg_video_input_avg_loss,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.jitter".format(self.metric_prefix),
                       avg_video_input_jitter,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.latency".format(self.metric_prefix),
                       avg_video_input_latency,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.max_loss".format(self.metric_prefix),
                       avg_video_input_max_loss,
                       tags=base_metric_tags)
            base_metric_tags.remove("zoom_meeting_qos_video:input")

        if valid_video_output_records > 0:
            avg_video_output_avg_loss = calculate_average(video_output_avg_loss, valid_video_output_records)
            avg_video_output_jitter = calculate_average(video_output_jitter, valid_video_output_records)
            avg_video_output_latency = calculate_average(video_output_latency, valid_video_output_records)
            avg_video_output_max_loss = calculate_average(video_output_max_loss, valid_video_output_records)
            base_metric_tags.append("zoom_meeting_qos_video:output")
            self.gauge("{}.meeting.qos.bitrate".format(self.metric_prefix),
                       video_output_bitrate,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.average_loss".format(self.metric_prefix),
                       avg_video_output_avg_loss,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.jitter".format(self.metric_prefix),
                       avg_video_output_jitter,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.latency".format(self.metric_prefix),
                       avg_video_output_latency,
                       tags=base_metric_tags)
            self.gauge("{}.meeting.qos.max_loss".format(self.metric_prefix),
                       avg_video_output_max_loss,
                       tags=base_metric_tags)
            base_metric_tags.remove("zoom_meeting_qos_video:output")

    def parse_and_submit_user_qos(self, qos_values, metric_tags):
        bitrate = parse_kbps(
            get_and_except_string(qos_values, "bitrate"))
        avg_loss = percentage_to_float(
            get_and_except_string(qos_values, "avg_loss"))
        jitter = parse_milliseconds(
            get_and_except_string(qos_values, "jitter"))
        latency = parse_milliseconds(
            get_and_except_string(qos_values, "latency"))
        max_loss = percentage_to_float(
            get_and_except_string(qos_values, "max_loss"))

        if bitrate:
            self.gauge("{}.user.qos.bitrate".format(self.metric_prefix),
                       bitrate,
                       tags=metric_tags)
        if avg_loss:
            self.gauge("{}.user.qos.average_loss".format(self.metric_prefix),
                       avg_loss,
                       tags=metric_tags)
        if jitter:
            self.gauge("{}.user.qos.jitter".format(self.metric_prefix),
                       jitter,
                       tags=metric_tags)
        if latency:
            self.gauge("{}.user.qos.latency".format(self.metric_prefix),
                       latency,
                       tags=metric_tags)
        if max_loss:
            self.gauge("{}.user.qos.max_loss".format(self.metric_prefix),
                       max_loss,
                       tags=metric_tags)

    def get_top_25_rooms_issues(self):
        request_path = "metrics/zoomrooms/issues"
        todays_date = str(datetime.date.today())
        response = self.call_api(request_path, "", todays_date, todays_date)

        issues = get_and_except_list(response, "room_issues")

        for issue in issues:
            issue_name = get_and_except_string(issue, "issue_name")

            metric_tags = self.tags.copy()
            metric_tags.append("zoom_room_issue_name:{}".format(issue_name))

            self.gauge("{}.room.issues.count".format(self.metric_prefix),
                       issue["zoom_rooms_count"],
                       tags=metric_tags)

    def get_im_metrics(self):
        request_path = "metrics/im"
        todays_date = str(datetime.date.today())
        response = self.call_api(request_path, "", todays_date, todays_date)

        total_send = 0
        total_receive = 0
        group_send = 0
        group_receive = 0
        calls_send = 0
        calls_receive = 0
        files_send = 0
        files_receive = 0
        images_send = 0
        images_receive = 0
        voice_send = 0
        voice_receive = 0
        videos_send = 0
        videos_receive = 0
        emoji_send = 0
        emoji_receive = 0

        while True:
            users = get_and_except_list(response, "users")

            for user in users:
                total_send += user["total_send"]
                total_receive += user["total_receive"]
                group_send += user["group_send"]
                group_receive += user["group_receive"]
                calls_send += user["calls_send"]
                calls_receive += user["calls_receive"]
                files_send += user["files_send"]
                files_receive += user["files_receive"]
                images_send += user["images_send"]
                images_receive += user["images_receive"]
                voice_send += user["voice_send"]
                voice_receive += user["voice_receive"]
                videos_send += user["videos_send"]
                videos_receive += user["videos_receive"]
                emoji_send += user["emoji_send"]
                emoji_receive += user["emoji_receive"]

            page_token = get_and_except_string(response, "next_page_token")

            if page_token == "":
                break
            else:
                response = self.call_api(request_path, page_token, todays_date, todays_date)

        metric_tags = self.tags.copy()

        metric_tags.append("zoom_user_im_metric:total_send")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   total_send,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:total_send")

        metric_tags.append("zoom_user_im_metric:total_receive")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   total_receive,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:total_receive")

        metric_tags.append("zoom_user_im_metric:group_send")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   group_send,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:group_send")

        metric_tags.append("zoom_user_im_metric:group_receive")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   group_receive,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:group_receive")

        metric_tags.append("zoom_user_im_metric:calls_sent")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   calls_send,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:calls_sent")

        metric_tags.append("zoom_user_im_metric:calls_received")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   calls_receive,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:calls_received")

        metric_tags.append("zoom_user_im_metric:files_sent")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   files_send,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:files_sent")

        metric_tags.append("zoom_user_im_metric:files_received")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   files_receive,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:files_received")

        metric_tags.append("zoom_user_im_metric:images_sent")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   images_send,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:images_sent")

        metric_tags.append("zoom_user_im_metric:images_received")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   images_receive,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:images_received")

        metric_tags.append("zoom_user_im_metric:voice_sent")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   voice_send,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:voice_sent")

        metric_tags.append("zoom_user_im_metric:voice_received")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   voice_receive,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:voice_received")

        metric_tags.append("zoom_user_im_metric:videos_sent")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   videos_send,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:videos_sent")

        metric_tags.append("zoom_user_im_metric:videos_received")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   videos_receive,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:videos_received")

        metric_tags.append("zoom_user_im_metric:emojis_sent")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   emoji_send,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:emojis_sent")

        metric_tags.append("zoom_user_im_metric:emojis_received")
        self.gauge("{}.user.im_metric".format(self.metric_prefix),
                   emoji_receive,
                   tags=metric_tags)
        metric_tags.remove("zoom_user_im_metric:emojis_received")

