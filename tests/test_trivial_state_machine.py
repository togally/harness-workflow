"""req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）/ chg-01（trivial 通道命令骨架）
tests/test_trivial_state_machine.py — validate_stage / get_next_stage / is_terminal_stage 单测
"""
from __future__ import annotations

import pytest

from harness_workflow.workflow_helpers import (
    validate_stage,
    get_next_stage,
    is_terminal_stage,
)


class TestValidateStage:
    """trivial 通道 stage 合法性校验。"""

    def test_trivial_define_valid(self):
        """TC-03：trivial_define 合法"""
        assert validate_stage("trivial", "trivial_define") is True

    def test_trivial_executing_valid(self):
        """trivial + executing 合法"""
        assert validate_stage("trivial", "executing") is True

    def test_trivial_done_valid(self):
        """trivial + done 合法"""
        assert validate_stage("trivial", "done") is True

    def test_trivial_testing_invalid(self):
        """TC-04：trivial 无 testing stage"""
        assert validate_stage("trivial", "testing") is False

    def test_trivial_acceptance_invalid(self):
        """TC-11（反例）：trivial 无 acceptance stage"""
        assert validate_stage("trivial", "acceptance") is False

    def test_trivial_planning_invalid(self):
        """trivial 无 planning stage"""
        assert validate_stage("trivial", "planning") is False

    def test_unknown_task_type_returns_false(self):
        """未知 task_type 返回 False（不抛异常）"""
        assert validate_stage("unknown_xyz", "done") is False


class TestGetNextStage:
    """trivial 通道 stage 流转。"""

    def test_trivial_define_to_executing(self):
        """TC-05：trivial_define → executing"""
        assert get_next_stage("trivial", "trivial_define") == "executing"

    def test_executing_to_done(self):
        """executing → done"""
        assert get_next_stage("trivial", "executing") == "done"

    def test_done_returns_none(self):
        """TC-06：done → None（terminal）"""
        assert get_next_stage("trivial", "done") is None

    def test_unknown_stage_returns_none(self):
        """非法 stage → None"""
        assert get_next_stage("trivial", "testing") is None

    def test_unknown_task_type_returns_none(self):
        """未知 task_type → None"""
        assert get_next_stage("unknown_xyz", "done") is None


class TestIsTerminalStage:
    """terminal stage 判定。"""

    def test_done_is_terminal_for_trivial(self):
        """trivial 通道 done 为 terminal"""
        assert is_terminal_stage("trivial", "done") is True

    def test_trivial_define_is_not_terminal(self):
        """trivial_define 非 terminal"""
        assert is_terminal_stage("trivial", "trivial_define") is False

    def test_executing_is_not_terminal_for_trivial(self):
        """executing 非 terminal"""
        assert is_terminal_stage("trivial", "executing") is False

    def test_bugfix_done_is_terminal(self):
        """bugfix done 也是 terminal"""
        assert is_terminal_stage("bugfix", "done") is True
