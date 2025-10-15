from .direct import DirectLinkSource
from .synapse import SynapseSource
from .localfile import LocalFileSource
from .source import BaseSource

supported_sources = [DirectLinkSource, SynapseSource, LocalFileSource]

__all__ = ["supported_sources", BaseSource]
