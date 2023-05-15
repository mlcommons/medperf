import os
from typing import Optional
from medperf.utils import generate_tmp_path, get_file_sha1, remove_path
from .sources import supported_sources
from medperf.exceptions import InvalidArgumentError, InvalidEntityError


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
        or a url. The later case will be interpreted as a direct download link.
    """

    for source_class in supported_sources:
        resource_identifier = source_class.validate_resource(resource)
        if resource_identifier:
            return source_class, resource_identifier

    # In this case the input format is not compatible with any source
    msg = f"""Invalid resource input: {resource}. A Resource must be a url or
    in the following format: '<source_prefix>:<resource_identifier>'. Run
    `medperf mlcube submit --help` for more details."""
    raise InvalidArgumentError(msg)


def valid_file_exists(output_path, expected_hash):
    """Checks if the existing file matches the passed expected hash.
    If it is not, or no hash was passed, it will be removed
    from the filesystem."""

    if expected_hash:
        file_hash = get_file_sha1(output_path)
        if file_hash == expected_hash:
            return True

    remove_path(output_path)
    return False


def tmp_download_resource(resource):
    """Downloads a resource to the temporary storage."""

    tmp_output_path = generate_tmp_path()
    source_class, resource_identifier = __parse_resource(resource)
    source = source_class()
    source.authenticate()
    source.download(resource_identifier, tmp_output_path)
    return tmp_output_path


def verify_or_get_hash(tmp_output_path, expected_hash):
    """Checks if the downloaded file matches the passed expected hash
    if provided. The function returns the calculated hash."""
    calculated_hash = get_file_sha1(tmp_output_path)
    if expected_hash and expected_hash != calculated_hash:
        raise InvalidEntityError(
            f"Hash mismatch. Expected {expected_hash}, found {calculated_hash}."
        )
    return calculated_hash


def to_permanent_path(tmp_output_path, output_path):
    """Writes a file from the temporary storage to the desired output path."""
    output_folder = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_folder, exist_ok=True)
    os.rename(tmp_output_path, output_path)


def download_resource(
    resource: str, output_path: str, expected_hash: Optional[str] = None
):
    """Downloads a resource/file from the internet. Passing a hash is optional.
    If hash is provided, the downloaded file's hash will be checked and an error
    will be raised if it is incorrect.

    The file will not be re-downloaded if it already exists and has the correct hash.

    Upon success, the function returns the hash of the downloaded file.

    Args:
        resource (str): The resource string. Must be in the form <source_prefix>:<resource_identifier>
        or a url.
        output_path (str): The path to download the resource to
        expected_hash (optional, str): The expected hash of the file to be downloaded

    Returns:
        The hash of the downloaded file (or existing file)

    """
    if os.path.exists(output_path) and valid_file_exists(output_path, expected_hash):
        return expected_hash

    tmp_output_path = tmp_download_resource(resource)

    calculated_hash = verify_or_get_hash(tmp_output_path, expected_hash)

    to_permanent_path(tmp_output_path, output_path)

    return calculated_hash
