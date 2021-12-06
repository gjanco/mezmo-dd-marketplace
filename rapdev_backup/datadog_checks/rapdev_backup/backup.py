try:
    from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
except ImportError:
    from checks import AgentCheck
import json
import datetime
from requests.exceptions import HTTPError
from datetime import datetime
import zipfile
from .helpers import *
from azure.storage.blob import ContentSettings
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

SUPPORTED_STORAGE_PLATFORMS = {"LOCAL", "AWS", "AZURE"}


class BackupCheck(AgentCheck):

    __NAMESPACE__ = "rapdev.backup"

    def __init__(self, *args, **kwargs):
        super(BackupCheck, self).__init__(*args, **kwargs)
        self.dd_api_key = get_config("api_key")
        self.dd_app_key = self.init_config.get("app_key")
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.__NAMESPACE__)

        self.timestamp_format = self.instance.get("timestamp_format", "%Y-%m-%dT%H%M%S")
        self.backup_storage_platform = self.instance.get("backup_storage_platform")
        self.backup_path = self.instance.get("backup_path")
        self.delete_local_backups = self.instance.get("delete_local_backups")

        # AWS authentication
        self.aws_access_key = self.instance.get("aws_access_key", None)
        self.aws_secret_key = self.instance.get("aws_secret_key", None)
        self.assume_role_arn = self.instance.get("assume_role_arn", None)
        self.assume_session_name = self.instance.get("assume_session_name", "DatadogBackupSession")
        self.assume_role_external_id = self.instance.get("assume_role_external_id")
        self.aws_s3_bucket_name = self.instance.get("aws_s3_bucket_name", None)
        self.aws_s3_sub_path = self.instance.get("aws_s3_sub_path", "")

        # Azure authentication
        self.azure_connection_string = self.instance.get("azure_connection_string", None)
        self.azure_container_name = self.instance.get("azure_container_name", None)

        self.check_initializations.append(self.validate_config)

    def check(self, instance):
        self.test_api_connection()

        # Create a backup to a local file
        backup_file_path = self.create_backup(self.dd_api_key, self.dd_app_key)
        backup_file_properties = backup_file_path.split("/")
        backup_file_name = backup_file_properties[-1]

        self.gauge(self.billing_metric, 1, tags=self.tags, raw=True)

        if self.backup_storage_platform == "LOCAL":
            return

        elif self.backup_storage_platform == "AWS":
            # Create an s3 client using credentials
            s3_client = setup_aws_connection(
                self.aws_access_key,
                self.aws_secret_key,
                self.assume_role_arn,
                self.assume_session_name,
                self.assume_role_external_id
            )

            if self.aws_s3_sub_path:
                backup_file_name = self.aws_s3_sub_path + backup_file_name

            if upload_backup_to_s3(s3_client, self.aws_s3_bucket_name, backup_file_path, backup_file_name):
                self.log.info("Successfully uploaded backup to S3 Bucket {}".format(self.aws_s3_bucket_name))
            else:
                self.log.error("Backup to S3 failed. Will clean up the created backups or exit.")

        elif self.backup_storage_platform == "AZURE":
            # Generate a new blob client
            blob_client = setup_azure_connection(
                self.azure_connection_string, self.azure_container_name, backup_file_name
            )
            # Set the blob type to zip so backup can be successfully unzipped
            with open(backup_file_path, "rb") as data:
                blob_client.upload_blob(data, content_settings=ContentSettings(content_type="application/zip"))
                self.log.info("Successfully uploaded Backup to Azure Blob.")

        if self.delete_local_backups == "True":
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
        if not self.dd_app_key:
            raise ConfigurationError("A valid Datadog APP key is required.")

        if self.backup_storage_platform not in SUPPORTED_STORAGE_PLATFORMS:
            raise ConfigurationError("Provided storage platform is not supported: {}"
                                     .format(self.backup_storage_platform))
        else:
            if self.backup_storage_platform == "AWS":
                # If aws, validate we have required creds
                if not self.aws_access_key or not self.aws_secret_key or not self.aws_s3_bucket_name:
                    raise ConfigurationError(
                        "AWS_ACCESS_KEY, AWS_SECRET_KEY, and AWS_S3_BUCKET_URL are all required "
                        + "for storing backups in AWS."
                    )
            elif self.backup_storage_platform == "AZURE":
                # If azure, validate we have required creds
                if not self.azure_connection_string or not self.azure_container_name:
                    raise ConfigurationError(
                        "AZURE_CONNECTION_STRING and AZURE_CONTAINER_NAME are required "
                        + "for Azure authentication."
                    )

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

        api_version = f'v{str(api_version_number)}/'

        try:
            # Make DD API GET request
            results = self.http.get(
                "https://api.datadoghq.com/api/" + api_version + request_path,
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

