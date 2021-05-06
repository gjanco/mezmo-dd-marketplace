# CHANGELOG - rapdev_zoom

## 4.1.0 / 2021-05-06
* [Removed] SLO from the Room Status dashboard.
* [Added] Table key to rooms dashboard.
* [Added] Unhealthy rooms to the top of table list.
* [Added] Table key to rooms dashboard
* [Added] PyJWT version handling
* [Added] New screenshot for Rooms dashboard.

## 4.0.0 / 2021-03-19
* [Removed] The get_room_status function. 
* [Added] Improved API requests to lower chances of hitting API limits. 
* [Added] Room status functionality to get_room_metrics call.
* [Added] API Limit handling to sleep or exit accordingly.
* [Added] API Limit service check.

## 3.0.0 / 2021-02-17

* [Removed] The registered users count metric.
* [Added] The active users counts tagged by account type (e.g. basic, licensed, etc...).
* [Removed] The user connection type tag.

## 2.0.1 / 2021-02-05

* [Modified] Audio/Video Widget Titles to align with Sending/Receiving metrics, rather than input/output
* [Removed] Underutilized Meeting CPU metrics

## 2.0.0 / 2021-02-02

* [Added] added User Details dashboard to provide the ability to further troubleshoot issues pertaining to a specific user.
* [Added] added CPU Metric ingestion.
* [Added] added users_to_track flag that allows you to specify a list of users for which the agent will only send metrics for.

