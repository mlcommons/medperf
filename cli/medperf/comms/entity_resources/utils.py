from .sources import supported_sources
from medperf.exceptions import InvalidArgumentError


def __parse_resource(resource):
    for source_class in supported_sources:
        resource_identifier = source_class.validate_resource(resource)
        if resource_identifier:
            return source_class, resource_identifier

    # In this case the input format is not compatible with any source
    msg = f"""Invalid resource input: {resource}. A Resource must be a url or
    in the following format: '<source>:<identifier>'. See <link> for details."""
    raise InvalidArgumentError(msg)


def download_resource(resource: str, output_path: str):
    """resource is supposed to start with a certain prefix
    """
    source_class, resource_identifier = __parse_resource(resource)
    source = source_class()
    source.authenticate()
    source.download(resource_identifier, output_path)
