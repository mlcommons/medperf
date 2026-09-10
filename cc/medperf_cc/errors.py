class CCError(Exception):
    """Base class for anything these components refuse to do."""


class AttestationError(CCError):
    """A token could not be verified, or did not say what was required."""


class ConfigurationError(CCError):
    """A cloud environment is not set up the way its owner or operator needs."""


class OperationError(CCError):
    """An operation against the cloud environment failed."""


class InternalError(CCError):
    """These components were used in a way that should not be reachable.

    Not a user's mistake and not the environment's: a caller built something
    incomplete and got far enough to use it."""
