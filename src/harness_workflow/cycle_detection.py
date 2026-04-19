"""Subagent call-chain cycle detection API.

本模块恢复 bugfix-6 之前丢失的 cycle-detection 对象模型，对外导出：

- ``CallChainNode``          : dataclass，表示调用链中的一个 subagent 节点
- ``CycleDetectionResult``   : dataclass，检测结果
- ``CycleDetector``          : 可 push / pop 的单例调用链管理器
- ``detect_subagent_cycle``  : 无状态函数，传入现有链和新节点描述，返回结果
- ``report_cycle_detection`` : 把结果写入 action-log.md 与 cycle-logs/ 目录
- ``get_cycle_detector``     : 返回进程级单例
- ``reset_cycle_detector``   : 重置进程级单例（主要给测试用）

CLI 命令 ``harness_workflow.tools.harness_cycle_detector`` 保持独立（文件级
JSON chain 持久化），本模块提供的是 in-process API，供 subagent 嵌套调用前
在派发层做快速判断。判定基于 ``agent_id`` 重复：只要新节点的 agent_id 已
出现在链中，即视为 cycle（`A -> B -> A`、`A -> B -> C -> A` 均命中）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

__all__ = [
    "CallChainNode",
    "CycleDetectionResult",
    "CycleDetector",
    "detect_subagent_cycle",
    "report_cycle_detection",
    "get_cycle_detector",
    "reset_cycle_detector",
]


@dataclass
class CallChainNode:
    """调用链中的单个 subagent 节点。

    字段与 bugfix-6 之前的历史测试完全兼容：

    - ``level``               : 调用层级（主 agent = 0）
    - ``agent_id``            : 节点唯一标识，cycle 判定的依据
    - ``role``                : 角色名（executing / testing / ...）
    - ``task``                : 任务描述
    - ``session_memory_path`` : 该节点 session-memory.md 的路径
    - ``parent_agent_id``     : 父节点的 agent_id（顶层为 None）
    """

    level: int
    agent_id: str
    role: str
    task: str
    session_memory_path: str
    parent_agent_id: Optional[str] = None


@dataclass
class CycleDetectionResult:
    """cycle 检测结果。"""

    has_cycle: bool
    cycle_path: list = field(default_factory=list)
    message: str = ""


def _build_cycle_result(chain_ids: list, new_agent_id: str) -> CycleDetectionResult:
    """如果 ``new_agent_id`` 已在 ``chain_ids`` 中，构造 has_cycle=True 的结果。"""
    if new_agent_id not in chain_ids:
        return CycleDetectionResult(has_cycle=False, cycle_path=[], message="")

    start = chain_ids.index(new_agent_id)
    cycle_path = chain_ids[start:] + [new_agent_id]
    arrow = " -> ".join(cycle_path)
    message = f"Cycle detected: {arrow}"
    return CycleDetectionResult(has_cycle=True, cycle_path=cycle_path, message=message)


def detect_subagent_cycle(
    chain: list,
    new_agent_id: str,
    new_role: str = "",
    new_task: str = "",
    new_session_memory_path: str = "",
) -> CycleDetectionResult:
    """无状态 cycle 判定。

    输入现有 ``chain``（``CallChainNode`` 列表或等价 dict 列表）和新节点信息，
    返回 ``CycleDetectionResult``。只要 ``new_agent_id`` 重复出现在链中即命中。

    ``new_role`` / ``new_task`` / ``new_session_memory_path`` 仅用于与历史调
    用方保持签名兼容，当前实现不参与判定，可省略。
    """

    # 兼容 CallChainNode 和 dict 两种表达
    chain_ids = []
    for node in chain or []:
        if isinstance(node, CallChainNode):
            chain_ids.append(node.agent_id)
        elif isinstance(node, dict):
            chain_ids.append(node.get("agent_id"))
        else:
            # 其它对象退化为 getattr
            chain_ids.append(getattr(node, "agent_id", None))

    return _build_cycle_result(chain_ids, new_agent_id)


class CycleDetector:
    """进程级的调用链管理器。

    通过 ``add_node`` 压入节点并立即返回 ``CycleDetectionResult``；若命中
    cycle，则**不**把节点压入链。其它方法：

    - ``get_chain_depth()``    : 当前链长度
    - ``get_chain_snapshot()`` : 返回链的 dict 列表（深拷贝，调用方可安全读写）
    - ``pop()``                : 弹出并返回链尾节点；空链返回 None
    - ``clear()``              : 清空链
    """

    def __init__(self) -> None:
        self._chain: list = []

    def add_node(self, node: CallChainNode) -> CycleDetectionResult:
        chain_ids = [n.agent_id for n in self._chain]
        result = _build_cycle_result(chain_ids, node.agent_id)
        if not result.has_cycle:
            self._chain.append(node)
        return result

    def get_chain_depth(self) -> int:
        return len(self._chain)

    def get_chain_snapshot(self) -> list:
        snapshot = []
        for node in self._chain:
            snapshot.append(
                {
                    "level": node.level,
                    "agent_id": node.agent_id,
                    "role": node.role,
                    "task": node.task,
                    "session_memory_path": node.session_memory_path,
                    "parent_agent_id": node.parent_agent_id,
                }
            )
        return snapshot

    def pop(self) -> Optional[CallChainNode]:
        if not self._chain:
            return None
        return self._chain.pop()

    def clear(self) -> None:
        self._chain.clear()


# --- singleton plumbing ------------------------------------------------------

_detector_singleton: Optional[CycleDetector] = None


def get_cycle_detector() -> CycleDetector:
    """返回进程级单例 CycleDetector（按需构造）。"""
    global _detector_singleton
    if _detector_singleton is None:
        _detector_singleton = CycleDetector()
    return _detector_singleton


def reset_cycle_detector() -> None:
    """重置进程级单例；主要给测试使用，也可在 run 切换时调用。"""
    global _detector_singleton
    _detector_singleton = None


# --- reporting ---------------------------------------------------------------


def report_cycle_detection(
    result: CycleDetectionResult,
    action_log_path: Path,
    root_path: Path,
) -> None:
    """把 cycle 检测结果写入 action-log.md 和 cycle-logs/ 目录。

    约定：

    - ``action_log_path`` 所在目录必须已存在（调用方负责 mkdir）
    - 若 action log 已存在则追加，否则新建
    - 另外在 ``<root_path>/.workflow/state/cycle-logs/`` 下落一份独立报告
    - ``has_cycle=False`` 时直接返回，不写日志
    """

    if not result.has_cycle:
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    arrow = " -> ".join(result.cycle_path) if result.cycle_path else "(unknown)"
    report_lines = [
        f"## [{timestamp}] Cycle Detection Alert",
        "",
        "- **Type**: Subagent Call Cycle Detected",
        f"- **Cycle Path**: {arrow}",
        f"- **Message**: {result.message}",
        "- **Action**: Terminated - cannot spawn already-in-chain agent",
        "",
    ]
    report_content = "\n".join(report_lines)

    action_log_path = Path(action_log_path)
    action_log_path.parent.mkdir(parents=True, exist_ok=True)
    if action_log_path.exists():
        with open(action_log_path, "a", encoding="utf-8") as f:
            f.write("\n" + report_content)
    else:
        action_log_path.write_text(report_content, encoding="utf-8")

    cycle_log_dir = Path(root_path) / ".workflow" / "state" / "cycle-logs"
    cycle_log_dir.mkdir(parents=True, exist_ok=True)
    cycle_log_file = cycle_log_dir / (
        "cycle-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + ".md"
    )
    cycle_log_file.write_text(report_content, encoding="utf-8")
