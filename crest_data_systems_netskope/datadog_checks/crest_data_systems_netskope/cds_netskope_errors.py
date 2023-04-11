# Copyright (C) 2023 Crest Data Systems.
# All rights reserved


class APIError(Exception):
    """Base class of API related errors."""

    message = "Unknown API error occurred."

    def __init__(self, message=message, response=None):
        """Initialize an object."""
        self.response = response
        super().__init__(message)


class EmptyResponseError(APIError):
    """Did not receive response object from API request."""

    message = "Not received response object from API."

    def __init__(self, message=message):
        """Initialize an object."""
        super().__init__(message)


class InvalidAPICredentialsError(APIError):
    """Invalid API Credentials."""

    message = "API Credentials are invalid."

    def __init__(self, message=message):
        """Initialize an object."""
        super().__init__(message)


class SSLError(APIError):
    """SSL verification failure."""

    message = "SSL verification failed."

    def __init__(self, message=message):
        """Initialize an object."""
        super().__init__(message)


class BillingSubmitError(Exception):
    """Error occurred while submitting billing logs/metrics."""

    message = "Error occurred while submitting billing logs/metrics."

    def __init__(self, message=message):
        """Initialize an object."""
        super().__init__(message)
