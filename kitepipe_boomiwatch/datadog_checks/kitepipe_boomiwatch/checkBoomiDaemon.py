# import libraries
import platform
import re
import subprocess

import psutil

# import local code
from .globals import __NAMESPACE__


def checkBoomiDaemon(self, instance, boomi_install_dir):

    # Interrogates OS to find out if Boomi daemon is running
    # INPUTS:
    # instance...           Caller passes its instance.
    # boomi_install_dir...  If running on Linux, this proc will look for boomi_install_dir
    #                       as a substring of `ps -ef` to judge whether Boomi daemon is
    #                       running on this box.
    #
    # OUTPUTS:
    # boolean indicating that Boomi daemon is running or not,
    # or None if overall failure to check Boomi daemon.

    ###############
    # Begin the log
    self.log.debug("Entered checkBoomiDaemon.")

    ###########################
    # Bifurcate according to OS
    our_os = platform.system()

    #####################################################################
    # If anything below errors out, we simply write a warning to the log.
    try:
        if our_os == "Windows":
            # OS is Windows
            # Iterate over the windows services
            for windows_service in psutil.win_service_iter():
                # Get the path of the executing binary
                binpath = windows_service.binpath()

                # Check if this path looks like a Boomi runtime.
                found = re.search('\\\\bin\\\\atom\\.exe', binpath)
                if found:
                    # We assume we found a Windows service running a Boomi runtime.
                    # Get the status
                    service_status = windows_service.status()
                    # Get the name
                    service_name = windows_service.name()

                    # Output the service_check with the info we have gathered
                    self.service_check(
                        __NAMESPACE__ + 'boomi_daemon_running',
                        self.OK if service_status == "running" else self.CRITICAL,
                        tags=[
                            "service_check:true",
                            "boomi_daemon_name:" + service_name,
                            "boomi_daemon_binpath:" + binpath,
                            "boomi_daemon_status:" + service_status,
                        ],
                    )

                    #######################################
                    # Let caller know the daemon is running
                    return True
            ###########################################
            # Output the service_check to show Boomi daemon NOT running
            self.service_check(
                __NAMESPACE__ + 'boomi_daemon_running',
                self.CRITICAL,
                tags=[
                    "service_check:true",
                    "boomi_daemon_name:unknown",
                    "boomi_daemon_binpath:unknown",
                    "boomi_daemon_status:not_running",
                ],
            )  # Let caller know the daemon is NOT running
            return False

        else:
            # Here we assume OS is linux-like
            # Get all process state into a string
            b_all_ps = subprocess.check_output(['ps', '-ef'])
            all_ps = b_all_ps.decode("utf-8")

            # Search this string for the boomi_install_dir
            found = re.search(' (' + boomi_install_dir + '.*?([^/ ]+)) ', all_ps)
            if found:
                # Boomi must be running on this box.

                # Get the name of the executable
                service_name = found.group(2)
                # Get the path of the executable
                binpath = found.group(1)

                # Output the service_check with the info we have gathered
                self.service_check(
                    __NAMESPACE__ + 'boomi_daemon_running',
                    self.OK,
                    tags=[
                        "service_check:true",
                        "boomi_daemon_name:" + service_name,
                        "boomi_daemon_binpath:" + binpath,
                        "boomi_daemon_status:running",
                    ],
                )

                #######################################
                # Let caller know the daemon is running
                return True
            else:
                # Output the service_check to show Boomi daemon NOT running
                self.service_check(
                    __NAMESPACE__ + 'boomi_daemon_running',
                    self.CRITICAL,
                    tags=[
                        "service_check:true",
                        "boomi_daemon_name:unknown",
                        "boomi_daemon_binpath:unknown",
                        "boomi_daemon_status:not_running",
                    ],
                )

                ###########################################
                # Output the service_check to show Boomi daemon NOT running
                self.service_check(
                    __NAMESPACE__ + 'boomi_daemon_running',
                    self.CRITICAL,
                    tags=[
                        "service_check:true",
                        "boomi_daemon_name:unknown",
                        "boomi_daemon_binpath:unknown",
                        "boomi_daemon_status:not_running",
                    ],
                )
                # Let caller know the daemon is NOT running
                return False

    except Exception as e:
        ################
        # Log a warning
        msg = 'Failure when interrogating OS to see if Boomi daemon/service is running: ' + str(e)
        self.warning(msg)
        # Output the service_check to show Boomi daemon NOT running
        self.service_check(
            __NAMESPACE__ + 'boomi_daemon_running',
            self.CRITICAL,
            tags=[
                "service_check:true",
                "boomi_daemon_name:unknown",
                "boomi_daemon_binpath:unknown",
                "boomi_daemon_status:not_running",
            ],
        )
        # Let caller know that we failed to perform this task
        return None
