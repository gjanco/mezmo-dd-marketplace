import json
import os.path
import re

from common import load_endpoints
from flask import Flask, jsonify, request

app = Flask(__name__)

endpoints = {}
DATE_REGEX = (
    "\\d{4}-[01]\\d-[0-3]\\dT[0-2]\\d:[0-5]\\d:[0-5]\\d\\.\\d+([+-][0-2]\\d:[0-5]\\d|Z)"
)


def compare_exp_req(exp_dict, req_dict):
    check_call = True
    for exp_k in exp_dict:
        found = False
        for req_k in req_dict:
            if exp_k.lower() == req_k.lower():
                found = True
                check_call = False
                exp = str(exp_dict[exp_k])
                req = str(req_dict[req_k])
                if exp.startswith("%regex%") or exp.startswith("%date%"):
                    if exp.startswith("%regex%"):
                        regex_expr = exp[7:]
                    else:
                        regex_expr = DATE_REGEX
                    if re.search(regex_expr, req):
                        break
                    else:
                        return False
                else:
                    if exp == req:
                        break
                    else:
                        return False
        if not found and not check_call:
            return False
    return True


def get_response_selector_key(endpoint):
    response_selectors = endpoint.get("response_selectors")
    response_selector_key = ""
    if response_selectors:
        for key in response_selectors:
            if response_selector_key:
                response_selector_key += "&"
            value = request.args.get(key)
            if value:
                response_selector_key += key + "=" + value
    if not response_selector_key:
        response_selector_key = "default"
    return response_selector_key


def path_n(*params):
    response_headers = {"ContentType": "application/json"}
    url = str("/".join(item for item in params if item))
    endpoint = endpoints.get(url)
    if endpoint:
        check_headers = compare_exp_req(
            endpoint.get("headers", {}), dict(request.headers)
        )
        check_qparams = compare_exp_req(
            endpoint.get("query_params", {}), dict(request.args)
        )
        if check_headers and check_qparams:
            response_location = endpoint["response"].get(
                get_response_selector_key(endpoint), ""
            )
            if response_location:
                response_content = os.path.join(
                    "apis_response", endpoint["api_name"], response_location
                )
                with open(response_content) as f:
                    response = json.load(f)
            else:
                response = ""
            response_body = jsonify(response)
            response_code = 200
        else:
            response_body = jsonify(
                error="bad request",
                description="query params ok:{} headers ok:{}".format(
                    check_headers, check_qparams
                ),
            )
            response_code = 400
    else:
        response_body = jsonify(
            error="unexpected request",
            description="the url:{} isn't mocked".format(url),
        )
        response_code = 400
    return response_body, response_code, response_headers


route = (
    "/<a>/<b>/<c>/<d>/<e>/<f>/<g>/<h>/<i>/<j>/<k>/<l>/<m>/<n>/<o>/<p>/<q>/<r>/<s>/<t>"
)


@app.route(route[: 4 * 1], methods=["GET", "POST"])
@app.route(route[: 4 * 2], methods=["GET", "POST"])
@app.route(route[: 4 * 3])
@app.route(route[: 4 * 4])
@app.route(route[: 4 * 5], methods=["GET", "POST"])
@app.route(route[: 4 * 6])
@app.route(route[: 4 * 7], methods=["GET", "POST"])
@app.route(route[: 4 * 8])
@app.route(route[: 4 * 9])
@app.route(route[: 4 * 10])
@app.route(route[: 4 * 11])
@app.route(route[: 4 * 12])
@app.route(route[: 4 * 13])
@app.route(route[: 4 * 14])
@app.route(route[: 4 * 15])
@app.route(route[: 4 * 16])
@app.route(route[: 4 * 17])
@app.route(route[: 4 * 18])
@app.route(route[: 4 * 19])
@app.route(route[: 4 * 20])
@app.route("/")
def path_20(
    a=None,
    b=None,
    c=None,
    d=None,
    e=None,
    f=None,
    g=None,
    h=None,
    i=None,
    j=None,
    k=None,
    ll=None,
    m=None,
    n=None,
    o=None,
    p=None,
    q=None,
    r=None,
    s=None,
    t=None,
):
    return path_n(a, b, c, d, e, f, g, h, i, j, k, ll, m, n, o, p, q, r, s, t)


if __name__ == "__main__":
    endpoints = load_endpoints("apis")
    app.run(host="0.0.0.0", port=int("8000"), debug=False)
