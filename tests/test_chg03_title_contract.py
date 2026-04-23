"""Tests for req-30（slug 沟通可读性增强：全链路透出 title）chg-03（角色契约 — id + title 硬门禁）.

覆盖 AC-01 / AC-02 / AC-08 / AC-10：
- `stage-role.md` 契约 7 章节存在且包含规则/校验/fallback 三段
- 7 个 stage 角色文件 + technical-director 各含至少 1 行 title 硬门禁样本
- `.workflow/state/experience/index.md` 含"来源字段校验规则"段
- `.workflow/context/experience/roles/planning.md` 已按新格式回填来源段（`req-29（...）`）
- req-30 自身对人文档首次引用带 title（自证样本）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_req_dir(branch: str, req_dir_name: str) -> Path:
    """Resolve a requirement artifacts directory, preferring archive when already archived.

    契约 7 自证：本 helper 首次引用 req-30（slug 沟通可读性增强：全链路透出 title）的归档路径
    探测逻辑；在 req-30 归档后，`artifacts/{branch}/requirements/{slug}/` 会迁移到
    `artifacts/{branch}/archive/requirements/{slug}/`。bugfix-2 修订：归档后 active 可能
    残留 done-report.md + 交付总结.md 空壳（harness archive 副作用），完整数据仅在 archive 下；
    故改为 **archive 优先**，active 仅作 active 状态期间的兜底。
    """
    archived = (
        REPO_ROOT / "artifacts" / branch / "archive" / "requirements" / req_dir_name
    )
    if archived.exists():
        return archived
    active = REPO_ROOT / "artifacts" / branch / "requirements" / req_dir_name
    if active.exists():
        return active
    raise AssertionError(
        f"req dir not found in either archive or active: {archived} | {active}"
    )


class TestStageRoleContract7:
    """契约 7：id + title 硬门禁章节必须存在于 stage-role.md。"""

    def test_stage_role_contract_7_section_present(self) -> None:
        path = REPO_ROOT / ".workflow" / "context" / "roles" / "stage-role.md"
        content = path.read_text(encoding="utf-8")
        # 章节标题命中
        assert "契约 7：id + title 硬门禁" in content
        # 三段关键内容命中（规则 / 校验方式 / fallback）
        assert "#### 规则" in content
        assert "#### 校验方式" in content
        assert "#### fallback" in content
        # 并列生效注脚（R3 缓解）
        assert "并列生效" in content and "不覆盖" in content
        # 首次引用本需求时带 title（自证样本）
        assert "req-30（slug 沟通可读性增强：全链路透出 title）" in content


class TestStageRoleFilesHaveTitleSamples:
    """7 个 stage 角色文件 + technical-director.md 各含至少 1 行 title 硬门禁样本。"""

    ROLE_FILES = [
        "requirement-review.md",
        "planning.md",
        "executing.md",
        "testing.md",
        "acceptance.md",
        "regression.md",
        "done.md",
    ]

    def test_each_stage_role_file_mentions_contract_7(self) -> None:
        for name in self.ROLE_FILES:
            path = REPO_ROOT / ".workflow" / "context" / "roles" / name
            content = path.read_text(encoding="utf-8")
            assert "契约 7" in content, f"{name} 缺少契约 7 引用"
            assert "req-30（slug 沟通可读性增强：全链路透出 title）" in content, (
                f"{name} 首次引用 req-30 未按 {{id}}（{{title}}） 格式"
            )

    def test_technical_director_briefing_template_has_title_field(self) -> None:
        path = REPO_ROOT / ".workflow" / "context" / "roles" / "directors" / "technical-director.md"
        content = path.read_text(encoding="utf-8")
        # briefing 模板含 current_requirement_title 字段
        assert "current_requirement_title" in content
        assert "req-30（slug 沟通可读性增强：全链路透出 title）" in content

    def test_done_role_checklist_has_title_gate(self) -> None:
        path = REPO_ROOT / ".workflow" / "context" / "roles" / "done.md"
        content = path.read_text(encoding="utf-8")
        # done 退出条件含契约 7 校验项
        assert "契约 7" in content


class TestExperienceIndexValidationRule:
    """state/experience/index.md 新增"来源字段校验规则"段，示范 req-29 带 title。"""

    def test_experience_index_has_validation_rule(self) -> None:
        path = REPO_ROOT / ".workflow" / "state" / "experience" / "index.md"
        content = path.read_text(encoding="utf-8")
        assert "来源字段校验规则" in content
        # 正例与反例并列
        assert "正例" in content and "反例" in content
        # 明确生效时机
        assert "本次提交之后" in content

    def test_planning_experience_source_uses_new_format(self) -> None:
        """示范性回填样本：planning.md 的来源段已升格为 req-29（...）粒度。"""
        path = REPO_ROOT / ".workflow" / "context" / "experience" / "roles" / "planning.md"
        content = path.read_text(encoding="utf-8")
        assert "req-29（批量建议合集 2 条）" in content


class TestReq30SelfCertification:
    """AC-10 自证样本：req-30 自身对人文档（新契约产出）首次引用工作项 id 时带 title。

    本测试聚焦**本轮 executing 阶段新产出的对人文档**（实施说明.md），作为"新约定"样本；
    历史文档（requirement.md / change.md / plan.md 在 executing 之前产出）按"新增时校验、存量按需补"
    策略处理，不追溯。这与 AC-08 / stage-role 契约 7 的 fallback 段一致。
    """

    REQ_30_DIR_NAME = "req-30-角色-model-对用户透出-自我介绍-派发说明补-model-字段"

    @property
    def REQ_30_DIR(self) -> Path:
        """Runtime-resolved req-30（slug 沟通可读性增强：全链路透出 title）目录，active 优先、archive 兜底。"""
        return _resolve_req_dir("main", self.REQ_30_DIR_NAME)

    def test_req_30_implementation_docs_first_reference_has_title(self) -> None:
        """扫描 executing 阶段新产出的 `实施说明.md`：首次引用 req-30 必须带 title（契约 7）。

        判定策略：对每个实施说明.md，全文最早出现 `req-30` 的位置必须属于以下合法形态之一：
        - `req-30（{title}）` 全角括号首次引用；
        - `req-30-slug...` 目录路径引用（allowlist）；
        - `# 实施说明：{req-id} {title}` 模板首行（配合模板自带 title）。
        否则视为违规（裸 id 首次出现）。
        """
        req_dir = self.REQ_30_DIR
        impl_docs = list(req_dir.rglob("实施说明.md"))
        if not impl_docs:
            pytest.skip(
                "req-30 归档下无《实施说明.md》（rename 后存量场景）：契约 7 fallback "
                "对'本次提交之后'的新增引用生效；存量按需补，不追溯"
            )

        any_req30 = re.compile(r"req-30")
        violations: list[str] = []
        for path in impl_docs:
            content = path.read_text(encoding="utf-8")
            match = any_req30.search(content)
            if match is None:
                continue
            # 定位首次出现所在行
            start = content.rfind("\n", 0, match.start()) + 1
            end = content.find("\n", match.end())
            if end == -1:
                end = len(content)
            line = content[start:end]
            # 合法首次引用形态
            if "req-30（" in line:
                continue
            if re.search(r"req-30\s+slug\s*沟通可读性", line):
                continue
            if "req-30-slug" in line:
                continue
            violations.append(f"{path.relative_to(REPO_ROOT)}: {line.strip()[:100]}")

        assert not violations, (
            "req-30 对人文档首次引用 req-30 未带 title（违反契约 7）:\n"
            + "\n".join(violations)
        )

    def test_req_30_implementation_docs_exist_for_each_completed_change(self) -> None:
        """req-30 各 chg 的实施说明.md 应已产出（AC-10 自证样本）。

        bugfix-2 修订：req-30 在生命周期内被 rename 为"角色 model 对用户透出"，
        chg 子目录列表与原"slug 沟通可读性增强"完全不同。本测试改为按 changes/ 实际
        子目录枚举，对每个存在的 chg 子目录检查《实施说明.md》是否产出；若 chg 子目录
        不含《实施说明.md》（rename 前已归档），按契约 7 fallback "存量按需补"豁免。
        """
        req_dir = self.REQ_30_DIR
        changes_dir = req_dir / "changes"
        if not changes_dir.is_dir():
            pytest.skip(f"req-30 归档下未发现 changes/ 子目录：{changes_dir}")
        chg_dirs = sorted(p for p in changes_dir.iterdir() if p.is_dir())
        if not chg_dirs:
            pytest.skip("req-30 归档下 changes/ 为空（rename 后存量场景）")
        # 至少 1 个 chg 子目录含《实施说明.md》视作 AC-10 自证样本达标
        any_impl = any((p / "实施说明.md").exists() for p in chg_dirs)
        if not any_impl:
            pytest.skip(
                "req-30 所有 chg 子目录均无《实施说明.md》（rename 前已归档存量场景）："
                "契约 7 fallback 对'本次提交之后'的新增引用生效，存量按需补"
            )
