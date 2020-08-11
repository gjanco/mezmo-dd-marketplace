import pytest

from datadog_checks.mulesoft_anypoint.vendor.integration_core.core_parsing import (  # isort:skip
    RE_CURLY_BRACES_KEYS,  # isort:skip
)  # isort:skip


@pytest.mark.unit
def test_regex_get_list(regex_parser, url_with_rep_params, abcd_cb_keys):
    parsed_list = regex_parser.get_list(RE_CURLY_BRACES_KEYS, url_with_rep_params)
    assert len(parsed_list) == 5
    assert all([key in parsed_list for key in abcd_cb_keys])


@pytest.mark.unit
def test_regex_get_set(regex_parser, url_with_rep_params, abcd_cb_keys):
    parsed_set = regex_parser.get_set(RE_CURLY_BRACES_KEYS, url_with_rep_params)
    assert len(parsed_set) == 4
    assert all([key in parsed_set for key in abcd_cb_keys])


@pytest.mark.unit
def test_regex_get_one(regex_parser, url_with_rep_params, abcd_cb_keys):
    parsed_one = regex_parser.get_one(RE_CURLY_BRACES_KEYS, url_with_rep_params)
    assert parsed_one == abcd_cb_keys[0]


@pytest.mark.unit
def test_regex_get_empty_list(regex_parser, fake_expr, url_with_rep_params):
    parsed_list = regex_parser.get_list(fake_expr, url_with_rep_params)
    assert isinstance(parsed_list, list)
    assert not parsed_list


@pytest.mark.unit
def test_regex_get_empty_set(regex_parser, fake_expr, url_with_rep_params):
    parsed_set = regex_parser.get_set(fake_expr, url_with_rep_params)
    assert isinstance(parsed_set, list)
    assert not parsed_set


@pytest.mark.unit
def test_regex_get_empty_one(regex_parser, fake_expr, url_with_rep_params):
    parsed_one = regex_parser.get_one(fake_expr, url_with_rep_params)
    assert not parsed_one
