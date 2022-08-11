# CHANGELOG - rapdev_servicenow

## 1.2.2 / 2022-08-06

-  [Added] configurable option `statsdo_auth` for authenticated stats.do
-  [Added] configurable endpoint option `stats_auth_url` for authenticated stats.do
-  [Added] logic and validation to support authenticated stats.do

## 1.2.1 / 2022-07-19

- [Fixed] missing timezone definition on datetime calculation resulting in TypeError
 
## 1.2.0 / 2022-06-03

- [Added] configurable datetime string format to yaml
- [Added] support for datetime string configuration to match ServiceNow
- [Added] metric: `rapdev.servicenow.incident_total_year`
- [Removed] extraneous debug logging
- [Removed] support for python 2

## 1.1.0 / 2022-03-31

- [Added] auth parameter to service-now endpoints
- [Added] configurable opt_fields to yaml which adds additional tagging to incident metric

## 1.0.0 / 2021-05-13

- [Added] initial Marketplace release.


