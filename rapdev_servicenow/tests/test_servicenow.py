import pytest

from datadog_checks.base import ConfigurationError
from datadog_checks.rapdev_servicenow import ServicenowCheck

from .constants import Config

def test_nothing():
    assert 1
## Temporarily disable tests to generate mocks
# @pytest.mark.unit
# def test_validate_config():
#     # fail empty config
#     with pytest.raises(ConfigurationError):
#         c = ServicenowCheck("servicenow", {}, [{}])
#         c.validate_config()

#     # fail no checks configured
#     with pytest.raises(ConfigurationError):
#         c = ServicenowCheck("servicenow", {}, [Config.INSTANCE_NAME_ONLY])
#         c.validate_config()
    
#     # fail invalid bools
#     with pytest.raises(ConfigurationError):
#         c = ServicenowCheck("servicenow", {}, [Config.INVALID_BOOLS])
#         c.validate_config()

#     # fail itsm with no creds
#     with pytest.raises(ConfigurationError):
#         c = ServicenowCheck("servicenow", {}, [Config.ITSM_NO_CREDS])
#         c.validate_config()

#     # pass only statsdo
#     c = ServicenowCheck("servicenow", {}, [Config.ONLY_STATSDO])
#     c.validate_config()

#     # pass only itsm
#     c = ServicenowCheck("servicenow", {}, [Config.ITSM_WITH_CREDS])
#     c.validate_config()

#     # pass statsdo and itsm
#     c = ServicenowCheck("servicenow", {}, [Config.STATSDO_AND_ITSM])
#     c.validate_config()

# @pytest.mark.unit
# @pytest.mark.usefixtures("dd_environment")
# def test_check_itsm_connection(aggregator, instance):
#     c = ServicenowCheck("servicenow", {}, [instance])
#     c.check_itsm_connection()
#     print(aggregator._metrics)
#     # successful connection
#     aggregator.assert_metric("rapdev.servicenow.http_response", count=1)
#     aggregator.assert_metric_has_tag("rapdev.servicenow.http_response", "status_code:200", count=1)
#     aggregator.assert_service_check("rapdev.servicenow.table_api_connection", ServicenowCheck.OK)

#     # unsuccessful connection
#     instance["basic_auth_username"] = "wrong"
#     c = ServicenowCheck("servicenow", {}, [instance])
#     c.check_itsm_connection()

#     aggregator.assert_service_check("rapdev.servicenow.table_api_connection", ServicenowCheck.CRITICAL)
#     aggregator.assert_metric("rapdev.servicenow.http_response")
#     aggregator.assert_metric_has_tag("rapdev.servicenow.http_response", "status_code:401")

# @pytest.mark.integration
# @pytest.mark.usefixtures("dd_environment")
# def test_failed_check_itsm(aggregator, instance):
#     # bogus creds
#     c = ServicenowCheck("servicenow", {}, [Config.ITSM_WITH_CREDS]) # bogus creds

#     # exception is normally handled in ServicenowCheck.check()
#     with pytest.raises(Exception):
#         c.check_itsm(Config.ITSM_WITH_CREDS)

#     aggregator.assert_service_check("rapdev.servicenow.table_api_connection", ServicenowCheck.CRITICAL)

# @pytest.mark.unit
# @pytest.mark.usefixtures("dd_environment")
# def test_get_or_update_cache(aggregator, instance):
#     c = ServicenowCheck("servicenow", {}, [Config.ITSM_INSTANCE_V42])

#     test_cache = {0: None}

#     sys_id_no_cache = "78bf2743db0268102ed422e648961938"
#     sys_id_in_cache = 0
#     table = "sys_user"
#     cache = test_cache

#     answer = c.get_or_update_cache(sys_id_in_cache, table, cache)

#     assert answer == test_cache[sys_id_in_cache]

#     answer = c.get_or_update_cache(sys_id_no_cache, table, cache)

#     assert answer == test_cache[sys_id_no_cache]

# @pytest.mark.integration
# @pytest.mark.usefixtures("dd_environment")
# def test_successful_check(aggregator, instance):
#     c = ServicenowCheck("servicenow", {}, [instance])
#     c.check(instance)
#     aggregator.assert_service_check("rapdev.servicenow.itsm_check_online", ServicenowCheck.OK)

@pytest.mark.integration
@pytest.mark.usefixtures("dd_environment")
def test_statsdo(aggregator, instance):
    c = ServicenowCheck("servicenow", {}, [instance])
    c.stats_url = instance['url']
    c.check_statsdo()
    print(aggregator._metrics)
    print("AG")
    aggregator.assert_service_check("rapdev.servicenow.statsdo_connection", ServicenowCheck.OK)
    