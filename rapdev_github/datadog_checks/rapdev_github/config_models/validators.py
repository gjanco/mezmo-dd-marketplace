
from os import path
from datadog_checks.base import ConfigurationError

# Here you can include additional config validators or transformers
#
def initialize_instance(values, **kwargs):
    error_list = [] 
    try:
        if 'base_url' not in values:
            error_list += "The Github API URL is required"
        if 'org' not in values:
            error_list += "The name of organization/enterprise is required"
        if 'mode' not in values :
            error_list += "The mode is required"
        if 'key_path' not in values:
            error_list += "The path to the private key is required"
        if 'gh_app_id' not in values:
            error_list += "The GitHub AppID is required"
        if 'org_app_id' not in values:
            error_list += "The Org AppID is required" 
        if 'base_url' in values and 'gh_app_id' in values and 'org_app_id' in values and 'key_path'  in values:
            if not path.exists(values['key_path']):
                error_list += "The private key file path is invalid" 
        if error_list:
            raise ConfigurationError("\n".join(error_list))
    except ConfigurationError as e:
        raise ConfigurationError(f"Please fix the following errors: {e}")
    
    return values
