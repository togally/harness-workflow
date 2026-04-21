"""req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 5

覆盖 sug-18（ff 模式下 subagent 任务拆分粒度与 API idle timeout 保护）：
在 ff 模式派发 subagent 长任务时包一层 timeout，超时抛 FFSubagentIdleTimeout
由主 agent 接住后上报，而不是悬挂等待。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def test_dispatch_with_timeout_returns_value_when_fast() -> None:
    from harness_workflow.ff_timeout import dispatch_with_timeout

    def callable_fast() -> int:
        return 42

    assert dispatch_with_timeout(callable_fast, idle_seconds=5) == 42


def test_dispatch_with_timeout_raises_on_idle() -> None:
    from harness_workflow.ff_timeout import FFSubagentIdleTimeout, dispatch_with_timeout

    def callable_slow() -> int:
        time.sleep(2)
        return 1

    try:
        dispatch_with_timeout(callable_slow, idle_seconds=1)
    except FFSubagentIdleTimeout:
        return
    raise AssertionError("expected FFSubagentIdleTimeout")


def test_dispatch_with_timeout_propagates_callable_exceptions() -> None:
    from harness_workflow.ff_timeout import dispatch_with_timeout

    def boom() -> None:
        raise ValueError("boom")

    try:
        dispatch_with_timeout(boom, idle_seconds=5)
    except ValueError as e:
        assert str(e) == "boom"
        return
    raise AssertionError("expected ValueError to propagate")
