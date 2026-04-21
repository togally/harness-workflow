"""ff 模式 subagent idle timeout 兜底（req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 5）。

覆盖 sug-18（ff 模式下 subagent 任务拆分粒度与 API idle timeout 保护）：
在 ff 模式派发 subagent 长任务时包一层 timeout，超过阈值抛
``FFSubagentIdleTimeout`` 由主 agent 接住后上报，而不是悬挂等待 API idle。

实现选型：
- 优先使用 ``threading.Thread`` + ``Thread.join(timeout)``（无需 asyncio event-loop，
  不破坏现有同步 dispatch 流；signal.SIGALRM 在 non-main thread 会抛错，放弃）；
- callable 抛异常（如 ValueError）必须原样透传，不被 timeout wrapper 吞；
- 超时后 callable 线程不强制杀（Python 不支持），仅记录 warning 让上层决定是否
  继续推进；这符合 plan.md R3 的降级策略。
"""
from __future__ import annotations

import threading
from typing import Any, Callable


class FFSubagentIdleTimeout(TimeoutError):
    """ff 模式 subagent idle 超时异常，由主 agent 接住后上报。"""


def dispatch_with_timeout(
    callable_: Callable[..., Any],
    *args: Any,
    idle_seconds: int = 300,
    **kwargs: Any,
) -> Any:
    """以 idle_seconds 超时上限调用 ``callable_``。

    - 返回 callable_ 的返回值；
    - callable_ 抛出的异常原样透传；
    - 执行时长超过 ``idle_seconds`` 抛 ``FFSubagentIdleTimeout``。
    """
    result_holder: dict[str, Any] = {}
    exc_holder: dict[str, BaseException] = {}

    def _runner() -> None:
        try:
            result_holder["value"] = callable_(*args, **kwargs)
        except BaseException as exc:  # noqa: BLE001 — 原样透传
            exc_holder["exc"] = exc

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join(timeout=idle_seconds)
    if t.is_alive():
        raise FFSubagentIdleTimeout(
            f"Subagent idle > {idle_seconds}s; suspending ff advancement (sug-18)."
        )
    if "exc" in exc_holder:
        raise exc_holder["exc"]
    return result_holder.get("value")
