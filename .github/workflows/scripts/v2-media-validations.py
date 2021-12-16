from github import Github
from PIL import Image
from datadog_checks.dev.tooling.datastructures import JSONDict
from datadog_checks.dev.tooling.commands.console import annotate_errors
import os
import json

# Requirement constants
MINIMUM_WIDTH = 1440
MAXIMUM_WIDTH = 2880
MEDIA_PATH = '/tile/media'
# These values represent 16:9 aspect ratio (with tolerance)
MIN_ASPECT_RATIO = 1.77
MAX_ASPECT_RATIO = 1.78


def get_changed_integrations(changed_files):
    """
    Helper function takes in a list of changed files and returns a list of integrations where
    files were changed. Validations will run for each integration found.
    """
    names_to_exclude = (
        '.azure-pipelines',
        '.github',
        '.gitlab',
        '.in-toto',
    )
    check_name_to_validate = set()
    for file in changed_files:
        parts = file.filename.lstrip('/').split('/')
        check_name = parts[0]
        if check_name not in names_to_exclude:
            check_name_to_validate.add(check_name)
    return list(check_name_to_validate)


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
            aspect_ratio = round(width / height, 2)
            if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
                output = (f'  The aspect ratio for the image at `{image_path}` is {aspect_ratio}, but should be 16:9 '
                          f'(1.78).')
                error_output.append(output)
            if width < MINIMUM_WIDTH:
                output = (f'  The width for the image at `{image_path}` should be a minimum of {MINIMUM_WIDTH}px, but '
                          f'is currently {width}px.')
                error_output.append(output)
            elif width > MAXIMUM_WIDTH:
                output = (f'  The width for the image at `{image_path}` should be a maximum of {MAXIMUM_WIDTH}px, but '
                          f'is currently {width}px.')
                error_output.append(output)
        except FileNotFoundError:
            output = f'  Image could not be opened at `{image_path}`.'
            error_output.append(output)

    return error_output


def main():
    repo = Github(os.environ.get('GITHUB_TOKEN')).get_repo(os.environ.get('GITHUB_REPOSITORY'))
    checks_changed = []
    with open(os.environ['GITHUB_EVENT_PATH']) as event_file:
        # Get the PR triggering the action, if not a PR, then stop validations
        try:
            event = json.load(event_file)
            pr_number = event['pull_request']['number']
            pr = repo.get_pull(pr_number)
        except KeyError:
            print('Stopping validations because this is not a PR.')
            return

        # Check for changes to manifest.json files in this PR
        changed_files = pr.get_files()
        changed_integrations = get_changed_integrations(changed_files)
        checks_changed.extend(changed_integrations)

    # Skip if no manifest files were changed in this PR
    if not checks_changed:
        print(f'There are no integration changes - skipping media validations!')
        return

    # For every changed manifest in this PR, validate the media elements listed in the file
    all_errors = []
    for current_check_name in checks_changed:
        manifest_path = f'{current_check_name}/manifest.json'
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
        raise AssertionError(f'Media validations have failed for this PR.')
    else:
        print(f'All media elements have been successfully validated!')


main()
