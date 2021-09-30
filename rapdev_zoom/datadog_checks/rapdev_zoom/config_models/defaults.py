# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from datadog_checks.base.utils.models.fields import get_default_field_value


def shared_service(field, value):
    return get_default_field_value(field, value)


def instance_allow_redirects(field, value):
    return True


def instance_auth_token(field, value):
    return get_default_field_value(field, value)


def instance_auth_type(field, value):
    return 'basic'


def instance_aws_host(field, value):
    return get_default_field_value(field, value)


def instance_aws_region(field, value):
    return get_default_field_value(field, value)


def instance_aws_service(field, value):
    return get_default_field_value(field, value)


def instance_collect_meeting_host(field, value):
    return True


def instance_collect_participant_details(field, value):
    return True


def instance_connect_timeout(field, value):
    return get_default_field_value(field, value)


def instance_disable_generic_tags(field, value):
    return False


def instance_empty_default_hostname(field, value):
    return False


def instance_extra_headers(field, value):
    return get_default_field_value(field, value)


def instance_headers(field, value):
    return get_default_field_value(field, value)


def instance_kerberos_auth(field, value):
    return 'disabled'


def instance_kerberos_cache(field, value):
    return get_default_field_value(field, value)


def instance_kerberos_delegate(field, value):
    return False


def instance_kerberos_force_initiate(field, value):
    return False


def instance_kerberos_hostname(field, value):
    return get_default_field_value(field, value)


def instance_kerberos_keytab(field, value):
    return get_default_field_value(field, value)


def instance_kerberos_principal(field, value):
    return get_default_field_value(field, value)


def instance_log_requests(field, value):
    return False


def instance_min_collection_interval(field, value):
    return 60


def instance_ntlm_domain(field, value):
    return get_default_field_value(field, value)


def instance_password(field, value):
    return get_default_field_value(field, value)


def instance_persist_connections(field, value):
    return False


def instance_proxy(field, value):
    return get_default_field_value(field, value)


def instance_read_timeout(field, value):
    return get_default_field_value(field, value)


def instance_request_size(field, value):
    return 16


def instance_room_only_mode(field, value):
    return False


def instance_service(field, value):
    return get_default_field_value(field, value)


def instance_skip_proxy(field, value):
    return False


def instance_tags(field, value):
    return get_default_field_value(field, value)


def instance_timeout(field, value):
    return 10


def instance_tls_ca_cert(field, value):
    return get_default_field_value(field, value)


def instance_tls_cert(field, value):
    return get_default_field_value(field, value)


def instance_tls_ignore_warning(field, value):
    return False


def instance_tls_private_key(field, value):
    return get_default_field_value(field, value)


def instance_tls_use_host_header(field, value):
    return False


def instance_tls_verify(field, value):
    return True


def instance_use_legacy_auth_encoding(field, value):
    return True


def instance_username(field, value):
    return get_default_field_value(field, value)


def instance_users_to_track(field, value):
    return get_default_field_value(field, value)
