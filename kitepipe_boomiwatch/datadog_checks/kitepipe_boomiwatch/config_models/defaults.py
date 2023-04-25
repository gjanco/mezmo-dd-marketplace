# This file is autogenerated.
# To change this file you should edit assets/configuration/spec.yaml and then run the following commands:
#     ddev -x validate config -s <INTEGRATION_NAME>
#     ddev -x validate models -s <INTEGRATION_NAME>

from datadog_checks.base.utils.models.fields import get_default_field_value


def shared_service(field, value):
    return get_default_field_value(field, value)


def instance_boomi_account_id(field, value):
    return get_default_field_value(field, value)


def instance_boomi_api_gateway_install_dir(field, value):
    return '<some absolute disk path>'


def instance_boomi_api_gateway_node_id(field, value):
    return '10_10_1_1'


def instance_boomi_api_token(field, value):
    return get_default_field_value(field, value)


def instance_boomi_api_url(field, value):
    return 'https://api.boomi.com'


def instance_boomi_api_userid(field, value):
    return 'service-user@yourdomain.com'


def instance_boomi_molecule_node_id(field, value):
    return '10_10_0_1'


def instance_disable_generic_tags(field, value):
    return False


def instance_empty_default_hostname(field, value):
    return False


def instance_metric_patterns(field, value):
    return get_default_field_value(field, value)


def instance_min_collection_interval(field, value):
    return 15


def instance_service(field, value):
    return get_default_field_value(field, value)


def instance_tags(field, value):
    return get_default_field_value(field, value)