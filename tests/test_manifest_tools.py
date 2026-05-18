import json
import pytest
from scripts.manifest_tools import scan_mdx_for_tracked_blocks, generate_manifest_json


def _write_mdx(tmp_path, blocks_mdx: str) -> None:
    d = tmp_path / "docs"
    d.mkdir(exist_ok=True)
    (d / "scent.mdx").write_text(blocks_mdx, encoding="utf-8")


def test_scan_mdx(tmp_path):
    _write_mdx(tmp_path, """
# Scent
<TrackedBlock blockId="scent-intro" topic="scent" label="Introduction">
  Welcome to scent.
</TrackedBlock>
<TrackedBlock blockId="scent-detail" topic="scent" />
""")
    manifest = scan_mdx_for_tracked_blocks(str(tmp_path))
    assert len(manifest) == 2
    assert manifest[0]["block_id"] == "scent-intro"
    assert manifest[0]["topic"] == "scent"
    assert manifest[0]["label"] == "Introduction"
    assert manifest[1]["block_id"] == "scent-detail"


def test_generate_manifest_json_structure(tmp_path):
    _write_mdx(tmp_path, '<TrackedBlock blockId="b1" topic="sound" />')
    out = tmp_path / "manifest.json"
    entries, version = generate_manifest_json(str(tmp_path), str(out))

    assert out.exists()
    data = json.loads(out.read_text())
    assert "version" in data
    assert "generated_at" in data
    assert "blocks" in data
    assert isinstance(data["blocks"], list)
    assert data["version"] == version


def test_generate_manifest_json_returns_entries_and_version(tmp_path):
    _write_mdx(tmp_path, '<TrackedBlock blockId="b1" topic="sound" />')
    out = tmp_path / "manifest.json"
    entries, version = generate_manifest_json(str(tmp_path), str(out))

    assert isinstance(entries, list)
    assert len(entries) == 1
    assert isinstance(version, str) and len(version) == 12


def test_version_is_deterministic(tmp_path):
    _write_mdx(tmp_path, '<TrackedBlock blockId="b1" topic="sound" />')
    out1 = tmp_path / "m1.json"
    out2 = tmp_path / "m2.json"
    _, v1 = generate_manifest_json(str(tmp_path), str(out1))
    _, v2 = generate_manifest_json(str(tmp_path), str(out2))
    assert v1 == v2


def test_version_changes_when_blocks_change(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    f = d / "page.mdx"

    f.write_text('<TrackedBlock blockId="b1" topic="sound" />', encoding="utf-8")
    _, v1 = generate_manifest_json(str(tmp_path), str(tmp_path / "m1.json"))

    f.write_text('<TrackedBlock blockId="b2" topic="light" />', encoding="utf-8")
    _, v2 = generate_manifest_json(str(tmp_path), str(tmp_path / "m2.json"))

    assert v1 != v2
