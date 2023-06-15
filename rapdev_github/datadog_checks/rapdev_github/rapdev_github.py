# Import base datadog functions
try:
    from datadog_checks.base import AgentCheck, ConfigurationError
except ImportError:
    from checks import AgentCheck
# Import helpers functions
from .helpers import generate_btoken
from os import path
import requests
from requests.exceptions import HTTPError
from datetime import datetime, timedelta
import json
from json import JSONDecodeError

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

        self.enable_repo_metrics = self.instance.get("enable_repo_metrics", False)
        self.base_url = self.instance.get("base_url")
        self.org = self.instance.get("org")
        self.key_path = self.instance.get("key_path")
        self.org_app_id = self.instance.get("org_app_id")
        self.gh_app_id = self.instance.get("gh_app_id")
        self.repo_list = self.instance.get("repo_list", [])
        self.workflow_list = self.instance.get("workflow_repo_list", [])
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.extra_headers = {}
        self.datetime_format = "%Y-%m-%d %H:%M:%S.%f"
        self.status_list = ["success", "failure", "cancelled", "completed", "timed_out"]
        
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

        # Generates Auth token for the run.
        self.get_oauth_token()

        # Reads the cache for the last time this function was run
        # 
        self.read_cache()
        self.list_workflows()

        # Writes the current date and time to the cache
        self.write_cache()
        self.show_self_hosted_runners()
        self.show_installed_runners()
        self.show_billing_runners()
        self.list_org_repos()
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
            raise ConfigurationError("TOKEN ERROR: Please check your config and permissions")

        oauth_token = f"token {response.get('token')}"

        # Check to see if a token was actually returned
        
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
            # self.last_run = datetime.strptime(str(self.persistent_cache['timestamp']), "%Y-%m-%d %H:%M:%S.%f")
            self.log.debug("Found existing persistent cache")
        except Exception:
            self.log.debug("No persistent cache found, creating new one")
            self.persistent_cache = {"timestamp": self.now, }
            self.last_run = datetime.datetime.strptime(str(self.persistent_cache['timestamp']), self.datetime_format)
           

    # Write the current time to the cache
    def write_cache(self):
        self.persistent_cache["timestamp"] = self.time
        self.log.debug("Caching timestamp: {}".format(self.time))
        try:
            self.write_persistent_cache("logs", json.dumps(self.persistent_cache, default=str))
        except ValueError:
            self.log.debug("Error writing to persistent cache")

    # Main calling function that sends out HTTP requests as well as gets pages if applicable
    
    def call_api(self, request_path, workflow=False):
        url_req = f"{self.base_url}{request_path}?page=1"

        if workflow:
            url_req =f"{url_req}&created=>={self.time - timedelta(days=1)}"

        try:
            api_results = self.http.get(url_req, extra_headers=self.extra_headers)
            api_results.raise_for_status()

            try: 
                final_results = api_results.json()
            except(JSONDecodeError) as e: 
                raise Exception(f"{e}: JSON body content is missing, please ensure the config is correct.")


            # If there is pagination in the reponse while loop will update extend the final results object with the list. 
            while 'next' in api_results.links.keys():
                try: 
                    api_results=self.http.get(api_results.links['next']['url'], extra_headers=self.extra_headers)
                    api_results.raise_for_status()
                    self.service_check("can_connect", AgentCheck.OK, self.tags, message="Request Successful")
                    additional_results = api_results.json()
                    final_results += additional_results
                except(HTTPError, ConnectionError) as e:
                    self.service_check("can_connect", AgentCheck.Error, self.tags, message="Request Failed")
                    raise Exception(f"{e}: Cannot connect to API during pagination, please ensure the config is correct.")
                except(JSONDecodeError) as e: 
                    raise Exception(f"{e}:  JSON body content is missing, please ensure the config is correct.")

            return final_results

        except(HTTPError, ConnectionError) as e:
            self.service_check("can_connect", AgentCheck.CRITICAL, self.tags, message="Request Failed")
            raise Exception(f"{e}: Cannot connect to API, please ensure the config is correct.")

    # Metric to list all repositories in an organization.
    # v1.0.1 Removed legacy pagination. 
    def list_org_repos(self):
        if self.enable_repo_metrics: 

            url = f"{self.mode}/{self.org}/repos"
        
            repos = self.call_api(url)
            
            for repo in repos:
                list_repo_tags = self.tags.copy()
                
                # Execute calls that return all commits in repository and get authors
                repo_name = repo.get("name", "")
                repo_url = f"repos/{self.org}/{repo_name}/stats/contributors"
                pull_url = f"repos/{self.org}/{repo_name}/pulls"
                self.show_num_commits_per_repo_body(repo_url, pull_url, repo_name)


                repo_stargazer_count = repo.get("stargazers_count")
                repo_watcher_count = repo.get("watchers_count")
                repo_forks_count = repo.get("forks_count")
                repo_issues_count = repo.get("open_issues_count")
                repo_size = repo.get("size")

                list_repo_tags += [ repo.get("visibility", True), repo.get("language", "no_language"), repo.get("name", ""), repo.get("id")]

                self.gauge("repos.stargazers", repo_stargazer_count, tags=list_repo_tags)
                self.gauge("repos.watchers", repo_watcher_count, tags=list_repo_tags)
                self.gauge("repos.forks", repo_forks_count, tags=list_repo_tags)
                self.gauge("repos.issues", repo_issues_count, tags=list_repo_tags)
                self.gauge("repos.size", repo_size, tags=list_repo_tags)

                self.count("repos.count.total", 1, tags=list_repo_tags)


    def show_num_commits_per_repo_body(self, repo_url, pull_url, repo_name):
        authors = []

        try:
            authors = self.call_api(repo_url)
            pulls = self.call_api(pull_url)
        except Exception as e:
            self.log.debug(f"Maybe Error? {e}")

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

        users = self.call_api(url)
        
        for user in users:
            members_tags = self.tags.copy()

            if user_type := user.get("type"):
                members_tags.append(f"user_type:{user_type}")

            if user_admin := user.get("site_admin"):
                members_tags.append(f"is_admin:{user_admin}")

            if user_login := user.get("login"):
                members_tags.append(f"login:{user_login}")

            self.count("users.count", 1, tags=members_tags)

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

            repo_tags.append(f"repo_name:{repo}")

            response= self.call_api(url, True)

            for workflow in response.get("workflow_runs", []):

                workflow_updated = datetime.strptime(workflow.get("updated_at"), "%Y-%m-%dT%H:%M:%SZ")

                if workflow_updated >= self.last_run:

                    workflow_tags = repo_tags.copy()

                    # Tag each instance with a unique ID
                    workflow_runnum = workflow.get("run_number")

                    workflow_status = workflow.get("conclusion")

                    workflow_tags.append(f"repo_name:{repo}")
                    if workflow_status:
                        workflow_tags.append(f"status:{workflow_status}")
                        
                    if workflow_runnum:
                        workflow_tags.append(f"reponum:{workflow_runnum}")

                    if workflow_status:
                        if workflow_status in self.status_list:
                            self.gauge("repos.workflows", 1, tags=workflow_tags)
