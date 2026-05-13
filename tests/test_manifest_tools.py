import os
import json
import pytest
from scripts.manifest_tools import scan_mdx_for_tracked_blocks

def test_scan_mdx(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    f = d / "scent.mdx"
    f.write_text("""
# Scent
<TrackedBlock blockId="scent-intro" topic="scent" label="Introduction">
  Welcome to scent.
</TrackedBlock>
<TrackedBlock blockId="scent-detail" topic="scent" />
""", encoding="utf-8")

    manifest = scan_mdx_for_tracked_blocks(str(tmp_path))
    assert len(manifest) == 2
    assert manifest[0]["block_id"] == "scent-intro"
    assert manifest[0]["topic"] == "scent"
    assert manifest[0]["label"] == "Introduction"
    assert manifest[1]["block_id"] == "scent-detail"
