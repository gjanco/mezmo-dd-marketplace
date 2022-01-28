import pytest

from datadog_checks.crest_data_systems_dell_emc_isilon import CrestDataSystemsDellEmcIsilonCheck


def test_check_with_missing_config(aggregator, instance):

    check = CrestDataSystemsDellEmcIsilonCheck("crest_data_systems_dell_emc_isilon", {}, [instance])
    ex_message = "Could not connect to EMC Server as configurations are missing in configuration file."
    with pytest.raises(Exception, match=ex_message):
        check.check(instance)

    aggregator.assert_service_check("cds.emc.isilon.can_connect", CrestDataSystemsDellEmcIsilonCheck.CRITICAL)


def test_check_with_invalid_config(aggregator, instance):
    invalid_instance = {"ip_address": "8.8.8.8", "port": "8080", "username": "test", "password": "test"}
    check = CrestDataSystemsDellEmcIsilonCheck("crest_data_systems_dell_emc_isilon", {}, [invalid_instance])

    with pytest.raises(Exception):
        check.check(invalid_instance)

    aggregator.assert_service_check("cds.emc.isilon.can_connect", CrestDataSystemsDellEmcIsilonCheck.CRITICAL)
