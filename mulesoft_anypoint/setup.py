from codecs import open  # To use a consistent encoding
from os import path

from setuptools import setup

HERE = path.dirname(path.abspath(__file__))

# Get version info
ABOUT = {}
with open(path.join(HERE, "datadog_checks", "mulesoft_anypoint", "__about__.py")) as f:
    exec(f.read(), ABOUT)

# Get the long description from the README file
with open(path.join(HERE, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


CHECKS_BASE_REQ = "datadog-checks-base>=11.0.0"


setup(
    name="datadog-mulesoft_anypoint",
    version=ABOUT["__version__"],
    description="The mulesoft_anypoint check",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="datadog agent mulesoft_anypoint check mulesoft anypoint ARM monitoring ARM mule agent ARM rest services "
    "Cloudhub Exchange Object Store Access management Hybrid standalone Naked mules Flow designer API",
    # The project's main homepage.
    url="",
    # Author details
    author="IO Connect Services",
    author_email="support_ddp@ioconnectservices.com",
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
        "Programming Language :: Python :: 3.7",
    ],
    # The package we're going to ship
    packages=["datadog_checks.mulesoft_anypoint"],
    # Run-time dependencies
    install_requires=[
        CHECKS_BASE_REQ,
        "requests",
        "pytest",
        "responses",
        "parameterized",
        "pyyaml",
        "six",
    ],
    # Extra files to ship with the wheel package
    include_package_data=True,
)
