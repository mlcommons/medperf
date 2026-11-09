"""Resource archives cannot write outside their extraction directory."""
import gzip
import io
import tarfile
from types import SimpleNamespace

import pytest

from medperf import utils
from medperf.exceptions import ExecutionError


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("kind", ["parent", "absolute", "symlink", "hardlink", "fifo"])
def test_untar_rejects_unsafe_members_before_writing(tmp_path, monkeypatch, legacy, kind):
    if legacy:
        monkeypatch.setattr(utils, "tarfile", SimpleNamespace(open=tarfile.open, TarError=tarfile.TarError))
    archive = tmp_path / "resource.tar.gz"
    outside = tmp_path / "escaped"
    with tarfile.open(archive, "w:gz") as tar:
        valid = tarfile.TarInfo("valid")
        valid.size = 2
        tar.addfile(valid, io.BytesIO(b"ok"))
        member = tarfile.TarInfo(str(outside) if kind == "absolute" else "../escaped")
        if kind in {"symlink", "hardlink"}:
            member.name = "link"
            member.type = tarfile.SYMTYPE if kind == "symlink" else tarfile.LNKTYPE
            member.linkname = "../escaped"
        elif kind == "fifo":
            member.name = "fifo"
            member.type = tarfile.FIFOTYPE
        tar.addfile(member)
    dest = tmp_path / "extracted"
    with pytest.raises(ExecutionError, match="Unsafe archive member"):
        utils.untar(str(archive), extract_to=str(dest))
    assert not outside.exists()
    assert not (dest / "valid").exists()
    assert archive.exists()


@pytest.mark.parametrize("legacy", [False, True])
def test_untar_preserves_normal_resource_layout(tmp_path, monkeypatch, legacy):
    if legacy:
        monkeypatch.setattr(utils, "tarfile", SimpleNamespace(open=tarfile.open, TarError=tarfile.TarError))
    archive = tmp_path / "resource.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo("dataset/example.txt")
        member.size = 2
        tar.addfile(member, io.BytesIO(b"ok"))
    dest = tmp_path / "extracted"
    assert gzip.decompress(archive.read_bytes()).startswith(b"dataset/example.txt")
    assert utils.untar(str(archive), extract_to=str(dest)) == str(dest)
    assert (dest / "dataset/example.txt").read_bytes() == b"ok"
    assert not archive.exists()
