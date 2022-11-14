class CommunicationRetrievalError(Exception):
    """Raised when the communication interface can't retrieve an element"""


class CommunicationRequestError(Exception):
    """Raised when the communication interface can't handle a request appropiately"""


class CommunicationAuthenticationError(Exception):
    """Raised when the communication interface can't handle an authentication request"""


class InvalidEntityError(Exception):
    """Raised when an entity is considered invalid"""


class InvalidArgumentError(Exception):
    """Raised when an argument or set of arguments are consided invalid"""


class EntityRetrievalError(Exception):
    """Raised when an entity could not be retrieved"""
