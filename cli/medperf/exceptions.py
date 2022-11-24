class MedperfException(Exception):
    def __init__(self, message="", clean=True):
        super().__init__(message)
        self.clean = clean


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


class ExecutionError(Exception):
    """Raised when an execution component fails"""
