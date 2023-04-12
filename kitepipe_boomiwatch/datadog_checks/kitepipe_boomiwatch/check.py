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


class BoomiWatchCheck(AgentCheck):
    def __init__(self, name, init_config, instances):
        super(BoomiWatchCheck, self).__init__(name, init_config, instances)

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
        # Report that config is now validated
        self.log.debug('config_validated')
        self.service_check(
            __NAMESPACE__ + 'config_validated',
            self.OK,
            tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
        )

        #############################
        # Get installation directory
        # Try two ways to find it--this shows if we are an API Gateway or a Molecule/Atom
        # Check if API Gateway install dir is defined.  If so, this must be an API Gateway node.
        install_dir = instance.get('boomi_api_gateway_install_dir', None)
        if install_dir is None:
            # This must be a Molecule node or Atom.  Get that install dir.
            install_dir = instance.get('boomi_atom_or_molecule_install_dir', None)

        #######################################
        # Get container ID for billing purposes
        container_id = getContainerId(self, install_dir)

        #######################
        # Report billing metric
        self.count(
            "datadog.marketplace.kitepipe.boomiwatch", 1, ["billing_key:" + container_id + "_" + cluster_node_id]
        )

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
            res, startDateTime, endDateTime = self.setupDatetimeRange(
                boomi_atom_or_molecule_install_dir, seconds_of_lag, cluster_node_id
            )
            # Bail out if failure
            if res is not None:
                self.service_check(
                    __NAMESPACE__ + "completed",
                    self.CRITICAL,
                    tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                )
                raise Exception(res)
            # Report that datetime range was set up
            self.log.debug('datetime_range_set_up')
            self.service_check(
                __NAMESPACE__ + 'datetime_range_set_up',
                self.OK,
                tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
            )

            #######################
            # Should we exit early?
            if instance.get('early_exit_000'):
                # We should exit early.
                return

            ##########################################################
            # Is the datetime range wider than min_boomi_api_interval?
            okToMakeBoomiAPICalls = None
            seconds_since_last_api_call = (endDateTime - startDateTime).total_seconds()
            msg = str(seconds_since_last_api_call) + " seconds since last Boomi API call."
            self.log.debug(msg)
            if seconds_since_last_api_call > min_boomi_api_interval:
                # Datetime range is wider than min_boomi_api_interval.
                # It's OK to make Boomi API calls.
                okToMakeBoomiAPICalls = True
                # Report that Boomi API calls are permitted
                self.log.debug('boomi_api_calls_permitted')
                self.service_check(
                    __NAMESPACE__ + 'boomi_api_calls_permitted',
                    self.OK,
                    tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                )
            else:
                # It's too soon to make more Boomi API calls
                okToMakeBoomiAPICalls = False
                # Report that Boomi API calls will be skipped
                self.log.debug('skipping_boomi_api_calls')
                self.service_check(
                    __NAMESPACE__ + 'skipping_boomi_api_calls',
                    self.OK,
                    tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                )

            ########################
            # Should we exit early?
            if instance.get('early_exit_001'):
                # We should exit early.
                # Persist last-end-datetime
                res = self.persistEndDatetime(boomi_atom_or_molecule_install_dir, endDateTime)
                # Bail out if failure
                if res is not None:
                    # Report failure
                    self.service_check(
                        __NAMESPACE__ + "completed",
                        self.CRITICAL,
                        tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                    )
                    raise Exception(res)
                # Report that End Datetime was persisted
                self.log.debug('persisted_end_datetime')
                self.service_check(
                    __NAMESPACE__ + 'persisted_end_datetime',
                    self.OK,
                    tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                )
                # Exit early
                return

            #########################################################################
            # OK to make Boomi API calls (is it not too soon based on last datetime)?
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
                self.service_check(
                    __NAMESPACE__ + 'queried_boomi_executions',
                    self.OK,
                    tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                )

                ############################
                # Were there any executions?
                if len(arr_executions) > 0:
                    # There were some executions.

                    # Report that there were some Boomi Executions
                    self.log.debug('found_boomi_executions')
                    self.service_check(
                        __NAMESPACE__ + 'found_boomi_executions',
                        self.OK,
                        tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
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
                self.service_check(
                    __NAMESPACE__ + 'queried_boomi_auditlogs',
                    self.OK,
                    tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                )

                ############################
                # Were there any auditlogs?
                if len(arr_auditlogs) > 0:
                    # There were some auditlogs.
                    # Report that there were some Boomi AuditLogs
                    self.log.debug('found_boomi_auditlogs')
                    self.service_check(
                        __NAMESPACE__ + 'found_boomi_auditlogs',
                        self.OK,
                        tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
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
                self.service_check(
                    __NAMESPACE__ + 'queried_boomi_events',
                    self.OK,
                    tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                )

                ############################
                # Were there any events?
                if len(arr_events) > 0:
                    # There were some events.
                    # Report that there were some Boomi Events
                    self.log.debug('found_boomi_events')
                    self.service_check(
                        __NAMESPACE__ + 'found_boomi_events',
                        self.OK,
                        tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                    )

                #############################
                # Get Atom status(API call).
                arr_atoms = queryAtomStatusViaApi(
                    self, boomi_api_url, boomi_api_userid, boomi_api_token, boomi_account_id
                )
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
                        msg = 'runtime ' + runtime_name + ' of type ' + runtime_type + ' reported ' + runtime_status
                        self.log.debug(msg)
                        # Is atom online?
                        if runtime_status == "ONLINE":
                            # Atom is online.
                            # Output service check for online atom.
                            self.service_check(__NAMESPACE__ + 'runtime_reported_online', self.OK, tags=runtime_tags)
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
                res = self.persistEndDatetime(boomi_atom_or_molecule_install_dir, endDateTime)
                # Bail out if failure
                if res is not None:
                    # Report failure
                    self.service_check(
                        __NAMESPACE__ + "completed",
                        self.CRITICAL,
                        tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                    )
                    raise Exception(res)
                # Report that End Datetime was persisted
                self.log.debug('persisted_end_datetime')
                self.service_check(
                    __NAMESPACE__ + 'persisted_end_datetime',
                    self.OK,
                    tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                )

                ######################################
                # Submit all collected info to Datadog

                #########################################
                # Submit metrics and logs from executions
                if len(arr_executions) > 0:
                    self.sendMetricsFromLog(arr_executions)
                    # Report that we submitted execution metrics
                    self.log.debug('submitted_execution_metrics')
                    self.service_check(
                        __NAMESPACE__ + 'submitted_execution_metrics',
                        self.OK,
                        tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                    )

                    ################################################
                    # Remap the logs so that DD will parse them well
                    arr_remapped_executions = self.remapLogs(arr_executions)
                    #################
                    # Submit the logs
                    self.sendLogs(arr_remapped_executions, instance, cluster_node_id)
                    # Report that we submitted execution logs
                    self.log.debug('submitted_execution_logs')
                    self.service_check(
                        __NAMESPACE__ + 'submitted_execution_logs',
                        self.OK,
                        tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                    )

                ##############################
                # Submit events from auditlogs
                if len(arr_auditlogs) > 0:
                    for auditlog in arr_auditlogs:

                        # Calculate the Datadog Event alert_type and priority
                        alert_type, priority = self.auditLogToEventDict(auditlog.get('level', 'none'))

                        # Translate Boomi AuditLog date to epoch
                        boomi_auditlog_date = datetime.datetime.strptime(auditlog['date'][0:19], '%Y-%m-%dT%H:%M:%S')
                        dd_event_timestamp = (boomi_auditlog_date - datetime.datetime(1970, 1, 1)).total_seconds()

                        # Prepare tags
                        tags = [
                            "AuditLogUserId:" + auditlog.get('userId', 'none'),
                            "AuditLogType:" + auditlog.get('type', 'none'),
                            "AuditLogAction:" + auditlog.get('action', 'none'),
                            "AuditLogModifier:" + auditlog.get('modifier', 'none'),
                            "AuditLogLevel:" + auditlog.get('level', 'none'),
                            "AuditLogEventSource:" + auditlog.get('source', 'none'),
                            "BoomiSource:audit_log",
                        ]
                        # Add AtomID if it exists in the AuditLog
                        if 'containerId' in auditlog:
                            tags.append("AtomId:" + auditlog.get('containerId', 'none'))

                        # Prepare text
                        text = "Type: " + auditlog.get('type', 'none') + "\n"
                        text += "Action: " + auditlog.get('action', 'none') + "\n"
                        text += "Modifier: " + auditlog.get('modifier', 'none') + "\n"
                        text += "Level: " + auditlog.get('level', 'none') + "\n"
                        text += "Source: " + auditlog.get('source', 'none') + "\n"
                        text += "Message: " + auditlog.get('message', 'none') + "\n-------\n"
                        text += "AuditLogProperties...\n"
                        # Iterate over AuditLogProperties and add them to text.
                        for auditlogproperty in auditlog.get('AuditLogProperty', 'none'):
                            text += (
                                auditlogproperty.get('name', 'none')
                                + ": "
                                + auditlogproperty.get('value', 'none')
                                + "\n"
                            )

                        # Create a Datadog Event dict
                        event_dict = {
                            "timestamp": dd_event_timestamp,
                            "event_type": "Boomi AuditLog",
                            "api_key": dd_api_key,
                            "msg_title": "AuditLog: " + auditlog.get('message', 'none'),
                            "msg_text": text,
                            "aggregation_key": auditlog.get('documentId', 'none'),
                            "alert_type": alert_type,
                            "source_type_name": "BoomiWatch",
                            "tags": tags,
                            "priority": priority,
                        }
                        # Submit the event
                        self.log.debug("Submitting events to DD from Boomi AuditLog API data.")
                        self.log.debug(event_dict)
                        self.event(event_dict)
                        # Record success
                        self.service_check(
                            __NAMESPACE__ + "submitted_auditlog_events",
                            self.OK,
                            tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                        )

                #################################
                # Submit events from Boomi events
                if len(arr_events) > 0:
                    for event in arr_events:

                        # Calculate the Datadog Event alert_type and priority
                        alert_type, priority = self.boomiEventToEventDict(event.get('eventLevel', 'none'))

                        # Translate Boomi Event date to epoch
                        boomi_event_date = datetime.datetime.strptime(event['eventDate'][0:19], '%Y-%m-%dT%H:%M:%S')
                        dd_event_timestamp = (boomi_event_date - datetime.datetime(1970, 1, 1)).total_seconds()

                        # Prepare tags
                        tags = [
                            "EventAtomName:" + event.get('atomName', 'none'),
                            "EventAtomId:" + event.get('atomId', 'none'),
                            "EventProcessName:" + self.cleanupTagValue(event.get('processName', 'none')),
                            "EventLevel:" + event.get('eventLevel', 'none'),
                            "EventType:" + event.get('eventType', 'none'),
                            "EventAtomSphereEnvironment:" + event.get('environment', 'none'),
                            "EventClassification:" + event.get('classification', 'none'),
                            "BoomiSource:platform_event",
                        ]

                        # Prepare text
                        event_text = "Process Name: " + self.cleanupTagValue(event.get('processName', 'none')) + "\n"
                        event_text += "Execution ID: " + event.get('executionId', 'none') + "\n"
                        # Label the status field differently based on event type.
                        if event.get('eventType', "none") == "user.notification":
                            event_text += "Notification: " + event.get('status', 'none') + "\n"
                        else:
                            event_text += "Status: " + event.get('status', 'none') + "\n"
                        event_text += "Level: " + event.get('eventLevel', 'none') + "\n"
                        # If there is an error string, output error fields
                        if event.get('error', False):
                            event_text += "Error: " + event.get('error', 'none') + "\n"
                            event_text += "Error Type: " + event.get('errorType', 'none') + "\n"
                        # If there are nonzero document counts, output them
                        if (
                            event.get('inboundDocumentCount', 0)
                            + event.get('errorDocumentCount', 0)
                            + event.get('outboundDocumentCount', 0)
                            > 0
                        ):
                            event_text += "Inbound Doc Count: " + str(event.get('inboundDocumentCount', 0)) + "\n"
                            event_text += "Error Doc Count: " + str(event.get('errorDocumentCount', 0)) + "\n"
                            event_text += "Outbound Doc Count: " + str(event.get('outboundDocumentCount', 0)) + "\n"

                        # Prepare event title
                        event_title = ""
                        if event.get('eventType', 'none') == 'user.notification':
                            event_title = event.get('status', 'User Notification')
                        elif event.get('eventType', 'none') == 'atom.status':
                            event_title = (
                                "Atom Status: '" + event.get('atomName', '') + "' " + event.get('status', 'unknown')
                            )
                        elif event.get('eventType', 'none') == 'process.execution':
                            event_title = (
                                self.cleanupTagValue(event.get('processName', 'Unknown Process'))
                                + " "
                                + event.get('status', 'unknown')
                            )
                        elif event.get('eventType', 'none') == 'process.missedSchedule':
                            event_title = (
                                self.cleanupTagValue(event.get('processName', 'Unknown Process')) + " Missed Schedule"
                            )

                        # Create a Datadog Event dict
                        event_dict = {
                            "timestamp": dd_event_timestamp,
                            "event_type": "Boomi Event",
                            "api_key": dd_api_key,
                            "msg_title": event_title,
                            "msg_text": event_text,
                            "aggregation_key": event.get('eventId', 'none'),
                            "alert_type": alert_type,
                            "source_type_name": "BoomiWatch",
                            "tags": tags,
                            "priority": priority,
                        }
                        # Submit the event
                        self.log.debug("Submitting events to DD from Boomi Event API data.")
                        self.log.debug(event_dict)
                        self.event(event_dict)
                        # Record success
                        self.service_check(
                            __NAMESPACE__ + "submitted_boomievent_events",
                            self.OK,
                            tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
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
            success = checkBoomiNodeViewFile(
                self, instance, boomi_atom_or_molecule_install_dir, boomi_molecule_node_id, 'molecule'
            )
            if success:
                # Report that we checked molecule view file
                self.service_check(
                    __NAMESPACE__ + 'checked_molecule_view_file',
                    self.OK,
                    tags=["service_check:true", "cluster_node_id:" + boomi_molecule_node_id],
                )
            else:
                # Report that we failed checking molecule view file
                self.service_check(
                    __NAMESPACE__ + 'checked_molecule_view_file',
                    self.CRITICAL,
                    tags=["service_check:true", "cluster_node_id:" + boomi_molecule_node_id],
                )
        else:
            # Report that Boomi node view file was NOT checked
            self.log.debug('skipped_molecule_view_file')
            self.service_check(
                __NAMESPACE__ + 'skipped_molecule_view_file',
                self.OK,
                tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
            )

        #############################################
        # Should we check API Gateway cluster status?
        # (Is boomi_api_gateway_node_id populated?)
        boomi_api_gateway_node_id = instance.get('boomi_api_gateway_node_id', None)
        boomi_api_gateway_install_dir = instance.get('boomi_api_gateway_install_dir', None)
        if boomi_api_gateway_node_id is not None:
            # boomi_api_gateway_node_id is populated.
            # Check api gateway node view file for this node.
            success = checkBoomiNodeViewFile(
                self, instance, boomi_api_gateway_install_dir, boomi_api_gateway_node_id, 'api_gateway'
            )
            if success:
                # Report that we checked api gateway view file
                self.service_check(
                    __NAMESPACE__ + 'checked_api_gateway_view_file',
                    self.OK,
                    tags=["service_check:true", "cluster_node_id:" + boomi_api_gateway_node_id],
                )
            else:
                # Report that we failed checking api gateway view file
                self.service_check(
                    __NAMESPACE__ + 'checked_api_gateway_view_file',
                    self.CRITICAL,
                    tags=["service_check:true", "cluster_node_id:" + boomi_api_gateway_node_id],
                )
        else:
            # Report that Boomi node view file was NOT checked
            self.log.debug('skipped_api_gateway_view_file')
            self.service_check(
                __NAMESPACE__ + 'skipped_api_gateway_view_file',
                self.OK,
                tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
            )

        ##########################################
        # Report that this check ran to completion
        self.log.debug('SUCCESSFUL COMPLETION')
        self.service_check(
            __NAMESPACE__ + 'completed', self.OK, tags=["service_check:true", "cluster_node_id:" + cluster_node_id]
        )
        self.gauge(__NAMESPACE__ + "integration_completed", 1, ["cluster_node_id:" + cluster_node_id])

    ##########################################################
    def setupDatetimeRange(self, boomi_atom_or_molecule_install_dir, seconds_of_lag, cluster_node_id):
        # Sets up datetime range for Boomi API calls.
        # INPUTS:
        # boomi_atom_or_molecule_install_dir...
        #                      This plus /work/<LAST_END_DATETIME_FILENAME> is where the last end datetime is stored.
        #                      We want to use this and not the built-in DD "cache" because we want a destination
        #                      that can be shared among multiple nodes of a molecule.
        # seconds_of_lag...    We want to query Boomi API in arrears, to minimize the number of
        #                      in-progress executions we pick up.
        #
        # OUTPUTS:
        # errmsg...            Null if no error.
        # startDateTime...     This will be equal to the datetime persisted in <LAST_END_DATETIME_FILENAME>,
        #                      or will be the current moment if persisted value is not parseable.
        #                      If this date is too far in the past, we will set it to the oldest
        #                      permitted date which is about a week ago.
        # endDateTime...       This will be equal to current moment minus seconds_of_lag

        # Begin the log
        self.log.debug("Entered setupDatetimeRange.")

        # Calculate lagged current moment.
        lagged_current_moment = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=seconds_of_lag
        )
        # Remove any microseconds to bring the time to a whole second.
        lagged_current_moment = lagged_current_moment.replace(microsecond=0)
        # Log this calculated lagged_current_moment
        logmsg = "Calculated lagged_current_moment of {}".format(lagged_current_moment.isoformat()[0:19])
        self.log.info(logmsg)

        # Build path to the last_end_datetime file
        last_end_datetime_path = os.path.join(boomi_atom_or_molecule_install_dir, "work", LAST_END_DATETIME_FILENAME)
        # Open the file that lives at that path... so we can read the last_end_datetime.
        last_end_datetime_file = None
        try:
            last_end_datetime_file = open(last_end_datetime_path, 'r')
            # Read 19 chars which should give us a datetime in format yyyy-MM-dd'T'HH:mm:ss
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

        # If execution reached here, we read the last_end_datetime successfully into memory.
        logmsg = "Read last_end_datetime of \"{}\" from disk into memory.".format(last_end_datetime_string)
        self.log.debug(logmsg)

        # First set a default value for last_end_datetime in case we fail to parse.
        last_end_datetime = lagged_current_moment

        # Parse the info from last_end_datetime_string into last_end_datetime
        try:
            last_end_datetime = datetime.datetime.strptime(last_end_datetime_string, '%Y-%m-%dT%H:%M:%S')
            # Add UTC timezone
            last_end_datetime = last_end_datetime.replace(tzinfo=datetime.timezone.utc)
        except ValueError as err:
            # Failed to parse.  We'll just leave last_end_datetime as-is
            # which is equal to lagged_current_moment.
            # Note this in the log.
            logmsg = "Failed to parse last_end_datetime value... {}".format(err)
            self.log.warning(logmsg)
            # Persist what we have as last_end_datetime
            res = self.persistEndDatetime(boomi_atom_or_molecule_install_dir, last_end_datetime)
            # Bail out if failure
            if res is not None:
                # Report failure
                self.service_check(
                    __NAMESPACE__ + "completed",
                    self.CRITICAL,
                    tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
                )
                raise Exception(res)
            self.service_check(
                __NAMESPACE__ + "used_default_last_end_datetime",
                self.WARNING,
                tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
            )

        # If we reached here, we have a parsed last_end_datetime.
        # Create oldest_permitted_end_datetime which needs to be a bit less than a week ago
        oldest_permitted_end_datetime = datetime.datetime.utcnow() - datetime.timedelta(hours=160)
        # Remove any microseconds to bring the time to a whole second.
        oldest_permitted_end_datetime = oldest_permitted_end_datetime.replace(microsecond=0)
        # Add UTC timezone
        oldest_permitted_end_datetime = oldest_permitted_end_datetime.replace(tzinfo=datetime.timezone.utc)

        # Is Last End Datetime too far in the past?
        # Querying too-old executions from Boomi is not possible
        # and loading too-old logs/metrics to DD is likewise not possible.
        if last_end_datetime < oldest_permitted_end_datetime:
            # Last End Datetime is too far in the past.
            # Use Oldest Permitted End Datetime instead.
            last_end_datetime = oldest_permitted_end_datetime
            self.log.warning(
                '''\
Last End Datetime is too long ago.  Using oldest permitted end datetime instead, which is now - 160 hours.'''
            )
        # If we reached here, we have all the values the caller wanted to receive
        # Return what caller wanted.
        logmsg = "Using startDateTime of {} and endDateTime of {}".format(
            last_end_datetime.isoformat()[0:19], lagged_current_moment.isoformat()[0:19]
        )
        self.log.info(logmsg)
        return None, last_end_datetime, lagged_current_moment

    #############################################################
    def persistEndDatetime(self, boomi_atom_or_molecule_install_dir, dateTimeToPersist):
        # Persists last used endDateTime to the Boomi installation directory.
        # INPUTS:
        # boomi_atom_or_molecule_install_dir...
        #                      This plus /work/<LAST_END_DATETIME_FILENAME> is where the last end datetime is stored.
        # dateTimeToPersist... We'll render this datetime into format %Y-%m-%dT%H:%M:%S and save it to disk
        #
        # OUTPUTS:
        # errmsg...            Null if no error.

        # Begin the log
        self.log.debug("Entered persistEndDatetime.")

        # Caller has passed us a datetime to persist
        # We'll persist it rendered as 2022-12-31T12:34:56" and we consider that to be UTC.

        # Build path to the last_end_datetime file
        last_end_datetime_path = os.path.join(boomi_atom_or_molecule_install_dir, "work", LAST_END_DATETIME_FILENAME)
        # Open the file that lives at that path... so we can write the last_end_datetime.
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

        # If execution reached here, we wrote the last_end_datetime successfully to disk.
        logmsg = "Wrote last_end_datetime of \"{}\" to disk.".format(dateTimeToPersist.isoformat()[0:19])
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

        # Calls Boomi Executions API, pages over results, returns array of executions.
        # For any in-progress executions, stashes execution ID in DD cache.
        # For any execution IDs in cache, re-attempt query.
        #
        # INPUTS:
        # boomi_api_url...     Base URL for making Boomi API calls, e.g. https://api.boomi.com
        # boomi_api_userid...  User Id for Basic Auth into Boomi Platform API calls; do not prepend BOOMI_TOKEN.
        # boomi_api_token...   API token (password not supported)
        # startDateTime...     TZ-aware datetime with UTC TZ, precise to the second but not more granular than that.
        # endDateTime...       Corresponds to startDateTime.
        # boomi_account_id...  Boomi AtomSphere Platform account ID; used in making API calls.
        #
        # OUTPUTS:
        # arr_executions...    Array of execution objects just as they came from Boomi API but assembled into array.

        # Begin the log
        self.log.debug("Entered queryBoomiExecutionsApi.")

        # Create an array to hold the output.
        arr_executions = []

        #################################################
        # QUERYING PREVIOUSLY INCOMPLETE EXECUTIONS BY ID
        #################################################

        # Prepare the data to be used as request JSON input to Boomi Executions API...
        # for specific execution IDs.  This data comes from the DD cache.
        execReq = self.popExecutionIdCache()

        # Is the result None?  That means there are no previously incomplete executions
        if execReq is not None:
            # There are some previously incomplete executions.
            self.log.debug("Querying previously incomplete executions.")

            # Make API call and obtain results.
            in_progress_results = self.queryBoomiExecutionsApi_sub(
                boomi_api_url, boomi_account_id, boomi_api_userid, boomi_api_token, execReq, cluster_node_id
            )
            # Append to output
            arr_executions.extend(in_progress_results)

        ###################################
        # QUERYING EXECUTIONS BY DATE RANGE
        ###################################

        # Prepare the data to be used as request JSON input to Boomi Executions API...
        # for all executions in date range.
        execReq = {
            "QueryFilter": {
                "expression": {
                    "argument": [startDateTime.isoformat()[0:19] + "Z", endDateTime.isoformat()[0:19] + "Z"],
                    "operator": "BETWEEN",
                    "property": "executionTime",
                }
            }
        }

        # Make API call, parse results, and append to output.
        arr_executions.extend(
            self.queryBoomiExecutionsApi_sub(
                boomi_api_url, boomi_account_id, boomi_api_userid, boomi_api_token, execReq, cluster_node_id
            )
        )

        # Return results to caller
        return arr_executions

    def queryBoomiExecutionsApi_sub(
        self, boomi_api_url, boomi_account_id, boomi_api_userid, boomi_api_token, execReq, cluster_node_id
    ):

        # Prepares URL, gets API response pages, pushes in-progress results to cache,
        # outputs completed results as array.
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
        sExecutionsApiUrl = "{}/api/rest/v1/{}/ExecutionRecord/query".format(boomi_api_url, boomi_account_id)

        # Get first page of Boomi Executions API response
        executionResponse = self.getBoomiExecutionsApiResponsePage(
            boomi_api_userid, boomi_api_token, sExecutionsApiUrl, execReq, cluster_node_id
        )

        # If we reached here, we got a first page.
        logmsg = "Total count of Executions in Query Result: {}".format(executionResponse['numberOfResults'])
        self.log.info(logmsg)

        # Iterate over the results on this page.
        for executionResult in executionResponse['result']:
            # Is the execution in progress?
            if executionResult['status'] in ['INPROCESS', 'STARTED']:
                # Execution is in progress
                self.handleInProgressExecution(executionResult, cluster_node_id)
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
                    self.handleInProgressExecution(executionResult, cluster_node_id)
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
        msg = "Found an in-progress execution: {}".format(executionResult['executionId'])
        self.log.debug(msg)

        # Stash the execution ID.
        self.pushExecutionIdToCache(executionResult['executionId'])

        # Want to send some metrics about the in-progress execution.
        # First, set up tags.
        metricTags = [
            "atom.name:" + executionResult.get('atomName', 'Unknown'),
            "execution.status:" + executionResult.get('status', 'Unknown'),
            "boomi.process.name:" + self.cleanupTagValue(executionResult.get('processName', 'Unknown')),
            "status:" + statusDict[executionResult.get('status', 'UNKNOWN')],
            "cluster_node_id:" + executionResult.get('nodeId', 'Unknown'),
        ]
        # Calculate the metric value.  It's the number of minutes between execution start time and UTCNow.
        try:
            executionTime = executionResult.get('executionTime', None)
            d_executionTime = datetime.datetime.strptime(executionTime, "%Y-%m-%dT%H:%M:%SZ")
            d_now = datetime.datetime.utcnow()
            diff = d_now - d_executionTime
            metricVal = diff.total_seconds() / 60
            # Send the metric
            self.gauge(__NAMESPACE__ + "execution.measure.inProgressExecutionDuration", metricVal, metricTags)
        except Exception as e:
            msg = "Failed to send metrics for in-progress Boomi executions: {}".format(e)
            self.log.warning(msg)
            self.service_check(
                __NAMESPACE__ + "longrunning_execution_failed_metric_submission",
                self.WARNING,
                tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
            )

    def pushExecutionIdToCache(self, execution_id):

        # Pushes an execution id (string value) to DD cache by appending what's already there.
        # INPUTS:
        # execution_id...       String of Boomi execution ID
        #
        # OUTPUTS:
        # (none)

        # Read existing value from the cache
        in_progress_execution_ids = self.read_persistent_cache("in_progress_execution_ids")

        # Is it None or empty string?
        if in_progress_execution_ids is None or in_progress_execution_ids == '':
            # Nothing was in the cache.
            # Insert our value.
            in_progress_execution_ids = execution_id
        else:
            # Something was in the cache.
            # Append our value
            in_progress_execution_ids += "," + execution_id

        # Write to cache
        self.write_persistent_cache("in_progress_execution_ids", in_progress_execution_ids)
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
        in_progress_execution_ids = self.read_persistent_cache("in_progress_execution_ids")

        # Wipe cache
        self.write_persistent_cache("in_progress_execution_ids", "")

        # Is it None or empty string?
        if in_progress_execution_ids is None or in_progress_execution_ids == '':
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
                execution_id_params.append(
                    {"argument": [execution_id], "operator": "EQUALS", "property": "executionId"}
                )
            # Build the parent structure for this list of execution IDs
            out = {"QueryFilter": {"expression": {"operator": "or", "nestedExpression": execution_id_params}}}
            # Return it to caller
            return out

    def getBoomiExecutionsApiResponsePage(
        self, boomi_api_userid, boomi_api_token, boomi_api_url, jRequest, cluster_node_id
    ):

        # Calls Boomi Executions API and retrieves one page of results.
        # INPUTS:
        # self...              Reference to Datadog AgentCheck object that ultimately launched this.
        # boomi_api_userid...  User Id for Basic Auth into Boomi Platform API calls; do not prepend BOOMI_TOKEN.
        # boomi_api_token...   API token (password not supported)
        # boomi_api_url...     Full URL for making Boomi API calls,
        #                      e.g. https://api.boomi.com/api/rest/v1/<BOOMI_ACCOUNT>/ExecutionRecord/query
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
        self.count(__NAMESPACE__ + "boomi_api_calls_attempted", 1, tags=["boomiapicalltype:ExecutionRecord"])

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
            self.service_check(
                __NAMESPACE__ + "completed",
                self.CRITICAL,
                tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
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
    Boomi API Executions query response JSON content was not as expected; missing 'result' or 'numberOfResults'.
    Boomi Executions API URL: {}
    Boomi Executions API Request Body: {}
    Boomi Executions API Response: {}\
    '''.format(
                boomi_api_url, jRequest, response_json
            )
            # Write to log
            self.log.error(errmsg)
            # Blow up this execution
            self.service_check(
                __NAMESPACE__ + "completed",
                self.CRITICAL,
                tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
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
            response = self.http.post(
                'https://http-intake.logs.%s/v1/input' % datadog_site, headers=headers, json=log, auth=None
            )
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
            self.service_check(
                __NAMESPACE__ + "completed",
                self.CRITICAL,
                tags=["service_check:true", "cluster_node_id:" + cluster_node_id],
            )
            raise Exception(errmsg)

    ########################
    def remapLogs(self, arr_logs):

        # Detects log type and remaps it so it can be parsed successfully in Datadog.
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
                arr_remapped_logs = list(map(self.remapExecutionLogs, arr_logs))
                return arr_remapped_logs
            else:
                # We don't know what kind of log it is.
                # Return it without changes.
                return arr_logs

    def remapExecutionLogs(self, executionLog):

        # Remaps a single Boomi executionLog it so it can be parsed successfully in Datadog.
        # INPUTS:
        # executionLog...       JSON of single executionRecord.
        #
        # OUTPUTS:
        # (unnamed)...          JSON after remapping.

        # First build the tags
        clean_process_name = self.cleanupTagValue(executionLog.get('processName', 'Unknown'))
        clean_atom_name = self.cleanupTagValue(executionLog.get('atomName', 'Unknown'))
        clean_execution_status = self.cleanupTagValue(executionLog.get('status', ''))
        ddtags_value = "atom.name:{},execution.status:{},boomi.process.name:{},status:{},host:{}".format(
            clean_atom_name,
            clean_execution_status,
            clean_process_name,
            statusDict[executionLog.get('status', 'UNKNOWN').replace(",", ";")],
            executionLog.get('nodeId', 'Unknown'),
        )

        return {
            'executionId': executionLog.get('executionId', ''),
            'executionTime': executionLog.get('executionTime', ''),
            'executionStatus': clean_execution_status,
            'executionType': executionLog.get('executionType', ''),
            'boomiProcessName': clean_process_name,
            'atomName': clean_atom_name,
            'inboundDocumentCount': executionLog.get('inboundDocumentCount', ''),
            'inboundErrorDocumentCount': executionLog.get('inboundErrorDocumentCount', ''),
            'outboundDocumentCount': executionLog.get('outboundDocumentCount', ''),
            'duration': executionLog.get('executionDuration', [None, None])[1],
            'inboundDocumentSize': executionLog.get('inboundDocumentSize', [None, None])[1],
            'outboundDocumentSize': executionLog.get('outboundDocumentSize', [None, None])[1],
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
                # This is an execution log.  We will parse it to generate metrics.
                # Iterate over the execution records
                for each_log in arr_log:
                    # Build the metric's tags.
                    metricTags = [
                        "atom.name:" + each_log.get('atomName', 'Unknown'),
                        "execution.status:" + each_log.get('status', 'Unknown'),
                        "boomi.process.name:" + self.cleanupTagValue(each_log.get('processName', 'Unknown')),
                        "status:" + statusDict[each_log.get('status', 'UNKNOWN')],
                        "cluster_node_id:" + each_log.get('nodeId', 'Unknown'),
                    ]
                    if 'status' in each_log:
                        # We got it. Send metric.
                        self.count(__NAMESPACE__ + "execution.status", 1, metricTags)
                    if 'inboundDocumentCount' in each_log:
                        # We got it.  Build the metric's value.
                        metricVal = each_log.get('inboundDocumentCount', 0)
                        # Send metric
                        self.gauge(__NAMESPACE__ + "execution.measure.inboundDocumentCount", metricVal, metricTags)
                    if 'inboundErrorDocumentCount' in each_log:
                        # We got it.  Build the metric's value.
                        metricVal = each_log.get('inboundErrorDocumentCount', 0)
                        # Send metric
                        self.gauge(__NAMESPACE__ + "execution.measure.inboundErrorDocumentCount", metricVal, metricTags)
                    if 'outboundDocumentCount' in each_log:
                        # We got it.  Build the metric's value.
                        metricVal = each_log.get('outboundDocumentCount', 0)
                        # Send metric
                        self.gauge(__NAMESPACE__ + "execution.measure.outboundDocumentCount", metricVal, metricTags)
                    if 'executionDuration' in each_log:
                        # We got it.  Build the metric's value.
                        metricVal = each_log.get('executionDuration', [None, 0])[1]
                        # Send metric
                        self.gauge(__NAMESPACE__ + "execution.measure.duration", metricVal, metricTags)
                    if 'inboundDocumentSize' in each_log:
                        # We got it.  Build the metric's value.
                        metricVal = each_log.get('inboundDocumentSize', [None, 0])[1]
                        # Send metric
                        self.gauge(__NAMESPACE__ + "execution.measure.inboundDocumentSize", metricVal, metricTags)
                    if 'outboundDocumentSize' in each_log:
                        # We got it.  Build the metric's value.
                        metricVal = each_log.get('outboundDocumentSize', [None, 0])[1]
                        # Send metric
                        self.gauge(__NAMESPACE__ + "execution.measure.outboundDocumentSize", metricVal, metricTags)
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
        # auditLogLevel...  String with value 'DEBUG', 'INFO', 'WARNING', 'ERROR'
        #
        # OUTPUTS
        #
        # alert_type...     String with value 'error', 'warning', 'success', 'info',
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
        # alert_type...         String with value 'error', 'warning', 'success', 'info',
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
