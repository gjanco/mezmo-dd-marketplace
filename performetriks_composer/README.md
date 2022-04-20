# Performetriks Composer

## Overview
Performetriks Composer is a tool that allows you to manage your entire Datadog environment configuration. Composer provides a quick, easy way to document and store your Datadog configuration, as well as find and resolve configuration errors in your Datadog environment.

### Composer Use Cases

**Backup Datadog configuration**

No matter how many Datadog environments you have, Composer allows you to create backups of all your configuration items. You can start a backup ad-hoc or entirely automate a backup from a CI/CD pipeline.

**Check in to software configuration management systems**

Composer allows you to manage your monitoring configurations as code and check that code into a repository, ensuring that there is a record of all monitoring settings.

**Find changes**

If several admins manage your Datadog environment, they need to ensure that everyone knows and agrees when any settings are adjusted. Composer simplifies this process by ensuring there is always a backup available, allowing admins to detect the most recent changes.

**Restore your configuration**

Errors in monitoring configuration can be difficult to spot, but Composer simplifies this process dramatically. Select your most recent Datadog configuration from the created backup and undo your mistakes within seconds.

**Upload your configuration**

It's all about monitoring as code these days. Composer allows your team to store monitoring settings in your code repositories, track changes, and upload these settings to existing or new Datadog environments.


For more information, please see the [Composer Datadog Product Guide][1]


## Setup

1. To download Composer, visit the [Composer Datadog Product Guide][1] and click the Download Composer Now button.

2. Unzip the downloaded file and place the validate license into the `bin` folder.

3. Open a new terminal window and enter the following command:
    `cd <path-to-Datadog_Composer>/bin`

4. Run `java -jar DatadogComposer.jar` to start Composer.

5. Open a web browser and enter `localhost:9191` in your address bar. The Composer start page appears.

6. Navigate to the Datadog tab and create an environment JSON file to store your Datadog API and Application keys. For more information, see [API and Application Keys](https://docs.datadoghq.com/account_management/api-app-keys/).

7. To set up the repository to store your Datadog configuration files, click the Git menu item and create a Gitlab JSON file.

8. To store Datadog configuration data, navigate to the **Backup** tab.

9. To sync Datadog configuration data with Git, navigate to the **Checkin** tab and select your repository credentials from the dropdown menu.

10. To upload Datadog configurations to your Datadog environment, navigate to the **Upload** tab.

11. To begin restoring a Datadog configuration in your Datadog environment, navigate to the **Restore** tab.

## Support
For support or feature requests, please contact Performetriks through the following channel:
Email: [composer@performetriks.com](mailto:composer@performetriks.com)

[1]:https://www.performetriks.com/composer-datadog-product-guide
