"""
Pytest: analyst role merge static assertions.

Traceability:
  - req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））
  - chg-04（CLI 兼容 pytest 补强 + escape hatch 文字落地）

Covers AC-7（CLI 兼容性零回归）and AC-12（escape hatch 路径）.

All tests are independent, use pathlib + yaml + re, follow the
existing style of test_roles_exit_contract.py / test_assistant_role_contract7.py.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LIVE = ROOT / ".workflow"
MIRROR = ROOT / "src/harness_workflow/assets/scaffold_v2/.workflow"


def _get_model(role_def: object) -> str:
    """v1/v2 兼容：取 role_def 的 model 字段。

    v1：role_def = "model_name" 字符串
    v2：role_def = {model: "model_name", stages: [...]} dict
    """
    if isinstance(role_def, str):
        return role_def
    if isinstance(role_def, dict):
        return str(role_def.get("model", ""))
    return ""


def test_role_model_map_has_analyst():
    """role-model-map roles['analyst'].model == 'opus'（AC-7：analyst 注册正确；兼容 v1/v2 schema）"""
    m = yaml.safe_load((LIVE / "context/role-model-map.yaml").read_text(encoding="utf-8"))
    analyst_model = _get_model(m["roles"]["analyst"])
    assert analyst_model == "opus", (
        f"role-model-map.yaml analyst model = {analyst_model!r}, expected 'opus' "
        "(req-40（阶段合并与用户介入窄化）/ chg-02（角色索引 + role-model-map 更新）)"
    )


def test_role_model_map_legacy_aliases():
    """legacy key requirement-review / planning 仍指 opus（AC-7：兼容旧派发语境；兼容 v1/v2 schema）"""
    m = yaml.safe_load((LIVE / "context/role-model-map.yaml").read_text(encoding="utf-8"))
    rr_model = _get_model(m["roles"]["requirement-review"])
    assert rr_model == "opus", (
        f"role-model-map.yaml requirement-review model = {rr_model!r}, expected 'opus' "
        "(chg-02（角色索引 + role-model-map 更新）)"
    )
    pl_model = _get_model(m["roles"]["planning"])
    assert pl_model == "opus", (
        f"role-model-map.yaml planning model = {pl_model!r}, expected 'opus' "
        "(chg-02（角色索引 + role-model-map 更新）)"
    )


def test_analyst_file_exists_and_sections():
    """analyst.md 存在且二级节 ≥ 6（AC-7：角色文件完整）"""
    p = LIVE / "context/roles/analyst.md"
    assert p.exists(), (
        "analyst.md not found (chg-01（analyst.md 角色文件新建）not landed)"
    )
    body = p.read_text(encoding="utf-8")
    # count lines starting with "## " (which captures 首节 "## 角色定义" already at col 0)
    section_count = len(re.findall(r"^## ", body, re.MULTILINE))
    assert section_count >= 6, (
        f"analyst.md has only {section_count} top-level sections, expected >= 6 "
        "(req-40（阶段合并与用户介入窄化）/ chg-01（analyst.md 角色文件新建）)"
    )


def test_analyst_file_mirror_sync():
    """analyst.md live == mirror 字节一致（硬门禁五：scaffold_v2 mirror 同步）"""
    live_path = LIVE / "context/roles/analyst.md"
    mirror_path = MIRROR / "context/roles/analyst.md"
    assert live_path.exists(), "live analyst.md not found"
    assert mirror_path.exists(), (
        f"mirror analyst.md not found at {mirror_path} "
        "(硬门禁五：scaffold_v2 mirror 未同步，chg-01（analyst.md 角色文件新建）)"
    )
    assert live_path.read_bytes() == mirror_path.read_bytes(), (
        "analyst.md live vs mirror byte mismatch "
        "(硬门禁五：scaffold_v2 mirror 同步失败)"
    )


def test_role_model_map_mirror_sync():
    """role-model-map.yaml live == mirror 字节一致（硬门禁五：mirror 同步）"""
    live_path = LIVE / "context/role-model-map.yaml"
    mirror_path = MIRROR / "context/role-model-map.yaml"
    assert live_path.exists(), "live role-model-map.yaml not found"
    assert mirror_path.exists(), (
        f"mirror role-model-map.yaml not found at {mirror_path} "
        "(硬门禁五：scaffold_v2 mirror 未同步，chg-02（角色索引 + role-model-map 更新）)"
    )
    assert live_path.read_bytes() == mirror_path.read_bytes(), (
        "role-model-map.yaml live vs mirror byte mismatch "
        "(硬门禁五：scaffold_v2 mirror 同步失败)"
    )


def test_harness_manager_routes_to_analyst():
    """harness-manager.md 含 analyst 派发目标 ≥ 2 处（AC-7：路由落地）"""
    body = (LIVE / "context/roles/harness-manager.md").read_text(encoding="utf-8")
    analyst_count = body.count("analyst")
    assert analyst_count >= 2, (
        f"harness-manager.md contains 'analyst' only {analyst_count} times, "
        "expected >= 2 (chg-03（harness-manager 路由改写）not landed)"
    )
    # §3.4 harness requirement / harness change 两行已将派发目标改写为 analyst
    has_route = (
        re.search(r"harness requirement.*analyst", body, re.DOTALL)
        or re.search(r"加载\s*analyst", body)
        or re.search(r"harness change.*analyst", body, re.DOTALL)
    )
    assert has_route, (
        "harness-manager.md missing 'harness requirement/change -> analyst' routing pattern "
        "(chg-03（harness-manager 路由改写）/ req-40（阶段合并与用户介入窄化）)"
    )


def test_technical_director_auto_advance_clause():
    """technical-director.md 含 req_review→planning 自动静默推进 + escape hatch 触发词（AC-12）"""
    body = (LIVE / "context/roles/directors/technical-director.md").read_text(encoding="utf-8")
    assert "requirement_review" in body, (
        "technical-director.md missing 'requirement_review' "
        "(chg-03（technical-director 自动静默推进子句）not landed)"
    )
    assert "planning" in body, (
        "technical-director.md missing 'planning' stage reference"
    )
    has_auto = "自动" in body or "静默" in body
    assert has_auto, (
        "technical-director.md missing '自动' or '静默' auto-advance keywords "
        "(chg-03（technical-director 自动静默推进子句）not landed)"
    )
    # escape hatch 4 触发词至少 1 处命中（AC-12）
    has_escape = re.search(r"我要自拆|我自己拆|让我自己拆|我拆 chg", body)
    assert has_escape, (
        "technical-director.md missing escape hatch trigger words "
        "(AC-12：escape hatch 路径；chg-03（technical-director escape hatch 触发词）not landed)"
    )


def test_stage_role_flow_exemption_clause():
    """stage-role.md 含 stage 流转点豁免子条款 + req-40（AC-7：stage 流转协议）"""
    body = (LIVE / "context/roles/stage-role.md").read_text(encoding="utf-8")
    assert "req-40" in body, (
        "stage-role.md missing 'req-40' reference "
        "(chg-03（stage-role 决策批量化扩展）not landed)"
    )
    has_exemption = "stage 流转点豁免" in body or "相邻同类型 stage" in body
    assert has_exemption, (
        "stage-role.md missing flow exemption clause "
        "('stage 流转点豁免' or '相邻同类型 stage') "
        "(chg-03（stage-role 决策批量化扩展）/ req-40（阶段合并与用户介入窄化）not landed)"
    )


def test_index_md_has_analyst_row():
    """index.md 含 analyst 行 + roles/analyst.md 路径 + 合并注释（AC-7：角色索引落地）"""
    body = (LIVE / "context/index.md").read_text(encoding="utf-8")
    assert "analyst" in body, (
        "context/index.md missing 'analyst' entry "
        "(chg-02（角色索引 + role-model-map 更新）not landed)"
    )
    assert "roles/analyst.md" in body, (
        "context/index.md missing 'roles/analyst.md' path reference "
        "(chg-02（角色索引 + role-model-map 更新）not landed)"
    )
    has_merge_note = "原 requirement-review" in body or "原 planning" in body
    assert has_merge_note, (
        "context/index.md missing merge annotation "
        "('原 requirement-review' or '原 planning') "
        "(chg-02（角色索引 + role-model-map 更新）not landed)"
    )
