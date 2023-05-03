class MedperfException(Exception):
    """Medperf base exception"""


class CommunicationError(MedperfException):
    """Raised when an error happens due to the communication interface"""


class CommunicationRetrievalError(CommunicationError):
    """Raised when the communication interface can't retrieve an element"""


class CommunicationRequestError(CommunicationError):
    """Raised when the communication interface can't handle a request appropiately"""


class CommunicationAuthenticationError(CommunicationError):
    """Raised when the communication interface can't handle an authentication request"""


class InvalidEntityError(MedperfException):
    """Raised when an entity is considered invalid"""


class InvalidArgumentError(MedperfException):
    """Raised when an argument or set of arguments are consided invalid"""


class ExecutionError(MedperfException):
    """Raised when an execution component fails"""


class CleanExit(MedperfException):
    """Raised when Medperf needs to stop for non erroneous reasons"""
