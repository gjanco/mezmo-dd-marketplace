# import libraries
import datetime
import re
from os.path import exists, getmtime, join

# import local code
from .globals import __NAMESPACE__


def checkBoomiNodeViewFile(self, instance, ar1, ar2, boomi_runtime_type):

    # Rename args
    boomi_install_dir = ar1
    cluster_node_id = ar2
    # Looks for and evaluates Boomi cluster "view" files
    # INPUTS:
    # instance...           Caller passes its instance.
    # boomi_install_dir...  This plus /bin/views is where the cluster view
    #                       files live.
    # cluster_node_id...    Boomi cluster node ID from the .conf file so
    #                       that this server knows its node_id.
    # boomi_runtime_type... 'api_gateway' or 'molecule'; used as metric tag.
    #
    # OUTPUTS:
    # boolean indicating success or failure

    ###############
    # Begin the log
    self.log.debug("Entered checkBoomiNodeViewFile.")

    try:

        ###################################
        # Calculate the view file directory
        view_file_dir = join(boomi_install_dir, "bin", "views")

        ############
        # Build path
        expected_file_name = "node." + cluster_node_id + ".dat"
        view_file_path = join(view_file_dir, expected_file_name)

        ################################
        # Calculate if view file exists.
        view_file_exists = exists(view_file_path)

        #############################
        # Build tags for this metric.
        metricTags = [
            "cluster_node_id:" + cluster_node_id,
            "cluster_node_role:" + boomi_runtime_type,
        ]

        ###############################
        # Record existence or otherwise
        if view_file_exists:
            # Report file existence as metric
            self.gauge(__NAMESPACE__ + "view_file_exist", 1, metricTags)
            msg = "View file exists for node: " + cluster_node_id
            self.log.debug(msg)
        else:
            # Report file non-existence as metric
            self.gauge(__NAMESPACE__ + "view_file_exist", 0, metricTags)
            msg = "View file missing for node: " + cluster_node_id
            self.log.debug(msg)

        ###################
        # Get file contents
        with open(view_file_path, 'r') as view_file_handle:
            view_file_contents = view_file_handle.readlines()

        ###############
        # Get file time
        view_file_time = getmtime(view_file_path)

        #########################
        # Get file age in seconds
        dt1 = datetime.datetime.utcnow()
        dt2 = datetime.datetime.fromtimestamp(view_file_time)
        view_file_age = (dt1 - dt2).total_seconds()

        #############################################
        # Calculate if "problem" appears in view file
        vfpe = 'PROBLEM' in ' '.join(map(str.upper, view_file_contents))
        view_file_problem_exists = vfpe
        problem_string = 'none'
        # Iterate over lines in file.
        for line in view_file_contents:
            # Does this line show a "problem"?
            found = re.search("^problem=(.+)$", line)
            if found:
                # Save the problem string
                problem_string = found.groups()[0]
                # Stop looking
                break

        ##########################
        # Report view file metrics
        metricTags = [
            "cluster_node_id:" + cluster_node_id,
            "cluster_node_role:" + boomi_runtime_type,
            "cluster_problem:" + problem_string,
        ]
        st = __NAMESPACE__ + "view_file_age_seconds"
        self.gauge(st, view_file_age, metricTags)
        msg = "View file age: " + str(view_file_age)
        self.log.debug(msg)
        st = __NAMESPACE__ + "view_file_problem"
        self.gauge(st, int(view_file_problem_exists), metricTags)
        msg = "View file problem: " + problem_string
        self.log.debug(msg)

        ##########################
        # Report success to caller
        return True

    except Exception as e:
        ################
        # Log a warning
        msg = (
            'Failed to check Boomi cluster view file. Please ensure the \
cluster Node ID is accurate in \
datadog-agent/conf.d/kitepipe_atomwatch.d/conf.yaml and restart Datadog \
agent.  Node IDs can change during Node restarts.  Also please ensure \
dd-agent user has access to read Boomi cluster view files.  Error details: '
            + str(e)
        )
        self.warning(msg)
        # Let caller know that Boomi node view file was NOT checked
        return False
