from .direct import DirectLinkSource
from .synapse import SynapseSource

supported_sources = [DirectLinkSource, SynapseSource]

__all__ = [supported_sources]
