# import libraries
import datetime
import json
import os
import re

from datadog_checks.base import AgentCheck

# import local code
from .checkBoomiDaemon import checkBoomiDaemon
from .checkBoomiNodeViewFile import checkBoomiNodeViewFile
from .getContainerId import getContainerId
from .globals import __NAMESPACE__, LAST_END_DATETIME_FILENAME
from .queryAtomStatusViaApi import queryAtomStatusViaApi
from .queryAuditLogsApi import queryBoomiAuditLogsApi
from .queryEventsApi import queryBoomiEventsApi
from .verifyConfig import verifyConfig

###########################################################################
# We need a dict to translate Boomi execution status to Datadog log status.
statusDict = {
    "ABORTED": "Error",
    "COMPLETE": "Info",
    "COMPLETE_WARN": "Warn",
    "DISCARDED": "Warn",
    "ERROR": "Error",
    "INPROCESS": "Error",
    "STARTED": "Error",
    "UNKNOWN": "Unknown",
}


class AtomWatchCheck(AgentCheck):
    def __init__(self, name, init_config, instances):
        super(AtomWatchCheck, self).__init__(name, init_config, instances)

    def check(self, instance):

        ##############################
        # Verify the configuration
        (
            dd_api_key,
            boomi_api_url,
            boomi_api_userid,
            boomi_api_token,
            boomi_account_id,
            boomi_atom_or_molecule_install_dir,
            seconds_of_lag,
            min_boomi_api_interval,
            cluster_node_id,
            boomi_role,
        ) = verifyConfig(self, instance)
        baomid = boomi_atom_or_molecule_install_dir
        # Report that config is now validated
        self.log.debug('config_validated')
        self.service_check(
            __NAMESPACE__ + 'config_validated',
            self.OK,
            tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
        )

        #############################
        # Get installation directory
        # Try two ways to find it--this shows if we are an API Gateway or
        # a Molecule/Atom.
        # Check if API Gateway install dir is defined.  If so, this must be
        # an API Gateway node.
        install_dir = instance.get('boomi_api_gateway_install_dir', None)
        if install_dir is None:
            # This must be a Molecule node or Atom.  Get that install dir.
            st = 'boomi_atom_or_molecule_install_dir'
            install_dir = instance.get(st, None)

        #######################################
        # Get container ID for billing purposes
        container_id = getContainerId(self, install_dir)

        #######################
        # Report billing metric
        st1 = "datadog.marketplace.kitepipe.atomwatch"
        st2 = "billing_key:" + container_id + "_" + cluster_node_id
        self.count(st1, 1, [st2])

        ############################################
        # Check if Boomi daemon / service is running
        # Do we have an installation directory?
        if install_dir is not None:
            # We have an installation directory.
            # Use it to check Boomi daemon / service.
            checkBoomiDaemon(self, instance, install_dir)

        #################################
        # Should we make Boomi API calls?
        if boomi_api_url:

            # We should make Boomi API calls.

            ########################
            # Set up datetime range.
            fn = self.setupDatetimeRange
            ar1 = seconds_of_lag
            res, startDateTime, endDateTime = fn(baomid, ar1, cluster_node_id)
            # Bail out if failure
            if res is not None:
                st = "cluster_node_id:" + cluster_node_id
                self.service_check(
                    __NAMESPACE__ + "completed",
                    self.CRITICAL,
                    tags=["service_check:true", st],
                )
                raise Exception(res)
            # Report that datetime range was set up
            self.log.debug('datetime_range_set_up')
            st = "cluster_node_id:" + cluster_node_id
            self.service_check(
                __NAMESPACE__ + 'datetime_range_set_up',
                self.OK,
                tags=["service_check:true", st],
            )

            #######################
            # Should we exit early?
            if instance.get('early_exit_000'):
                # We should exit early.
                return

            ##########################################################
            # Is the datetime range wider than min_boomi_api_interval?
            okToMakeBoomiAPICalls = None
            sslac = (endDateTime - startDateTime).total_seconds()
            seconds_since_last_api_call = sslac
            msg = str(seconds_since_last_api_call)
            msg += " seconds since last Boomi API call."
            self.log.debug(msg)
            if seconds_since_last_api_call > min_boomi_api_interval:
                # Datetime range is wider than min_boomi_api_interval.
                # It's OK to make Boomi API calls.
                okToMakeBoomiAPICalls = True
                # Report that Boomi API calls are permitted
                self.log.debug('boomi_api_calls_permitted')
                st = "cluster_node_id:" + cluster_node_id
                self.service_check(
                    __NAMESPACE__ + 'boomi_api_calls_permitted',
                    self.OK,
                    tags=[
                        "service_check:true",
                    ],
                )
            else:
                # It's too soon to make more Boomi API calls
                okToMakeBoomiAPICalls = False
                # Report that Boomi API calls will be skipped
                self.log.debug('skipping_boomi_api_calls')
                st = "cluster_node_id:" + cluster_node_id
                self.service_check(
                    __NAMESPACE__ + 'skipping_boomi_api_calls',
                    self.OK,
                    tags=[
                        "service_check:true",
                    ],
                )

            ########################
            # Should we exit early?
            if instance.get('early_exit_001'):
                # We should exit early.
                # Persist last-end-datetime
                res = self.persistEndDatetime(baomid, endDateTime)
                # Bail out if failure
                if res is not None:
                    # Report failure
                    st = "cluster_node_id:" + cluster_node_id
                    self.service_check(
                        __NAMESPACE__ + "completed",
                        self.CRITICAL,
                        tags=["service_check:true", st],
                    )
                    raise Exception(res)
                # Report that End Datetime was persisted
                self.log.debug('persisted_end_datetime')
                st = "cluster_node_id:" + cluster_node_id
                self.service_check(
                    __NAMESPACE__ + 'persisted_end_datetime',
                    self.OK,
                    tags=["service_check:true", st],
                )
                # Exit early
                return

            ##########################################################
            # OK to make Boomi API calls (is it not too soon based on
            # last datetime)?
            if okToMakeBoomiAPICalls or instance.get('force_boomi_api_calls'):

                ###################
                # Query Executions.
                arr_executions = self.queryBoomiExecutionsApi(
                    boomi_api_url,
                    boomi_api_userid,
                    boomi_api_token,
                    startDateTime,
                    endDateTime,
                    boomi_account_id,
                    cluster_node_id,
                )
                # Report that we queried Boomi Executions
                self.log.debug('queried_boomi_executions')
                st = "cluster_node_id:" + cluster_node_id
                self.service_check(
                    __NAMESPACE__ + 'queried_boomi_executions',
                    self.OK,
                    tags=["service_check:true", st],
                )

                ############################
                # Were there any executions?
                if len(arr_executions) > 0:
                    # There were some executions.

                    # Report that there were some Boomi Executions
                    self.log.debug('found_boomi_executions')
                    st = "cluster_node_id:" + cluster_node_id
                    self.service_check(
                        __NAMESPACE__ + 'found_boomi_executions',
                        self.OK,
                        tags=["service_check:true", st],
                    )

                ##################
                # Query AuditLogs.
                arr_auditlogs = queryBoomiAuditLogsApi(
                    self,
                    boomi_api_url,
                    boomi_api_userid,
                    boomi_api_token,
                    startDateTime,
                    endDateTime,
                    boomi_account_id,
                    cluster_node_id,
                )
                # Report that we queried Boomi AuditLogs
                self.log.debug('queried_boomi_auditlogs')
                st = "cluster_node_id:" + cluster_node_id
                self.service_check(
                    __NAMESPACE__ + 'queried_boomi_auditlogs',
                    self.OK,
                    tags=["service_check:true", st],
                )

                ############################
                # Were there any auditlogs?
                if len(arr_auditlogs) > 0:
                    # There were some auditlogs.
                    # Report that there were some Boomi AuditLogs
                    self.log.debug('found_boomi_auditlogs')
                    st = "cluster_node_id:" + cluster_node_id
                    self.service_check(
                        __NAMESPACE__ + 'found_boomi_auditlogs',
                        self.OK,
                        tags=["service_check:true", st],
                    )

                ###############
                # Query Events.
                arr_events = queryBoomiEventsApi(
                    self,
                    boomi_api_url,
                    boomi_api_userid,
                    boomi_api_token,
                    startDateTime,
                    endDateTime,
                    boomi_account_id,
                    cluster_node_id,
                )
                # Report that we queried Boomi Events
                self.log.debug('queried_boomi_events')
                st = "cluster_node_id:" + cluster_node_id
                self.service_check(
                    __NAMESPACE__ + 'queried_boomi_events',
                    self.OK,
                    tags=["service_check:true", st],
                )

                ############################
                # Were there any events?
                if len(arr_events) > 0:
                    # There were some events.
                    # Report that there were some Boomi Events
                    self.log.debug('found_boomi_events')
                    st = "cluster_node_id:" + cluster_node_id
                    self.service_check(
                        __NAMESPACE__ + 'found_boomi_events',
                        self.OK,
                        tags=["service_check:true", st],
                    )

                #############################
                # Get Atom status(API call).
                ar1 = boomi_api_url
                ar2 = boomi_api_userid
                ar3 = boomi_api_token
                ar4 = boomi_account_id
                arr_atoms = queryAtomStatusViaApi(self, ar1, ar2, ar3, ar4)
                # Report that we queried Atoms
                self.log.debug('queried_boomi_atoms')

                ########################
                # Were there any atoms?
                if len(arr_atoms) > 0:
                    # There were some atoms.
                    # Report that there were some Boomi Atoms
                    self.log.debug('found_boomi_atoms')

                    # Iterate over results
                    for atom_result in arr_atoms:
                        # Get the atom name
                        runtime_name = atom_result.get('name', 'unknown')
                        # Get the atom status
                        runtime_status = atom_result.get('status', 'unknown')
                        # Get the atom type
                        runtime_type = atom_result.get('type', 'unknown')
                        # Build the tags
                        runtime_tags = [
                            "service_check:true",
                            "runtime_status:" + runtime_status,
                            "runtime_name:" + runtime_name,
                            "runtime_type:" + runtime_type,
                        ]
                        # Logging
                        msg = 'runtime ' + runtime_name + ' of type '
                        msg += runtime_type + ' reported ' + runtime_status
                        self.log.debug(msg)
                        # Is atom online?
                        if runtime_status == "ONLINE":
                            # Atom is online.
                            # Output service check for online atom.
                            st = __NAMESPACE__ + 'runtime_reported_online'
                            self.service_check(st, self.OK, tags=runtime_tags)
                        else:
                            # Atom is not online.
                            # Output service check for non-online atom.
                            self.service_check(
                                __NAMESPACE__ + 'runtime_reported_online',
                                self.CRITICAL,
                                tags=runtime_tags,
                            )

                ###################################################
                # If we reached here, all API calls were successful
                # and we collected info to be submitted to DataDog.
                # It's now OK to persist last-end-datetime so that
                # this same date range won't be queried again.

                ###########################
                # Persist last-end-datetime
                res = self.persistEndDatetime(baomid, endDateTime)
                # Bail out if failure
                if res is not None:
                    # Report failure
                    st = "cluster_node_id:" + cluster_node_id
                    self.service_check(
                        __NAMESPACE__ + "completed",
                        self.CRITICAL,
                        tags=["service_check:true", st],
                    )
                    raise Exception(res)
                # Report that End Datetime was persisted
                self.log.debug('persisted_end_datetime')
                st = "cluster_node_id:" + cluster_node_id
                self.service_check(
                    __NAMESPACE__ + 'persisted_end_datetime',
                    self.OK,
                    tags=["service_check:true", st],
                )

                ######################################
                # Submit all collected info to Datadog

                #########################################
                # Submit metrics and logs from executions
                if len(arr_executions) > 0:
                    self.sendMetricsFromLog(arr_executions)
                    # Report that we submitted execution metrics
                    self.log.debug('submitted_execution_metrics')
                    st = "cluster_node_id:" + cluster_node_id
                    self.service_check(
                        __NAMESPACE__ + 'submitted_execution_metrics',
                        self.OK,
                        tags=["service_check:true", st],
                    )

                    ################################################
                    # Remap the logs so that DD will parse them well
                    arr_remapped_executions = self.remapLogs(arr_executions)
                    #################
                    # Submit the logs
                    ar1 = arr_remapped_executions
                    self.sendLogs(ar1, instance, cluster_node_id)
                    # Report that we submitted execution logs
                    self.log.debug('submitted_execution_logs')
                    st = "cluster_node_id:" + cluster_node_id
                    self.service_check(
                        __NAMESPACE__ + 'submitted_execution_logs',
                        self.OK,
                        tags=["service_check:true", st],
                    )

                ##############################
                # Submit events from auditlogs
                if len(arr_auditlogs) > 0:
                    for auditlog in arr_auditlogs:

                        # Calculate the Datadog Event alert_type and priority
                        ar1 = auditlog.get('level', 'none')
                        alert_type, priority = self.auditLogToEventDict(ar1)

                        # Translate Boomi AuditLog date to epoch
                        ar1 = auditlog['date'][0:19]
                        ar2 = '%Y-%m-%dT%H:%M:%S'
                        b_a_d = datetime.datetime.strptime(ar1, ar2)
                        ar1 = b_a_d - datetime.datetime(1970, 1, 1)
                        # boomi_auditlog_date = b_a_d
                        dd_event_timestamp = ar1.total_seconds()

                        # Prepare tags
                        st1 = auditlog.get('modifier', 'none')
                        st2 = auditlog.get('source', 'none')
                        tags = [
                            "AuditLogUserId:" + auditlog.get('userId', 'none'),
                            "AuditLogType:" + auditlog.get('type', 'none'),
                            "AuditLogAction:" + auditlog.get('action', 'none'),
                            "AuditLogModifier:" + st1,
                            "AuditLogLevel:" + auditlog.get('level', 'none'),
                            "AuditLogEventSource:" + st2,
                            "BoomiSource:audit_log",
                        ]
                        # Add AtomID if it exists in the AuditLog
                        if 'containerId' in auditlog:
                            st1 = auditlog.get('containerId', 'none')
                            tags.append("AtomId:" + st1)

                        # Prepare text
                        text = "Type: " + auditlog.get('type', 'none') + "\n"
                        text += "Action: " + auditlog.get('action', 'none')
                        text += "\n"
                        text += "Modifier: "
                        text += auditlog.get('modifier', 'none') + "\n"
                        text += "Level: " + auditlog.get('level', 'none')
                        text += "\n"
                        text += "Source: " + auditlog.get('source', 'none')
                        text += "\n"
                        text += "Message: " + auditlog.get('message', 'none')
                        text += "\n-------\n"
                        text += "AuditLogProperties...\n"
                        # Iterate over AuditLogProperties and add them to text.
                        ar1 = auditlog.get('AuditLogProperty', 'none')
                        for auditlogproperty in ar1:
                            text += (
                                auditlogproperty.get('name', 'none')
                                + ": "
                                + auditlogproperty.get('value', 'none')
                                + "\n"
                            )

                        # Create a Datadog Event dict
                        st1 = auditlog.get('message', 'none')
                        st2 = auditlog.get('documentId', 'none')
                        event_dict = {
                            "timestamp": dd_event_timestamp,
                            "event_type": "Boomi AuditLog",
                            "api_key": dd_api_key,
                            "msg_title": "AuditLog: " + st1,
                            "msg_text": text,
                            "aggregation_key": st2,
                            "alert_type": alert_type,
                            "source_type_name": "AtomWatch",
                            "tags": tags,
                            "priority": priority,
                        }
                        # Submit the event
                        st1 = "Submitting events to DD from Boomi "
                        st1 += "AuditLog API data."
                        self.log.debug(st1)
                        self.log.debug(event_dict)
                        self.event(event_dict)
                        # Record success
                        st1 = "cluster_node_id:" + cluster_node_id
                        self.service_check(
                            __NAMESPACE__ + "submitted_auditlog_events",
                            self.OK,
                            tags=["service_check:true", st1],
                        )

                #################################
                # Submit events from Boomi events
                if len(arr_events) > 0:
                    for event in arr_events:

                        # Calculate the Datadog Event alert_type and priority
                        fn = self.boomiEventToEventDict
                        ar1 = event.get('eventLevel', 'none')
                        alert_type, priority = fn(ar1)

                        # Translate Boomi Event date to epoch
                        st1 = event['eventDate'][0:19]
                        st2 = '%Y-%m-%dT%H:%M:%S'
                        b_e_d = datetime.datetime.strptime(st1, st2)
                        ar1 = b_e_d - datetime.datetime(1970, 1, 1)
                        dd_event_timestamp = ar1.total_seconds()
                        # boomi_event_date = b_e_d

                        # Prepare tags
                        st1 = event.get('processName', 'none')
                        st2 = self.cleanupTagValue(st1)
                        st3 = event.get('environment', 'none')
                        st4 = event.get('classification', 'none')
                        tags = [
                            "EventAtomName:" + event.get('atomName', 'none'),
                            "EventAtomId:" + event.get('atomId', 'none'),
                            "EventProcessName:" + st2,
                            "EventLevel:" + event.get('eventLevel', 'none'),
                            "EventType:" + event.get('eventType', 'none'),
                            "EventAtomSphereEnvironment:" + st3,
                            "EventClassification:" + st4,
                            "BoomiSource:platform_event",
                        ]

                        # Prepare text
                        st1 = event.get('processName', 'none')
                        st2 = self.cleanupTagValue(st1)
                        st3 = event.get('executionId', 'none')
                        event_text = "Process Name: " + st2 + "\n"
                        event_text += "Execution ID: " + st3 + "\n"
                        # Label the status field differently based
                        # on event type.
                        st1 = event.get('eventType', "none")
                        if st1 == "user.notification":
                            st2 = event.get('status', 'none')
                            event_text += "Notification: " + st2 + "\n"
                        else:
                            st3 = event.get('status', 'none')
                            event_text += "Status: " + st3 + "\n"
                        st4 = event.get('eventLevel', 'none')
                        event_text += "Level: " + st4 + "\n"
                        # If there is an error string, output error fields
                        if event.get('error', False):
                            st5 = event.get('error', 'none')
                            event_text += "Error: " + st5 + "\n"
                            st6 = event.get('errorType', 'none')
                            event_text += "Error Type: " + st6 + "\n"
                        # If there are nonzero document counts, output them
                        if (
                            event.get('inboundDocumentCount', 0)
                            + event.get('errorDocumentCount', 0)
                            + event.get('outboundDocumentCount', 0)
                            > 0
                        ):
                            st7 = str(event.get('inboundDocumentCount', 0))
                            event_text += "Inbound Doc Count: " + st7 + "\n"
                            st7 = str(event.get('errorDocumentCount', 0))
                            event_text += "Error Doc Count: " + st7 + "\n"
                            st7 = str(event.get('outboundDocumentCount', 0))
                            event_text += "Outbound Doc Count: " + st7 + "\n"

                        # Prepare event title
                        event_title = ""
                        etyp = event.get('eventType', 'none')
                        if etyp == 'user.notification':
                            e_t = event.get('status', 'User Notification')
                            event_title = e_t
                        elif etyp == 'atom.status':
                            event_title = "Atom Status: '"
                            event_title += event.get('atomName', '') + "' "
                            event_title += event.get('status', 'unknown')
                        elif etyp == 'process.execution':
                            st1 = event.get('processName', 'Unknown Process')
                            event_title = self.cleanupTagValue(st1)
                            event_title += " " + event.get('status', 'unknown')
                        elif etyp == 'process.missedSchedule':
                            st1 = event.get('processName', 'Unknown Process')
                            event_title = self.cleanupTagValue(st1)
                            event_title += " Missed Schedule"
                        # Create a Datadog Event dict
                        event_dict = {
                            "timestamp": dd_event_timestamp,
                            "event_type": "Boomi Event",
                            "api_key": dd_api_key,
                            "msg_title": event_title,
                            "msg_text": event_text,
                            "aggregation_key": event.get('eventId', 'none'),
                            "alert_type": alert_type,
                            "source_type_name": "AtomWatch",
                            "tags": tags,
                            "priority": priority,
                        }
                        # Submit the event
                        st1 = "Submitting events to DD from Boomi "
                        st1 += "Event API data."
                        self.log.debug(st1)
                        self.log.debug(event_dict)
                        self.event(event_dict)
                        # Record success
                        st1 = "cluster_node_id:" + cluster_node_id
                        self.service_check(
                            __NAMESPACE__ + "submitted_boomievent_events",
                            self.OK,
                            tags=["service_check:true", st1],
                        )

        # Done making Boomi API calls.
        ##############################

        ##########################################
        # Should we check Molecule cluster status?
        # (Is boomi_molecule_node_id populated?)
        boomi_molecule_node_id = instance.get('boomi_molecule_node_id', None)
        if boomi_molecule_node_id is not None:
            # boomi_molecule_node_id is populated.
            # Check molecule node view file for this node.
            fn = checkBoomiNodeViewFile
            ar1 = boomi_molecule_node_id
            success = fn(self, instance, baomid, ar1, 'molecule')
            if success:
                # Report that we checked molecule view file
                st1 = "cluster_node_id:" + boomi_molecule_node_id
                self.service_check(
                    __NAMESPACE__ + 'checked_molecule_view_file',
                    self.OK,
                    tags=["service_check:true", st1],
                )
            else:
                # Report that we failed checking molecule view file
                st1 = "cluster_node_id:" + boomi_molecule_node_id
                self.service_check(
                    __NAMESPACE__ + 'checked_molecule_view_file',
                    self.CRITICAL,
                    tags=["service_check:true", st1],
                )
        else:
            # Report that Boomi node view file was NOT checked
            self.log.debug('skipped_molecule_view_file')
            st1 = "cluster_node_id:" + cluster_node_id
            self.service_check(
                __NAMESPACE__ + 'skipped_molecule_view_file',
                self.OK,
                tags=["service_check:true", st1],
            )

        #############################################
        # Should we check API Gateway cluster status?
        # (Is boomi_api_gateway_node_id populated?)
        bagni = instance.get('boomi_api_gateway_node_id', None)
        boomi_api_gateway_node_id = bagni
        bagid = instance.get('boomi_api_gateway_install_dir', None)
        # boomi_api_gateway_install_dir = bagid
        if boomi_api_gateway_node_id is not None:
            # boomi_api_gateway_node_id is populated.
            # Check api gateway node view file for this node.
            fn = checkBoomiNodeViewFile
            success = fn(self, instance, bagid, bagni, 'api_gateway')
            if success:
                # Report that we checked api gateway view file
                self.service_check(
                    __NAMESPACE__ + 'checked_api_gateway_view_file',
                    self.OK,
                    tags=["service_check:true", "cluster_node_id:" + bagni],
                )
            else:
                # Report that we failed checking api gateway view file
                self.service_check(
                    __NAMESPACE__ + 'checked_api_gateway_view_file',
                    self.CRITICAL,
                    tags=["service_check:true", "cluster_node_id:" + bagni],
                )
        else:
            # Report that Boomi node view file was NOT checked
            self.log.debug('skipped_api_gateway_view_file')
            st1 = "cluster_node_id:" + cluster_node_id
            self.service_check(
                __NAMESPACE__ + 'skipped_api_gateway_view_file',
                self.OK,
                tags=["service_check:true", st1],
            )

        ##########################################
        # Report that this check ran to completion
        self.log.debug('SUCCESSFUL COMPLETION')
        st1 = __NAMESPACE__ + 'completed'
        st2 = "cluster_node_id:" + cluster_node_id
        self.service_check(st1, self.OK, tags=["service_check:true", st2])
        st1 = "cluster_node_id:" + cluster_node_id
        self.gauge(__NAMESPACE__ + "integration_completed", 1, [st1])

    ##########################################################
    def setupDatetimeRange(self, baomid, seconds_of_lag, cluster_node_id):

        # Rename arguments
        # boomi_atom_or_molecule_install_dir = baomid

        # Sets up datetime range for Boomi API calls.
        # INPUTS:
        # boomi_atom_or_molecule_install_dir...
        #                      This plus /work/<LAST_END_DATETIME_FILENAME>
        #                      is where the last end datetime is stored.
        #                      We want to use this and not the built-in DD
        #                      "cache" because we want a destination
        #                      that can be shared among multiple nodes of
        #                      a molecule.
        # seconds_of_lag...    We want to query Boomi API in arrears, to
        #                      minimize the number of in-progress executions
        #                      we pick up.
        #
        # OUTPUTS:
        # errmsg...            Null if no error.
        # startDateTime...     This will be equal to the datetime persisted in
        #                      <LAST_END_DATETIME_FILENAME> or will be the
        #                      current moment if persisted value is not
        #                      parseable. If this date is too far in the past,
        #                      we will set it to the oldest permitted date
        #                      which is about a week ago.
        # endDateTime...       This will be equal to current moment minus
        #                      seconds_of_lag

        # Begin the log
        self.log.debug("Entered setupDatetimeRange.")

        # Calculate lagged current moment.
        ar1 = datetime.datetime.now(datetime.timezone.utc)
        ar2 = datetime.timedelta(seconds=seconds_of_lag)
        lagged_current_moment = ar1 - ar2
        # Remove any microseconds to bring the time to a whole second.
        lagged_current_moment = lagged_current_moment.replace(microsecond=0)
        # Log this calculated lagged_current_moment
        logmsg = "Calculated lagged_current_moment of "
        logmsg += lagged_current_moment.isoformat()[0:19]
        self.log.info(logmsg)

        # Build path to the last_end_datetime file
        LEDF = LAST_END_DATETIME_FILENAME
        last_end_datetime_path = os.path.join(baomid, "work", LEDF)
        # Open the file that lives at that path... so we can read
        # the last_end_datetime.
        last_end_datetime_file = None
        try:
            last_end_datetime_file = open(last_end_datetime_path, 'r')
            # Read 19 chars which should give us a datetime in
            # format yyyy-MM-dd'T'HH:mm:ss
            last_end_datetime_string = last_end_datetime_file.read(19)
        except OSError as e:
            errmsg = '''\
    Failed to open disk path "{}" and read last end datetime.
    Error message: {}\
    '''.format(
                last_end_datetime_path, str(e)
            )
            self.log.error(errmsg)
            # Caller will see this nonnull return and will raise an Exception.
            return errmsg, None, None
        finally:
            # Clean up.
            if last_end_datetime_file is not None:
                last_end_datetime_file.close()

        # If execution reached here, we read the last_end_datetime
        # successfully into memory.
        logmsg = "Read last_end_datetime of \""
        logmsg += last_end_datetime_string
        logmsg += "\" from disk into memory."
        self.log.debug(logmsg)

        # First set a default value for last_end_datetime in case we
        # fail to parse.
        last_end_datetime = lagged_current_moment

        # Parse the info from last_end_datetime_string into last_end_datetime
        try:
            leds = last_end_datetime_string
            st1 = '%Y-%m-%dT%H:%M:%S'
            led = datetime.datetime.strptime(leds, st1)
            # Add UTC timezone
            led = led.replace(tzinfo=datetime.timezone.utc)
            last_end_datetime = led
        except ValueError as err:
            # Failed to parse.  We'll just leave last_end_datetime as-is
            # which is equal to lagged_current_moment.
            # Note this in the log.
            logmsg = "Failed to parse last_end_datetime value... "
            logmsg += str(err)
            self.log.warning(logmsg)
            # Persist what we have as last_end_datetime
            res = self.persistEndDatetime(baomid, last_end_datetime)
            # Bail out if failure
            if res is not None:
                # Report failure
                st1 = "cluster_node_id:" + cluster_node_id
                self.service_check(
                    __NAMESPACE__ + "completed",
                    self.CRITICAL,
                    tags=["service_check:true", st1],
                )
                raise Exception(res)
            st1 = "cluster_node_id:" + cluster_node_id
            self.service_check(
                __NAMESPACE__ + "used_default_last_end_datetime",
                self.WARNING,
                tags=["service_check:true", st1],
            )

        # If we reached here, we have a parsed last_end_datetime.
        # Create oldest_permitted_end_datetime which needs to be a bit
        # less than a week ago
        oped = datetime.datetime.utcnow() - datetime.timedelta(hours=160)
        # Remove any microseconds to bring the time to a whole second.
        oped = oped.replace(microsecond=0)
        # Add UTC timezone
        oped = oped.replace(tzinfo=datetime.timezone.utc)
        oldest_permitted_end_datetime = oped

        # Is Last End Datetime too far in the past?
        # Querying too-old executions from Boomi is not possible
        # and loading too-old logs/metrics to DD is likewise not possible.
        if last_end_datetime < oldest_permitted_end_datetime:
            # Last End Datetime is too far in the past.
            # Use Oldest Permitted End Datetime instead.
            last_end_datetime = oldest_permitted_end_datetime
            st1 = "\nLast End Datetime is too long ago. "
            st1 += "Using oldest permitted end datetime instead, "
            st1 += "which is now - 160 hours."
            self.log.warning(st1)
        # If we reached here, we have all the values the caller
        # wanted to receive.  Return what caller wanted.
        logmsg = "Using startDateTime of "
        logmsg += last_end_datetime.isoformat()[0:19]
        logmsg += " and endDateTime of "
        logmsg += lagged_current_moment.isoformat()[0:19]
        self.log.info(logmsg)
        return None, last_end_datetime, lagged_current_moment

    #############################################################
    def persistEndDatetime(self, baomid, dateTimeToPersist):

        # Rename args
        # boomi_atom_or_molecule_install_dir = baomid

        # Persists last used endDateTime to the Boomi installation directory.
        # INPUTS:
        # boomi_atom_or_molecule_install_dir...
        #                      This plus /work/<LAST_END_DATETIME_FILENAME>
        #                      is where the last end datetime is stored.
        # dateTimeToPersist... We'll render this datetime into format
        #                      %Y-%m-%dT%H:%M:%S and save it to disk
        #
        # OUTPUTS:
        # errmsg...            Null if no error.

        # Begin the log
        self.log.debug("Entered persistEndDatetime.")

        # Caller has passed us a datetime to persist
        # We'll persist it rendered as 2022-12-31T12:34:56" and we consider
        # that to be UTC.

        # Build path to the last_end_datetime file
        LEDF = LAST_END_DATETIME_FILENAME
        last_end_datetime_path = os.path.join(baomid, "work", LEDF)
        # Open the file that lives at that path...
        # so we can write the last_end_datetime.
        last_end_datetime_file = None
        try:
            last_end_datetime_file = open(last_end_datetime_path, 'w')
            # Write to file
            last_end_datetime_file.write(dateTimeToPersist.isoformat()[0:19])
        except OSError as e:
            errmsg = '''\
    Failed to write last end datetime to disk path "{}"...
    Error message: {}\
    '''.format(
                last_end_datetime_path, str(e)
            )
            self.log.error(errmsg)
            # Caller will see this nonnull return and will raise an Exception.
            return errmsg
        finally:
            # Clean up.
            if last_end_datetime_file is not None:
                last_end_datetime_file.close()

        # If execution reached here, we wrote the last_end_datetime
        # successfully to disk.
        logmsg = "Wrote last_end_datetime of \""
        logmsg += dateTimeToPersist.isoformat()[0:19]
        logmsg += "\" to disk."
        self.log.debug(logmsg)
        # Return successfully
        return None

    def queryBoomiExecutionsApi(
        self,
        boomi_api_url,
        boomi_api_userid,
        boomi_api_token,
        startDateTime,
        endDateTime,
        boomi_account_id,
        cluster_node_id,
    ):

        # Calls Boomi Executions API, pages over results, returns array
        # of executions.
        # For any in-progress executions, stashes execution ID in DD cache.
        # For any execution IDs in cache, re-attempt query.
        #
        # INPUTS:
        # boomi_api_url...     Base URL for making Boomi API calls, e.g.
        #                      https://api.boomi.com
        # boomi_api_userid...  User Id for Basic Auth into Boomi Platform
        #                      API calls; do not prepend BOOMI_TOKEN.
        # boomi_api_token...   API token (password not supported)
        # startDateTime...     TZ-aware datetime with UTC TZ, precise to
        #                      the second but not more granular than that.
        # endDateTime...       Corresponds to startDateTime.
        # boomi_account_id...  Boomi AtomSphere Platform account ID; used
        #                      in making API calls.
        #
        # OUTPUTS:
        # arr_executions...    Array of execution objects just as they came
        #                      from Boomi API but assembled into array.

        # Begin the log
        self.log.debug("Entered queryBoomiExecutionsApi.")

        # Create an array to hold the output.
        arr_executions = []

        #################################################
        # QUERYING PREVIOUSLY INCOMPLETE EXECUTIONS BY ID
        #################################################

        # Prepare the data to be used as request JSON input to Boomi
        # Executions API for specific execution IDs.
        # This data comes from the DD cache.
        execReq = self.popExecutionIdCache()

        # Is the result None?  That means there are no previously
        # incomplete executions
        if execReq is not None:
            # There are some previously incomplete executions.
            self.log.debug("Querying previously incomplete executions.")

            # Make API call and obtain results.
            ar1 = boomi_api_url
            ar2 = boomi_account_id
            ar3 = boomi_api_userid
            in_progress_results = self.queryBoomiExecutionsApi_sub(
                ar1, ar2, ar3, boomi_api_token, execReq, cluster_node_id
            )
            # Append to output
            arr_executions.extend(in_progress_results)

        ###################################
        # QUERYING EXECUTIONS BY DATE RANGE
        ###################################

        # Prepare the data to be used as request JSON input to Boomi
        # Executions API for all executions in date range.
        st1 = startDateTime.isoformat()[0:19] + "Z"
        execReq = {
            "QueryFilter": {
                "expression": {
                    "argument": [st1, endDateTime.isoformat()[0:19] + "Z"],
                    "operator": "BETWEEN",
                    "property": "executionTime",
                }
            }
        }

        # Make API call, parse results, and append to output.
        ar1 = boomi_api_url
        ar2 = boomi_account_id
        ar3 = boomi_api_userid
        ar4 = boomi_api_token
        ar5 = cluster_node_id
        fn = self.queryBoomiExecutionsApi_sub
        arr_executions.extend(fn(ar1, ar2, ar3, ar4, execReq, ar5))

        # Return results to caller
        return arr_executions

    def queryBoomiExecutionsApi_sub(self, ar1, ar2, ar3, ar4, execReq, ar5):

        # Rename args
        boomi_api_url = ar1
        boomi_account_id = ar2
        boomi_api_userid = ar3
        boomi_api_token = ar4
        cluster_node_id = ar5

        # Prepares URL, gets API response pages, pushes in-progress
        # results to cache, outputs completed results as array.
        #
        # INPUTS:
        # boomi_api_url...      (self-explanatory)
        # boomi_account_id...   (self-explanatory)
        # boomi_api_userid...   (self-explanatory)
        # boomi_api_token...    (self-explanatory)
        # execReq...            JSON data to use as Boomi API request
        # cluster_node_id...    (self-explanatory)
        #
        # OUTPUTS:
        # arr_executions...     Array of execution data

        # Prepare output
        arr_executions = []

        # Prepare URL for first page of Boomi Executions API response.
        sExecutionsApiUrl = boomi_api_url
        sExecutionsApiUrl += "/api/rest/v1/"
        sExecutionsApiUrl += boomi_account_id
        sExecutionsApiUrl += "/ExecutionRecord/query"

        # Get first page of Boomi Executions API response
        ar1 = boomi_api_userid
        executionResponse = self.getBoomiExecutionsApiResponsePage(
            ar1, boomi_api_token, sExecutionsApiUrl, execReq, cluster_node_id
        )

        # If we reached here, we got a first page.
        logmsg = "Total count of Executions in Query Result: "
        logmsg += str(executionResponse['numberOfResults'])
        self.log.info(logmsg)

        # Iterate over the results on this page.
        for executionResult in executionResponse['result']:
            # Is the execution in progress?
            if executionResult['status'] in ['INPROCESS', 'STARTED']:
                # Execution is in progress
                fn = self.handleInProgressExecution
                fn(executionResult, cluster_node_id)
            else:
                # Execution is not in progress.
                # Append to output
                arr_executions.append(executionResult)

        # Iterate over remaining pages
        while 'queryToken' in executionResponse:
            # Get subsequent page of Boomi Executions API response.
            executionResponse = self.getBoomiExecutionsApiResponsePage(
                boomi_api_userid,
                boomi_api_token,
                sExecutionsApiUrl + "More",
                executionResponse['queryToken'],
                cluster_node_id,
            )

            # If we reached here, we got a subsequent page.
            self.log.info("Got subsequent page of ExecutionRecords.")

            # Iterate over the results on this page.
            for executionResult in executionResponse['result']:
                # Is the execution in progress?
                if executionResult['status'] in ['INPROCESS', 'STARTED']:
                    # Execution is in progress
                    fn = self.handleInProgressExecution
                    fn(executionResult, cluster_node_id)
                else:
                    # Execution is not in progress.
                    # Append to output
                    arr_executions.append(executionResult)

        # Return results
        return arr_executions

    def handleInProgressExecution(self, executionResult, cluster_node_id):

        # Stashes execution ID in cache, sends metrics to DD
        #
        # INPUTS
        # executionResult...    JSON of ExecutionRecord
        # cluster_node_id...    Used in tagging metrics and service_checks
        #
        # OUTPUTS
        # (none)

        # Execution is in progress.
        msg = "Found an in-progress execution: "
        msg += executionResult['executionId']
        self.log.debug(msg)

        # Stash the execution ID.
        self.pushExecutionIdToCache(executionResult['executionId'])

        # Want to send some metrics about the in-progress execution.
        # First, set up tags.
        st1 = executionResult.get('processName', 'Unknown')
        metricTags = [
            "atom.name:" + executionResult.get('atomName', 'Unknown'),
            "execution.status:" + executionResult.get('status', 'Unknown'),
            "boomi.process.name:" + self.cleanupTagValue(st1),
            "status:" + statusDict[executionResult.get('status', 'UNKNOWN')],
            "cluster_node_id:" + executionResult.get('nodeId', 'Unknown'),
        ]
        # Calculate the metric value.  It's the number of minutes between
        # execution start time and UTCNow.
        try:
            executionTime = executionResult.get('executionTime', None)
            st1 = "%Y-%m-%dT%H:%M:%SZ"
            d_executionTime = datetime.datetime.strptime(executionTime, st1)
            d_now = datetime.datetime.utcnow()
            diff = d_now - d_executionTime
            metricVal = diff.total_seconds() / 60
            # Send the metric
            st1 = "execution.measure.inProgressExecutionDuration"
            self.gauge(__NAMESPACE__ + st1, metricVal, metricTags)
        except Exception as e:
            msg = "Failed to send metrics for in-progress Boomi executions: "
            msg += str(e)
            self.log.warning(msg)
            st1 = "longrunning_execution_failed_metric_submission"
            st2 = "cluster_node_id:" + cluster_node_id
            self.service_check(
                __NAMESPACE__ + st1,
                self.WARNING,
                tags=["service_check:true", st2],
            )

    def pushExecutionIdToCache(self, execution_id):

        # Pushes an execution id (string value) to DD cache by appending
        # what's already there.
        # INPUTS:
        # execution_id...       String of Boomi execution ID
        #
        # OUTPUTS:
        # (none)

        # Read existing value from the cache
        st1 = "in_progress_execution_ids"
        in_progress_execution_ids = self.read_persistent_cache(st1)

        # Is it None or empty string?
        ipei = in_progress_execution_ids
        if ipei is None or ipei == '':
            # Nothing was in the cache.
            # Insert our value.
            in_progress_execution_ids = execution_id
        else:
            # Something was in the cache.
            # Append our value
            in_progress_execution_ids += "," + execution_id

        # Write to cache
        ipei = in_progress_execution_ids
        self.write_persistent_cache("in_progress_execution_ids", ipei)
        msg = "Wrote to cache: " + in_progress_execution_ids
        self.log.debug(msg)

    def popExecutionIdCache(self):

        # Clears execution ID cache.
        # Returns data structure that will be used to query Boomi API by
        # a list of execution IDs.
        #
        # INPUTS:
        # (none)
        #
        # OUTPUTS:
        # (Data structure suitable for Boomi API query)

        # Read existing value from cache.
        st1 = "in_progress_execution_ids"
        in_progress_execution_ids = self.read_persistent_cache(st1)

        # Wipe cache
        self.write_persistent_cache("in_progress_execution_ids", "")

        # Is it None or empty string?
        ipei = in_progress_execution_ids
        if ipei is None or ipei == '':
            # Nothing was in the cache.
            # Return nothing
            return None
        else:
            # Something was in the cache.
            # Split by comma
            arr = in_progress_execution_ids.split(",")
            # Create empty array
            execution_id_params = []
            # Iterate over execution IDs
            for execution_id in arr:
                # Append execution ID in the necessary structure.
                st1 = '{"argument": ["'
                st1 += execution_id
                st1 += '"], "operator": "EQUALS", "property": "executionId"}'
                execution_id_params.append(json.loads(st1))
            # Build the parent structure for this list of execution IDs
            st1 = '{"QueryFilter": {"expression": '
            st1 += '{"operator": "or", "nestedExpression": '
            st1 += json.dumps(execution_id_params)
            st1 += '}}}'
            out = json.loads(st1)
            # Return it to caller
            return out

    def getBoomiExecutionsApiResponsePage(self, ar1, ar2, ar3, ar4, ar5):

        # Rename args
        boomi_api_userid = ar1
        boomi_api_token = ar2
        boomi_api_url = ar3
        jRequest = ar4
        cluster_node_id = ar5

        # Calls Boomi Executions API and retrieves one page of results.
        # INPUTS:
        # self...              Reference to Datadog AgentCheck object that
        #                      ultimately launched this.
        # boomi_api_userid...  User Id for Basic Auth into Boomi Platform
        #                      API calls; do not prepend BOOMI_TOKEN.
        # boomi_api_token...   API token (password not supported)
        # boomi_api_url...     Full URL for making Boomi API calls,
        #                      e.g. https://api.boomi.com/api/rest/v1/
        #                      <BOOMI_ACCOUNT>/ExecutionRecord/query
        # jRequest...          JSON request body for making API call.
        #
        # OUTPUTS:
        # response_json...     JSON response body from API call.

        # Begin the log
        self.log.debug("Entered getBoomiExecutionsApiResponsePage.")
        logmsg = "Boomi Executions API URL: {}".format(boomi_api_url)
        self.log.debug(logmsg)
        logmsg = "Boomi Executions API Request Body: {}".format(jRequest)
        self.log.debug(logmsg)

        # Perform HTTP Request.
        response_json = ""
        # Submit a metric showing that we tried to make a Boomi API call.
        st1 = __NAMESPACE__ + "boomi_api_calls_attempted"
        self.count(st1, 1, tags=["boomiapicalltype:ExecutionRecord"])

        try:
            response = self.http.post(
                boomi_api_url,
                json=jRequest,
                headers={'Accept': 'application/json'},
                auth=("BOOMI_TOKEN." + boomi_api_userid, boomi_api_token),
            )
            response.raise_for_status()
            response_json = response.json()
        except Exception as e:
            # Failure performing HTTP request
            errmsg = '''\
    Failed to get Boomi executions API response page at URL {}.
    POSTed body was...
    {}
    Error message was...
    {}\
    '''.format(
                boomi_api_url, jRequest, str(e)
            )
            # Write to log
            self.log.error(errmsg)
            # Blow up this execution
            st1 = "cluster_node_id:" + cluster_node_id
            self.service_check(
                __NAMESPACE__ + "completed",
                self.CRITICAL,
                tags=["service_check:true", st1],
            )
            raise Exception(errmsg)

        # Log some info about the response.
        logmsg = "Execution Response Data:\n{}".format(response_json)
        self.log.debug(logmsg)

        # If we reached here, we have JSON returned from Boomi API call.
        # Inspect JSON contents
        if 'result' in response_json and 'numberOfResults' in response_json:
            # JSON contents are as expected.
            # Return data to caller.
            return response_json
        else:
            # JSON contents are NOT as expected
            errmsg = '''\
    Boomi API Executions query response JSON content was not as expected.
    Missing 'result' or 'numberOfResults'.
    Boomi Executions API URL: {}
    Boomi Executions API Request Body: {}
    Boomi Executions API Response: {}\
    '''.format(
                boomi_api_url, jRequest, response_json
            )
            # Write to log
            self.log.error(errmsg)
            # Blow up this execution
            st1 = "cluster_node_id:" + cluster_node_id
            self.service_check(
                __NAMESPACE__ + "completed",
                self.CRITICAL,
                tags=["service_check:true", st1],
            )
            raise Exception(errmsg)

    ########################
    def sendLogs(self, log, instance, cluster_node_id):

        # Sends logs to Datadog API
        # INPUTS:
        # log...                JSON value that constitutes the log.
        # instance...           Caller sends the instance of the Check
        #
        # OUTPUTS:
        # (none)

        # Begin the log
        self.log.debug("Entered sendLogs.  Outbound logs JSON:")
        self.log.debug(json.dumps(log))
        dd_api_key = instance.get("dd_api_key")
        datadog_site = instance.get("site", "datadoghq.com")
        headers = {
            'Content-Type': 'application/json',
            'DD-API-KEY': dd_api_key,
        }
        try:
            response_json = None
            st1 = 'https://http-intake.logs.%s/v1/input' % datadog_site
            hd = headers
            response = self.http.post(st1, headers=hd, json=log, auth=None)
            response.raise_for_status()
            response_json = response.json()
            self.log.debug(json.dumps(response_json))
        except Exception as e:
            errmsg = '''Failed to send logs to Datadog API: {}
API response body: {}\
'''.format(
                str(e), response_json
            )
            self.log.error(errmsg)
            # Blow up this execution
            st1 = "cluster_node_id:" + cluster_node_id
            self.service_check(
                __NAMESPACE__ + "completed",
                self.CRITICAL,
                tags=["service_check:true", st1],
            )
            raise Exception(errmsg)

    ########################
    def remapLogs(self, arr_logs):

        # Detects log type and remaps it so it can be parsed successfully
        # in Datadog.
        # INPUTS:
        # arr_logs...           JSON array of log entries.
        #
        # OUTPUTS:
        # arr_remapped_logs...  JSON array after remapping.

        # Begin the log
        self.log.debug("Entered remapLogs.")

        # Can we figure out the log type?
        if "@type" in arr_logs[0]:
            # We can figure out the log type
            # Is it an execution log?
            if arr_logs[0]["@type"] == "ExecutionRecord":
                # This is an execution log.
                # Map it as such.
                fn = self.remapExecutionLogs
                arr_remapped_logs = list(map(fn, arr_logs))
                return arr_remapped_logs
            else:
                # We don't know what kind of log it is.
                # Return it without changes.
                return arr_logs

    def remapExecutionLogs(self, executionLog):

        # Remaps a single Boomi executionLog it so it can be parsed
        # successfully in Datadog.
        # INPUTS:
        # executionLog...       JSON of single executionRecord.
        #
        # OUTPUTS:
        # (unnamed)...          JSON after remapping.

        # First build the tags
        st1 = executionLog.get('processName', 'Unknown')
        clean_process_name = self.cleanupTagValue(st1)
        st1 = executionLog.get('atomName', 'Unknown')
        clean_atom_name = self.cleanupTagValue(st1)
        st1 = executionLog.get('status', '')
        clean_execution_status = self.cleanupTagValue(st1)
        st1 = executionLog.get('status', 'UNKNOWN')
        ddtags_value = "atom.name:" + clean_atom_name
        ddtags_value += ",execution.status:" + clean_execution_status
        ddtags_value += ",boomi.process.name:"
        ddtags_value += clean_process_name
        ddtags_value += ",status:"
        ddtags_value += statusDict[st1.replace(",", ";")]
        ddtags_value += ",host:"
        ddtags_value += executionLog.get('nodeId', 'Unknown')

        st1 = executionLog.get('inboundDocumentCount', '')
        st2 = executionLog.get('inboundErrorDocumentCount', '')
        st3 = executionLog.get('outboundDocumentCount', '')
        st4 = executionLog.get('inboundDocumentSize', [None, None])[1]
        st5 = executionLog.get('outboundDocumentSize', [None, None])[1]
        return {
            'executionId': executionLog.get('executionId', ''),
            'executionTime': executionLog.get('executionTime', ''),
            'executionStatus': clean_execution_status,
            'executionType': executionLog.get('executionType', ''),
            'boomiProcessName': clean_process_name,
            'atomName': clean_atom_name,
            'inboundDocumentCount': st1,
            'inboundErrorDocumentCount': st2,
            'outboundDocumentCount': st3,
            'duration': executionLog.get('executionDuration', [None, None])[1],
            'inboundDocumentSize': st4,
            'outboundDocumentSize': st5,
            'nodeId': executionLog.get('nodeId', ''),
            'message': executionLog.get('message', ''),
            'status': statusDict[executionLog.get('status', 'UNKNOWN')],
            'ddsource': 'kitepipe-boomi',
            'ddtags': ddtags_value,
            'host': executionLog.get('nodeId', 'Unknown'),
            'service': 'BoomiExecutionRecord',
        }

    ##########################
    def sendMetricsFromLog(self, arr_log):

        # Sends metrics to Datadog API based on Boomi API JSON responses)
        # INPUTS:
        # arr_log...            JSON array of Boomi API JSON responses.
        #
        # OUTPUTS:
        # (none)

        # Begin the log
        self.log.debug("Entered sendMetricsFromLog.")

        # Can we figure out the log type?
        if "@type" in arr_log[0]:
            # We can figure out the log type
            # Is it an execution log?
            if arr_log[0]["@type"] == "ExecutionRecord":
                # This is an execution log.  We will parse it
                # to generate metrics.
                # Iterate over the execution records
                for each_log in arr_log:
                    # Build the metric's tags.
                    st1 = each_log.get('status', 'Unknown')
                    st2 = each_log.get('processName', 'Unknown')
                    st3 = each_log.get('status', 'UNKNOWN')
                    metricTags = [
                        "atom.name:" + each_log.get('atomName', 'Unknown'),
                        "execution.status:" + st1,
                        "boomi.process.name:" + self.cleanupTagValue(st2),
                        "status:" + statusDict[st3],
                        "cluster_node_id:" + each_log.get('nodeId', 'Unknown'),
                    ]
                    if 'status' in each_log:
                        # We got it. Send metric.
                        st1 = __NAMESPACE__ + "execution.status"
                        self.count(st1, 1, metricTags)
                    if 'inboundDocumentCount' in each_log:
                        # We got it.  Build the metric's value.
                        metricVal = each_log.get('inboundDocumentCount', 0)
                        # Send metric
                        st1 = __NAMESPACE__
                        st1 += "execution.measure.inboundDocumentCount"
                        self.gauge(st1, metricVal, metricTags)
                    if 'inboundErrorDocumentCount' in each_log:
                        # We got it.  Build the metric's value.
                        st1 = 'inboundErrorDocumentCount'
                        metricVal = each_log.get(st1, 0)
                        # Send metric
                        st1 = __NAMESPACE__
                        st1 += "execution.measure.inboundErrorDocumentCount"
                        self.gauge(st1, metricVal, metricTags)
                    if 'outboundDocumentCount' in each_log:
                        # We got it.  Build the metric's value.
                        metricVal = each_log.get('outboundDocumentCount', 0)
                        # Send metric
                        st1 = __NAMESPACE__
                        st1 += "execution.measure.outboundDocumentCount"
                        self.gauge(st1, metricVal, metricTags)
                    if 'executionDuration' in each_log:
                        # We got it.  Build the metric's value.
                        st1 = 'executionDuration'
                        metricVal = each_log.get(st1, [None, 0])[1]
                        # Send metric
                        st1 = "execution.measure.duration"
                        self.gauge(__NAMESPACE__ + st1, metricVal, metricTags)
                    if 'inboundDocumentSize' in each_log:
                        # We got it.  Build the metric's value.
                        st1 = 'inboundDocumentSize'
                        metricVal = each_log.get(st1, [None, 0])[1]
                        # Send metric
                        st1 = "execution.measure.inboundDocumentSize"
                        self.gauge(__NAMESPACE__ + st1, metricVal, metricTags)
                    if 'outboundDocumentSize' in each_log:
                        # We got it.  Build the metric's value.
                        st1 = 'outboundDocumentSize'
                        metricVal = each_log.get(st1, [None, 0])[1]
                        # Send metric
                        st1 = __NAMESPACE__
                        st1 += "execution.measure.outboundDocumentSize"
                        self.gauge(st1, metricVal, metricTags)
                return None
            else:
                # We don't know what kind of log it is.
                # Don't send any metrics from this log.
                return None

    def cleanupTagValue(self, tag_value):

        # Cleans up tag values as required by Datadog.

        # INPUTS:
        # tag_value...           Tag value that may have illegal chars
        #
        # OUTPUTS:
        # clean_tag_value...     Cleaned-up tag value.

        clean_tag_value = tag_value.replace("", "")
        interim_tag_value = re.sub("[^a-zA-Z0-9]+", "_", tag_value)
        clean_tag_value = re.sub("^_+", "", interim_tag_value)
        return clean_tag_value.lower()

    def auditLogToEventDict(self, auditLogLevel):

        # Takes string with Boomi API AuditLog "level" value
        # and returns two strings to use when creating
        # Datadog Events.
        #
        # INPUTS
        #
        # self...           (required)
        # auditLogLevel...  String with value 'DEBUG', 'INFO',
        #                   'WARNING', 'ERROR'
        #
        # OUTPUTS
        #
        # alert_type...     String with value 'error', 'warning',
        #                   'success', 'info',
        #                   user_update, recommendation, snapshot
        # priority...       String with value 'normal' or 'low'

        # Establish default return values
        alert_type = "info"
        priority = "normal"

        if auditLogLevel == "DEBUG":
            alert_type = "info"
            priority = "low"
        elif auditLogLevel == "INFO":
            alert_type = "info"
            priority = "low"
        elif auditLogLevel == "WARNING":
            alert_type = "warning"
            priority = "normal"
        elif auditLogLevel == "ERROR":
            alert_type = "error"
            priority = "normal"

        return alert_type, priority

    def boomiEventToEventDict(self, boomiEventLevel):

        # Takes string with Boomi API Event "level" value
        # and returns two strings to use when creating
        # Datadog Events.
        #
        # INPUTS
        #
        # self...               (required)
        # boomiEventLevel...    String with value 'INFO', 'WARNING', 'ERROR'
        #
        # OUTPUTS
        #
        # alert_type...         String with value 'error', 'warning',
        #                       'success', 'info',
        #                       user_update, recommendation, snapshot
        # priority...           String with value 'normal' or 'low'

        # Establish default return values
        alert_type = "info"
        priority = "normal"

        if boomiEventLevel == "ERROR":
            alert_type = "error"
            priority = "normal"
        elif boomiEventLevel == "INFO":
            alert_type = "info"
            priority = "low"
        elif boomiEventLevel == "WARNING":
            alert_type = "warning"
            priority = "normal"

        return alert_type, priority
