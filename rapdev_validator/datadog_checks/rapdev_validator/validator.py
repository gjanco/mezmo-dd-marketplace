try:
    from datadog_checks.base import AgentCheck, is_affirmative, ConfigurationError
except ImportError:
    from checks import AgentCheck
import re
import os
import yaml
import json
import traceback
from sys import platform
from requests import HTTPError

IGNORE_APPS = {
    "alb",
    "elb",
    "nlb",
    "rds"
}

REQUIRED_TAGS = []

API_URL = "https://api.datadoghq.com"

class ValidatorCheck(AgentCheck):
    """
    class inherits from AgentCheck class and handles everything regarding the checking of tags on hosts
    in your Datadog environment
    
    attribs:
        org (str): the name of the org (or parent_billing org if in a multi org env) associated with the
                   api key for the current instance
        yaml_tag_dict (dict): dictionary of required tag keys mapped to allowed values as specified in
                              the conf.yaml for this integration
        ignore_paas (bool): default False, pulled in from conf.yaml, set to True to ignore validation for
                            hosts using apps ALB, ELB, NLB, and RDS
        ignore_hosts (list[str]): list of python regexes, pulled in from the conf.yaml, defining patterns
                                  for hostnames to ignore validation on
        metric_prefix (str): static prefix for all metrics submitted to the Datadog api with this integration
    """
    

    __NAMESPACE__ = "rapdev.validator"

    def __init__(self, *args, **kwargs):
        """
        initialization of the class, calls its parent, validates the config and gathers/formats
        required information for the check
        """
        super(ValidatorCheck, self).__init__(*args, **kwargs)
        self.options = self.get_keys()
        self.check_initializations.append(self.validate_config)
        
        self.org = self.get_org(self.options)
        self.yaml_tag_dict = yaml.load(str(self.instance.get("required_tags")))
        self.ignore_paas = is_affirmative(self.instance.get("ignore_paas", False))
        self.ignore_hosts = set(self.instance.get("hosts_to_ignore", []))
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])

    def check(self, _):
        """
        main check loop grabs all of the hosts from the Datadog api, and iterates over them, checking the agent
        and tag information as it goes, and submits its findings to the Datadog api
        """
        self.tags = list(set(self.tags))
        self.log.debug("Attempting to grab the total number of active hosts from your Datadog account....")

        response = self.http.get("{}/api/v1/hosts/totals".format(API_URL), extra_headers=self.options).json()
        total_hosts = response.get("total_active")
        
        # Try to run the main functions. Raises an exception and failing service check if the API doesn't return hosts
        n = 0
        count = 1000
        while n < total_hosts:
            response = self.http.get("{}/api/v1/hosts?start={}&count={}".format(API_URL, n, count), extra_headers=self.options).json()
            host_list = response.get("host_list", [])
            for host in host_list:
                if not self.is_ignored_host(host.get("name")):
                    self.validate_agent(host)
                    if not self.ignore_paas:
                        self.validate_tags(host)
                    elif self.ignore_paas and not set(host["apps"]).intersection(IGNORE_APPS):
                        self.validate_tags(host)
                
                n += 1
    
    def get_config(self, key, passthrough_exceptions=False):
        """
        function to read in the value for a specific key from the main datadog.yaml config file
        
        args:
            key (str): target key to read the value of
            passthrough_exceptions (bool): default False, flag to allow exceptions to bubble up normally instead
                                           of raising a custom exception (used because set_proxy code expects
                                           a KeyError to bubble up)
                                           
        returns:
            (multiple types): returns the parsed out value from the target key. since it's yaml, technically
                              can return str, int, list, or dict depending on the target data. here we're only
                              using it for strings though
                              
        raises:
            (Exception): custom exception is raised if the os platform is not supported, as well as for
                         all other exceptions if passthrough_exceptions is set to False
            (FileNotFoundError): raises this exeption if passthrough_exceptions is True and the datadog.yaml file
                                 can not be found
            (KeyError): raises this exception if passthrough_exceptions is True and the key specified is not present
                        (or commented out) in the main datadog.yaml
        """
        config_file_name = "datadog.yaml"
        # Windows
        if platform == "win32":
            path = os.path.join(os.getenv("PROGRAMDATA"), "Datadog")
        # Linux
        elif platform == "linux" or platform == "linux2":
            path = "/etc/datadog-agent/"
        # Mac
        elif platform == "darwin":
            path = "/opt/datadog-agent/etc/"
        # Unsupported
        else:
            raise Exception("OS Platform {} not supported.".format(platform))
            
        target = os.path.join(path, config_file_name)
        try:
            with open(target, "r") as infile:
                parsed_yaml = yaml.load(infile.read(), Loader=yaml.FullLoader)
                
            return parsed_yaml[key]
            
        # catching all exeptions and then filtering on type instead of catching each exception
        # separately to reduce copied code
        except Exception as e:
            exception_text = "Unexpected exception when retrieving {} from {}: {}".format(key, target, traceback.format_exc())
            
            if type(e) is FileNotFoundError:
                exception_text = "No configuration file {} found. Please try again with a valid configuration file.".format(target)
            elif type(e) is KeyError:
                exception_text = "{} not found in {}. Please make sure the target key is defined properly and uncommented.".format(key, target)
            
            self.log.error(exception_text)
            
            if passthrough_exceptions:
                raise e
            else:
                raise Exception(exception_text)
        
    def get_keys(self):
        """
        function to retrieve the api and app key being used for the current instance
        
        notes:
            - first attempts to retrieve both the api key and app key from the current instance config
            - api key
                - if it is not specified for the current instance it then attempts to retrieve it from the
                  init_config section for the entire integration
                - if the api key is not found in the init_config section, it attempts to grab it from the main
                  datadog.yaml config
                - it should throw an exception at that point if it is still not able to find it, but if
                  it were to reach this point, it will throw a configuration error exception here
            - app key
                - if it is not specified for the current instance it then attempts to retrieve it from the
                  init_config section for the entire integration
                - if it is still not found it will then throw a configuration error exception
            - allowing the user to specify in the init_config section ensures backwards compatibility
              with previous versions of this integration
        
        returns:
            options (dict): dictionary containing the api key, and app key mapped to their proper name for
                            use with the Datadog python library, and its initialize function
                            
        raises:
            (datadog_checks.base.ConfigurationError): raises this exception if it is not able to determine either
                                                      the api key, or app key, for the current instance
        """
        api_key = self.instance.get("api_key", False) # default to instance based api key
        app_key = self.instance.get("app_key", False) # default to instance based app key
        
        # if no api key specified for instance, grab from init_config
        if not api_key:
            api_key = self.init_config.get("api_key", False)
        # if no api key specified for instance, grab from main datadog.yaml
        if not api_key:
            api_key = self.get_config("api_key")
        # if no api key found and somehow gets here, throw an exception
        # (it should not be able to get here with passthrough_exceptions set to False for get_config)
        if not api_key:
            raise ConfigurationError("No api key found")
            
        # if no app key specfied for instance, grab from init_config
        if not app_key:
            app_key = self.init_config.get("app_key", False)
        # if no app key found throw an exception
        if not app_key:
            raise ConfigurationError("No app key found")
            
        options = {
            "Content-Type": "Application/json",
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key
        }
        
        return options
    
    def validate_config(self):
        """
        This function validates that the required config is present in the conf.yaml
        
        raises:
            (datadog_checks.base.ConfigurationError): raises this exception if any of the checks in the function
                                                      fail, meaning required data is missing from the config(s)
        """
        if not self.yaml_tag_dict:
            raise ConfigurationError("Please provide a list of required tag keys and values")
    
    def obf_text(self, secret_text):
        """
        function to obfuscate text and only display the last 4 characters, except in the case of strings
        that are 8 characters or less, then it obfuscates the entire string. this is used for logging
        which api key retrieving the related org name failed on, without having to write the entire api key
        to the log
        
        args:
            secret_text (str): text to obfuscate
            
        returns:
            (str): text with everything but the last 4 characters obfuscated, except where the string is
                   8 characters or less, then it will be a string of equivalent length only containing astericies
        """
        text_len = len(secret_text)
        
        if text_len <= 8: # probably shouldn't display 4 characters of an 8 char secret string
            return ''.join('*' * text_len)
        else:
            return ''.join('*' * (text_len - 4)) + secret_text[-4:]
    
    def get_org(self, options, retries=3):
        """
        recursive function to retrieve the org name related to the current api/app key being used.
        timeout for each request is hardcoded to 10 seconds. it only needs to retrieve the org name on
        initialization, and is necessary for tagging metrics by org, therefor if this fails all retries
        it throws an uncaught exception, halting the integration
        
        args:
            options (dict): dictionary containing the current instance's api and app key
            retries (int): default 3, number of times to retry getting the org name
            
        returns:
            org_name (str): name of the org associate with the current api/app key. in multi org accounts
                            it will choose the first account it finds marked 'parent_billing' in its billing type
                            
        raises:
            (requests.HTTPError): will raise this if it fails all retries due to an HTTPError, causing the
                                  integration to halt
        """
        try:
            response = self.http.get("{}/api/v1/org".format(API_URL), extra_headers=self.options, timeout=10)
            response.raise_for_status()
            orgs = response.json().get("orgs")
            org_name = None
            
            # use parent_billing for name from multi org accounts
            if len(orgs) > 1:
                for org in orgs:
                    if org.get("billing").get("type") == "parent_billing":
                        org_name = org.get("name")
                        break
            else:
                org_name = orgs[0].get("name")
                
            return org_name
            
        except HTTPError as e:
            self.log.error("Failed retrieving org for api key: {}, retries left: {}".format(self.obf_text(options.get('api_key', "")), retries))
            if retries > 0:
                return self.get_org(options, retries-1)
            else:
                self.log.error("Failed final retry while retrieving org. traceback: {}".format(traceback.format_exc()))
                raise e
                
    def validate_agent(self, host):
        """
        This function checks if agents are installed on the hosts
        
        metrics submitted:
            gauges:
                - {self.metric_prefix}.agent.installed: 1 if the agent is installed, 0 otherwise
                
            agent checks:
                - {self.metric_prefix}.agent.is_installed: AgentCheck.OK if the agent is installed,
                                                           AgentCheck.CRITICAL otherwise
                                                           
        args:
            host (dict): host dictionary containing all relevant host data from the Datadog api, including
                         but not limited to; hostname, and tags
        """
        if not set(host["apps"]).intersection(IGNORE_APPS):
            hostname = host["name"]
            metric_tags = self.tags.copy()
            metric_tags.append("validated_host:{}".format(hostname))
            metric_tags.append("org:{}".format(self.org))
            source_list = host["sources"]

            # Checks if agent is present in the source list, and tags the metrics with the version
            if "agent" in source_list and host['meta'] and 'agent_version' in host['meta'].keys():
                metric_tags.append("agent_version:{}".format(host['meta']['agent_version']))
                self.service_check("agent.is_installed", AgentCheck.OK, tags=metric_tags)
                self.gauge("agent.installed", 1, tags=metric_tags, hostname=None)
            else:
                self.service_check("agent.is_installed", AgentCheck.CRITICAL, tags=metric_tags)
                self.gauge("agent.installed", 0, tags=metric_tags, hostname=None)
    
    def validate_tags(self, host):
        """
        This function validates the tag keys and their values for the host being checked
        
        metrics submitted:
            gauges:
                - {self.metric_prefix}.host.checked: submits 1 for each host that has been checked
                - {self.metric_prefix}.host.keys_checked: submits 1 for each host that has had its tag keys checked
                - {self.metric_prefix}.tag.missing_key: submits 1 for each key missing, otherwise 0 if the key is found
                - {self.metric_prefix}.tag.bad_value: submits 1 if the current key has an invalid value, otherwise 0
                - {self.metric_prefix}.host.missing_key: submits 1 if any of the keys were missing on this host, otherwise 0
                - {self.metric_prefix}.host.bad_value_checked: submits 1 if the host had at least 1 key match, otherwise 0
                - {self.metric_prefix}.host.bad_value: submits 1 if any values for any keys were invalid, otheriwse 0
                
            agent checks:
                - {self.metric_prefix}.tag.key_validator: AgentCheck.OK for each valid key,
                                                          AgentCheck.CRITICAL for each invalid key
                - {self.metric_prefix}.tag.value_validator: AgentCheck.OK for each valid value for a valid key,
                                                            AgentCheck.CRITICAL for each invalid value for a valid key
        
        args:
            host (dict): host dictionary containing all relevant host data from the Datadog api, including
                         but not limited to; hostname, and tags
        """
        hostname = host["name"]
        metric_tags = self.tags.copy()
        metric_tags.append("validated_host:{}".format(hostname))
        metric_tags.append("org:{}".format(self.org))
        host_tag_list = []
        tag_source_list = host["tags_by_source"]
        
        self.gauge("host.checked", 1, tags=metric_tags, hostname=None)
        
        # Create list of all host tags coming into Datadog for this host
        for source in tag_source_list:
            host_tag_list.append(tag_source_list.get(source))
        
        host_tag_dict = {}

        # Split the stringed tags into key:value pairs and create a dictionary
        for tag in host_tag_list:
            for item in tag:
                if ":" in item:
                    key, value = item.split(":", 1)
                    host_tag_dict[key] = value
                else:
                    key, value = item, "NONE"
                    host_tag_dict[key] = value

        validator_dict = {}
        key_list = []
        had_key = False
        # Loop through the keys supplied in the YAML conf
        for key in self.yaml_tag_dict.keys():
            key_lower = key.lower()
            self.gauge("host.keys_checked", 1, tags=metric_tags, hostname=None)
            key_tags = metric_tags.copy()
            key_tags.append("tag_key:{}".format(key_lower))

            # Check if the key outlined as required in the YAML is assigned to the host being checked
            if key_lower not in host_tag_dict.keys():
                key_list.append(False)
                self.service_check("tag.key_validator", AgentCheck.CRITICAL, tags=key_tags)
                self.gauge("tag.missing_key", 1, tags=key_tags, hostname=None)
            
            # Only submits tag value based metrics if the key is found on the host
            else:
                key_list.append(True)
                self.service_check("tag.key_validator", AgentCheck.OK, tags=key_tags)
                self.gauge("tag.missing_key", 0, tags=key_tags, hostname=None)
                value_tags = key_tags.copy()
                had_key = True

                # Create a dictionary to be used to check if the key being checked contains any allowed values
                validator_dict[key_lower] = []
                for key_value in self.yaml_tag_dict.get(key):
                    if key_value == "*":
                        key_value_lower = key_value
                    else:
                        key_value_lower = key_value.lower()
                    if key_value_lower == host_tag_dict.get(key_lower) or key_value_lower == "*":
                        validator_dict[key_lower].append(True)
                        break
                    else:
                        validator_dict[key_lower].append(False)
                value_tags.append("tag_value:{}".format(host_tag_dict.get(key_lower)))

                # Validates if this key contains any of the allowed values from the YAML
                if any(validator_dict[key_lower]):
                    self.service_check("tag.value_validator", AgentCheck.OK, tags=value_tags)
                    self.gauge("tag.bad_value", 0, tags=value_tags, hostname=None)
                else:
                    self.service_check("tag.value_validator", AgentCheck.CRITICAL, tags=value_tags)
                    self.gauge("tag.bad_value", 1, tags=value_tags, hostname=None)

        # Labels host as good if all keys checked via YAML are present on host
        if all(key_list):
            self.gauge("host.missing_key", 0, tags=metric_tags, hostname=None)
        else:
            self.gauge("host.missing_key", 1, tags=metric_tags, hostname=None)

        # Labels host as good if all keys checked via YAML have allowed values
        # If 1 key is found without any allowed value, host is marked bad
        if had_key:
            self.gauge("host.bad_value_checked", 1, tags=metric_tags, hostname=None)
            for val_key, val_list in validator_dict.items():
                if any(val_list):
                    self.gauge("host.bad_value", 0, tags=metric_tags, hostname=None)
                else:
                    self.gauge("host.bad_value", 1, tags=metric_tags, hostname=None)
                    break
        else:
            self.gauge("host.bad_value_checked", 0, tags=metric_tags, hostname=None)
    
    def is_ignored_host(self, hostname):
        """
        function checks if the passed in hostname matches any of the regex for ignored hosts returning
        true if it is an ignored host, and false otherwise. case insensitive regex matching
        
        args:
            hostname (str): hostname to check against ignored host regexes
            
        returns:
            (bool): True if the host matches an ignored host regex (should be ignored), 
                    otherwise False (should be validated)
        """
        for ignored_host_regex in self.ignore_hosts:
            if re.match(ignored_host_regex, hostname, re.I):
                return True
                
        return False
