# Plan: 三端支持

## 执行步骤

### Step 0: 设计统一入口架构
**目标：** 创建统一的顶层入口文件，三端入口文件都引用它

**设计思路：**
```
项目根目录/
├── WORKFLOW.md              # 统一顶层入口（核心规则 + 加载流程）
├── AGENTS.md                # codex 入口 → 引用 WORKFLOW.md
├── CLAUDE.md                # cc 入口 → 引用 WORKFLOW.md
└── .qoder/
    └── skills/harness/
        └── SKILL.md         # qoder 入口 → 引用 WORKFLOW.md
```

**WORKFLOW.md 内容结构：**
```markdown
# Harness Workflow

## 角色
流程控制 agent，负责编排整个工作流。

## 全局硬门禁
1. 未读取 `.workflow/state/runtime.yaml` → 立即停止
2. 节点任务必须派发给 subagent
3. 无 `current_requirement` → 引导创建需求
4. `conversation_mode: harness` → 锁定当前节点

## 入口
读 `.workflow/context/index.md` 获取完整加载规则。
```

**三端入口文件改造：**
- `AGENTS.md`: 保留平台特定内容 + 引用 WORKFLOW.md
- `CLAUDE.md`: 简化为引用 WORKFLOW.md
- `.qoder/skills/harness/SKILL.md`: 保留 skill 元数据 + 引用 WORKFLOW.md

---

### Step 1: 创建备份目录结构和工具函数
**产物：**
- `.workflow/context/backup/` 目录
- `src/harness_.workflow/backup.py` — 备份/恢复工具模块

**实现要点：**
```python
# backup.py 核心函数
def backup_config(platform: str, root: str) -> None:
    """将平台配置移动到备份目录"""

def restore_config(platform: str, root: str) -> bool:
    """从备份恢复配置，返回是否成功"""

def get_backup_status(root: str) -> dict[str, bool]:
    """获取各平台备份状态"""
```

**备份目录结构：**
```
.workflow/context/backup/
├── codex/
│   └── AGENTS.md
├── qoder/
│   └── agents.md
└── cc/
    └── commands/   # 目录整体备份
```

---

### Step 2: 添加交互式平台选择
**产物：**
- 修改 `src/harness_.workflow/cli.py`
- 添加 `questionary` 依赖

**实现要点：**
```python
import questionary

def prompt_platform_selection() -> list[str]:
    """交互式平台多选"""
    platforms = questionary.checkbox(
        "选择要支持的平台（空格选择，回车确认）:",
        choices=[
            {"name": "codex (AGENTS.md)", "value": "codex", "checked": True},
            {"name": "qoder (.qoder/agents.md)", "value": "qoder", "checked": True},
            {"name": "cc (.claude/commands/)", "value": "cc", "checked": True},
        ]
    ).ask()
    return platforms or []
```

---

### Step 3: 修改 install 命令逻辑
**产物：**
- 修改 `src/harness_.workflow/core.py` 的 `install_repo()` 函数

**实现逻辑：**
```
1. 检查是否已有配置（各平台）
2. 调用交互式选择，获取用户勾选的平台列表
3. 对于每个平台：
   - 如果勾选：
     - 如果备份中存在 → 调用 restore_config() 恢复
     - 否则 → 正常生成配置
   - 如果未勾选：
     - 如果当前存在配置 → 调用 backup_config() 移到备份
4. 记录用户选择到 .workflow/state/platforms.yaml
```

---

### Step 4: 添加 platforms.yaml 状态文件
**产物：**
- `.workflow/state/platforms.yaml` — 记录用户选择的平台

**文件格式：**
```yaml
enabled:
  - codex
  - cc
disabled:
  - qoder
last_updated: 2026-04-13
```

---

### Step 5: 修改 update 命令支持同步备份
**产物：**
- 修改 `src/harness_.workflow/core.py` 的更新逻辑

**实现逻辑：**
```
1. 读取 platforms.yaml 获取启用/禁用列表
2. 对于启用的平台 → 正常更新配置
3. 对于禁用的平台（备份中）→ 同步更新备份中的配置
4. 如果 platforms.yaml 不存在 → 按旧逻辑处理（全部更新）
```

---

### Step 6: 测试验证
**测试用例：**
1. 全新 install，全选 → 三个平台配置都生成
2. 全新 install，只选 codex → 只有 codex 配置
3. 已有配置，取消勾选 qoder → qoder 配置移到备份
4. 再次 install，勾选 qoder → 从备份恢复（不重新生成）
5. 执行 update → 启用的配置更新，备份中的配置同步更新

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `WORKFLOW.md` | 新增 | 统一顶层入口文件 |
| `AGENTS.md` | 修改 | 简化，引用 WORKFLOW.md |
| `CLAUDE.md` | 修改 | 简化，引用 WORKFLOW.md |
| `.qoder/skills/harness/SKILL.md` | 修改 | 引用 WORKFLOW.md |
| `src/harness_.workflow/backup.py` | 新增 | 备份/恢复工具模块 |
| `src/harness_.workflow/cli.py` | 修改 | 添加交互式选择 |
| `src/harness_.workflow/core.py` | 修改 | install/update 逻辑调整 |
| `.workflow/context/backup/` | 新增 | 备份目录 |
| `.workflow/state/platforms.yaml` | 新增 | 平台状态记录 |
| `pyproject.toml` | 修改 | 添加 questionary 依赖 |

## 预估影响
- 低风险：仅修改 install/update 流程，不影响其他命令
- 向后兼容：无 platforms.yaml 时按旧逻辑运行
