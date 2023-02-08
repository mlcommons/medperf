from .sources.public import PublicSource
from .sources.synapse import SynapseSource
from .download import download_resource

sources = {
    PublicSource.prefix: PublicSource,
    SynapseSource.prefix: SynapseSource,
}

__all__ = [download_resource, sources]
