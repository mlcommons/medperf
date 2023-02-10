from .sources import supported_sources


def __parse_resource(resource):
    for source_prefix in supported_sources.keys():
        if resource.startswith(source_prefix + ":"):
            prefix = source_prefix
            prefix_len = len(prefix) + 1
            resource_identifier = resource[prefix_len:]
            return prefix, resource_identifier

    print("defaulting to public")
    return "public", resource


def download_resource(resource: str, output_path: str):
    """resource is supposed to start with a certain prefix
    """
    prefix, resource_identifier = __parse_resource(resource)
    SourceClass = supported_sources[prefix]
    source = SourceClass()
    source.authenticate()
    source.download(resource_identifier, output_path)
