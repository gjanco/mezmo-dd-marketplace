try:
    from datadog_checks.base import AgentCheck, is_affirmative, ConfigurationError
except ImportError:
    from checks import AgentCheck
import os
import yaml
from .datadog import initialize, api

IGNORE_APPS = {
    "alb",
    "elb",
    "nlb",
    "rds"
}


def get_config(key):
    config_file_name = "datadog.yaml"
    platform = os.name
    # Windows
    if platform == "nt":
        path = "%ProgramData%" + "\\" + "Datadog" + "\\"
    # Mac/Linux/BSD
    elif platform == "posix":
        path = "/etc/datadog-agent/"
    result = None
    for root, dirs, files in os.walk(path):
        if config_file_name in files:
            result = os.path.join(root, config_file_name)
            break

    if result:
        config_yaml = open(result)
        parsed_yaml = yaml.load(config_yaml, Loader=yaml.FullLoader)

        return parsed_yaml[key]
    else:
        raise Exception("No configuration file %s found. Please try again with a valid configuration file.",
                        config_file_name)


class ValidatorCheck(AgentCheck):
    def __init__(self,*args, **kwargs):
        super(ValidatorCheck, self).__init__(*args, **kwargs)
        self.options = {
            "api_key": get_config("api_key"),
            "app_key": self.init_config.get("app_key")
        }
        self.yaml_tag_dict = yaml.load(str(self.instance.get("required_tags")))
        self.ignore_paas = is_affirmative(self.instance.get("ignore_paas", False))
        self.ignore_hosts = set(self.instance.get("hosts_to_ignore", []))
        self.metric_prefix = "rapdev.validator"
        self.set_proxies()
        self.check_initializations.append(self.validate_config)

    def check(self, instance):
        initialize(**self.options)
        self.log.debug("Attempting to grab the total number of active hosts from your Datadog account....")

        total_hosts = api.Hosts.totals().get('total_active')
        
        # Try to run the main functions. Raises an exception and failing service check if the API doesn't return hosts
        n = 0
        while n < total_hosts:
            response = api.Hosts.search(start=n, count=1000)
            self.host_list = response["host_list"]
            for host in self.host_list:
                if host["name"].lower() not in self.ignore_hosts:
                    self.validate_agent(host)
                    if not self.ignore_paas:
                        self.validate_tags(host)
                    elif self.ignore_paas and not set(host["apps"]).intersection(IGNORE_APPS):
                        self.validate_tags(host)

                n += 1

    # This function validates the tag keys and their values for the host being checked
    def validate_tags(self, host):
        metric_tags = []
        host_tag_list = []
        tag_source_list = host["tags_by_source"]
        hostname = host["name"]
        metric_tags.append("validated_host:{}".format(hostname))
        
        self.gauge("{}.host.checked".format(self.metric_prefix), 1, tags=metric_tags, hostname=None)
        
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
            self.gauge("{}.host.keys_checked".format(self.metric_prefix), 1,  tags=metric_tags, hostname=None)
            key_tags = metric_tags.copy()
            key_tags.append("tag_key:{}".format(key_lower))

            # Check if the key outlined as required in the YAML is assigned to the host being checked
            if key_lower not in host_tag_dict.keys():
                key_list.append(False)
                self.service_check("{}.tag.key_validator".format(self.metric_prefix), AgentCheck.CRITICAL,  tags=key_tags, hostname=None)
                self.gauge("{}.tag.missing_key".format(self.metric_prefix), 1,  tags=key_tags, hostname=None)
            
            # Only submits tag value based metrics if the key is found on the host
            else:
                key_list.append(True)
                self.service_check("{}.tag.key_validator".format(self.metric_prefix), AgentCheck.OK,  tags=key_tags, hostname=None)
                self.gauge("{}.tag.missing_key".format(self.metric_prefix), 0,  tags=key_tags, hostname=None)
                value_tags = metric_tags.copy()
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
                value_tags.append("tag_key:{}".format(key_lower))
                value_tags.append("tag_value:{}".format(host_tag_dict.get(key_lower)))

                # Validates if this key contains any of the allowed values from the YAML
                if any(validator_dict[key_lower]):
                    self.service_check("{}.tag.value_validator".format(self.metric_prefix), AgentCheck.OK,  tags=value_tags, hostname=None)
                    self.gauge("{}.tag.bad_value".format(self.metric_prefix), 0,  tags=value_tags, hostname=None)
                else:
                    self.service_check("{}.tag.value_validator".format(self.metric_prefix), AgentCheck.CRITICAL,  tags=value_tags, hostname=None)
                    self.gauge("{}.tag.bad_value".format(self.metric_prefix), 1,  tags=value_tags, hostname=None)

        # Labels host as good if all keys checked via YAML are present on host
        if all(key_list):
            self.gauge("{}.host.missing_key".format(self.metric_prefix), 0,  tags=metric_tags, hostname=None)
        else:
            self.gauge("{}.host.missing_key".format(self.metric_prefix), 1,  tags=metric_tags, hostname=None)

        # Labels host as good if all keys checked via YAML have allowed values
        # If 1 key is found without any allowed value, host is marked bad
        if had_key:
            self.gauge('{}.host.bad_value_checked'.format(self.metric_prefix), 1,  tags=metric_tags, hostname=None)
            for val_key, val_list in validator_dict.items():
                if any(val_list):
                    self.gauge("{}.host.bad_value".format(self.metric_prefix), 0,  tags=metric_tags, hostname=None)
                else:
                    self.gauge("{}.host.bad_value".format(self.metric_prefix), 1,  tags=metric_tags, hostname=None)
                    break
        else:
            self.gauge("{}.host.bad_value_checked".format(self.metric_prefix), 0,  tags=metric_tags, hostname=None)

    # This function checks if agents are installed on the hosts
    def validate_agent(self, host):
        if not set(host["apps"]).intersection(IGNORE_APPS):
            hostname = host["name"]
            metric_tags = []
            metric_tags.append("validated_host:{}".format(hostname))
            source_list = host["sources"]

            # Checks if agent is present in the source list, and tags the metrics with the version
            if "agent" in source_list:
                metric_tags.append("agent_version:{}".format(host["meta"]["agent_version"]))
                self.service_check("{}.agent.is_installed".format(self.metric_prefix), AgentCheck.OK, tags=metric_tags, hostname=None)
                self.gauge("{}.agent.installed".format(self.metric_prefix), 1, tags=metric_tags, hostname=None)
            else:
                self.service_check("{}.agent.is_installed".format(self.metric_prefix), AgentCheck.CRITICAL, tags=metric_tags, hostname=None)
                self.gauge("{}.agent.installed".format(self.metric_prefix), 0, tags=metric_tags, hostname=None)

    # This functions sets the check to utilize the proxy, if defined in the datadog.yaml
    def set_proxies(self):
        try:
            proxy_config = get_config("proxy")
            if proxy_config:
                http_proxy = proxy_config.get("http", None)
                https_proxy = proxy_config.get("https", None)

                if http_proxy:
                    os.environ["http_proxy"] = http_proxy
                if https_proxy:
                    os.environ["https_proxy"] = https_proxy
            return
        except KeyError:
            self.log.info("No proxy configuration found. Continuing...")

    # This function validates that the required config is present in the conf.yaml
    def validate_config(self):
        if not self.yaml_tag_dict:
            raise ConfigurationError("Please provide a list of required tag keys and values")
        if not self.init_config.get("app_key"):
            raise ConfigurationError("Please provide a Datadog application key in the init_config")
