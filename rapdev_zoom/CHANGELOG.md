# CHANGELOG - rapdev_zoom

## 6.0.0 / 2023-05-19
* [Added] Server-to-Server Zoom API OAuth support
* [Added] Zoom Phone devices and calls ingestion with dashboard (with additional params)
* [Removed] Master API Params (functionality still supported via instances)

## 5.3.0 / 2022-09-08
* [Added] Fix for location hierarchy 
* [Added] Increased support for user QOS metrics

## 5.2.2 / 2022-06-02
* [Added] Room and room component location hierarchy template variables in Rooms dashboard
* [Added] Fix for when location hierarchy is not defined

## 5.2.1 / 2022-03-21
* [Added] Room and room component location hierarchy metric tags


## 5.2.0 / 2022-03-21
* [Added] Better error handling
* [Fixed] Incorrect widgets on 2 dashboards
* [Added] Better status handling for named room components
* [Fixed] Adding the zoom account name on service check failures

## 5.1.0 / 2021-10-27
* [Added] Functionality to support Zoom sub-accounts
* [Changed] Dashboards to include support for tags for sub-accounts

## 5.0.2 / 2021-09-09
* [Fixed] Billing metric tags

## 5.0.1 / 2021-09-07
* [Fixed] Fix for return type when daily api limit is hit

## 5.0.0 / 2021-08-20
* [Added] Metric for counting API calls
* [Added] Room only mode
* [Removed] IM metrics function
* [Removed] Plan usage function
* [Removed] Account function

## 4.2.0 / 2021-05-25
* [Added] API Error handling

## 4.1.1 / 2021-05-11
* [Added] TypeError handling
* [Removed] JWT from requirements
* [Added] PyJWT for requirements

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

