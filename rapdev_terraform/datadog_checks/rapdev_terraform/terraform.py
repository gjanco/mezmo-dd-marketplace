try:
    from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
except ImportError:
    from checks import AgentCheck
from datadog_checks.base.utils.subprocess_output import get_subprocess_output
import requests
import time
from .helpers import *
from requests.auth import HTTPBasicAuth

REQUIRED_TAGS = [
    "vendor:rapdev",
]


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class TerraformCheck(AgentCheck):
    def __init__(self, *args, **kwargs):
        super(TerraformCheck, self).__init__(*args, **kwargs)
        self.base_api_url = "https://app.terraform.io/api/v2/"
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])

        self.api_token = self.instance.get("api_token")
        self.metric_prefix = "rapdev.terraform"
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.metric_prefix)

        self.should_parse_agent_pools = self.instance.get("collect_agents")

    def check(self, instance):
        self.validate_config()
        self.test_api_connection()

        # If the list of org ids is not provided, get all orgs from api
        organization_ids = self.get_organization_ids()

        for org_id in organization_ids:
            # Agent pools
            if self.should_parse_agent_pools:
                self.get_agent_pools(org_id)

            # Get the workspaces and runs for the org
            self.get_workspace_ids(org_id)

            # Get the teams for the org
            self.get_organization_teams(org_id)

        self.get_terraform_variables()

    def validate_config(self):
        if not self.api_token:
            raise ConfigurationError("A Terraform API Key is required in the configuration yaml.")

    def test_api_connection(self):
        self.log.debug("Attempting connection test to Terraform API URL %s.", self.base_api_url)

        try:
            x = self.http.get(self.base_api_url + "account/details", auth=BearerAuth(self.api_token))
            x.raise_for_status()

            self.log.debug("Connection successful")
            self.service_check("{}.can_connect".format(self.metric_prefix), AgentCheck.OK, tags=self.tags)
        except requests.exceptions.HTTPError as e:
            self.service_check("{}.can_connect".format(self.metric_prefix), AgentCheck.CRITICAL, tags=self.tags)
            raise requests.exceptions.HTTPError("Cannot connect to the Terraform Cloud API. " \
                                                + "The check will not run correctly: {}".format(e))

    def call_api(self, request_path, next_page_token="", page_size=100):
        request_path = request_path + "?page[size]={}".format(page_size)

        if next_page_token:
            request_path = request_path + "&page[number]={}".format(next_page_token)

        try:
            while True:
                results = self.http.get(
                    self.base_api_url + request_path,
                    auth=BearerAuth(self.api_token)
                )

                if results.status_code == 429:
                    time.sleep(1)
                    continue

                results.raise_for_status()
                return results.json()
        except requests.exceptions.HTTPError as e:
            self.log.debug("Failed to call endpoint \"{}\". The check will not run correctly: {}"
                           .format(request_path, e))
            raise Exception("Error calling API: {}".format(e))

    def get_organization_ids(self):
        org_ids = []
        organizations = self.call_api("organizations").get("data")

        for org in organizations:
            metric_tags = self.tags.copy()
            org_id = org.get("id")
            org_attributes = org.get("attributes")

            org_ids.append(org_id)
            metric_tags.append("tf_org_id:{}".format(org_id))

            plan_expired = org_attributes.get("plan-expired")
            metric_tags.append("tf_org_plan_expired:{}".format(plan_expired))
            metric_tags.append("tf_org_has_2fa:{}".format(org_attributes.get("two-factor-conformant")))

            self.gauge("{}.org.count".format(self.metric_prefix),
                       1,
                       tags=metric_tags)

        return org_ids

    def get_organization_teams(self, org_id):
        request_path = "organizations/{}/teams".format(org_id)
        org_teams_response = self.call_api(request_path)

        parsed_users = set()

        while True:
            teams = org_teams_response.get("data")

            for team in teams:
                metric_tags = self.tags.copy()
                metric_tags.append("tf_org_id:{}".format(org_id))

                team_id = team.get("id")
                metric_tags.append("tf_team_id:{}".format(team_id))

                team_attributes = team.get("attributes")
                metric_tags.append("tf_team_name:{}".format(team_attributes.get("name")))
                metric_tags.append("tf_team_visibility:{}".format(team_attributes.get("visibility")))

                # Team permissions
                team_permissions = team_attributes.get("permissions")
                metric_tags.append("tf_team_perms_can_update_membership:{}".format(
                    team_permissions.get("can-update-membership")))
                metric_tags.append("tf_team_perms_can_destroy:{}".format(
                    team_permissions.get("can-destroy")))
                metric_tags.append("tf_team_perms_can_update_org_access:{}".format(
                    team_permissions.get("can-update-org-access")))
                metric_tags.append("tf_team_perms_can_update_api_token:{}".format(
                    team_permissions.get("can-update-api-token")))
                metric_tags.append("tf_team_perms_can_update_visibility:{}".format(
                    team_permissions.get("can-update-visibility")))

                self.gauge("{}.org.teams.count".format(self.metric_prefix),
                           1,
                           tags=metric_tags)

                self.gauge("{}.org.team.users.count".format(self.metric_prefix),
                           team_attributes.get("users-count"),
                           tags=metric_tags)

                users = team.get("relationships").get("users").get("data")
                parsed_users = self.get_user_information(users, parsed_users, org_id)

            next_page_token = org_teams_response.get("meta").get("pagination").get("next-page")
            if not next_page_token:
                break
            else:
                org_teams_response = self.call_api(request_path, next_page_token)

    def get_user_information(self, users, parsed_users, org_id):

        for user in users:
            user_id = user.get("id")

            if user_id not in parsed_users:
                metric_tags = self.tags.copy()
                metric_tags.append("tf_org_id:{}".format(org_id))
                metric_tags.append("tf_user_id:{}".format(user_id))
                parsed_users.add(user_id)

                request_path = "users/{}".format(user_id)
                user_data = self.call_api(request_path).get("data")
                user_attributes = user_data.get("attributes")

                metric_tags.append("tf_user_name:{}".format(user_attributes.get("username")))
                metric_tags.append("tf_user_is_service_account:{}".format(
                    user_attributes.get("is-service-account")))

                user_permissions = user_attributes.get("permissions")
                metric_tags.append("tf_user_perms_can_create_orgs:{}".format(
                    user_permissions.get("can-create-orgs")))
                metric_tags.append("tf_user_perms_can_change_email:{}".format(
                    user_permissions.get("can-change-email")))
                metric_tags.append("tf_user_perms_can_change_username:{}".format(
                    user_permissions.get("can-change-username")))
                metric_tags.append("tf_user_perms_can_manage_user_tokens:{}".format(
                    user_permissions.get("can-manage-user-tokens")))

                self.gauge("{}.org.users.count".format(self.metric_prefix),
                           1,
                           tags=metric_tags)

        return parsed_users

    def get_workspace_ids(self, org_id):
        request_path = "organizations/{}/workspaces".format(org_id)
        workspaces_response = self.call_api(request_path)

        while True:
            workspaces = workspaces_response.get("data")

            for workspace in workspaces:
                metric_tags = self.tags.copy()
                metric_tags.append("tf_org_id:{}".format(org_id))

                attributes = workspace.get("attributes")

                workspace_name = attributes.get("name")
                workspace_id = workspace.get("id")

                # Add the static workspace attributes to tags
                metric_tags.append("tf_workspace_name:{}".format(workspace_name))
                metric_tags.append("tf_workspace_id:{}".format(workspace_id))
                metric_tags.append("tf_workspace_tf_version:{}".format(attributes.get("terraform-version")))
                metric_tags.append("tf_workspace_environment:{}".format(attributes.get("environment")))
                metric_tags.append("tf_workspace_execution_mode:{}".format(attributes.get("execution-mode")))
                metric_tags.append("tf_workspace_source:{}".format(attributes.get("source")))

                days_since_updates = get_days_since_date(attributes.get("updated-at"))

                self.gauge("{}.org.workspace.last_updated".format(self.metric_prefix),
                           days_since_updates,
                           tags=metric_tags)

                self.gauge("{}.org.workspace.count".format(self.metric_prefix),
                           1,
                           tags=metric_tags)

                latest_run_id = workspace.get("relationships").get("latest-run").get("data").get("id")

                if latest_run_id:
                    self.get_latest_workspace_run(latest_run_id, workspace_name, workspace_id)

                # Get all the runs for this workspace
                self.get_workspace_runs(workspace_id, workspace_name)

            next_page_token = workspaces_response.get("meta").get("pagination").get("next-page")
            if not next_page_token:
                break
            else:
                workspaces_response = self.call_api(request_path, next_page_token)

    def get_latest_workspace_run(self, latest_run_id, workspace_name, workspace_id):
        request_path = "runs/{}".format(latest_run_id)
        runs_response = self.call_api(request_path)

        run = runs_response.get("data")

        metric_tags = self.tags.copy()
        metric_tags.append("tf_workspace_id:{}".format(workspace_id))
        metric_tags.append("tf_workspace_name:{}".format(workspace_name))
        metric_tags.append("tf_run_id:{}".format(latest_run_id))

        run_attributes = run.get("attributes")
        metric_tags.append("tf_run_source:{}".format(run_attributes.get("source")))
        metric_tags.append("tf_run_trigger_reason:{}".format(
            run_attributes.get("trigger-reason")))

        metric_tags.append("tf_run_has_changes:{}".format(
            run_attributes.get("has-changes")))

        # "Is" flags
        metric_tags.append("tf_run_is_destroy:{}".format(
            run_attributes.get("is-destroy")))
        metric_tags.append("tf_run_is_plan_only:{}".format(
            run_attributes.get("plan-only")))
        metric_tags.append("tf_run_is_refresh_only:{}".format(
            run_attributes.get("refresh-only")))

        run_status = run_attributes.get("status")

        if run_status == "pending":
            status = 0
        elif run_status == "applied":
            status = 1
        elif run_status == "planned_and_finished":
            status = 2
        elif run_status == "discarded":
            status = 3
        elif run_status == "canceled":
            status = 4
        elif run_status == "errored":
            status = 5
        else:
            status = 6

        self.gauge("{}.org.workspace.latest_run.status".format(self.metric_prefix),
                   status,
                   tags=metric_tags)

        days_since_run = get_days_since_date(run_attributes.get("created-at"))

        self.gauge("{}.org.workspace.latest_run.days_since".format(self.metric_prefix),
                   days_since_run,
                   tags=metric_tags)

    def get_workspace_runs(self, workspace_id, workspace_name):
        request_path = "workspaces/{}/runs".format(workspace_id)
        runs_response = self.call_api(request_path)

        while True:
            runs = runs_response.get("data")

            for run in runs:
                metric_tags = self.tags.copy()
                metric_tags.append("tf_workspace_id:{}".format(workspace_id))
                metric_tags.append("tf_workspace_name:{}".format(workspace_name))
                metric_tags.append("tf_run_id:{}".format(run.get("id")))

                run_attributes = run.get("attributes")
                metric_tags.append("tf_run_source:{}".format(run_attributes.get("source")))
                metric_tags.append("tf_run_trigger_reason:{}".format(
                    run_attributes.get("trigger-reason")))

                metric_tags.append("tf_run_has_changes:{}".format(
                    run_attributes.get("has-changes")))

                # "Is" flags
                metric_tags.append("tf_run_is_destroy:{}".format(
                    run_attributes.get("is-destroy")))
                metric_tags.append("tf_run_is_plan_only:{}".format(
                    run_attributes.get("plan-only")))
                metric_tags.append("tf_run_is_refresh_only:{}".format(
                    run_attributes.get("refresh-only")))

                run_status = run_attributes.get("status")

                if run_status == "pending":
                    status = 0
                elif run_status == "applied":
                    status = 1
                elif run_status == "planned_and_finished":
                    status = 2
                elif run_status == "discarded":
                    status = 3
                elif run_status == "canceled":
                    status = 4
                elif run_status == "errored":
                    status = 5
                else:
                    status = 6

                self.gauge("{}.org.workspace.runs.count".format(self.metric_prefix),
                           1,
                           tags=metric_tags)

                self.gauge("{}.org.workspace.run.status".format(self.metric_prefix),
                           status,
                           tags=metric_tags)

            next_page_token = runs_response.get("meta").get("pagination").get("next-page")
            if not next_page_token:
                break
            else:
                runs_response = self.call_api(request_path, next_page_token)

    def get_agent_pools(self, organization_id):
        request_path = "organizations/{}/agent-pools".format(organization_id)
        agent_pools_response = self.call_api(request_path)

        while True:
            agent_pools = agent_pools_response.get("data")
            for agent_pool in agent_pools:
                metric_tags = self.tags.copy()
                agent_pool_id = agent_pool.get("id")
                metric_tags.append("tf_agent_pool_id:{}".format(agent_pool_id))

                agent_pool_attributes = agent_pool.get("attributes")
                if agent_pool_attributes:
                    metric_tags.append("tf_agent_pool_name:{}".format(agent_pool_attributes.get("name")))

                self.gauge("{}.org.agent_pools.count".format(self.metric_prefix),
                           1,
                           tags=metric_tags)

                self.get_agent_pool_auth_tokens(agent_pool_id, metric_tags)

                self.get_agents(agent_pool_id, metric_tags)

            next_page_token = agent_pools_response.get("meta").get("pagination").get("next-page")
            if not next_page_token:
                break
            else:
                agent_pools_response = self.call_api(request_path, next_page_token)

    def get_agent_pool_auth_tokens(self, agent_pool_id, metric_tags):
        request_path = "agent-pools/{}/authentication-tokens".format(agent_pool_id)
        auth_tokens_response = self.call_api(request_path)

        while True:
            auth_tokens = auth_tokens_response.get("data")

            for auth_token in auth_tokens:
                token_tags = metric_tags.copy()
                token_tags.append("tf_agent_auth_token_id:{}".format(auth_token.get("id")))
                auth_token_creator = auth_token.get("relationships").get("created-by").get("data").get("id")
                token_tags.append("tf_agent_auth_token_creator:{}".format(auth_token_creator))

                self.gauge("{}.org.agent_pool.auth_tokens.count".format(self.metric_prefix),
                           1,
                           tags=token_tags)

            next_page_token = auth_tokens_response.get("meta").get("pagination").get("next-page")
            if not next_page_token:
                break
            else:
                auth_tokens_response = self.call_api(request_path, next_page_token)

    def get_agents(self, agent_pool_id, metric_tags):
        request_path = "agent-pools/{}/agents".format(agent_pool_id)
        agents_in_pool_response = self.call_api(request_path)

        while True:
            agents = agents_in_pool_response.get("data")

            for agent in agents:
                agent_tags = metric_tags.copy()

                agent_attributes = agent.get("attributes")

                agent_tags.append("tf_agent_name:{}".format(agent_attributes.get("name")))
                agent_tags.append("tf_agent_ip:{}".format(agent_attributes.get("ip-address")))

                agent_status = agent_attributes.get("status")

                if agent_status == "idle":
                    status = 0
                elif agent_status == "busy":
                    status = 1
                elif agent_status == "exited":
                    status = 2
                elif agent_status == "errored":
                    status = 3
                else:
                    status = 4

                self.gauge("{}.org.agent_pool.agents.count".format(self.metric_prefix),
                           1,
                           tags=agent_tags)

                self.gauge("{}.org.agent_pool.agent.status".format(self.metric_prefix),
                           status,
                           tags=agent_tags)

            next_page_token = agents_in_pool_response.get("meta").get("pagination").get("next-page")
            if not next_page_token:
                break
            else:
                agents_in_pool_response = self.call_api(request_path, next_page_token)

    def get_terraform_variables(self):
        request_path = "vars"
        terraform_variables = self.call_api(request_path).get("data")

        for variable in terraform_variables:
            metric_tags = self.tags.copy()
            metric_tags.append(variable.get("id"))

            variable_attributes = variable.get("attributes")

            metric_tags.append("tf_variable_key:{}".format(variable_attributes.get("key")))
            metric_tags.append("tf_variable_is_sensitive:{}".format(variable_attributes.get("sensitive")))
            metric_tags.append("tf_variable_category:{}".format(variable_attributes.get("category")))
            metric_tags.append("tf_variable_is_hcl:{}".format(variable_attributes.get("hcl")))

            self.gauge("{}.variables.count".format(self.metric_prefix),
                       1,
                       tags=metric_tags)

