# import libraries
from datadog_checks.base import ConfigurationError


def verifyConfig(self, instance):

    # Checks if required config values are established.
    # INPUTS:
    # instance...           Instance passed from parent
    #
    # OUTPUTS:
    # dd_api_key...             Value from conf.yaml
    # boomi_api_url...          Value from conf.yaml
    # boomi_api_userid...       Value from conf.yaml
    # boomi_api_token...        Value from conf.yaml
    # boomi_account_id...       Value from conf.yaml
    # boomi_atom_or_molecule_install_dir... Value from conf.yaml
    # seconds_of_lag...         Value from conf.yaml
    # min_boomi_api_interval... Value from conf.yaml
    # boomi_node_id...          Either molecule or api gateway node ID from conf.yaml
    # boomi_role...             molecule or api_gateway, depending on which type
    #                           of node id was populated in conf.yaml

    # Begin the log
    self.log.debug("Entered verifyConfig.")

    # Get environment variables.
    # Datadog API Key
    dd_api_key = instance.get('dd_api_key')
    # Boomi AtomSphere API URL
    boomi_api_url = instance.get('boomi_api_url')
    # AtomSphere API user ID
    boomi_api_userid = instance.get('boomi_api_userid')
    # AtomSphere API user token
    boomi_api_token = instance.get('boomi_api_token')
    # AtomSphere account ID
    boomi_account_id = instance.get('boomi_account_id')
    # Boomi installation directory
    boomi_atom_or_molecule_install_dir = instance.get('boomi_atom_or_molecule_install_dir')
    # Seconds of lag
    seconds_of_lag = instance.get('seconds_of_lag')
    # Molecule Node ID
    boomi_molecule_node_id = instance.get('boomi_molecule_node_id')
    # API Gateway Node ID
    boomi_api_gateway_node_id = instance.get('boomi_api_gateway_node_id')
    # API Gateway installation directory
    boomi_api_gateway_install_dir = instance.get('boomi_api_gateway_install_dir')

    # Did we get all the required environment variables?
    if not dd_api_key:
        raise ConfigurationError(
            'Configuration error.  Value of dd_api_key is missing. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply this value.'
        )
    if boomi_api_url and not boomi_api_userid:
        raise ConfigurationError(
            'Configuration error.  Value of boomi_api_url present but boomi_api_userid is missing. \
Populate boomi_api_url only on one server so that only one set of Boomi API calls is made. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply missing value.'
        )
    if boomi_api_url and not boomi_api_token:
        raise ConfigurationError(
            'Configuration error.  Value of boomi_api_url present but boomi_api_token is missing. \
Populate boomi_api_url only on one server so that only one set of Boomi API calls is made. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply missing value.'
        )
    if boomi_api_url and not boomi_account_id:
        raise ConfigurationError(
            'Configuration error.  Value of boomi_api_url present but boomi_account_id is missing. \
Populate boomi_api_url only on one server so that only one set of Boomi API calls is made. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply missing value.'
        )
    if not boomi_atom_or_molecule_install_dir:
        raise ConfigurationError(
            'Configuration error.  Value of boomi_atom_or_molecule_install_dir is missing. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply this value.'
        )
    if not seconds_of_lag:
        raise ConfigurationError(
            'Configuration error.  Value of seconds_of_lag is missing. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply this value.'
        )

    # Check the Minimum Collection Interval.  Does it exist?
    min_boomi_api_interval = instance.get('min_boomi_api_interval')
    if not min_boomi_api_interval:
        raise ConfigurationError(
            'Configuration error.  Value of min_boomi_api_interval is missing. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to supply this value. \
Value must be 300 or greater, which lets the Datadog Agent call Boomi Platform APIs every 5 minutes or \
less frequently.  It is not supported to call Boomi Platform APIs more frequently than \
every 5 minutes.'
        )
    # Is it an integer?
    try:
        _ = int(min_boomi_api_interval)
    except ValueError as ve:
        _ = ve
        raise ConfigurationError(
            'Configuration error.  Value of min_boomi_api_interval is not \
an integer. Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to correct this. \
Value must be 300 or greater, which lets the Datadog Agent call Boomi Platform APIs every 5 minutes or \
less frequently.  It is not supported to call Boomi Platform APIs more frequently than \
every 5 minutes.'
        )
    # Is the agent going to perform the check "too often"?
    # "Too often" is more frequently than 5 minutes.
    if int(min_boomi_api_interval) < 300:
        raise ConfigurationError(
            'Configuration error.  Value of min_boomi_api_interval is too low. \
Please edit datadog-agent/conf.d/kitepipe_boomiwatch.d/conf.yaml to increase this value. \
Value must be 300 or greater, which lets the Datadog Agent call Boomi Platform APIs every 5 minutes or \
less frequently.  It is not supported to call Boomi Platform APIs more frequently than \
every 5 minutes.'
        )

    # Is this configured as both an API Gateway and a Molecule node?
    if boomi_api_gateway_node_id is not None and boomi_molecule_node_id is not None:
        raise ConfigurationError(
            'Configuration error.  Both boomi_api_gateway_node_id and boomi_molecule_node_id \
are populated.  Only one of these must be populated, or neither.'
        )

    # If configured as API Gateway node, must also populate boomi_api_gateway_install_dir
    if boomi_api_gateway_node_id is not None and boomi_api_gateway_install_dir is None:
        raise ConfigurationError(
            'Configuration error.  boomi_api_gateway_node_id is populated but \
boomi_api_gateway_install_dir is blank.  If this server is an API Gateway node, \
please populate both of these values.'
        )

    # If we reached here, config is OK.

    # Check if this server is a Molecule or an API Gateway
    # so we can return boomi_role and boomi_node_id values.
    if boomi_api_gateway_node_id is not None:
        boomi_role = "api_gateway"
        boomi_node_id = boomi_api_gateway_node_id
    else:
        if boomi_molecule_node_id is not None:
            boomi_role = "molecule"
            boomi_node_id = boomi_molecule_node_id
        else:
            boomi_role = "unknown"
            boomi_node_id = "unknown"

    # Return values to caller.
    return (
        dd_api_key,
        boomi_api_url,
        boomi_api_userid,
        boomi_api_token,
        boomi_account_id,
        boomi_atom_or_molecule_install_dir,
        seconds_of_lag,
        min_boomi_api_interval,
        boomi_node_id,
        boomi_role,
    )
