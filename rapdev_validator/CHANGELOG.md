# CHANGELOG - rapdev_validator

## 2.1.1 / 2022-02-02

### Bugfix:
  * Fix bug causing infinite loop in core host loop 

## 2.1.0 / 2021-11-02

#### Feature Updates
  * Added a configuration flag for `dd_site` to allow EU, US3, US5, and GOV Datadog customers to utilize the integration due to having different API endpoints

## 2.0.0 / 2021-09-30

#### Feature Updates
  * added the ability to validate tags on Synthetics
  * added a synthetic dashboard for validated Synthetics

## 1.1.0 / 2021-08-12
### Feature Update & Bugfixes

#### Bugfixes:
  * fixed a bug where the `validate_agent` was attempting to grab metadata from the hosts without an Agent
  * fixed a bug that was causing the main `datadog.yaml` file to not be read correctly on Windows
  * fixed dashboard widgets that were not displaying properly when sorting by a variable

#### Feature Changes:
  * added the ability to specify an API and app key on a per instance basis, which overrides any API/app key specified on the integration level (as well as any API key from the main `datadog.yaml`, that is used if both per instance and integration API keys are not set). This change is backwards compatible with previous versions.
  * added the ability to retrieve the org name associated with the API/app keys being used, and submit that as a tag on all metrics and Agent checks
  * added sorting by org to the dashboard
  * added org information to included monitors

## 1.0.0 / 2021-06-11
* Initial Release
