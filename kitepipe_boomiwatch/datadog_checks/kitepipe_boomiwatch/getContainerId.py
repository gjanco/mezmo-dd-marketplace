# import libraries
import re
from os.path import join

from datadog_checks.base import ConfigurationError


def getContainerId(self, install_dir):

    # Looks for "container.id" file in install dir and extracts container ID
    # INPUTS:
    # install_dir...        This plus /conf/ is where the container.id file lives
    #
    # OUTPUTS:
    # container_id...       Container Id value from file.

    ###############
    # Begin the log
    self.log.debug("Entered getContainerId.")

    try:
        # Calculate the target directory
        container_id_file_path = join(install_dir, "conf", "container.id")

        ###################
        # Get file contents
        with open(container_id_file_path, 'r') as container_id_file_handle:
            container_id_file_contents = container_id_file_handle.readlines()

        ##############################
        # Iterate over lines in file.
        for line in container_id_file_contents:
            # Is this the line with container ID?
            found = re.search("^com\\.boomi\\.container\\.id=(.*)$", line)
            if found:
                # Found the correct line in the file.
                # Parse out the container ID
                container_id = found.group(1)
                # We got what we need; quit.
                msg = "Got container ID " + container_id
                self.log.debug(msg)
                return container_id

    except Exception as e:
        # We couldn't get the container ID
        # Build an error message
        msg = (
            'Configuration error.  Failed to get container id from installation directory `'
            + install_dir
            + '`. Error message: '
            + str(e)
            + '\n\nCheck if Boomi is installed in this directory and if the directory is readable by dd-agent user.'
        )
        # Show the error message.
        self.log.error(msg)
        # Throw config error
        raise ConfigurationError(msg)
