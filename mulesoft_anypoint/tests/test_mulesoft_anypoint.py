import os

import pytest

from datadog_checks.dev import get_here
from datadog_checks.mulesoft_anypoint import MulesoftAnypointCheck

from .docker.common import get_absolute_path_list, load_endpoints

# fmt: off
from datadog_checks.mulesoft_anypoint.vendor.integration_core.integration_core import get_metrics_prefix  # isort:skip
from datadog_checks.mulesoft_anypoint.vendor.integration_core.readers.mulesoft_anypoint.reader_mulesoft_anypoint import (  # isort:skip # noqa
    BASE_PREFIX,  # isort:skip
    LICENSE_CHECK,  # isort:skip
    SERVICE_CHECK,  # isort:skip
)  # isort:skip # noqa
# fmt: on


def run_integration(aggregator, instances, configured_init_config, check_metrics=True):
    for instance in instances:
        endpoints = load_endpoints(
            os.path.join(get_here(), "docker", "apis"), instance.get("api_filter")
        )
        c = MulesoftAnypointCheck(
            "mulesoft_anypoint",
            {},
            instances=[instance],
            init_config=configured_init_config,
        )
        c.check(instance)
        metric_prefix = get_metrics_prefix(BASE_PREFIX, instance.get("app_env"))
        if check_metrics:
            for end in endpoints:
                tags = create_base_tags(endpoints, end, instance)
                for metric in endpoints[end].get("metrics", []):
                    tagslist = metric.get("tag" or {})
                    tagslist.update(dict(tags or {}))
                    for k, v in metric.items():
                        if k in ["tag", "type"]:
                            continue
                        aggregator.assert_metric(
                            ".".join([metric_prefix, k]),
                            value=v,
                            tags=[
                                str(key + ":" + str(value))
                                for key, value in tagslist.items()
                            ],
                            metric_type=aggregator.METRIC_ENUM_MAP[metric.get("type")],
                        )
            aggregator.assert_service_check(
                ".".join([metric_prefix, SERVICE_CHECK]), MulesoftAnypointCheck.OK,
            )
            aggregator.assert_service_check(
                ".".join([metric_prefix, LICENSE_CHECK]), MulesoftAnypointCheck.OK,
            )


def create_base_tags(endpoints, end, configured_init_config):
    excluded_base_tags = endpoints[end].get("excluded_base_tags")
    base_tags = ["env_id", "org_id"]
    tags = {}
    for tag_key in base_tags:
        if not excluded_base_tags or tag_key not in excluded_base_tags:
            tags[tag_key] = configured_init_config.get(tag_key)
    return tags


@pytest.mark.integration
@pytest.mark.usefixtures("dd_environment")
def test_multi_api(aggregator, instance2, instance3, configured_init_config):
    run_integration(aggregator, [instance2, instance3], configured_init_config)


@pytest.mark.integration
@pytest.mark.usefixtures("dd_environment")
def test_no_license(aggregator, instance4, configured_init_config_no_license):
    os.environ["mininterval"] = "-1"
    run_integration(
        aggregator, [instance4], configured_init_config_no_license, check_metrics=False
    )
    metric_prefix = get_metrics_prefix(BASE_PREFIX, instance4.get("app_env"))
    aggregator.assert_service_check(
        ".".join([metric_prefix, SERVICE_CHECK]), MulesoftAnypointCheck.CRITICAL,
    )
    aggregator.assert_service_check(
        ".".join([metric_prefix, LICENSE_CHECK]), MulesoftAnypointCheck.CRITICAL,
    )
    del os.environ["mininterval"]


def conf_api_list():
    api_list = []
    for key in get_absolute_path_list(os.path.join(get_here(), "docker", "apis")):
        if key not in ["connected_apps", "license", "s3"]:
            api_list.append(key)
    return api_list


@pytest.mark.integration
@pytest.mark.parametrize("api_name", conf_api_list())
@pytest.mark.usefixtures("dd_environment")
def test_api(api_name, instance, aggregator, configured_init_config):
    instance["api_filter"] = [api_name]
    run_integration(aggregator, [instance], configured_init_config)


@pytest.mark.integration
@pytest.mark.usefixtures("dd_environment")
def test_service_check(aggregator, instance, configured_init_config):
    run_integration(aggregator, [instance], configured_init_config)


@pytest.mark.unit
def test_collect_results(
    check_ok,
    check_critical,
    license_ok,
    license_critical,
    configured_init_config,
    instance,
    aggregator,
):
    metric_prefix = get_metrics_prefix(
        BASE_PREFIX, configured_init_config.get("app_env")
    )
    check = MulesoftAnypointCheck(
        "mulesoft_anypoint",
        {},
        {},
        instances=[instance],
        init_config=configured_init_config,
    )

    check._report_service_check([check_ok, license_ok])
    aggregator.assert_service_check(
        ".".join([metric_prefix, SERVICE_CHECK]), MulesoftAnypointCheck.OK,
    )
    aggregator.assert_service_check(
        ".".join([metric_prefix, LICENSE_CHECK]), MulesoftAnypointCheck.OK,
    )

    aggregator.reset()
    check._report_service_check([check_critical, license_ok])
    aggregator.assert_service_check(
        ".".join([metric_prefix, SERVICE_CHECK]), MulesoftAnypointCheck.CRITICAL,
    )
    aggregator.assert_service_check(
        ".".join([metric_prefix, LICENSE_CHECK]), MulesoftAnypointCheck.OK,
    )

    aggregator.reset()
    check._report_service_check([check_critical, license_critical])
    aggregator.assert_service_check(
        ".".join([metric_prefix, SERVICE_CHECK]), MulesoftAnypointCheck.CRITICAL,
    )
    aggregator.assert_service_check(
        ".".join([metric_prefix, LICENSE_CHECK]), MulesoftAnypointCheck.CRITICAL,
    )
