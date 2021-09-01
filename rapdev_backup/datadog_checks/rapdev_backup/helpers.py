import boto3
from azure.storage.blob import BlobServiceClient
import copy

DASHBOARD_EXTRA_CONFIGS = [
    "author_name",
    "author_handle",
    "id",
    "url",
    "created_at",
    "modified_at",
]

MONITOR_EXTRA_CONFIGS = [
    "deleted",
    "matching_downtimes",
    "id",
    "multi",
    "created",
    "created_at",
    "creator",
    "org_id",
    "modified",
    "overall_state_modified",
    "overall_state",
]

SYNTHETIC_EXTRA_CONFIGS = [
    "public_id",
    "monitor_id",
]


##################
# Azure Functions
##################


def setup_azure_connection(connection_string, azure_container_name, backup_file_name):
    """Setup an Azure authenticated client to communicate to blob storage with

    :param string connection_string: azure connection string used to authenticate
    :param string azure_container_name: azure container used to store the blob storage
    :param string backup_file_name: the name of the blob to create
    :return: new blob client to hold backup file
    """
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(azure_container_name)

    return container_client.get_blob_client(backup_file_name)


def upload_blob(blob_client, file_name):
    """Upload a file to an Azure BlobStorage

    :param blob_client: Client previously authenticated to use Azure Blobs
    :param string file_name:
    :return: True if file was uploaded
    :raises Exception: when file fails to upload to azure blob
    """
    # Upload the file
    try:
        blob_client.upload_blob(file_name)
    except Exception as e:
        raise Exception("Error when uploading file to Azure Blob:", e)

    return True


##################
# AWS Functions
##################

def setup_aws_connection(aws_access_key, aws_secret_key, assume_role_arn=None, assume_session_name=None, external_id=None):
    """Setup an AWS authenticated client to communicate with S3

    :param string aws_access_key: the access key used to authenticate to aws
    :param string aws_secret_key: the secret key used to authenticate to aws
    :param string assume_role_arn: the arn of the role to assume (if assuming role)
    :param string assume_session_name: the name of the session for assuming a role (if assuming role)
    :param string external_id: the external_id to assume role for authentication (if required and assuming role)
    :return: AWS boto3 s3 client
    """
    if assume_role_arn:
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
        )

        if external_id:
            assumed_role_object = sts_client.assume_role(
                RoleArn=assume_role_arn,
                RoleSessionName=assume_session_name,
                ExternalId=external_id,
            )
        else:
            assumed_role_object = sts_client.assume_role(
                RoleArn=assume_role_arn,
                RoleSessionName=assume_session_name,
            )

        credentials = assumed_role_object["Credentials"]

        return boto3.client(
            's3',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
        )
    else:
        return boto3.client(
            "s3",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
        )


def upload_backup_to_s3(s3_client, bucket_name, file_name, object_name):
    """Upload a file to an S3 bucket

    :param boto3.client s3_client: Client previously authenticated to use AWS S3
    :param string bucket_name: Name of the bucket to upload to
    :param string file_name: name of the file we are uploading
    :param string object_name: name of the object to store the zipped file under
    :return: True if file was uploaded
    :raises Exception: when file fails to upload to s3 bucket
    """
    try:
        s3_client.upload_file(file_name, bucket_name, object_name)
    except Exception as e:
        raise Exception("Error when uploading file to AWS S3:", e)

    return True

##################
# Parsing Functions
##################


def cleanup_dashboard_json(dashboard_config):
    """Helper function that removes non-required/invalid json values from dashboard config

    :param dashboard_config: Json of a datadog dashboard
    :return: Updated Json of a datadog dashboard
    """

    dashboard_copy = copy.deepcopy(dashboard_config)

    for json_key in DASHBOARD_EXTRA_CONFIGS:
        dashboard_copy.pop(json_key, None)

    return dashboard_copy


def cleanup_monitor_json(monitor_config):
    """Helper function that removes non-required/invalid json values from monitor config

    :param monitor_config: Json of a monitor config
    :return: Updated Json of a monitor config
    """

    monitor_copy = copy.deepcopy(monitor_config)

    for json_key in MONITOR_EXTRA_CONFIGS:
        monitor_copy.pop(json_key, None)

    return monitor_copy


def cleanup_synthetic_json(synthetic_config):
    """Helper function that removes non-required/invalid json values from synthetic config
    :param synthetic_config: Json of a synthetic config
    :return: Updated Json of a synthetic config
    """

    synthetic_copy = copy.deepcopy(synthetic_config)

    for json_key in SYNTHETIC_EXTRA_CONFIGS:
        synthetic_copy.pop(json_key, None)

    return synthetic_copy
