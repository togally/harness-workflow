"""tests/test_hardgate_ten_playbook_navigation.py

req-57 / chg-05：硬门禁十 §1 升级——路书读法泛化到所有 stage 角色。

TC-01 §1 标题含"任意 harness stage 角色入场必先按工件文本命中路书"
TC-02 §1 明列 7 个 stage 角色（analyst / planning / executing / testing / acceptance / regression / done）
TC-03 §1 明列 5 类工件（requirement.md / change.md / plan.md / regression diagnosis / bugfix.md）
TC-04 §1 含 5 步（overview → 关键词命中 → domain README → 细节 → 禁 grep）
TC-05 live + scaffold_v2 mirror 双写 byte-identical
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE = REPO_ROOT / ".workflow/context/roles/base-role.md"
MIRROR = REPO_ROOT / "src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md"


@pytest.fixture
def live_text() -> str:
    return LIVE.read_text(encoding="utf-8")


@pytest.fixture
def mirror_text() -> str:
    return MIRROR.read_text(encoding="utf-8")


def _section_one_block(text: str) -> str:
    """提取硬门禁十 §1 段（从 ### §1 到下一个 ### §2 之前）。"""
    m = re.search(
        r"### §1[^\n]*\n(.*?)(?=\n### §2)",
        text,
        re.DOTALL,
    )
    assert m, "未找到硬门禁十 §1 段"
    return m.group(0)


def test_tc01_section_title_upgraded(live_text: str) -> None:
    section = _section_one_block(live_text)
    assert "任意 harness stage 角色入场必先按工件文本命中路书" in section, (
        "§1 标题未升级到 chg-05 版本"
    )


@pytest.mark.parametrize(
    "stage",
    ["analyst", "planning", "executing", "testing", "acceptance", "regression", "done"],
)
def test_tc02_seven_stage_roles_listed(live_text: str, stage: str) -> None:
    section = _section_one_block(live_text)
    assert stage in section, f"§1 未明列 stage 角色：{stage}"


@pytest.mark.parametrize(
    "artifact",
    ["requirement.md", "change.md", "plan.md", "regression", "bugfix.md"],
)
def test_tc03_five_artifact_types_listed(live_text: str, artifact: str) -> None:
    section = _section_one_block(live_text)
    assert artifact in section, f"§1 未明列工件类型：{artifact}"


def test_tc04_five_step_navigation_chain(live_text: str) -> None:
    section = _section_one_block(live_text)
    # 5 步关键词
    must_have = [
        "overview",
        "code-map.md",
        "LLM:CODE_MAP_KEYWORDS",
        "LLM:KEYWORDS",
        "domains/<领域>/README.md",
        "code.md",
        "data-model.md",
        "notes.md",
        "禁止跳过",
    ]
    missing = [kw for kw in must_have if kw not in section]
    assert not missing, f"§1 缺少步骤关键词：{missing}"


def test_tc05_live_and_mirror_byte_identical(live_text: str, mirror_text: str) -> None:
    assert live_text == mirror_text, (
        "硬门禁五：base-role.md live 与 scaffold_v2 mirror 必须 byte-identical"
    )
