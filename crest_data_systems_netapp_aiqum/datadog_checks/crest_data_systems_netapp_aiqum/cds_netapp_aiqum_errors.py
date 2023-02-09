class APIError(Exception):
    """Base class of API related errors."""

    message = "Unknown API error occurred."

    def __init__(self, message=message, response=None):
        """Initialize an object."""
        self.response = response
        super().__init__(message)


class EmptyAPIResponseError(APIError):
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


class FileLockException(Exception):
    """Base class of Lock related errors."""

    message = "Could not acquire lock, since syncing is already in progress"

    def __init__(self, message=message, response=None):
        """Initialize an object."""
        self.response = response
        super().__init__(message)
