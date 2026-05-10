"""pytest lint tests for req-56 / chg-03: skill 文档 mirror grep/diff 验证.

补足 chg-03 plan.md §4 测试用例表中未实现的 TC-04 / TC-05:
  TC-04: grep `--fallback` 四平台 SKILL.md 各命中 ≥ 1
  TC-05: diff -q 四平台 body 追加段内容一致（frontmatter 各异允许，body 段字节级一致）

注：TC-Dogfood-01/02/03 已实现于 tests/integration/test_req56_fallback_dogfood.py。
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SKILL_DOCS = {
    "claude":  REPO_ROOT / ".claude" / "commands" / "harness-requirement.md",
    "kimi":    REPO_ROOT / ".kimi" / "skills" / "harness-requirement" / "SKILL.md",
    "qoder":   REPO_ROOT / ".qoder" / "commands" / "harness-requirement.md",
    "codex":   REPO_ROOT / ".codex" / "skills" / "harness-requirement" / "SKILL.md",
}

# The shared body block appended by chg-03 starts with this line
BODY_BLOCK_START = "## --fallback 标志（req-56）"


def _extract_body_block(path: Path) -> str:
    """Extract the '--fallback 标志' body block from a skill doc."""
    text = path.read_text(encoding="utf-8")
    idx = text.find(BODY_BLOCK_START)
    if idx == -1:
        return ""
    return text[idx:]


class TestFallbackFlagInAllSkillDocs:
    """TC-04: grep `--fallback` 四平台 SKILL.md 各命中 ≥ 1.

    对应 AC-05（chg-03 plan §4 TC-04）。
    """

    def test_claude_skill_has_fallback(self) -> None:
        path = SKILL_DOCS["claude"]
        assert path.exists(), f"Skill doc not found: {path}"
        result = subprocess.run(
            ["grep", "-c", "--", "--fallback", str(path)],
            capture_output=True, text=True,
        )
        count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        assert count >= 1, f".claude skill doc: expected ≥1 '--fallback', got {count}"

    def test_kimi_skill_has_fallback(self) -> None:
        path = SKILL_DOCS["kimi"]
        assert path.exists(), f"Skill doc not found: {path}"
        result = subprocess.run(
            ["grep", "-c", "--", "--fallback", str(path)],
            capture_output=True, text=True,
        )
        count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        assert count >= 1, f".kimi skill doc: expected ≥1 '--fallback', got {count}"

    def test_qoder_skill_has_fallback(self) -> None:
        path = SKILL_DOCS["qoder"]
        assert path.exists(), f"Skill doc not found: {path}"
        result = subprocess.run(
            ["grep", "-c", "--", "--fallback", str(path)],
            capture_output=True, text=True,
        )
        count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        assert count >= 1, f".qoder skill doc: expected ≥1 '--fallback', got {count}"

    def test_codex_skill_has_fallback(self) -> None:
        path = SKILL_DOCS["codex"]
        assert path.exists(), f"Skill doc not found: {path}"
        result = subprocess.run(
            ["grep", "-c", "--", "--fallback", str(path)],
            capture_output=True, text=True,
        )
        count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        assert count >= 1, f".codex skill doc: expected ≥1 '--fallback', got {count}"


class TestSkillDocBodyBlockConsistency:
    """TC-05: 四平台 body 追加段（## --fallback 标志 以下）内容字节级一致.

    对应 AC-07（chg-03 plan §4 TC-05；frontmatter 各异允许，body 段必须一致）。
    """

    def test_all_four_body_blocks_identical(self) -> None:
        blocks: dict[str, str] = {}
        for platform, path in SKILL_DOCS.items():
            assert path.exists(), f"Skill doc not found: {path}"
            block = _extract_body_block(path)
            assert block, f"{platform} skill doc does not contain '{BODY_BLOCK_START}' section"
            blocks[platform] = block

        # Compare all to the first (claude) as baseline
        baseline_platform = "claude"
        baseline = blocks[baseline_platform]
        for platform, block in blocks.items():
            if platform == baseline_platform:
                continue
            assert block == baseline, (
                f"Body block of '{platform}' differs from '{baseline_platform}'.\n"
                f"Expected (claude):\n{baseline[:300]}...\n\n"
                f"Got ({platform}):\n{block[:300]}..."
            )

    def test_body_block_hash_consistent(self) -> None:
        """Extra: SHA256 of body blocks must be equal across all 4 platforms."""
        hashes: dict[str, str] = {}
        for platform, path in SKILL_DOCS.items():
            block = _extract_body_block(path)
            hashes[platform] = hashlib.sha256(block.encode("utf-8")).hexdigest()

        baseline_hash = hashes["claude"]
        for platform, h in hashes.items():
            assert h == baseline_hash, (
                f"SHA256 of body block for '{platform}' ({h}) != 'claude' ({baseline_hash})"
            )
