import json
import os


def copy_field(source, dest, field):
    value = source.get(field)
    if value:
        dest[field] = value


def copy_endpoint(in_ep):
    out_ep = {}
    for key in in_ep:
        if key != "children":
            copy_field(in_ep, out_ep, key)
    return out_ep


def deep_load_api(base_uri, json_api, loaded_api, api_name):
    for ep in json_api:
        full_ep = base_uri + ep
        loaded_api[full_ep] = copy_endpoint(json_api[ep])
        loaded_api[full_ep]["api_name"] = api_name
        children = json_api[ep].get("children")
        if children:
            deep_load_api(full_ep + "/", children, loaded_api, api_name)


def get_absolute_path_list(base_path):
    files = os.listdir(base_path)
    return {file[:-10]: os.path.join(base_path, file) for file in files}


def load_endpoints(base_path, api_filter=None):
    test_files = get_absolute_path_list(base_path)
    endpoints_list = {}
    json_ext = ".json"
    for api_name, api_path in test_files.items():
        if api_path.endswith(json_ext) and (not api_filter or api_name in api_filter):
            with open(api_path) as json_file:
                deep_load_api(
                    "",
                    json.load(json_file),
                    endpoints_list,
                    os.path.basename(api_path)[: -len(json_ext)],
                )
    return endpoints_list
