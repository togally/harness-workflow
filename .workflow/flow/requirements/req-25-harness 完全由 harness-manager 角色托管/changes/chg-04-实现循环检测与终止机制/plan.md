# Change Plan

## 1. Development Steps

1. 设计调用链记录数据结构 - Done (CallChainNode, CycleDetectionResult)
2. 实现循环检测算法（在调用链中检测闭环） - Done (CycleDetector, detect_subagent_cycle)
3. 实现终止机制（检测到循环后中断并上报） - Done (report_cycle_detection)
4. 在 subagent 启动逻辑中集成循环检测 - N/A (设计为独立模块，可在任意位置调用)
5. 测试各种循环场景 - Done (19 tests passing)

## 2. Verification Steps

- [x] A→B→A 循环能被检测并终止
- [x] A→B→C→A 深层循环能被检测并终止
- [x] 循环终止后上报信息完整
- [x] 正常调用链不受影响

## 3. Implementation Summary

### Data Structures (src/harness_workflow/core.py)

```python
@dataclass
class CallChainNode:
    level: int
    agent_id: str
    role: str
    task: str
    session_memory_path: str
    parent_agent_id: Optional[str] = None

@dataclass
class CycleDetectionResult:
    has_cycle: bool
    cycle_path: list[str] = field(default_factory=list)
    message: str = ""
```

### Core Functions

- `CycleDetector.add_node()` - 添加节点并检测循环
- `detect_subagent_cycle()` - 独立函数，检测调用链中是否会形成循环
- `report_cycle_detection()` - 将循环检测结果上报到 action-log 和 cycle-logs
- `get_cycle_detector()` / `reset_cycle_detector()` - 全局单例管理

### Usage Example

```python
from harness_workflow import (
    CallChainNode,
    CycleDetector,
    detect_subagent_cycle,
    report_cycle_detection,
    get_cycle_detector,
)

# 方法1：使用全局单例
detector = get_cycle_detector()
result = detector.add_node(CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"))
if result.has_cycle:
    # 循环被检测到，不能派发
    report_cycle_detection(result, action_log_path, root_path)

# 方法2：使用独立函数
chain = [
    CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
    CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
]
result = detect_subagent_cycle(chain, new_agent_id="agent-a", new_role="executing", new_task="Task A again", new_session_memory_path="path-c")
if result.has_cycle:
    # A -> B -> A 循环被检测到
    print(result.message)  # "Cycle detected: agent-a -> agent-b -> agent-a..."
```
