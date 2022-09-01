from datadog_checks.base import AgentCheck, ConfigurationError

import requests
import datetime
import json
from os import path
import os.path

REQUIRED_TAGS = [
    "vendor:rapdev"
]

class RapdevGitlabCheck(AgentCheck):

    # This will be the prefix of every metric and service check the integration sends
    __NAMESPACE__ = 'rapdev.gitlab'

    def __init__(self, *args, **kwargs):
        super(RapdevGitlabCheck, self).__init__(*args, **kwargs)

        self.base_url = self.instance.get("base_url")
        self.user = self.instance.get("user")
        self.password = self.instance.get("password")
        self.extra_headers = {}
        self.refresh_token = ""
        self.token_expir = (datetime.datetime.strptime(str(datetime.datetime.now()), "%Y-%m-%d %H:%M:%S.%f")) + datetime.timedelta(hours=2)
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.datetime_format = "%Y-%m-%d %H:%M:%S.%f"

    def check(self, instance):
        self.read_cache()
        self.list_projects()
        self.list_instance_statistics()
        self.sidekiq_queue_count()
        self.sidekiq_job_metrics()
        self.runner_data()
        self.list_issues()
        self.list_merge_requests()
        self.list_users()

    def get_token(self, token_type):

        try:
            if token_type == "token":
                token_url = f"{self.base_url}oauth/token?grant_type=password&username={self.user}&password={self.password}"
                self.log.debug("Getting a new token")
            elif token_type == "refresh":
                token_url = f"{self.base_url}oauth/token?refresh_token={self.refresh_token}&grant_type=refresh_token"
                self.log.debug("Refreshing old token")

            api_results = self.http.post(token_url)
            api_results = api_results.json()
            self.extra_headers['authorization'] = f"Bearer {api_results.get('access_token')}"
            self.refresh_token = api_results.get("refresh_token")
            self.service_check("get_token", AgentCheck.OK, self.tags)
            self.write_cache()

        except Exception as e:
            self.service_check("get_token", AgentCheck.CRITICAL, self.tags)
            self.log.error(f"An error has occurred: {e}")

    def read_cache(self):
        # Get current time
        self.now = (datetime.datetime.strptime(str(datetime.datetime.now()), self.datetime_format)) + datetime.timedelta(hours=2)

        # Try to read the cache for a date and a time, otherwise make a new one.
        try:
            self.persistent_cache = self.read_persistent_cache("logs")
            self.persistent_cache = json.loads(self.persistent_cache)
            self.token_expir = datetime.datetime.strptime(str(self.persistent_cache['timestamp']), self.datetime_format)
            self.extra_headers['authorization'] = self.persistent_cache['token']
            self.refresh_token = self.persistent_cache['refresh_token']
            self.log.debug("Found existing persistent cache")
        except Exception:
            self.log.debug("No persistent cache found, creating new one")
            self.persistent_cache = {"timestamp": self.now}
            self.token_expir = datetime.datetime.strptime(str(self.persistent_cache['timestamp']), self.datetime_format)
            self.get_token('token')

    def write_cache(self):
        self.persistent_cache["timestamp"] = self.now
        self.persistent_cache["token"] = self.extra_headers['authorization']
        self.persistent_cache["refresh_token"] = self.refresh_token
        self.log.debug("Caching timestamp: {}".format(self.now))
        try:
            self.write_persistent_cache("logs", json.dumps(self.persistent_cache, default=str))
        except ValueError:
            self.log.debug("Error writing to persistent cache")

    def page_count(self, json_dump):
        try:
            pageCount = int(json_dump.headers.get('X-Total-Pages'))
            return pageCount
        except Exception:
            return 1

    def call_api(self, url_req, page_token=0, per_page=100, scope=""):

        url_req = self.base_url + "api/v4/" + url_req

        url_req = url_req + f"?page={page_token}"

        if per_page:
            url_req = url_req + f"&per_page={per_page}"

        if scope:
            url_req = url_req + f"&scope={scope}"

        current_time = datetime.datetime.strptime(str(datetime.datetime.now()), "%Y-%m-%d %H:%M:%S.%f")

        if current_time >= self.token_expir:
            self.get_token("refresh")

        try:
            api_results = self.http.get(url_req, extra_headers=self.extra_headers)

            api_results.raise_for_status()

            self.service_check("can_connect", AgentCheck.OK, self.tags)

            if page_token != 0:
                return api_results.json(), self.page_count(api_results)
            else:
                return api_results.json()

        except Exception as e:
            self.log.error(f"{e}: Could not connect.")
            self.service_check("can_connect", AgentCheck.CRITICAL, self.tags)

    # Project

    def list_projects(self):

        self.log.debug("Listing projects, labels, and fetches")

        page_token = 1

        url = "projects"

        results, last_page = self.call_api(url, 1, 100)

        while True:
            for project in results:
                project_tags = self.tags.copy()
                project_id = project.get("id")
                project_name = project.get("name")

                project_tags.append(f"id:{project_id}")
                project_tags.append(f"project_name:{project_name}")

                self.gauge("project.count", 1, tags=project_tags)
                self.gauge("datadog.marketplace.rapdev.gitlab", 1, tags=[f"project_name:{project_name}"], raw=True)

                self.total_project_fetches(project_id, project_name)
                self.list_project_labels(project_id, project_name)

            if page_token == last_page:
                break
            else:
                page_token += 1
                results, fake_page = self.call_api(url, page_token, 100)

    def total_project_fetches(self, id, project):

        url = f"projects/{id}/statistics"

        results = self.call_api(url)

        fetches_tags = self.tags.copy()
        fetches = results.get("fetches")

        total_fetches = fetches.get("total")

        fetches_tags.append(f"project_name:{project}")

        self.gauge("project.fetches", total_fetches, tags=fetches_tags)

    def list_project_labels(self, id, project):

        page_token = 1

        url = f"projects/{id}/labels"

        results, last_page = self.call_api(url, 1, 100)

        while True:
            for label in results:
                label_tags = self.tags.copy()
                label_id = label.get("id")

                label_tags.append(f"id:{label_id}")
                label_tags.append(f"project_name:{project}")

                self.gauge("project.labels", 1, tags=label_tags)

            if page_token == last_page:
                break
            else:
                page_token += 1
                results, fake_page = self.call_api(url, page_token, 100)

    # Instance

    def list_instance_statistics(self):

        self.log.debug("Listing instance stats")

        url = "application/statistics"

        results = self.call_api(url)

        self.gauge("instance.forks", results.get("forks", 0), tags=self.tags)
        self.gauge("instance.issues", results.get("issues", 0), tags=self.tags)
        self.gauge("instance.merge_requests", results.get("merge_requests", 0), tags=self.tags)
        self.gauge("instance.notes", results.get("notes", 0), tags=self.tags)
        self.gauge("instance.ssh_keys", results.get("ssh_keys", 0), tags=self.tags)
        self.gauge("instance.users", results.get("users", 0), tags=self.tags)
        self.gauge("instance.groups", results.get("groups", 0), tags=self.tags)
        self.gauge("instance.active_users", results.get("active_users", 0), tags=self.tags)

    # Sidekiq

    def sidekiq_queue_count(self):

        self.log.debug("Listing sidekiq queue count")

        url = "sidekiq/queue_metrics"
        total = 0

        results = self.call_api(url)

        total = len(results.get("queues", {}))

        self.gauge("sidekiq.queue_count", total, tags=self.tags)

    def sidekiq_job_metrics(self):

        self.log.debug("Listing sidekiq job metrics")

        url = "sidekiq/job_stats"

        results = self.call_api(url)

        try:
            jobs = results.get("jobs")

            self.gauge("sidekiq.jobs_processed", jobs.get("processed", 0), tags=self.tags)
            self.gauge("sidekiq.jobs_failed", jobs.get("failed", 0), tags=self.tags)
            self.gauge("sidekiq.jobs_enqueued", jobs.get("enqueued", 0), tags=self.tags)
            self.gauge("sidekiq.jobs_dead", jobs.get("dead", 0), tags=self.tags)

        except Exception as e:
            self.log.debug(f"{e}\nCouldn't find Sidekiq Jobs")

    # Runners

    def runner_data(self):

        self.log.debug("Listing runner data")

        page_token = 1

        online_runners = 0
        offline_runners = 0
        stale_runners = 0
        never_contacted_runners = 0
        unknown_runners = 0

        url = "runners/all"

        results, last_page = self.call_api(url, 1, 100)

        while True:
            for runner in results:
                runner_tags = self.tags.copy()
                status = 0

                runner_id = runner.get("id")
                runner_type = runner.get("runner_type")
                runner_status = runner.get("status")

                runner_tags.append(f"id:{runner_id}")
                runner_tags.append(f"type:{runner_type}")

                if runner_status:
                    if runner_status == "online":
                        status = 1
                        online_runners += 1
                    if runner_status == "offline":
                        status = 2
                        offline_runners += 1
                    if runner_status == "stale":
                        status = 3
                        stale_runners += 1
                    if runner_status == "never_contacted":
                        status = 4
                        never_contacted_runners += 1
                    else:
                        status = 5
                        unknown_runners += 1

                self.gauge("runner.status", status, tags=runner_tags)
                self.gauge("runner.data", 1, tags=runner_tags)

            if page_token == last_page:
                break
            else:
                page_token += 1
                results, fake_page = self.call_api(url, page_token, 100)

        runner_tags = self.tags.copy()

        self.gauge("runner.status_count", online_runners, tags=runner_tags+["runner_status:online"])

        self.gauge("runner.status_count", offline_runners, tags=runner_tags+["runner_status:offline"])

        self.gauge("runner.status_count", stale_runners, tags=runner_tags+["runner_status:stale"])

        self.gauge("runner.status_count", never_contacted_runners, tags=runner_tags+["runner_status:never_contacted"])

    # Issues

    def list_issues(self):

        self.log.debug("Listing issues")

        page_token = 1
        counter = 0
        url = "/issues"

        results, last_page = self.call_api(url, page_token, 100, "all")

        while True:
            for issue in results:

                issue_tags = self.tags.copy() + [f"id:{issue.get('id')}", f"state:{issue.get('state')}", f"type:{issue.get('type')}"]
                self.gauge("issues", 1, tags=issue_tags)

            if page_token == last_page:
                break
            else:
                page_token += 1
                results, fake_page = self.call_api(url, page_token, 100, "all")

    # Merge Requests

    def list_merge_requests(self):

        self.log.debug("Listing merge requests")

        page_token = 1

        url = "merge_requests"

        results, last_page = self.call_api(url, 1, 100, "all")

        while True:
            for mr in results:
                mr_tags = self.tags.copy() + [f"title:{mr.get('title')}"]

                self.gauge("merge_requests", 1, tags=mr_tags)

            if page_token == last_page:
                break
            else:
                page_token += 1
                results, fake_page = self.call_api(url, page_token, 100, "all")

    def list_users(self):

        self.log.debug("Listing users")

        page_token = 1

        url = "users"

        results, last_page = self.call_api(url, 1, 100)

        while True:
            for user in results:
                user_tags = self.tags.copy() + [f"username:{user.get('username')}", f"is_admin:{user.get('is_admin')}", f"2fa_enabled:{user.get('two_factor_enabled')}"]

                self.gauge("users", 1, tags=user_tags)

            if page_token == last_page:
                break
            else:
                page_token += 1
                results, fake_page = self.call_api(url, page_token, 100)
