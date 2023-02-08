from .public import PublicSource
from .synapse import SynapseSource

supported_sources = {
    PublicSource.prefix: PublicSource,
    SynapseSource.prefix: SynapseSource,
}

__all__ = [supported_sources]
