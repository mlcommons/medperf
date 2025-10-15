from __future__ import annotations
import os
import logging
from typing import Any, Dict, Optional, TYPE_CHECKING, Tuple
from medperf.utils import generate_tmp_path, get_file_hash
from .sources import supported_sources
from medperf.exceptions import InvalidArgumentError, InvalidEntityError
import yaml

if TYPE_CHECKING:
    from .sources import BaseSource


def __parse_resource(resource: str) -> Tuple[type[BaseSource], str]:
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
    msg = f"""Invalid resource input: {resource}. A Resource must be a url, a local file or
    in the following format: '<source_prefix>:<resource_identifier>'. Run
    `medperf container submit --help` for more details."""
    raise InvalidArgumentError(msg)


def tmp_download_resource(resource):
    """Downloads a resource to the temporary storage.

    Args:
        resource (str): The resource string. Must be in the form <source_prefix>:<resource_identifier>
        or a url.

    Returns:
        tmp_output_path (str): The location where the resource was downloaded
    """

    tmp_output_path = generate_tmp_path()
    source_class, resource_identifier = __parse_resource(resource)
    source = source_class()
    source.authenticate()
    source.download(resource_identifier, tmp_output_path)
    return tmp_output_path


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

    Upon success, the function returns the hash of the downloaded file.

    Args:
        resource (str): The resource string. Must be in the form <source_prefix>:<resource_identifier>
        or a url.
        output_path (str): The path to download the resource to
        expected_hash (optional, str): The expected hash of the file to be downloaded

    Returns:
        The hash of the downloaded file (or existing file)

    """
    tmp_output_path = tmp_download_resource(resource)

    calculated_hash = get_file_hash(tmp_output_path)

    if expected_hash and calculated_hash != expected_hash:
        logging.debug(f"{resource}: Expected {expected_hash}, found {calculated_hash}.")
        raise InvalidEntityError(f"Hash mismatch: {resource}")

    to_permanent_path(tmp_output_path, output_path)

    return calculated_hash


def load_yaml_content(resource_path: str) -> Dict[str, Any]:
    source_class, resource_id = __parse_resource(resource_path)
    source_instance = source_class()

    source_instance.authenticate()
    content = source_instance.read_content(resource_identifier=resource_id)

    yaml_dict = yaml.safe_load(content)
    if yaml_dict is None:
        yaml_dict = {}

    return yaml_dict


if __name__ == '__main__':
    __parse_resource('https://storage.googleapis.com/medperf-storage/testfl/mlcube.yaml')