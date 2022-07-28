import jwt
import time
import re
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from datadog_checks.base import ConfigurationError

# Generate the Bearer Token


def generate_btoken(pathToKey, appID):
    try:
        with open(pathToKey, "rb") as mykey:
            pem = load_pem_private_key(mykey.read(), password=None, backend=default_backend())
    except Exception as e:
        raise ConfigurationError(f"ERROR: {e}\nFailed to create access token, please check your config and try again.")

    token = jwt.encode(
        {
            "iss": appID,
            "iat": int(time.time()),
            "exp": int(time.time() + 60),
        },
        pem,
        algorithm="RS256"
    )

    return token

# Finds the last page for pagination purposes.
# Call only after an http request

def find_last_page(json_dump):
    try:
        links = str(json_dump.headers.get('Link'))
        last_page = re.search("........rel=\"last\"", links)
        if last_page == None:
            return 1

        last_page = re.search("[0-9]+", last_page.group())
        last_page = last_page.group()
    except Exception as e:
        raise IOError(f"ERROR: {e}. Please check your config.")

    return int(last_page)
