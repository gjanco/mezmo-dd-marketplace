# Agent Check: Rapdev Backup

## Overview

The purpose of this Agent check is to create a zipped backup for a Datadog account's dashboards, synthetic tests, monitors,
and notebooks. That backup can then be stored on a local machine or in one of the supported 
cloud service providers (e.g. AWS or Azure).

## Setup

### Prerequisites

This Agent check is only intended to run on Python3.X version on Agent v7. 
Functionality for Python2.X is not guaranteed. For running python3 on Agent v6, please refer to 
[these docs](https://docs.datadoghq.com/agent/guide/agent-v6-python-3/?tab=hostagent).

Install or upgrade the following libraries using the Agent's embedded python, otherwise the check will not be able to run:
 
 - boto3 (aws)

   ```
   *Linux*
   sudo -Hu dd-agent /opt/datadog-agent/embedded/bin/pip install boto3 --upgrade
   
   *Windows*
   %PROGRAMFILES%\Datadog\"Datadog Agent"\embedded<PYTHON_MAJOR_VERSION>\python -m pip install boto3 --upgrade
   ```
 
 - azure

   ```
   *Linux*
   sudo -Hu dd-agent /opt/datadog-agent/embedded/bin/pip install azure-storage-blob --upgrade
   
   *Windows*
   %PROGRAMFILES%\Datadog\"Datadog Agent"\embedded<PYTHON_MAJOR_VERSION>\python -m pip install azure-storage-blob --upgrade
   ```

### Installation
Run the following command to enable the Backup Integration on your Datadog Agent:

```
*Linux*
sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_backup==1.0.0

*Powershell*
& "$env:ProgramFiles\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_backup==1.0.0

*Command Prompt*
"%PROGRAMFILES%\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_backup==1.0.0
```

### Datadog Configuration

Begin by generating Datadog [APP key](https://docs.datadoghq.com/account_management/api-app-keys/). 
and pass that value into the `init_config` section of your `conf.d/rapdev_backup.d/conf.yaml` under the field `app_key` as below:

```
init_config:
  app_key: "<MY_APP_KEY>"

instances:
  - backup_storage_platform: AWS
    aws_access_key: <MY_KEY>
    aws_secret_key: <MY_SECRET_KEY>
    aws_s3_bucket_name: my_bucket/my_backups_folder
```

### Backup Configurations

Figure out where you want to store your backups locally and provide the absolute path to the `backup_path` variable. 

Next, decide which platform to save backups to using the `backup_storage_platform` variable in the `rapdev_backup.d/conf.yaml`. 
Your options are below:
 - `AWS` (S3)
 - `AZURE` (Blob Storage)
 - `LOCAL` (stores locally in folder provided for `backup_path` variable). 

#### AWS Environment Configuration

1) In order to authenticate to AWS, you have two options:
  - Access Key on User (no assume role): Generate an AWS Access ID and Secret with permission to read and upload to S3. 
    Pass in the access key id to `aws_access_key` and the secret access key to `aws_secret_key` via the `conf.yaml`. 
    Please refer to the permissions at the bottom of the next section to understand what s3 permissions are needed.    

  - Access Key on User with `sts:AssumeRole`: Begin by creating an IAM role in the account that you want to store your backups to with read
    and write permissions to the s3 bucket you'd like to use. Provide the ARN of that role to the `assume_role_arn`
    configuration in the `conf.yaml`. Additionally, set up a
    [trust policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_permissions-to-switch.html) so
    this role can be assumed by the role in the next step. If desired, you can generate an external id for an extra 
    layer of security. Provide the id into the `assume_role_external_id` via the `conf.yaml`. See an example below
    an appropriate trust policy:
    
    ```
    {
     "Version": "2012-10-17",
     "Statement": {
       "Effect": "Allow",
       "Action": "sts:AssumeRole",
       "Resource": "arn:aws:iam::ACCOUNT-ID-WITHOUT-HYPHENS:role/MyRole123",
       "Condition": {"StringEquals": {"sts:ExternalId": "12345"}} # only add this if you are using an external id
     }
    }
    ```

    Switch to the account and/or role that is assuming the new role and generate an
    AWS Access ID and Secret for this role. Provide those values via the `aws_access_key` and `aws_secret_key` in 
    the `conf.yaml`. 
    
    If you'd like to customize the name of the assumed role session, do so via the `assume_session_name` variable
    otherwise it will default to "DatadogBackupSession".
    
    The role that is accessing the s3 buckets in both options should have at bare minimum the following permissions: 
    
    ```
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Action": [
            "s3:ListBucket"
          ],
          "Effect": "Allow",
          "Resource": "arn:aws:s3:::<bucket-name>"
        },
        {
          "Action": [
            "s3:DeleteObject",
            "s3:GetObject",
            "s3:PutObject",
            "s3:PutObjectAcl"
          ],
          "Effect": "Allow",
          "Resource": "arn:aws:s3:::<bucket-name>/*"
        }
      ]
    }
    ```

2) Create a new S3 bucket to store the backups to or pick an existing one. 
   Paste the name of the bucket in `aws_s3_bucket_name`.

#### Azure Environment Configuration

1) Create a storage account. Under `Access keys` for the storage account, 
   show your connection string and pass that value into the `azure_connection_string` variable.

2) Within the new storage account, create a new Container (Data Storage > Container). 
   Provide the name of the container for the variable `azure_container_name`.

### Extra configs

If you'd like to delete the backups that were created locally (even when storing to cloud), 
leave the default `delete_local_backups` set to `true`, otherwise set it to `false`. If `backup_storage_platform` is set to `LOCAL`, this 
variable will be ignored. Please be aware that this can eventually use up all available space on your machine(s) if you don't perform a periodic manual clean up when required (resource usage is based on your run interval).


Once all your configurations are setup, [restart the agent][1].

### Validation

[Run the Agent's status subcommand][2] and look for `rapdev_backup` under the Checks section.

Alternatively, you can get detailed information about the integration using the following command.
    
```
*Linux*
sudo -u dd-agent datadog-agent check rapdev_backup

*Powershell*
& "$env:ProgramFiles\Datadog\Datadog Agent\bin\agent.exe" check rapdev_backup

*Command Prompt*
"%PROGRAMFILES%\Datadog\Datadog Agent\bin\agent.exe" check rapdev_backup
```

## Data Collected

### Metrics

This integration does not include any metrics.

### Service Checks

This integration has the service check `rapdev.backup.can_connect` which returns `OK` if the Agent can communicate with the Datadog API otherwise it reports `CRITICAL`. 

### Events

This integration does not include any events.

## Support
For support or feature requests, contact RapDev.io through the following channels:

- Support: integrations@rapdev.io
- Sales: sales@rapdev.io
- Chat: RapDev.io/products
- Phone: 855-857-0222

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note](mailto:integrations@rapdev.io), and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here][3] to purchase this application.

[1]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[3]: https://app.datadoghq.com/marketplace/app/rapdev-backup/pricing
