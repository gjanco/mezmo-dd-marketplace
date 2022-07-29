# Agent Check: RapDev Backup

## Overview

The purpose of this Agent check is to create a zipped backup for a Datadog account's dashboards, Synthetic tests, monitors,
and notebooks. That backup can then be stored on a local machine or in one of the other supported platforms
(such as AWS, Azure, and GitHub).

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

## Setup

### Prerequisites

This Agent check is only intended to run on Python3.X version on Agent v7. 
Functionality for Python2.X is not guaranteed. For running python3 on Agent v6, please refer to 
[these docs][6].

Choose a library to install or upgrade through the Agent's embedded Python. In order for the check to run in non-`local` mode, at least one of the following libraries is required.
 
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
 
 - github
   
   ```
   *Linux*
   sudo -Hu dd-agent /opt/datadog-agent/embedded/bin/pip install pygithub --upgrade

   *Windows*
   %PROGRAMFILES%\Datadog\"Datadog Agent"\embedded<PYTHON_MAJOR_VERSION>\python -m pip install pygithub --upgrade
   ```

### Installation
Run the following command to enable the Backup Integration on your Datadog Agent:

```
*Linux*
sudo -u dd-agent datadog-agent integration install --third-party datadog-rapdev_backup==2.3.0

*Powershell*
& "$env:ProgramFiles\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_backup==2.3.0

*Command Prompt*
"%PROGRAMFILES%\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-rapdev_backup==2.3.0
```

### Datadog Configuration

Begin by generating Datadog [API & Application keys][4]. 
and pass that value into the `instances` section(s) of your `conf.d/rapdev_backup.d/conf.yaml` under the fields 
`api_key` and `app_key` as shown below:

```
init_config:

instances:
  - dd_api_key: <my_api_key1>
    dd_app_key: <my_app_key1>
    backup_storage_platform: local
    backup_path: /etc/datadog-backups/
```

### Backup Configurations

Figure out where you want to store your backups locally and provide the absolute path to the `backup_path` variable. 

Next, decide which platform to save backups to using the `backup_storage_platform` variable in the `rapdev_backup.d/conf.yaml`. 
Your options are below:
 - `aws` (S3)
 - `azure` (Blob Storage)
 - `github` (any repos)
 - `local` (stores locally in folder provided for `backup_path` variable). 

#### AWS Environment Configuration

1) In order to authenticate to AWS, you have three options:
  - [Instance Profile Assigned To an EC2 (Recommended)][7]: In the `conf.yaml`, set `use_instance_profile` to `True`.
    Next, generate a new IAM Role and attach it to your EC2 Instance. Make sure this role
    has access to write to the S3 bucket that you want to store backups to. 
    See the permissions at the bottom of the next section to understand what S3 permissions are required.

    <b>Note:</b> Setting this to `True` means that it uses the [boto3 credential chain][10], which can support more than instance profiles, such as AWS 
environment variables and shared credential files.

  - [Access Key on User (no assume role)][8]: Generate an AWS Access ID and Secret with permission to read and upload to S3. 
    Pass in the access key id to `aws_access_key` and the secret access key to `aws_secret_key` via the `conf.yaml`. 
    Please refer to the permissions at the bottom of the next section to understand what s3 permissions are needed.    

  - [Access Key on User with `sts:AssumeRole`][9]: Begin by creating an IAM role in the account that you want to store your backups to with read
    and write permissions to the s3 bucket you'd like to use. Provide the ARN of that role to the `assume_role_arn`
    configuration in the `conf.yaml`. Additionally, set up a
    [trust policy][5] so
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
   Paste the name of the bucket in `aws_s3_bucket_name` (no trailing `/` is required). If you'd like to include a sub path
   for your S3 bucket (e.g. `mybucket/sub_path/`) please include the subpath in the `aws_s3_sub_path`
   parameter with a trailing `/`. For example, if you add `mytesting_folder` inside the `testing123` bucket,
   your configuration may look like this:

   ```
   init_configs:
   
   instances:
     - dd_api_key: <my_dd_api_key>
       dd_app_key: <my_dd_app_key> 
       backup_storage_platform: aws
       backup_path: /etc/datadog-backups/  
       aws_access_key: <my_access_key>
       aws_secret_key: <my_secret_key>
       aws_s3_bucket_name: testing123
       aws_s3_sub_path: mytesting_folder/
   ```

#### Azure Environment Configuration

1) Create a storage account. Under `Access keys` for the storage account, 
   show your connection string and pass that value into the `azure_connection_string` variable.

2) Within the new storage account, create a new Container (Data Storage > Container). 
   Provide the name of the container for the variable `azure_container_name`. An example config looks like this:
   
   ```
   init_configs:
   
   instances:
     - dd_api_key: <my_dd_api_key>
       dd_app_key: <my_dd_app_key>
       backup_storage_platform: azure
       backup_path: /etc/datadog-backups/
       azure_connection_string: <my_connection_string>
       azure_container_name: <my_container_name>
   ```


#### Github Backup Storage Configuration

1) Begin by creating a GitHub repo to hold your backups (or use an existing one).

2) Create a [Github Personal Access Token][3] with full `repo` access and pass it into the config via the `github_access_token` param.
   
3) Fill in the rest of the fields. Below is an example of a valid GitHub configuration:
   
   ```
   init_configs:
   
   instances:
     - dd_api_key: <my_api_key1>
       dd_app_key: <my_app_key1>
       backup_storage_platform: github
       backup_path: /etc/datadog-backups/
       github_access_token: <my_gh_token>
       github_repo: <github_account>/<repo_name> # the "/" is required
       github_master_ref: "heads/main"
   ```

   *note*: `github_store_path` allows you to specify a sub-path within the repo.

### Extra configs

If you'd like to delete the backups that were created locally (even when storing to cloud), 
leave the default `delete_local_backups` set to `true`, otherwise set it to `false`. If `backup_storage_platform` is set to `LOCAL`, this 
variable will be ignored. Please be aware that this can eventually use up all available space on your machine(s) if you don't perform a periodic manual clean up when required (resource usage is based on your run interval).


Once all of your configurations are set up correctly, [restart the Agent][1].

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

- Support: datadog-engineering@rapdev.io
- Sales: sales@rapdev.io
- Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
- Phone: 855-857-0222

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop RapDev a [note](mailto:datadog-engineering@rapdev.io), and we'll build it!!*

[1]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[3]: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
[4]: https://docs.datadoghq.com/account_management/api-app-keys/
[5]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_permissions-to-switch.html
[6]: https://docs.datadoghq.com/agent/guide/agent-v6-python-3/?tab=hostagent
[7]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2_instance-profiles.html
[8]: https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys
[9]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use.html
[10]: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
