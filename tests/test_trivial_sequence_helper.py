"""req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）/ chg-01（trivial 通道命令骨架）
tests/test_trivial_sequence_helper.py — get_sequence_for_task_type 单测（TC-01 / TC-02）
"""
from __future__ import annotations

import pytest

from harness_workflow.workflow_helpers import (
    TRIVIAL_SEQUENCE,
    BUGFIX_SEQUENCE,
    WORKFLOW_SEQUENCE,
    SUGGESTION_SEQUENCE,
    get_sequence_for_task_type,
    VALID_TASK_TYPES,
)


class TestGetSequenceForTaskType:
    """TC-01 系列：各 task_type 正例 + TC-02 反例。"""

    def test_trivial_returns_trivial_sequence(self):
        """TC-01a：trivial → TRIVIAL_SEQUENCE"""
        assert get_sequence_for_task_type("trivial") == TRIVIAL_SEQUENCE

    def test_bugfix_returns_bugfix_sequence(self):
        """TC-01b：bugfix → BUGFIX_SEQUENCE"""
        assert get_sequence_for_task_type("bugfix") == BUGFIX_SEQUENCE

    def test_req_returns_workflow_sequence(self):
        """TC-01c：req → WORKFLOW_SEQUENCE"""
        assert get_sequence_for_task_type("req") == WORKFLOW_SEQUENCE

    def test_requirement_returns_workflow_sequence(self):
        """TC-01d：requirement（别名）→ WORKFLOW_SEQUENCE"""
        assert get_sequence_for_task_type("requirement") == WORKFLOW_SEQUENCE

    def test_sug_returns_suggestion_sequence(self):
        """TC-01e：sug → SUGGESTION_SEQUENCE"""
        assert get_sequence_for_task_type("sug") == SUGGESTION_SEQUENCE

    def test_suggestion_returns_suggestion_sequence(self):
        """TC-01f：suggestion（别名）→ SUGGESTION_SEQUENCE"""
        assert get_sequence_for_task_type("suggestion") == SUGGESTION_SEQUENCE

    def test_unknown_task_type_raises_value_error(self):
        """TC-02：未知 task_type → ValueError"""
        with pytest.raises(ValueError, match="Unknown task_type"):
            get_sequence_for_task_type("unknown_xyz")

    def test_returns_copy_not_reference(self):
        """返回的是副本，修改不影响常量"""
        seq = get_sequence_for_task_type("trivial")
        seq.append("fake_stage")
        assert "fake_stage" not in TRIVIAL_SEQUENCE


class TestTrivialSequenceConstant:
    def test_trivial_sequence_content(self):
        """TRIVIAL_SEQUENCE = [trivial_define, executing, done]"""
        assert TRIVIAL_SEQUENCE == ["trivial_define", "executing", "done"]

    def test_trivial_in_valid_task_types(self):
        """trivial 在 VALID_TASK_TYPES 内"""
        assert "trivial" in VALID_TASK_TYPES
