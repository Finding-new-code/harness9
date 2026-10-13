"""Contract checks for the optional H9 motion-direction skill."""

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = REPO_ROOT / "optional-skills" / "creative" / "h9-motion-direction" / "SKILL.md"


def _frontmatter(content: str) -> dict[str, str]:
    match = re.match(r"\A---\n(.*?)\n---\n", content, re.DOTALL)
    assert match, "skill must start with closed YAML frontmatter"
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            fields[key] = value.strip().strip('"')
    return fields


def test_motion_direction_skill_has_valid_metadata_and_references():
    content = SKILL_PATH.read_text(encoding="utf-8")
    fields = _frontmatter(content)
    description = fields["description"]

    assert fields["name"] == "h9-motion-direction"
    assert len(description) <= 60
    assert description.endswith(".")
    assert "version:" in content
    assert "author:" in content
    assert "platforms:" in content
    assert "related_skills: [hyperframes, creative-ideation, grounded-citations]" in content
    assert "## When to Use" in content
    assert "## Procedure" in content
    assert "## Pitfalls" in content
    assert "## Verification" in content
    assert (REPO_ROOT / "optional-skills" / "creative" / "hyperframes" / "SKILL.md").is_file()
    assert (REPO_ROOT / "optional-skills" / "creative" / "creative-ideation" / "SKILL.md").is_file()
    assert (REPO_ROOT / "skills" / "research" / "grounded-citations" / "SKILL.md").is_file()


def test_motion_direction_skill_uses_renderer_allowlist_and_preserves_fact_gates():
    content = SKILL_PATH.read_text(encoding="utf-8")
    for preset in ("rise", "slide_left", "zoom", "reveal", "cut"):
        assert f"`{preset}`" in content
    assert "does not invent facts" in content
    assert "does not rebuild a composition from edited script JSON" in content
