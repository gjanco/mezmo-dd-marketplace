import json as json_import
import os
import re
import tempfile
import time

import mock
import pytest

from datadog_checks.base import ConfigurationError
from datadog_checks.dev import get_here
from datadog_checks.kitepipe_boomiwatch import BoomiWatchCheck

# import local code
__NAMESPACE__ = 'kitepipe.boomiwatch.'
LAST_END_DATETIME_FILENAME = "kitepipe-boomiwatch-last-end-datetime.txt"


# We fake getting a Boomi API response
# by mocking the "http" class and its "post" and "get" methods.
# Invent a fake "get" method here...
def mock_get(boomi_api_url, headers, auth):

    # Build a function that will be the output
    class Mock_get_response:
        def raise_for_status(self):
            pass

        def json(self):
            # Prepare a return value.
            return_str = ""

            # Prepare a filename... this will point to some JSON data on disk
            # which will be injected into the program as though it came from
            # Boomi API.
            staged_json_filename = "default.json"

            # There is one supported scenario:
            #   1. Atom Get by ID

            # Inspect the passed URL.
            # Does it try to do an Atom Get (scenario 1)?
            found = re.search("/Atom/", boomi_api_url)
            if found:
                # The URL is trying to do an Atom Get
                staged_json_filename = "boomi_atom_get.json"

            # Read the Atom Get data from disk.
            f_name = os.path.join(get_here(), 'http', staged_json_filename)
            with open(f_name, 'r') as f:
                return_str = f.read()

            # Return string value from "json()" function
            return json_import.loads(return_str)

    # Return the output class
    return Mock_get_response()


# Invent a fake "post" method here...
def mock_post(boomi_api_url, json, headers, auth):

    # Is the caller trying to reach the Datadog API?
    # found = re.search("datadog", boomi_api_url)
    # if found:
    # Caller is trying to reach Datadog API.
    # Let them actually get there.
    # return requests.post(boomi_api_url, json=json, headers=headers)

    # Build a function that will be the output
    class Mock_post_response:
        def raise_for_status(self):
            pass

        def json(self):
            # Prepare a return value.
            return_str = ""

            # Prepare a filename... this will point to some JSON data on disk
            # which will be injected into the program as though it came from
            # Boomi API.
            staged_json_filename = "default.json"

            # There are 10 supported scenarios:
            #   1. ExecutionRecord Query first page by timestamp
            #   2. ExecutionRecord Query more with tokenA
            #   3. ExecutionRecord Query first page by execution ID
            #   4. ExecutionRecord Query more with tokenB
            #   5. AuditLog Query first page by timestamp.
            #   6. AuditLog Query more with tokenC
            #   7. Event Query first page by timestamp.
            #   8. Event Query more with tokenD
            #   9. Atom Query
            #   10. Datadog API

            # Inspect the passed URL.
            # Does it try to do a query of Execution Records (scenarios 1 and 3)?
            found = re.search("/ExecutionRecord/query$", boomi_api_url)
            if found:
                # The URL is trying to retrieve first page of ExecutionRecords.
                # Check the input JSON... is there a executionTime param?
                s_json = json_import.dumps(json)
                found = re.search("executionTime", s_json)
                if found:
                    # Caller wants page 1 of ExecutionRecord query by timestamp.
                    staged_json_filename = "boomi_executions_by_timestamp_pg_1.json"
                found = re.search("executionId", s_json)
                if found:
                    # Caller wants page 1 of ExecutionRecord query by execution ID.
                    staged_json_filename = "boomi_executions_by_execid_pg_1.json"

            # Inspect the passed URL.
            # Does it try to do a queryMore of Execution Records (scenarios 2 and 4)?
            found = re.search("/ExecutionRecord/queryMore", boomi_api_url)
            if found:
                # The URL is trying to retrieve "more" ExecutionRecords.
                # Check the input JSON... which token is it?
                if json == "tokenA":
                    # Caller wants page 2 of ExecutionRecord query by timestamp.
                    staged_json_filename = "boomi_executions_by_timestamp_pg_2.json"
                if json == "tokenB":
                    # Caller wants page 2 of ExecutionRecord query by execution ID.
                    staged_json_filename = "boomi_executions_by_execid_pg_2.json"

            # Inspect the passed URL.
            # Does it try to do a query of AuditLogs (scenario 5)?
            found = re.search("/AuditLog/query$", boomi_api_url)
            if found:
                # The URL is trying to retrieve first page of AuditLog.
                # Caller wants page 1 of AuditLog query by timestamp.
                staged_json_filename = "boomi_auditlogs_by_timestamp_pg_1.json"

            # Inspect the passed URL
            # Does it try to do a queryMore of AuditLogs (scenario 6)?
            found = re.search("/AuditLog/queryMore", boomi_api_url)
            if found:
                # The URL is trying to retrieve "more" AuditLogs.
                # Check the input JSON... is it tokenA?
                if json == "tokenC":
                    # Caller wants page 2 of AuditLog query by timestamp.
                    staged_json_filename = "boomi_auditlogs_by_timestamp_pg_2.json"

            # Inspect the passed URL.
            # Does it try to do a query of Events (scenario 7)?
            found = re.search("/Event/query$", boomi_api_url)
            if found:
                # The URL is trying to retrieve first page of Events.
                # Caller wants page 1 of Events query by timestamp.
                staged_json_filename = "boomi_events_by_timestamp_pg_1.json"

            # Inspect the passed URL
            # Does it try to do a queryMore of Events (scenario 8)?
            found = re.search("/Event/queryMore", boomi_api_url)
            if found:
                # The URL is trying to retrieve "more" Events.
                # Check the input JSON... is it tokenD?
                if json == "tokenD":
                    # Caller wants page 2 of Event query by timestamp.
                    staged_json_filename = "boomi_events_by_timestamp_pg_2.json"

            # Inspect the passed URL
            # Does it try to do a query of Atom (scenario 9)?
            found = re.search("/Atom/", boomi_api_url)
            if found:
                # The URL is trying to retrieve first page of Atoms
                # Caller wants the Atom API JSON response.
                staged_json_filename = "boomi_atom_query.json"

            # Inspect the passed URL.
            # Does it try to hit the Datadog API (scenario 10)?
            found = re.search("datadog", boomi_api_url)
            if found:
                # The URL is trying to hit Datadog API.
                staged_json_filename = "datadog_log_intake.json"

            # Read the chosen ExecutionRecord data from disk.
            f_name = os.path.join(get_here(), 'http', staged_json_filename)
            with open(f_name, 'r') as f:
                return_str = f.read()
            # Return string value from "json()" function
            return json_import.loads(return_str)

    # Return the output class
    return Mock_post_response()


@pytest.mark.unit
def test_config():
    # Testing all flavors of improper configuration in
    # datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml
    instance = {}
    c = BoomiWatchCheck('kitepipe_boomiwatch', {}, [instance])

    # BAD CONFIG: empty instance
    with pytest.raises(ConfigurationError):
        c.check(instance)

    # BAD CONFIG: Missing DD API key
    try:
        c.check({'not_a_property': 'not a value'})
    except Exception as e:
        assert (
            e.__str__()
            == "Configuration error.  Value of dd_api_key is missing. Please edit \
datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply this value."
        )

    # BAD CONFIG: Missing the Boomi API userid while boomi_api_url present
    try:
        c.check({'dd_api_key': 'some DD key', 'boomi_api_url': 'https://api.boomi.com'})
    except Exception as e:
        assert (
            e.__str__()
            == 'Configuration error.  Value of boomi_api_url present but boomi_api_userid is missing. \
Populate boomi_api_url only on one server so that only one set of Boomi API calls is made. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply missing value.'
        )

    # BAD CONFIG: Missing the the Boomi API token while boomi_api_url present
    try:
        c.check({'dd_api_key': 'some DD key', 'boomi_api_url': 'https://api.boomi.com', 'boomi_api_userid': 'foo'})
    except Exception as e:
        assert (
            e.__str__()
            == 'Configuration error.  Value of boomi_api_url present but boomi_api_token is missing. \
Populate boomi_api_url only on one server so that only one set of Boomi API calls is made. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply missing value.'
        )

    # BAD CONFIG: Missing the the Boomi account id while boomi_api_url present
    try:
        c.check(
            {
                'dd_api_key': 'some DD key',
                'boomi_api_url': 'https://api.boomi.com',
                'boomi_api_userid': 'foo',
                'boomi_api_token': 'bar',
            }
        )
    except Exception as e:
        assert (
            e.__str__()
            == 'Configuration error.  Value of boomi_api_url present but boomi_account_id is missing. \
Populate boomi_api_url only on one server so that only one set of Boomi API calls is made. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply missing value.'
        )

    # BAD CONFIG: Missing the the Boomi install dir
    try:
        c.check(
            {
                'dd_api_key': 'some DD key',
                'boomi_api_url': 'https://api.boomi.com',
                'boomi_api_userid': 'foo',
                'boomi_api_token': 'bar',
                'boomi_account_id': 'some account id',
            }
        )
    except Exception as e:
        assert (
            e.__str__()
            == "Configuration error.  Value of boomi_atom_or_molecule_install_dir is missing. Please \
edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply this value."
        )

    # BAD CONFIG: Missing the the seconds of lag
    try:
        c.check(
            {
                'dd_api_key': 'some DD key',
                'boomi_api_url': 'https://api.boomi.com',
                'boomi_api_userid': 'foo',
                'boomi_api_token': 'bar',
                'boomi_account_id': 'some account id',
                'boomi_atom_or_molecule_install_dir': 'some disk path',
            }
        )
    except Exception as e:
        assert (
            e.__str__()
            == "Configuration error.  Value of seconds_of_lag is missing. Please \
edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply this value."
        )

    # BAD CONFIG: Missing Min. Collection Interval
    try:
        c.check(
            {
                'dd_api_key': 'some DD key',
                'boomi_api_url': 'https://api.boomi.com',
                'boomi_api_userid': 'foo',
                'boomi_api_token': 'bar',
                'boomi_account_id': 'some account id',
                'boomi_atom_or_molecule_install_dir': 'some disk path',
                'seconds_of_lag': 60,
            }
        )
    except Exception as e:
        assert (
            e.__str__()
            == 'Configuration error.  Value of min_boomi_api_interval is missing. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply this value. Value \
must be 300 or greater, which lets the Datadog Agent call Boomi Platform APIs every 5 minutes or less frequently.  \
It is not supported to call Boomi Platform APIs more frequently than every 5 minutes.'
        )

    # BAD CONFIG: Min. Collection Interval not an integer
    try:
        c.check(
            {
                'dd_api_key': 'some DD key',
                'boomi_api_url': 'https://api.boomi.com',
                'boomi_api_userid': 'foo',
                'boomi_api_token': 'bar',
                'boomi_account_id': 'some account id',
                'boomi_atom_or_molecule_install_dir': 'some disk path',
                'seconds_of_lag': 60,
                'min_boomi_api_interval': '60q',
            }
        )
    except Exception as e:
        assert (
            e.__str__()
            == 'Configuration error.  Value of min_boomi_api_interval is not an integer. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to correct this. \
Value must be 300 or greater, which lets the Datadog Agent call Boomi Platform APIs every 5 minutes or \
less frequently.  It is not supported to call Boomi Platform APIs more frequently than \
every 5 minutes.'
        )

    # BAD CONFIG: Min. Collection Interval too low
    try:
        c.check(
            {
                'dd_api_key': 'some DD key',
                'boomi_atom_or_molecule_install_dir': 'some disk path',
                'seconds_of_lag': 60,
                'min_boomi_api_interval': 60,
            }
        )
    except Exception as e:
        assert (
            e.__str__()
            == 'Configuration error.  Value of min_boomi_api_interval is too low. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to increase this value. \
Value must be 300 or greater, which lets the Datadog Agent call Boomi Platform APIs every 5 minutes or \
less frequently.  It is not supported to call Boomi Platform APIs more frequently than \
every 5 minutes.'
        )

    # BAD CONFIG: Configured both as API Gateway and Molecule node
    try:
        c.check(
            {
                'dd_api_key': 'some DD key',
                'boomi_atom_or_molecule_install_dir': 'some disk path',
                'seconds_of_lag': 60,
                'min_boomi_api_interval': 600,
                'boomi_molecule_node_id': 'some id',
                'boomi_api_gateway_node_id': 'some id',
            }
        )
    except Exception as e:
        assert (
            e.__str__()
            == 'Configuration error.  Both boomi_api_gateway_node_id and boomi_molecule_node_id \
are populated.  Only one of these must be populated, or neither.'
        )

    # BAD CONFIG: Incomplete API Gateway node config
    try:
        c.check(
            {
                'dd_api_key': 'some DD key',
                'boomi_atom_or_molecule_install_dir': 'some disk path',
                'seconds_of_lag': 60,
                'min_boomi_api_interval': 600,
                'boomi_api_gateway_node_id': 'some id',
            }
        )
    except Exception as e:
        assert (
            e.__str__()
            == 'Configuration error.  boomi_api_gateway_node_id is populated but \
boomi_api_gateway_install_dir is blank.  If this server is an API Gateway node, \
please populate both of these values.'
        )


@pytest.mark.integration
# @pytest.mark.usefixtures('dd_environment')
def test_service_check(aggregator, instance):

    ################################
    # Test requires some secrets
    dd_api_key = "anything"
    boomi_api_userid = "anything"
    boomi_api_token = "anything"
    boomi_account_id = "anything"

    # Integration needs to read/write to the filesystem.
    # Make some folders in the system temp dir
    tmpdir = tempfile.gettempdir()
    try:
        os.mkdir(os.path.join(tmpdir, "atom"))
    except FileExistsError:
        pass
    try:
        os.mkdir(os.path.join(tmpdir, "gateway"))
    except FileExistsError:
        pass
    try:
        os.mkdir(os.path.join(tmpdir, "atom", "conf"))
    except FileExistsError:
        pass
    try:
        os.mkdir(os.path.join(tmpdir, "atom", "work"))
    except FileExistsError:
        pass
    try:
        os.mkdir(os.path.join(tmpdir, "atom", "bin"))
    except FileExistsError:
        pass
    try:
        os.mkdir(os.path.join(tmpdir, "atom", "bin", "views"))
    except FileExistsError:
        pass
    try:
        os.mkdir(os.path.join(tmpdir, "gateway", "bin"))
    except FileExistsError:
        pass
    try:
        os.mkdir(os.path.join(tmpdir, "gateway", "conf"))
    except FileExistsError:
        pass
    try:
        os.mkdir(os.path.join(tmpdir, "gateway", "bin", "views"))
    except FileExistsError:
        pass

    # Make the integration use these dirs.
    boomi_atom_or_molecule_install_dir = os.path.join(tmpdir, "atom")
    boomi_api_gateway_install_dir = os.path.join(tmpdir, "gateway")

    # Create files that integration expects to exist.
    filepath = os.path.join(boomi_atom_or_molecule_install_dir, "conf", "container.id")
    f = open(filepath, "w")
    f.write("com.boomi.container.id=atom_container_id\ncom.boomi.container.account=kitepipedev-BHRF6P")
    f.close()
    filepath = os.path.join(boomi_api_gateway_install_dir, "conf", "container.id")
    f = open(filepath, "w")
    f.write("com.boomi.container.id=api_gateway_container_id\ncom.boomi.container.account=kitepipedev-BHRF6P")
    f.close()
    filepath = os.path.join(boomi_atom_or_molecule_install_dir, "work", LAST_END_DATETIME_FILENAME)
    f = open(filepath, "w")
    f.write("2022-12-31T19:28:03")
    f.close()
    filepath = os.path.join(boomi_atom_or_molecule_install_dir, "bin", "views", "node.10_10_0_2.dat")
    f = open(filepath, "w")
    f.write("nothing here")
    f.close()
    filepath = os.path.join(boomi_atom_or_molecule_install_dir, "bin", "views", "node.10_10_0_3.dat")
    f = open(filepath, "w")
    f.write("nothing here")
    f.close()
    filepath = os.path.join(boomi_api_gateway_install_dir, "bin", "views", "node.10_10_1_2.dat")
    f = open(filepath, "w")
    f.write("nothing here\nalso nothing here\nproblem=ROLLING_RESTART_MULTIPLE_HEAD_NODES\nmaybe more stuff")
    f.close()
    filepath = os.path.join(boomi_api_gateway_install_dir, "bin", "views", "node.10_10_1_3.dat")
    f = open(filepath, "w")
    f.write("nothing here")
    f.close()

    #################################
    # Create an instance of our Check
    c = BoomiWatchCheck('kitepipe_boomiwatch', {}, [instance])

    ####################################
    # Run the check with early_exit_001.
    # In this test...
    #   Config should get validated
    #   Datetime range should get set up
    #   Boomi API calls should get permitted
    #   Last End Datetime should get persisted
    c.check(
        {
            'dd_api_key': dd_api_key,
            'boomi_api_url': 'http://localhost:8000',
            'boomi_api_userid': boomi_api_userid,
            'boomi_api_token': boomi_api_token,
            'boomi_account_id': boomi_account_id,
            'boomi_atom_or_molecule_install_dir': boomi_atom_or_molecule_install_dir,
            'seconds_of_lag': 60,
            'min_boomi_api_interval': 300,
            'early_exit_001': True,
        }
    )
    aggregator.assert_service_check(__NAMESPACE__ + 'config_validated', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'datetime_range_set_up', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'boomi_api_calls_permitted', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'persisted_end_datetime', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'boomi_daemon_running', BoomiWatchCheck.CRITICAL)

    ###################################
    # Pause 5 seconds and run the check
    # In this test...
    #    Boomi API calls should NOT get permitted
    #    View file should NOT be checked
    time.sleep(5)
    c.check(
        {
            'dd_api_key': dd_api_key,
            'boomi_api_url': 'http://does_not_matter',
            'boomi_api_userid': boomi_api_userid,
            'boomi_api_token': boomi_api_token,
            'boomi_account_id': boomi_account_id,
            'boomi_atom_or_molecule_install_dir': boomi_atom_or_molecule_install_dir,
            'seconds_of_lag': 60,
            'min_boomi_api_interval': 300,
        }
    )
    aggregator.assert_service_check(__NAMESPACE__ + 'skipping_boomi_api_calls', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'skipped_molecule_view_file', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'skipped_api_gateway_view_file', BoomiWatchCheck.OK)

    ########################################################
    # Run the check with no early exit.
    # In this test...
    #   Boomi Executions should be queried
    #   Boomi Executions should be found (multiple pages)
    #   Stashed execution IDs should be queried.
    #   Stashed execution ID queries should return data (multiple pages)
    #   Execution metrics should be submitted
    #   Execution logs should be submitted
    #   Molecule view files should be checked

    #   Stash some execution IDs so that Agent will try to query Boomi API for them
    c.write_persistent_cache("in_progress_execution_ids", "execID_1,execID_2")

    # Don't actually call Boomi API... use mock instead.
    with mock.patch('tests.test_kitepipe_boomiwatch.BoomiWatchCheck.http') as mock_http:
        # Here we supply our own "post()" and "get()" methods that will read from disk
        # instead of calling Boomi API.
        mock_http.post = mock_post
        mock_http.get = mock_get
        c.check(
            {
                'dd_api_key': dd_api_key,
                'boomi_api_url': 'http://does_not_matter',
                'boomi_api_userid': boomi_api_userid,
                'boomi_api_token': boomi_api_token,
                'boomi_account_id': boomi_account_id,
                'boomi_atom_or_molecule_install_dir': boomi_atom_or_molecule_install_dir,
                'seconds_of_lag': 60,
                'min_boomi_api_interval': 300,
                'force_boomi_api_calls': True,
                'boomi_molecule_node_id': '10_10_0_2',
            }
        )
    aggregator.assert_service_check(__NAMESPACE__ + 'queried_boomi_executions', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'found_boomi_executions', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'submitted_execution_metrics', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'submitted_execution_logs', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'queried_boomi_auditlogs', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'found_boomi_auditlogs', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'submitted_auditlog_events', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'queried_boomi_events', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'found_boomi_events', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'runtime_reported_online', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'runtime_reported_online', BoomiWatchCheck.CRITICAL)
    aggregator.assert_service_check(__NAMESPACE__ + 'submitted_boomievent_events', BoomiWatchCheck.OK)
    aggregator.assert_service_check(__NAMESPACE__ + 'checked_molecule_view_file', BoomiWatchCheck.OK)
    aggregator.assert_service_check(
        __NAMESPACE__ + 'longrunning_execution_failed_metric_submission', BoomiWatchCheck.WARNING
    )

    ########################################################
    # Run the check with no early exit.
    # In this test...
    #   API Gateway view files should be checked
    c.check(
        {
            'dd_api_key': dd_api_key,
            'boomi_atom_or_molecule_install_dir': boomi_atom_or_molecule_install_dir,
            'seconds_of_lag': 60,
            'min_boomi_api_interval': 300,
            'boomi_api_gateway_node_id': '10_10_1_2',
            'boomi_api_gateway_install_dir': boomi_api_gateway_install_dir,
        }
    )
    aggregator.assert_service_check(__NAMESPACE__ + 'checked_api_gateway_view_file', BoomiWatchCheck.OK)

    ########################################################
    # Run the check with early exit 000.
    # In this test...
    #   Datetime range should be set up.
    #   Last End Datetime should be persisted.
    # Setup: wipe the "last end datetime" file.
    last_end_datetime_path = os.path.join(boomi_atom_or_molecule_install_dir, "work", LAST_END_DATETIME_FILENAME)
    f = open(last_end_datetime_path, "w")
    f.truncate()
    f.close()
    c.check(
        {
            'dd_api_key': dd_api_key,
            'boomi_api_url': 'http://localhost:8000',
            'boomi_api_userid': boomi_api_userid,
            'boomi_api_token': boomi_api_token,
            'boomi_account_id': boomi_account_id,
            'boomi_atom_or_molecule_install_dir': boomi_atom_or_molecule_install_dir,
            'seconds_of_lag': 60,
            'min_boomi_api_interval': 300,
            'early_exit_000': True,
        }
    )
    aggregator.assert_service_check(__NAMESPACE__ + 'used_default_last_end_datetime', BoomiWatchCheck.WARNING)

    # Verify metrics
    aggregator.assert_metric("kitepipe.boomiwatch.boomi_api_calls_attempted")
    aggregator.assert_metric("kitepipe.boomiwatch.execution.measure.duration")
    aggregator.assert_metric("kitepipe.boomiwatch.execution.measure.inboundDocumentCount")
    aggregator.assert_metric("kitepipe.boomiwatch.execution.measure.inboundDocumentSize")
    aggregator.assert_metric("kitepipe.boomiwatch.execution.measure.inboundErrorDocumentCount")
    aggregator.assert_metric("kitepipe.boomiwatch.execution.measure.outboundDocumentCount")
    aggregator.assert_metric("kitepipe.boomiwatch.execution.measure.outboundDocumentSize")
    aggregator.assert_metric("kitepipe.boomiwatch.execution.measure.inProgressExecutionDuration")
    aggregator.assert_metric("kitepipe.boomiwatch.execution.status")
    aggregator.assert_metric("kitepipe.boomiwatch.view_file_age_seconds")
    aggregator.assert_metric("kitepipe.boomiwatch.view_file_exist")
    aggregator.assert_metric("kitepipe.boomiwatch.view_file_problem")
    aggregator.assert_metric("kitepipe.boomiwatch.integration_completed")
    aggregator.assert_metric("datadog.marketplace.kitepipe.boomiwatch")

    aggregator.assert_all_metrics_covered()
