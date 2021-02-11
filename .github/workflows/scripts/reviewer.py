from github import Github
import os
import json
import requests
import re


def file_use_requests(content):
    return 'from requests import' in content or 'import requests' in content

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
        print("This pull request is using requests, please use the RequestsWrapper instead: https://datadoghq.dev/integrations-core/base/http/.")
        pr.add_to_labels('review/requests')
