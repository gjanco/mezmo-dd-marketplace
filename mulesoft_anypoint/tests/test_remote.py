import pytest
import responses

from datadog_checks.mulesoft_anypoint.vendor.integration_core.core_remote.remote_base import (  # isort:skip
    ResponseStatus,  # isort:skip
)  # isort:skip
from datadog_checks.mulesoft_anypoint.vendor.integration_core.core_remote.remote_http import (  # isort:skip
    HttpRequest,  # isort:skip
    HttpRequestType,  # isort:skip
)  # isort:skip


@pytest.mark.unit
@responses.activate
def test_remote_get_ok(http_caller_no_auth, test_url, ok_resp):
    responses.add(responses.GET, test_url, json=ok_resp, status=200)
    http_request = HttpRequest(HttpRequestType.GET, test_url)
    response = http_caller_no_auth.call(http_request)
    assert response.status() == ResponseStatus.OK
    assert response.get_data().get("data") == "ok_default"


@pytest.mark.unit
@responses.activate
def test_remote_get_error_response(http_caller_no_auth, test_url):
    responses.add(responses.GET, test_url, json={}, status=400)
    http_request = HttpRequest(HttpRequestType.GET, test_url)
    response = http_caller_no_auth.call(http_request)
    assert response.status() == ResponseStatus.ERROR
    responses.reset()
    responses.add(responses.GET, test_url, json={}, status=500)
    http_request = HttpRequest(HttpRequestType.GET, test_url)
    response = http_caller_no_auth.call(http_request)
    assert response.status() == ResponseStatus.ERROR


@pytest.mark.unit
@responses.activate
def test_remote_get_not_connected_response(http_caller_no_auth, test_url):
    responses.add(responses.GET, test_url, json={}, status=401)
    http_request = HttpRequest(HttpRequestType.GET, test_url)
    response = http_caller_no_auth.call(http_request)
    assert response.status() == ResponseStatus.NOT_CONNECTED


@pytest.mark.unit
@responses.activate
def test_remote_get_lack_of_rights_response(http_caller_no_auth, test_url):
    responses.add(responses.GET, test_url, json={}, status=403)
    http_request = HttpRequest(HttpRequestType.GET, test_url)
    response = http_caller_no_auth.call(http_request)
    assert response.status() == ResponseStatus.LACK_OF_RIGHT


@pytest.mark.unit
@responses.activate
def test_remote_get_timeout_response(http_caller_no_auth, test_url):
    responses.add(responses.GET, test_url, json={}, status=408)
    http_request = HttpRequest(HttpRequestType.GET, test_url)
    response = http_caller_no_auth.call(http_request)
    assert response.status() == ResponseStatus.TIMEOUT


@pytest.mark.unit
@responses.activate
def test_remote_post_ok(http_caller_no_auth, test_url, ok_resp):
    responses.add(responses.POST, test_url, json=ok_resp, status=200)
    http_request = HttpRequest(HttpRequestType.POST, test_url)
    response = http_caller_no_auth.call(http_request)
    assert response.status() == ResponseStatus.OK
    assert response.get_data().get("data") == "ok_default"


@pytest.mark.unit
@responses.activate
def test_remote_bearer_auth(
    http_caller_no_auth, bearer_auth, test_url, configured_init_config, auth_resp
):
    responses.add(
        responses.POST,
        configured_init_config["hosts"].get("oauth_provider"),
        json=auth_resp,
        status=200,
    )
    http_request = HttpRequest(HttpRequestType.GET, test_url)
    bearer_auth.add_auth_to_request(http_caller_no_auth, http_request)
    assert (
        http_request.get_args().get("headers").get("Authorization")
        == "Bearer 00000000-0000-0000-0000-000000000000"
    )


@pytest.mark.unit
@responses.activate
def test_remote_http_with_auth_ok(
    http_caller_bearer_auth, test_url, configured_init_config, auth_resp, ok_resp
):
    responses.add(responses.GET, test_url, json=ok_resp, status=200)
    responses.add(
        responses.POST,
        configured_init_config["hosts"].get("oauth_provider"),
        json=auth_resp,
        status=200,
    )
    http_request = HttpRequest(HttpRequestType.GET, test_url)
    response = http_caller_bearer_auth.call(http_request)
    assert response.status() == ResponseStatus.OK
    assert response.get_data().get("data") == "ok_default"


@pytest.mark.unit
@responses.activate
def test_remote_http_with_auth_error(
    http_caller_bearer_auth, test_url, configured_init_config, auth_resp, ok_resp
):
    responses.add(responses.GET, test_url, json=ok_resp, status=403)
    responses.add(
        responses.POST,
        configured_init_config["hosts"].get("oauth_provider"),
        json=auth_resp,
        status=200,
    )
    http_request = HttpRequest(HttpRequestType.GET, test_url)
    response = http_caller_bearer_auth.call(http_request)
    assert response.status() == ResponseStatus.LACK_OF_RIGHT
