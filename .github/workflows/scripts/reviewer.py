from github import Github
import os
import json
import requests
import re


REQUEST_LIBRARY_FUNCTIONS = {
    'requests.get',
    'requests.post',
    'requests.head',
    'requests.put',
    'requests.patch',
    'requests.delete',
    'requests.options',
}


def file_use_requests(content):
    for line in content.splitlines():
        # HTTP Validation can be skipped for specific cases
        # See https://github.com/DataDog/marketplace/pull/99#issuecomment-783457414
        if not 'SKIP_HTTP_VALIDATION' in line:
            for http_func in REQUEST_LIBRARY_FUNCTIONS:
                if http_func in line:
                    return True
    return False


def file_http_post_put(content):
    # Look for both [http|requests].[post|put]
    return re.search("(requests|http).(post|put)", content) is not None


repo = Github(os.environ.get('GITHUB_TOKEN')).get_repo(os.environ.get('GITHUB_REPOSITORY'))

with open(os.environ['GITHUB_EVENT_PATH']) as event_file:
    # Get the PR triggering the action
    event = json.load(event_file)
    pr_number = event['pull_request']['number']
    pr = repo.get_pull(pr_number)

    use_request = False
    http_post = False

    for file in pr.get_files():
        if '/datadog_checks/' in file.filename:
            if file_use_requests(file.patch):
                use_request = True
            if file_http_post_put(file.patch):
                http_post = True

    if http_post:
        print("This pull request makes POST or PUT http requests.")
        pr.add_to_labels('review/http')
    if use_request:
        raise Exception("This pull request is using requests, please use the RequestsWrapper instead: https://datadoghq.dev/integrations-core/base/http/.")
