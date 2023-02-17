from .sources import supported_sources
from medperf.exceptions import InvalidArgumentError


def __parse_resource(resource: str):
    """Parses a resource string and returns its identifier and the source class
    it can be downloaded from.
    The function iterates over all supported sources and checks which one accepts
    this resource. A resource is a string that should match a certain pattern to be
    downloaded by a certain resource.

    If the resource pattern does not correspond to any supported source, the
    function raises an `InvalidArgumentError`

    Args:
        resource (str): The resource string. Must be in the form <source_prefix>:<resource_identifier>
        or a url. The later case will be interpreted as a public-access resource.
    """

    for source_class in supported_sources:
        resource_identifier = source_class.validate_resource(resource)
        if resource_identifier:
            return source_class, resource_identifier

    # In this case the input format is not compatible with any source
    msg = f"""Invalid resource input: {resource}. A Resource must be a url or
    in the following format: '<source_prefix>:<resource_identifier>'. See <link> for details."""
    raise InvalidArgumentError(msg)


def download_resource(resource: str, output_path: str):
    """Download a resource
    Args:
        resource (str): The resource string. Must be in the form <source_prefix>:<resource_identifier>
        or a url.
        output_path (str): The path to download the resource to

    """
    source_class, resource_identifier = __parse_resource(resource)
    source = source_class()
    source.authenticate()
    source.download(resource_identifier, output_path)
