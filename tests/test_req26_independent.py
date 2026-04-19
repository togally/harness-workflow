"""Independent-perspective tests for req-26 (testing subagent L1).

本文件由测试工程师（testing 角色）在 chg-06 smoke 之外、以**独立视角**补充的
静态核查，覆盖 executing 侧 `test_smoke_req26.py::DualTrackContractStaticTest`
未覆盖的边界：

- AC-06 契约 3：7 份中文对人文档文件名（`需求摘要.md` / `变更简报.md` /
  `实施说明.md` / `测试结论.md` / `验收摘要.md` / `回归简报.md` /
  `交付总结.md`）必须分别在对应 stage 角色文件里出现且**路径与粒度正确**；
- AC-06 契约 4：每个 stage 角色的"退出条件"清单必须包含"对人文档 {文件名}.md
  已产出"的硬门禁条目；
- AC-06 契约 3：最小字段模板四字段（通过/失败统计、关键失败根因、未覆盖场景、
  风险评估）在 testing.md 里顺序正确。

硬约束（与 briefing 一致）：
- 不跑真 CLI；
- 不改功能代码；
- 不重复 `test_smoke_req26.py::DualTrackContractStaticTest` 已有用例，只加独立视角漏测。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROLES_DIR = REPO_ROOT / ".workflow" / "context" / "roles"


STAGE_HUMAN_DOC_SPEC = {
    "requirement-review.md": {
        "filename": "需求摘要.md",
        "path_prefix": "artifacts/{branch}/requirements/{req-id}-{slug}/",
        "granularity": "req",
    },
    "planning.md": {
        "filename": "变更简报.md",
        "path_prefix": "artifacts/{branch}/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/",
        "granularity": "change",
    },
    "executing.md": {
        "filename": "实施说明.md",
        "path_prefix": "artifacts/{branch}/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/",
        "granularity": "change",
    },
    "testing.md": {
        "filename": "测试结论.md",
        "path_prefix": "artifacts/{branch}/requirements/{req-id}-{slug}/",
        "granularity": "req",
    },
    "acceptance.md": {
        "filename": "验收摘要.md",
        "path_prefix": "artifacts/{branch}/requirements/{req-id}-{slug}/",
        "granularity": "req",
    },
    "regression.md": {
        "filename": "回归简报.md",
        "path_prefix": "artifacts/{branch}/requirements/{req-id}-{slug}/regressions/",
        "granularity": "regression",
    },
    "done.md": {
        "filename": "交付总结.md",
        "path_prefix": "artifacts/{branch}/requirements/{req-id}-{slug}/",
        "granularity": "req",
    },
}


class HumanDocFilenameTest(unittest.TestCase):
    """AC-06 契约 3：7 份中文文件名与路径前缀必须在对应 stage 文件里字面出现。"""

    def test_each_role_mentions_correct_human_doc_filename(self) -> None:
        for role_file, spec in STAGE_HUMAN_DOC_SPEC.items():
            path = ROLES_DIR / role_file
            text = path.read_text(encoding="utf-8")
            self.assertIn(
                spec["filename"], text,
                f"{role_file} 必须出现中文对人文档文件名 `{spec['filename']}`",
            )

    def test_each_role_mentions_correct_path_prefix(self) -> None:
        for role_file, spec in STAGE_HUMAN_DOC_SPEC.items():
            path = ROLES_DIR / role_file
            text = path.read_text(encoding="utf-8")
            self.assertIn(
                spec["path_prefix"], text,
                f"{role_file} 必须声明路径前缀 `{spec['path_prefix']}`",
            )


class HumanDocExitConditionHardGateTest(unittest.TestCase):
    """AC-06 契约 4：对人文档条目必须进入"退出条件"清单。"""

    def test_each_role_has_exit_condition_for_human_doc(self) -> None:
        for role_file, spec in STAGE_HUMAN_DOC_SPEC.items():
            path = ROLES_DIR / role_file
            text = path.read_text(encoding="utf-8")
            # 必须能定位"退出条件"章节
            self.assertIn("## 退出条件", text, f"{role_file} 缺少 `## 退出条件` 章节")
            # 并且退出条件章节内含该文件名的 checkbox
            # 粗略切分：退出条件到下一个二级标题
            section_match = re.search(
                r"## 退出条件\s*\n(.*?)(?=\n## |\Z)",
                text,
                flags=re.DOTALL,
            )
            self.assertIsNotNone(section_match, f"{role_file} 退出条件章节无法定位")
            section = section_match.group(1)
            self.assertIn(
                f"对人文档 `{spec['filename']}`",
                section,
                f"{role_file} 退出条件里必须有 `对人文档 {spec['filename']}` 条目",
            )
            self.assertIn(
                "- [ ]",
                section,
                f"{role_file} 退出条件里必须至少有一个 checkbox",
            )


class TestingMinimalFieldTemplateTest(unittest.TestCase):
    """AC-06 契约 3：testing.md 的最小字段模板四字段顺序不得变更。

    字段顺序：通过/失败统计 → 关键失败根因 → 未覆盖场景 → 风险评估
    """

    def test_field_order_in_testing_md(self) -> None:
        text = (ROLES_DIR / "testing.md").read_text(encoding="utf-8")
        expected_fields = [
            "## 通过/失败统计",
            "## 关键失败根因",
            "## 未覆盖场景",
            "## 风险评估",
        ]
        # 取最后一处（对人文档章节内的字段）而非随机文本
        positions = []
        for field in expected_fields:
            idx = text.rfind(field)
            self.assertGreater(idx, 0, f"testing.md 缺少字段 `{field}`")
            positions.append((field, idx))
        # 必须严格递增
        for i in range(1, len(positions)):
            prev_field, prev_idx = positions[i - 1]
            cur_field, cur_idx = positions[i]
            self.assertLess(
                prev_idx, cur_idx,
                f"testing.md 字段顺序错误：`{prev_field}` 应出现在 `{cur_field}` 之前",
            )


class StageRoleContractReferencesRolesTest(unittest.TestCase):
    """AC-06：stage-role.md 契约 3 的命名表应声明齐全 7 份文件名。"""

    def test_stage_role_lists_all_seven_human_doc_filenames(self) -> None:
        text = (ROLES_DIR / "stage-role.md").read_text(encoding="utf-8")
        for spec in STAGE_HUMAN_DOC_SPEC.values():
            self.assertIn(
                spec["filename"], text,
                f"stage-role.md 契约命名表必须列出 `{spec['filename']}`",
            )


if __name__ == "__main__":
    unittest.main()
