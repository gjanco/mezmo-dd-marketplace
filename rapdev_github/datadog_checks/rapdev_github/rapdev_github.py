# Import base datadog functions
from datadog_checks.base import AgentCheck, ConfigurationError

# Import helpers functions
from .helpers import generate_btoken, find_last_page
import os.path
from os import path
import requests
from requests.exceptions import HTTPError
import datetime
import json

# Any required tags
REQUIRED_TAGS = [
    "vendor:rapdev"
]

# Class for BearerAuth to assign headers
class BearerAuth(requests.auth.AuthBase):

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


class GitHubCheck(AgentCheck):

    __NAMESPACE__ = "rapdev.github"

    # Base agent that sets variables and the namespace
    def __init__(self, *args, **kwargs):
        super(GitHubCheck, self).__init__(*args, **kwargs)

        self.base_url = self.instance.get("base_url")
        self.org = self.instance.get("org")
        self.key_path = self.instance.get("key_path")
        self.org_app_id = self.instance.get("org_app_id")
        self.gh_app_id = self.instance.get("gh_app_id")
        self.repo_list = self.instance.get("repo_list", [])
        self.workflow_list = self.instance.get("workflow_repo_list", [])
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.extra_headers = {}
        self.status_list = ["success", "failure", "cancelled", "completed", "timed_out"]
        self.datetime_format = "%Y-%m-%d %H:%M:%S.%f"

        # Get whether or not we are dealing with an organization or an enterprise
        mode = self.instance.get("github_mode", "organization")
        if mode == "enterprise":
            self.mode = "enterprises"
        elif mode == "organization":
            self.mode = "orgs"
        else:
            raise ConfigurationError("Your GitHub mode may be typed incorrectly, "
                                     "make sure it is either 'organization' or 'enterprise'.")

    # Initializer that runs and updates all metrics
    def check(self, instance):
        # Reads the cache for the last time this function was run
        self.read_cache()
        self.list_workflows()

        # Writes the current date and time to the cache
        self.write_cache()
        self.show_self_hosted_runners()
        self.show_installed_runners()
        self.show_billing_runners()
        self.list_org_repos()
        self.show_num_commits_per_repo()
        self.list_org_members()
        self.list_cache()

    # Gets the OAuth token with the Bearer token for organization authorization
    def get_oauth_token(self):
        response = self.http.post(f"{self.base_url}app/installations/{self.org_app_id}/access_tokens",
                                  auth=BearerAuth(generate_btoken(self.key_path, self.gh_app_id)))

        # Sets the post response to dict/json format for easy reading and parsing
        try:
            response = response.json()
        except Exception:
            self.log.error(response.raise_for_status())
            raise ConfigurationError("ERROR: Unable to get access token, please check your config and try again.")

        oauth_token = f"token {response.get('token')}"

        # Check to see if a token was actually returned
        if oauth_token == "token None":
            raise ConfigurationError("TOKEN ERROR: Please check your config and permissions")
        self.extra_headers['authorization'] = oauth_token

    # Read the timestamp of the last run from the cache
    def read_cache(self):
        # Get current time
        self.now = datetime.datetime.strptime(str(datetime.datetime.now()), self.datetime_format)

        # Try to read the cache for a date and a time, otherwise make a new one.
        try:
            self.persistent_cache = self.read_persistent_cache("logs")
            self.persistent_cache = json.loads(self.persistent_cache)
            self.last_run = datetime.datetime.strptime(str(self.persistent_cache['timestamp']), self.datetime_format)
            self.log.debug("Found existing persistent cache")
        except Exception:
            self.log.debug("No persistent cache found, creating new one")
            self.persistent_cache = {"timestamp": self.now}
            self.last_run = datetime.datetime.strptime(str(self.persistent_cache['timestamp']), self.datetime_format)

    # Write the current time to the cache
    def write_cache(self):
        self.persistent_cache["timestamp"] = self.now
        self.log.debug("Caching timestamp: {}".format(self.now))
        try:
            self.write_persistent_cache("logs", json.dumps(self.persistent_cache, default=str))
        except ValueError:
            self.log.debug("Error writing to persistent cache")

    # Main calling function that sends out HTTP requests as well as gets pages if applicable
    def call_api(self, request_path, page_size=100, page_token=0, workflow=False):
        # Get the oauth token and then use it to get the API results
        url_req = self.base_url + request_path

        if page_size:
            url_req = url_req + f"?per_page={page_size}"

        if page_token:
            url_req = url_req + f"&page={page_token}"

        if workflow:
            url_req = url_req + f"&created=>={self.now - datetime.timedelta(days=1)}"

        try:
            self.get_oauth_token()

            api_results = self.http.get(url_req, extra_headers=self.extra_headers)

            response_code = api_results.status_code
            api_results.raise_for_status()

        except(Exception) as e:
            self.service_check("can_connect", AgentCheck.CRITICAL, self.tags, message="Request Failed")
            raise Exception(f"Cannot connect to API, please ensure the config is correct.")

        else:
            if response_code == 200 or 202:
                self.service_check("can_connect", AgentCheck.OK, self.tags)
                if page_token != 0:
                    return api_results.json(), find_last_page(api_results)
                else:
                    return api_results.json()
            else:
                raise HTTPError(f"ERROR {response_code}: Non-200 response code returned from API")

    # Metric to list all repositories in an organization.
    def list_org_repos(self):

        url = f"{self.mode}/{self.org}/repos"
        page_token = 1

        repos, last_page = self.call_api(url, 100, page_token)

        while True:
            for repo in repos:
                list_repo_tags = self.tags.copy()

                repo_name = repo.get("name", "")
                repo_id = repo.get("id")
                repo_visibility = repo.get("visibility", True)
                repo_stargazer_count = repo.get("stargazers_count")
                repo_watcher_count = repo.get("watchers_count")
                repo_forks_count = repo.get("forks_count")
                repo_issues_count = repo.get("open_issues_count")
                repo_size = repo.get("size")
                repo_language = repo.get("language", "")

                list_repo_tags.append(f"visibility:{repo_visibility}")
                list_repo_tags.append(f"language:{repo_language}")
                list_repo_tags.append(f"repo_name:{repo_name}")
                list_repo_tags.append(f"repo_id:{repo_id}")

                self.gauge("repos.stargazers", repo_stargazer_count, tags=list_repo_tags)
                self.gauge("repos.watchers", repo_watcher_count, tags=list_repo_tags)
                self.gauge("repos.forks", repo_forks_count, tags=list_repo_tags)
                self.gauge("repos.issues", repo_issues_count, tags=list_repo_tags)
                self.gauge("repos.size", repo_size, tags=list_repo_tags)

                self.gauge("repos.count.total", 1, tags=list_repo_tags)

                self.gauge("datadog.marketplace.rapdev.github", 1, tags=[f"repo_name:{repo_name}"], raw=True)

            if last_page == page_token:
                break
            else:
                page_token += 1
                repos, fake_page = self.call_api(url, 100, page_token)

    # Metric to show the number of commits for all repositories in an organization. Can be sorted by repo authors.
    def show_num_commits_per_repo(self):
        if not self.repo_list:

            url = f"{self.mode}/{self.org}/repos"
            page_token = 1

            repos, last_page = self.call_api(url, 100, page_token)

            while True:
                for repo in repos:
                    repo_name = repo.get("name", "")

                    repo_url = f"repos/{self.org}/{repo_name}/stats/contributors"
                    pull_url = f"repos/{self.org}/{repo_name}/pulls"

                    self.show_num_commits_per_repo_body(repo_url, pull_url, repo_name)

                if last_page == page_token:
                    break
                else:
                    page_token += 1
                    repos, fake_page = self.call_api(url, 100, page_token)

        else:
            for repo_name in self.repo_list:
                repo_url = f"repos/{self.org}/{repo_name}/stats/contributors"
                pull_url = f"repos/{self.org}/{repo_name}/pulls"

                self.show_num_commits_per_repo_body(repo_url, pull_url, repo_name)

    def show_num_commits_per_repo_body(self, repo_url, pull_url, repo_name):
        authors = []

        try:
            authors = self.call_api(repo_url, False)
            pulls = self.call_api(pull_url, False)
        except Exception as e:
            self.log.debug(f"WARNING: Skipping repos.pull_reqs and repos.commits. {e}")
            return

        for pull in pulls:
            pull_req_tags = self.tags.copy()

            pull_state = pull.get("state")

            pull_userdetails = pull.get("user")
            pull_user = pull_userdetails.get("login")

            pull_req_tags.append(f"pull_req_user:{pull_user}")
            pull_req_tags.append(f"pull_req_state:{pull_state}")

            self.gauge("repos.pull_reqs", 1, tags=pull_req_tags)

        for author in authors:
            commits_tags = self.tags.copy()

            repo_author = author.get("author", [])
            repo_author_commits = author.get("total")
            repo_login = repo_author.get("login", "")

            commits_tags.append(f"repo_author:{repo_login}")
            commits_tags.append(f"repo_name:{repo_name}")

            self.gauge("repos.commits", repo_author_commits, tags=commits_tags)

    # Metric that lists all members in an organization,
    # can be sorted by the type of user, and whether or not a user is a site admin
    def list_org_members(self):

        url = f"{self.mode}/{self.org}/members"
        page_token = 1

        users, last_page = self.call_api(url, 100, page_token)

        while True:
            for user in users:
                members_tags = self.tags.copy()

                user_type = user.get("type", "")
                user_admin = user.get("site_admin", True)
                user_login = user.get("login")

                if user_type:
                    members_tags.append(f"user_type:{user_type}")

                if user_admin:
                    members_tags.append(f"is_admin:{user_admin}")

                if user_login:
                    members_tags.append(f"login:{user_login}")

                self.gauge("users.count", 1, tags=members_tags)

            if last_page == page_token:
                break
            else:
                page_token += 1
                users, fake_page = self.call_api(url, 100, page_token)

    def show_self_hosted_runners(self):
        # List Amount of Self-Hosted Runners
        url = f"{self.mode}/{self.org}/actions/runners"

        response = self.call_api(url)

        self_runners = response.get("runners")

        for runner in self_runners:
            self_runners_tags = self.tags.copy()
            self_runner_status = runner.get("status")
            self_runners_tags.append(f"os:{runner.get('os')}")

            self.gauge("runners.self_hosted_runners_total", 1, tags=self_runners_tags)

            if self_runner_status == "online":
                self.service_check("self_hosted_runner.is_running", AgentCheck.OK, tags=self_runners_tags)
            elif self_runner_status == "offline":
                self.service_check("self_hosted_runner.is_running", AgentCheck.CRITICAL, tags=self_runners_tags)
            else:
                self.service_check("self_hosted_runner.is_running", AgentCheck.UNKNOWN, tags=self_runners_tags)

    def show_installed_runners(self):
        # List Installed Runners Apps
        url = f"{self.mode}/{self.org}/actions/runners/downloads"

        runner_apps = self.call_api(url)

        for runner_app in runner_apps:
            runner_app_metric_tags = self.tags.copy()
            runner_app_os = runner_app.get("os")
            runner_app_arch = runner_app.get("architecture")

            runner_app_metric_tags.append(f"runner_os:{runner_app_os}")
            runner_app_metric_tags.append(f"runner_architecture:{runner_app_arch}")

            self.gauge("runners.count", 1, tags=runner_app_metric_tags)

    def show_billing_runners(self):
        # Show Billing Info for Runners
        url = f"{self.mode}/{self.org}/settings/billing/actions"

        self_runner_billing = self.call_api(url)

        billing_paid_mins_used = self_runner_billing.get("total_paid_minutes_used")
        minutes_used_breakdown = self_runner_billing.get("minutes_used_breakdown")
        included_mins = self_runner_billing.get("included_minutes")

        for os in minutes_used_breakdown.keys():
            if os != "total":
                mins_breakdown_tags = self.tags.copy()
                mins_breakdown_tags.append(f"os:{os}")

                self.gauge("runners.mins_used", minutes_used_breakdown.get(os), tags=mins_breakdown_tags)

        # Total PAID Minutes Used
        self.gauge("runners.paid_mins_used", billing_paid_mins_used, tags=self.tags)

        # Max mins
        self.gauge("runners.included_mins", included_mins, tags=self.tags)

    def list_cache(self):
        url = f"{self.mode}/{self.org}/actions/cache/usage-by-repository"

        response = self.call_api(url)

        usages = response.get("repository_cache_usages", [])

        for usage in usages:
            cache_tags = self.tags.copy()
            repo_name = usage.get("full_name")
            repo_name = repo_name[len(self.org + "/"):]

            cache_size = usage.get("active_caches_size_in_bytes")
            cache_count = usage.get("active_caches_count")

            cache_tags.append(f"repo_name:{repo_name}")

            self.gauge("repos.cachesize", cache_size, tags=cache_tags)
            self.gauge("repos.cachecount", cache_count, tags=cache_tags)

    def list_workflows(self):
        for repo in self.workflow_list:
            repo_tags = self.tags.copy()
            url = f"repos/{self.org}/{repo}/actions/runs"
            page_token = 1

            repo_tags.append(f"repo_name:{repo}")

            response, last_page = self.call_api(url, 100, page_token, True)

            while True:
                workflows = response.get("workflow_runs", [])

                for workflow in workflows:

                    workflow_updated = datetime.datetime.strptime(workflow.get("updated_at"), "%Y-%m-%dT%H:%M:%SZ")

                    if workflow_updated >= (self.last_run):

                        workflow_tags = repo_tags.copy()

                        # Tag each instance with a unique ID
                        workflow_runnum = workflow.get("run_number")

                        workflow_status = workflow.get("conclusion")

                        workflow_tags.append(f"status:{workflow_status}")
                        workflow_tags.append(f"repo_name:{repo}")
                        workflow_tags.append(f"reponum:{workflow_runnum}")

                        if workflow_status:
                            if workflow_status in self.status_list:
                                self.gauge("repos.workflows", 1, tags=workflow_tags)

                if last_page == page_token:
                    break
                else:
                    page_token += 1
                    response, fake_page = self.call_api(url, 100, page_token, True)
