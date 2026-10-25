"""The publish workflow must not run on a bare tag push."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "publish.yml"


def test_publish_workflow_triggers_on_a_release_not_a_tag_push():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "release:" in text
    assert "published" in text
    assert "workflow_dispatch:" in text
    assert "tags:" not in text
    assert "cellpy_figure/schema/figure-1.json" in text
    assert "id-token: write" in text
