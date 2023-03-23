# CHANGELOG - rapdev_validator

## 2.2.0 / 2023-03-20
### Feature Updates
* [Added] Updated `required_tags` to allow values to be validated against regex patterns

## 2.1.2 / 2022-05-23
### Feature Updates
* [Added] Added the `dd_org_name` configuration flag in lieu of programatically grabbing the organization information, as this requires billing scoped permissions to Datadog's API

## 2.1.1 / 2022-02-02
### Bugfix:
* [BugFix] Fix bug causing infinite loop in core host loop 

## 2.1.0 / 2021-11-02
#### Feature Updates
* [Added] Added a configuration flag for `dd_site` to allow EU, US3, US5, and GOV Datadog customers to utilize the integration due to having different API endpoints

## 2.0.0 / 2021-09-30
#### Feature Updates
* [Added] Added the ability to validate tags on Synthetics
* [Added] Added a synthetic dashboard for validated Synthetics

## 1.1.0 / 2021-08-12
### Feature Update & Bugfixes

#### Bugfixes:
* [BugFix] Fixed a bug where the `validate_agent` was attempting to grab metadata from the hosts without an Agent
* [BugFix] Fixed a bug that was causing the main `datadog.yaml` file to not be read correctly on Windows
* [BugFix] Fixed dashboard widgets that were not displaying properly when sorting by a variable

#### Feature Changes:
* [Added] Added the ability to specify an API and app key on a per instance basis, which overrides any API/app key specified on the integration level (as well as any API key from the main `datadog.yaml`, that is used if both per instance and integration API keys are not set). This change is backwards compatible with previous versions
* [Added] Added the ability to retrieve the org name associated with the API/app keys being used, and submit that as a tag on all metrics and Agent checks
* [Added] Added sorting by org to the dashboard
* [Added] Added org information to included monitors

## 1.0.0 / 2021-06-11
* Initial Release