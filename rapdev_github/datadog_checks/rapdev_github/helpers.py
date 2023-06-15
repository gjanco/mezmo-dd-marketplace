import jwt
import time
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
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
