"""Stands in for fastpdb, which has no Linux arm64 wheel: it is compiled from
Rust, and so is a dependency of biotite, which it builds on. polaris imports
fastpdb, but uses it only to read and store protein structures (PDB files),
which these tasks don't have. Using it here raises an error."""

MESSAGE = "fastpdb is not installed in this image: protein structure (PDB) data is not supported"


class _Unavailable:
    def __getattr__(self, name):
        raise ImportError(MESSAGE)


# polaris uses fastpdb.struc (biotite.structure) and fastpdb.PDBFile
struc = _Unavailable()


class PDBFile:
    def __init__(self, *args, **kwargs):
        raise ImportError(MESSAGE)

    @staticmethod
    def read(*args, **kwargs):
        raise ImportError(MESSAGE)


__all__ = ["PDBFile"]
