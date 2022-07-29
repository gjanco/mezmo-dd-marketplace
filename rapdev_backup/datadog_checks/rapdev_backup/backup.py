try:
    from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
except ImportError:
    from checks import AgentCheck
import json
import datetime
from requests.exceptions import HTTPError
from datetime import datetime
import zipfile
import sys
from .helpers import *
try:
    from azure.storage.blob import ContentSettings
except ImportError:
    pass

try:
    from github import Github
    from github import InputGitTreeElement
except ImportError:
    pass

import base64
import os

try:
    from datadog_agent import get_config
except ImportError:
    def get_config(key):
        return ""

REQUIRED_SETTINGS = [
    "api_key",
    "api_secret",
]
REQUIRED_TAGS = [
    "vendor:rapdev",
]

API_URL_MAP = {
    "com": "api.datadoghq.com",
    "eu": "api.datadoghq.eu",
    "us3": "api.us3.datadoghq.com",
    "us5": "api.us5.datadoghq.com",
    "gov": "api.ddog-gov.com"
}

BACKUP_AWS = "aws"
BACKUP_AZURE = "azure"
BACKUP_GITHUB = "github"
BACKUP_LOCAL = "local"

SUPPORTED_STORAGE_PLATFORMS = {
    BACKUP_AWS,
    BACKUP_AZURE,
    BACKUP_GITHUB,
    BACKUP_LOCAL
}


class BackupCheck(AgentCheck):

    __NAMESPACE__ = "rapdev.backup"

    def __init__(self, *args, **kwargs):
        super(BackupCheck, self).__init__(*args, **kwargs)
        # Get the appropriate URL for datadog account
        self.dd_site = self.instance.get("dd_site", "com")
        self.api_url = API_URL_MAP.get(self.dd_site)
        self.dd_api_key = self.get_key("dd_api_key")
        self.dd_app_key = self.get_key("dd_app_key")
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.__NAMESPACE__)

        # Standard params for every run
        self.timestamp_format = self.instance.get("timestamp_format", "%Y-%m-%dT%H%M%S")
        self.backup_storage_platform = self.instance.get("backup_storage_platform", "").lower()
        self.backup_path = self.instance.get("backup_path")
        self.delete_local_backups = self.instance.get("delete_local_backups")

        # AWS authentication/params
        self.aws_access_key = self.instance.get("aws_access_key", None)
        self.aws_secret_key = self.instance.get("aws_secret_key", None)
        self.assume_role_arn = self.instance.get("assume_role_arn", None)
        self.assume_session_name = self.instance.get("assume_session_name", "DatadogBackupSession")
        self.assume_role_external_id = self.instance.get("assume_role_external_id")
        self.aws_s3_bucket_name = self.instance.get("aws_s3_bucket_name", None)
        self.aws_s3_sub_path = self.instance.get("aws_s3_sub_path", "")
        self.use_instance_profile = self.instance.get("use_instance_profile", False)

        # Azure authentication/params
        self.azure_connection_string = self.instance.get("azure_connection_string", None)
        self.azure_container_name = self.instance.get("azure_container_name", None)

        # Github authentication/params
        self.github_access_token = self.instance.get("github_access_token", None)
        self.github_repo = self.instance.get("github_repo", None)
        self.github_store_path = self.instance.get("github_store_path", "dd_backups")
        self.github_enterprise = self.instance.get("github_enterprise", None)
        self.master_ref = self.instance.get("github_master_ref", "heads/main")

        self.check_initializations.append(self.validate_config)

    def check(self, instance):
        self.test_api_connection()

        # Create a backup to a local file
        backup_file_path = self.create_backup(self.dd_api_key, self.dd_app_key)
        backup_file_properties = backup_file_path.split("/")
        backup_file_name = backup_file_properties[-1]

        self.gauge(self.billing_metric, 1, tags=self.tags, raw=True)

        if self.backup_storage_platform == BACKUP_LOCAL:
            return

        elif self.backup_storage_platform == BACKUP_AWS:
            # Create an s3 client using credentials
            s3_client = setup_aws_connection(
                self.aws_access_key,
                self.aws_secret_key,
                self.assume_role_arn,
                self.assume_session_name,
                self.assume_role_external_id,
                self.use_instance_profile
            )

            if self.aws_s3_sub_path:
                backup_file_name = self.aws_s3_sub_path + backup_file_name

            if upload_backup_to_s3(s3_client, self.aws_s3_bucket_name, backup_file_path, backup_file_name):
                self.log.info("Successfully uploaded backup to S3 Bucket {}".format(self.aws_s3_bucket_name))
            else:
                self.log.error("Backup to S3 failed. Will clean up the created backups or exit.")

        elif self.backup_storage_platform == BACKUP_AZURE:
            # Generate a new blob client
            blob_client = setup_azure_connection(
                self.azure_connection_string, self.azure_container_name, backup_file_name
            )
            # Set the blob type to zip so backup can be successfully unzipped
            with open(backup_file_path, "rb") as data:
                blob_client.upload_blob(data, content_settings=ContentSettings(content_type="application/zip"))
                self.log.info("Successfully uploaded Backup to Azure Blob.")

        elif self.backup_storage_platform == BACKUP_GITHUB:
            try:
                # Connect using custom name if github enterprise
                if self.github_enterprise:
                    github_connection = Github(
                        base_url="https://{}/api/v3".format(self.github_enterprise),
                        login_or_token=self.github_access_token
                    )
                # Otherwise use normal github connection
                else:
                    github_connection = Github(self.github_access_token)

                # Get the repo we care about (will fail if no access)
                repo = github_connection.get_repo(self.github_repo)

                # validate repo
                if not repo:
                    raise Exception("Repo not found: {}".format(self.github_repo))

                # build commit with backup and push
                commit_message = "Uploading backup {} to Github".format(backup_file_name) 
                master_ref = repo.get_git_ref(self.master_ref)
                master_sha = master_ref.object.sha
                base_tree = repo.get_git_tree(master_sha)
                data = base64.b64encode(open(backup_file_path, "rb").read())
                blob = repo.create_git_blob(data.decode("utf-8"), "base64")
                element = InputGitTreeElement(
                        path="{}/{}".format(
                            self.github_store_path, 
                            backup_file_name
                        ),
                        mode='100644', 
                        type='blob', 
                        sha=blob.sha
                )
                element_list = list()
                element_list.append(element)
                tree = repo.create_git_tree(element_list, base_tree)
                parent = repo.get_git_commit(master_sha)
                commit = repo.create_git_commit(commit_message, tree, [parent])
                master_ref.edit(commit.sha)

            except Exception as e:
                raise Exception("Unable to upload backup to github: {}".format(e))

        if self.delete_local_backups:
            try:
                os.remove(backup_file_path)
                os.removedirs(self.backup_path)
            except Exception as e:
                raise Exception("Failed to remove backup file and/or directory: {}".format(e))

    def test_api_connection(self):
        self.log.debug("Attempting connection test to Datadog API.")

        try:
            x = self.call_api("validate", self.dd_api_key, self.dd_app_key, jsonify=False)

            response_code = x.status_code
            if response_code == 200:
                self.log.debug("Connection successful")
                self.service_check("can_connect", AgentCheck.OK, tags=self.tags)
        except HTTPError as e:
            self.service_check("can_connect", AgentCheck.CRITICAL, tags=self.tags)
            raise HTTPError("Cannot authenticate to Datadog API. The check will not run: {}".format(e))

    def validate_config(self):
        if not self.backup_path:
            raise ConfigurationError("The backup_path variable is required.")
        if not self.backup_storage_platform:
            raise ConfigurationError("The backup_storage_platform variable is required.")
        if self.dd_site not in API_URL_MAP.keys():
            raise ConfigurationError("Please provide a valid Datadog site - com, eu, us3, us5, or gov")

        if self.backup_storage_platform not in SUPPORTED_STORAGE_PLATFORMS:
            raise ConfigurationError("Provided storage platform is not supported: {}"
                                     .format(self.backup_storage_platform))
        else:
            if self.backup_storage_platform == BACKUP_AWS:
                # If AWS and using instance profile, validate creds aren't set
                if self.use_instance_profile:
                    if self.aws_access_key or self.aws_secret_key:
                        raise ConfigurationError(
                            "Integration is setup to run via Instance Profile. Access Key and Secret Key should not be set!"
                        )
                # If AWS and using hardcoded creds, validate we have required creds
                elif not self.aws_access_key or not self.aws_secret_key:
                    raise ConfigurationError(
                        "aws_access_key, aws_secret_key, and aws_s3_bucket_url are all required "
                        + "for storing backups in AWS."
                    )

                if not self.aws_s3_bucket_name:
                    raise ConfigurationError(
                        "An S3 Bucket name is required to store backups to AWS S3."
                    )

                # Validate that boto3 has been installed and imported
                if not sys.modules.get('boto3'):
                    raise ImportError("Please install/update the AWS Boto3 Python library.")

            elif self.backup_storage_platform == BACKUP_AZURE:
                # If azure, validate we have required creds
                if not self.azure_connection_string or not self.azure_container_name:
                    raise ConfigurationError(
                        "azure_connection_string and azure_container_name are required "
                        + "for Azure authentication."
                    )

                # Validate that azure library has been installed and imported
                if not sys.modules.get('azure.storage.blob'):
                    raise ImportError("Please install/update the Azure Blob Python library")

            elif self.backup_storage_platform == BACKUP_GITHUB:
                # Make sure at least repo and access token is provided
                if not self.github_repo or not self.github_access_token:
                    raise ConfigurationError(
                        "github_repo and github_access_token are required to run in github mode."
                    )

                # Validate that github library have been installed and imported
                if not sys.modules.get('github'):
                    raise ImportError("Please install/update the Github Python library.")

    def get_key(self, key):
        # Try to grab key from instances (1st choice)
        config_key = self.instance.get(key, "")

        if not config_key:
            # If instance key not set, grab key from init_config (2nd choice)
            config_key = self.init_config.get(key, "")

            if not config_key and key == "api_key":
                # If both aren't set, try to grab api_key from yaml (and anywhere else)
                config_key = get_config(key)

        if not config_key:
            raise ConfigurationError("No key {} found".format(key))

        return config_key

    def call_api(self, request_path, dd_api_key, dd_app_key, jsonify=True, api_version_number=1):
        """Helper function used to call the DD API

        :param string request_path: the endpoint that we are calling from the Datadog API
        :param string dd_api_key: Datadog api key used to authenticate to API
        :param string dd_app_key: Datadog app key used to authenticate to API
        :param boolean jsonify: whether or not to return the json of the response
        :param int api_version_number: the version of the Datadog API we are calling
        :return: json of request made
        """

        headers = {
            "content-type": "application/json",
            "DD-API-KEY": dd_api_key,
            "DD-APPLICATION-KEY": dd_app_key,
        }

        api_version = f'v{str(api_version_number)}'

        try:
            # Make DD API GET request
            results = self.http.get(
                "https://{}/api/{}/{}".format(self.api_url, api_version, request_path),
                extra_headers=headers
            )

            # Raise an error if there was one
            results.raise_for_status()
            # If call is successful, return json result
            if jsonify:
                return results.json()
            else:
                return results
        except HTTPError as e:
            raise HTTPError("Non-200 response code returned from DD API: {}".format(e))

    def fetch_monitors(self, target_zip, api_key, app_key):
        """Get the monitors from datadog api and save json to zipped file

        :param zipfile.ZipFile target_zip: location/name of file to write json data to
        :param string api_key: contains dd api key for auth
        :param string app_key: contains dd app key for auth
        :return None: when no monitors are found in the datadog account (not an error, but no monitors)
        """
        # Get all monitors from DD using API lib
        monitor_data = self.call_api("monitor", api_key, app_key)
        index = {}

        # Throw if no monitors found
        if len(monitor_data) == 0:
            self.log.info("No monitors found in your Datadog Account. Please create monitors to back them up.")
            return

        # Go through each monitor json
        for monitor in monitor_data:
            id = monitor.get("id")
            name = monitor.get("name")

            # If monitor has null id or name continue to next monitor
            if not id or not name:
                continue

            monitor = cleanup_monitor_json(monitor)

            # Build the path for the monitor exported json file
            target_file = os.path.join("monitors", f"{id}.json")
            # Open the zip file provided to the call
            with target_zip.open(target_file, "w") as outfile:
                # Write the json contents of the monitor to the target file path
                outfile.write(json.dumps(monitor, indent=2).encode("utf-8"))

            # Create a dict key with monitor id storing the name of the monitor as the value
            index[id] = name

        index_path = os.path.join("monitors", "monitor_index.txt")
        with target_zip.open(index_path, "w") as outfile:
            for monitor_id, name in index.items():
                monitor_string = f"{monitor_id}: {name}\n"
                outfile.write(monitor_string.encode("utf-8"))

    def fetch_dashboards(self, target_zip, api_key, app_key):
        """Get the dashboards from datadog api and save json to zipped file

        :param zipfile.ZipFile target_zip: location/name of file to write json data to
        :param string api_key: contains dd api key for auth
        :param string app_key: contains dd app key for auth
        :return None: when no dashboards are found in the datadog account (not an error, but no dashboards)
        """
        dashboard_list = self.call_api("dashboard", api_key, app_key).get("dashboards")
        index = {}

        if not dashboard_list or len(dashboard_list) == 0:
            self.log.info("No dashboards found in your Datadog Account. Please create dashboards to back them up.")
            return

        for dashboard in dashboard_list:
            id = dashboard.get("id")
            target_file = os.path.join("dashboards", f"{id}.json")

            # get dashboard config from api
            dashboard_config = self.call_api("dashboard/{}".format(id), api_key, app_key)

            dashboard_config = cleanup_dashboard_json(dashboard_config)

            with target_zip.open(target_file, "w") as outfile:
                outfile.write(json.dumps(dashboard_config, indent=2).encode("utf-8"))

            index[id] = dashboard_config.get("title")

        index_path = os.path.join("dashboards", "dashboard_index.txt")
        with target_zip.open(index_path, "w") as outfile:
            for dashboard_id, name in index.items():
                dashboard_string = f"{dashboard_id}: {name}\n"
                outfile.write(dashboard_string.encode("utf-8"))

    def fetch_synthetics(self, target_zip, api_key, app_key):
        """Get the dashboards from datadog api and save json to zipped file

        :param zipfile.ZipFile target_zip: location/name of file to write json data to
        :param string api_key: contains dd api key for auth
        :param string app_key: contains dd app key for auth
        :return None: when no synthetics are found in the datadog account (not an error, but no synthetics)
        """
        synthetics_list = self.call_api("synthetics/tests", api_key, app_key).get("tests")
        index = {}

        if not synthetics_list or len(synthetics_list) == 0:
            self.log.info("No synthetics found in your Datadog Account. Please create synthetics to back them up.")
            return

        for synthetic in synthetics_list:
            test_type = synthetic.get("type")
            public_id = synthetic.get("public_id")

            if test_type == "api":
                # call api endpoint to get the test
                synthetic_config = self.call_api(
                    "synthetics/tests/api/{}".format(public_id),
                    api_key,
                    app_key,
                )
            elif test_type == "browser":
                # call browser endpoint to get the test
                synthetic_config = self.call_api(
                    "synthetics/tests/browser/{}".format(public_id),
                    api_key,
                    app_key,
                )
            else:
                raise Exception("Synthetic test type %s is not supported.", test_type)

            synthetic_config = cleanup_synthetic_json(synthetic_config)

            target_file = os.path.join("synthetics", f"{public_id}.json")
            with target_zip.open(target_file, "w") as outfile:
                outfile.write(json.dumps(synthetic_config, indent=2).encode("utf-8"))

            index[public_id] = synthetic_config.get("name")

        index_path = os.path.join("synthetics", "synthetic_index.txt")
        with target_zip.open(index_path, "w") as outfile:
            for synthetic_id, name in index.items():
                synthetic_string = f"{synthetic_id}: {name}\n"
                outfile.write(synthetic_string.encode("utf-8"))

    def fetch_notebooks(self, target_zip, api_key, app_key):
        """Get the dashboards from datadog api and save json to zipped file

        :param zipfile.ZipFile target_zip: location/name of file to write json data to
        :param string api_key: contains dd api key for auth
        :param string app_key: contains dd app key for auth
        :return None: when no notebooks are found in the datadog account (not an error, but no notebooks)
        """
        notebooks_list = self.call_api("notebooks", api_key, app_key).get("data")
        index = {}

        if not notebooks_list or len(notebooks_list) == 0:
            self.log.info(
                "No notebooks were found in your Datadog Account. Please create notebooks to back them up."
            )
            return

        for notebook in notebooks_list:
            notebook_id = notebook.get("id")

            target_file = os.path.join("notebooks", f"{notebook_id}.json")
            with target_zip.open(target_file, "w") as outfile:
                outfile.write(json.dumps(notebook, indent=2).encode("utf-8"))

            notebook_attr = notebook.get("attributes")

            if notebook_attr:
                notebook_name = notebook_attr.get("name")
                index[notebook_id] = notebook_name

        index_path = os.path.join("notebooks", "notebook_index.txt")
        with target_zip.open(index_path, "w") as outfile:
            for notebook_id, name in index.items():
                notebook_string = f"{notebook_id}: {name}\n"
                outfile.write(notebook_string.encode("utf-8"))

    def create_backup(self, dd_api_key, dd_app_key):
        if not os.path.exists(self.backup_path):
            try:
              os.makedirs(self.backup_path)
            except Exception as e:
              raise Exception("Failed to create directory to store file: {}".format(e))

        backup_file_name = f"datadog_backup_{datetime.now().strftime(self.timestamp_format)}.zip"
        backup_file_path = f"{self.backup_path}/{backup_file_name}"

        with zipfile.ZipFile(
            backup_file_path, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as target_zip:
            self.fetch_dashboards(target_zip, dd_api_key, dd_app_key)
            self.fetch_monitors(target_zip, dd_api_key, dd_app_key)
            self.fetch_synthetics(target_zip, dd_api_key, dd_app_key)
            self.fetch_notebooks(target_zip, dd_api_key, dd_app_key)

        return backup_file_path


