import pytest

from datadog_checks.crest_data_systems_microsoft_defender import CrestDataSystemsMicrosoftDefenderCheck


def test_check_with_missing_config(aggregator, instance):

    check = CrestDataSystemsMicrosoftDefenderCheck("crest_data_systems_microsoft_defender", {}, [instance])
    ex_message = "Could not connect to Microsoft 365 Defender as client_id, client_secret, tenant_id"
    ex_message += " or min_collection_interval are missing in configuration file."
    with pytest.raises(Exception, match=ex_message):
        check.check(instance)

    aggregator.assert_service_check(
        "cds.ms.defender.endpoint.can_connect", CrestDataSystemsMicrosoftDefenderCheck.CRITICAL
    )


def test_check_with_invalid_config(aggregator, instance):
    invalid_instance = {
        "client_id": "123",
        "client_secret": "123",
        "tenant_id": "123",
        "log_index": "main",
        "min_collection_interval": "7200",
    }
    check = CrestDataSystemsMicrosoftDefenderCheck("crest_data_systems_microsoft_defender", {}, [invalid_instance])

    with pytest.raises(Exception):
        check.check(invalid_instance)

    aggregator.assert_service_check(
        "cds.ms.defender.endpoint.can_connect", CrestDataSystemsMicrosoftDefenderCheck.CRITICAL
    )
