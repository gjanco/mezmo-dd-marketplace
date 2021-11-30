from github import Github
from PIL import Image
from datadog_checks.dev.tooling.datastructures import JSONDict
from datadog_checks.dev.tooling.commands.console import annotate_errors
import os
import json

# Requirement constants
TARGET_ASPECT_RATIO = round(16 / 9, 4)
MINIMUM_WIDTH = 1440
MAXIMUM_WIDTH = 2880
MEDIA_PATH = '/tile/media'


def get_check_name_from_manifest_path(file_path):
    """
    Helper function to get the check name based on a manifest.json path
    """
    parts = file_path.lstrip('/').split('/')
    if len(parts) != 2:
        return None
    if parts[1] == 'manifest.json':
        return parts[0]
    else:
        return None


def validate_media_elements(check_name, manifest_dict):
    """
    Validate that media elements included in each changed manifest.json meet the following
    requirements:
        - 1440px <= image width <= 2880px
        - 16:9 exact aspect ratio
    """
    print(f'Validating media elements for `{check_name}`.')
    error_output = []
    manifest = JSONDict(manifest_dict)
    media = manifest.get_path(MEDIA_PATH)

    for media_element in media:
        path = media_element['image_url']
        image_path = os.path.join(check_name, path)

        try:
            image = Image.open(image_path)
            width, height = image.size
            aspect_ratio = round(width / height, 4)
            if aspect_ratio != TARGET_ASPECT_RATIO:
                output = (f'  The aspect ratio for the image at `{image_path}` is {aspect_ratio}, but should be 16:9 '
                          '({TARGET_ASPECT_RATIO}).')
                error_output.append(output)
            if width < MINIMUM_WIDTH:
                output = (f'  The width for the image at `{image_path}` should be a minimum of {MINIMUM_WIDTH}px, but '
                          'is currently {width}px.')
                error_output.append(output)
            elif width > MAXIMUM_WIDTH:
                output = (f'  The width for the image at `{image_path}` should be a maximum of {MAXIMUM_WIDTH}px, but '
                          'is currently {width}px.')
                error_output.append(output)
        except FileNotFoundError:
            output = f'  Image could not be opened at `{image_path}`.'
            error_output.append(output)

    return error_output


def main():
    repo = Github(os.environ.get('GITHUB_TOKEN')).get_repo(os.environ.get('GITHUB_REPOSITORY'))

    manifests_changed = []
    with open(os.environ['GITHUB_EVENT_PATH']) as event_file:
        # Get the PR triggering the action
        event = json.load(event_file)
        pr_number = event['pull_request']['number']
        pr = repo.get_pull(pr_number)

        # Check for changes to manifest.json files in this PR
        for file in pr.get_files():
            if 'manifest.json' in file.filename:
                manifests_changed.append(file.filename)

    # Skip if no manifest files were changed in this PR
    if not manifests_changed:
        print(f'There are no manifest.json changes - skipping media validations!')
        return

    # For every changed manifest in this PR, validate the media elements listed in the file
    all_errors = []
    for manifest_path in manifests_changed:
        current_check_name = get_check_name_from_manifest_path(manifest_path)
        if current_check_name:
            try:
                with open(manifest_path) as manifest_file:
                    manifest_data = json.load(manifest_file)
                    errors = validate_media_elements(current_check_name, manifest_data)
                    all_errors.extend(errors)
                    annotate_errors(manifest_path, errors)
            except FileNotFoundError:
                print(f'Could not find manifest file at this path: {manifest_path}')

    # Print error output in addition to annotating
    if all_errors:
        for err in all_errors:
            print(err)
        raise AssertionError(f'Media validations have failed for this manifest file: {manifest_path}')
    else:
        print(f'All media elements have been successfully validated!')


main()
