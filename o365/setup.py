# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from codecs import open  # To use a consistent encoding
from os import path

from setuptools import setup

HERE = path.dirname(path.abspath(__file__))

# Get version info
ABOUT = {}
with open(path.join(HERE, "datadog_checks", "o365", "__about__.py")) as f:
    exec(f.read(), ABOUT)

# Get the long description from the README file
with open(path.join(HERE, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


def get_dependencies():
    dep_file = path.join(HERE, "requirements.in")
    if not path.isfile(dep_file):
        return []

    with open(dep_file, encoding="utf-8") as f:
        return f.readlines()


CHECKS_BASE_REQ = "datadog-checks-base>=11.0.0"


setup(
    name="datadog-o365",
    version=ABOUT["__version__"],
    description="Microsoft Office 365 integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="RapDev agent microsoft office 365 office365 yammer skype outlook onedrive sharepoint email o365 check",
    # Author details
    author="RapDev",
    author_email="integrations@rapdev.io",
    # License
    license="BSD-3-Clause",
    # See https://pypi.org/classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.8",
    ],
    # The package we're going to ship
    packages=["datadog_checks.o365"],
    # Run-time dependencies
    install_requires=[CHECKS_BASE_REQ],
    extras_require={"deps": get_dependencies()},
    # Extra files to ship with the wheel package
    include_package_data=True,
)
