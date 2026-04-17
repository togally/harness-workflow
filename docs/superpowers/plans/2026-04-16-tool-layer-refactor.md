# 工具层重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Harness 工作流引入基础角色、工具索引/匹配/评分闭环、skill hub 扩展和操作日志。

**Architecture:** 在 Context 层新增 `base-role.md` 作为抽象父角色；在 Tools 层新增 `keywords.yaml`、`ratings.yaml`、`missing-log.yaml` 及 CLI 命令 `tool-search`、`tool-rate`；在 State 层新增 `action-log.md` 的写入逻辑。

**Tech Stack:** Python 3.14, argparse, PyYAML-style simple YAML parser (existing), subprocess, unittest

---

## 文件映射

| 文件 | 职责 |
|------|------|
| `.workflow/context/roles/base-role.md` | 定义所有 stage 角色的通用硬门禁和行为准则 |
| `.workflow/context/index.md` | 修改加载顺序，在加载具体 stage 角色前先加载 base-role |
| `.workflow/tools/index/keywords.yaml` | 关键词 → 工具映射索引 |
| `.workflow/tools/index/missing-log.yaml` | 记录本地未命中且 skill hub 也未找到的工具查询 |
| `.workflow/tools/ratings.yaml` | 工具评分数据库，累计均分 |
| `src/harness_workflow/core.py` | 实现 `tool_search`、`tool_rate`、`log_action` 等核心函数 |
| `src/harness_workflow/cli.py` | 注册 `tool-search`、`tool-rate` CLI 子命令 |
| `tests/test_cli.py` | 新增对 `tool-search` 和 `tool-rate` 的集成测试 |

---

## Task 1: 创建基础角色文件 base-role.md

**Files:**
- Create: `.workflow/context/roles/base-role.md`

- [ ] **Step 1: 编写 base-role.md**

创建 `.workflow/context/roles/base-role.md`，内容如下：

```markdown
# Base Role

本文件是 Harness 工作流所有 stage 角色的抽象父类。各 stage 角色文件在加载时，必须先读取本文件，再叠加自身特定约束。

## 硬门禁一：工具优先

在执行任何实质性操作前，必须先启动 `toolsManager` subagent 查询可用工具：
1. 读取 `.workflow/tools/index/keywords.yaml`，按关键词匹配
2. 若有匹配，优先使用匹配的工具
3. 若本地无匹配，查询 skill hub（`https://skillhub.cn/skills/find-skills`）
4. 若 skill hub 也未找到，才允许由模型自行判断

## 硬门禁二：操作说明与日志

每执行一个操作前，必须在对话中说明："接下来我要执行 [操作名称]"；执行后，必须说明："执行完成，结果是 [结果摘要]"。同时，将操作摘要追加到 `.workflow/state/action-log.md`。

## 通用准则

- 上下文负载达到阈值时（消息 >100 / 读取 >50 / 时长 >2h），主动建议维护
- 遇到职责外问题时，记录到 `session-memory.md` 的 `## 待处理捕获问题` 区块
- 每个 stage 的特有行为在 `base-role.md` 之后加载

## toolsManager 调用规范

- 将当前操作意图用关键词形式传递给 toolsManager
- 接收返回的 `tool_id`、`使用说明` 和 `confidence`
- 一个任务周期内，同类型的工具查询结果可复用
```

- [ ] **Step 2: Commit**

```bash
git add .workflow/context/roles/base-role.md
git commit -m "feat: add base-role.md as abstract parent for all stages"
```

---

## Task 2: 修改角色加载顺序

**Files:**
- Modify: `.workflow/context/index.md`

- [ ] **Step 1: 在 index.md Step 2 中插入 base-role 加载**

修改 `.workflow/context/index.md`，在 Step 2 的表格后面、"角色文件包含该阶段的完整行为约束"之前，插入以下段落：

```markdown
### 加载基础角色

在加载具体 stage 角色文件前，**必须先加载** `.workflow/context/roles/base-role.md`。`base-role.md` 中定义的通用硬门禁和行为准则对所有 stage 角色生效。
```

并修改加载顺序速查中的 `roles/{stage}.md` 一行，改为：

```
roles/base-role.md + roles/{stage}.md  ← 基础角色 + 阶段角色
```

- [ ] **Step 2: Commit**

```bash
git add .workflow/context/index.md
git commit -m "feat: load base-role before stage-specific roles"
```

---

## Task 3: 在 core.py 中实现工具搜索和评分函数

**Files:**
- Modify: `src/harness_workflow/core.py`

- [ ] **Step 1: 在 core.py 顶部附近添加新的常量路径**

在 `STATE_RUNTIME_PATH = ".workflow/state/runtime.yaml"` 附近，添加：

```python
TOOL_KEYWORDS_PATH = Path(".workflow/tools/index/keywords.yaml")
TOOL_RATINGS_PATH = Path(".workflow/tools/ratings.yaml")
TOOL_MISSING_LOG_PATH = Path(".workflow/tools/index/missing-log.yaml")
ACTION_LOG_PATH = Path(".workflow/state/action-log.md")
```

（如果路径常量是以字符串形式定义的，保持风格一致即可。）

- [ ] **Step 2: 实现 `search_tools` 函数**

在 `core.py` 的 `apply_all_suggestions` 函数之后，`create_requirement` 之前，插入以下代码：

```python
def search_tools(root: Path, keywords: list[str]) -> dict[str, object] | None:
    """Search local tool index by keywords and return the best match."""
    ensure_harness_root(root)
    keywords_file = root / TOOL_KEYWORDS_PATH
    if not keywords_file.exists():
        return None

    data = load_simple_yaml(keywords_file)
    tools = data.get("tools", [])
    if not isinstance(tools, list):
        return None

    ratings_file = root / TOOL_RATINGS_PATH
    ratings: dict[str, dict[str, object]] = {}
    if ratings_file.exists():
        ratings_data = load_simple_yaml(ratings_file)
        ratings = ratings_data.get("ratings", {})
        if not isinstance(ratings, dict):
            ratings = {}

    query_set = {k.lower() for k in keywords}
    candidates: list[tuple[str, int, float]] = []  # (tool_id, overlap, score)

    for tool in tools:
        if not isinstance(tool, dict):
            continue
        tool_id = str(tool.get("tool_id", ""))
        if not tool_id:
            continue
        tool_keywords = tool.get("keywords", [])
        if not isinstance(tool_keywords, list):
            continue
        tool_set = {str(tk).lower() for tk in tool_keywords}
        overlap = len(query_set & tool_set)
        if overlap == 0:
            continue
        score = float(ratings.get(tool_id, {}).get("score", 0.0)) if isinstance(ratings.get(tool_id), dict) else 0.0
        candidates.append((tool_id, overlap, score))

    if not candidates:
        return None

    # Sort by overlap desc, score desc, then random shuffle for ties
    import random
    random.shuffle(candidates)
    candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)

    best_id = candidates[0][0]
    best_tool = next((t for t in tools if isinstance(t, dict) and t.get("tool_id") == best_id), None)
    if not best_tool:
        return None

    return {
        "tool_id": best_id,
        "catalog": str(best_tool.get("catalog", "")),
        "description": str(best_tool.get("description", "")),
        "overlap": candidates[0][1],
        "score": candidates[0][2],
    }
```

- [ ] **Step 3: 实现 `rate_tool` 函数**

紧接 `search_tools` 之后插入：

```python
def rate_tool(root: Path, tool_id: str, rating: int) -> int:
    """Rate a tool and update cumulative average in ratings.yaml."""
    ensure_harness_root(root)
    if not 1 <= rating <= 5:
        raise SystemExit("Rating must be between 1 and 5.")

    ratings_file = root / TOOL_RATINGS_PATH
    ratings_data = load_simple_yaml(ratings_file) if ratings_file.exists() else {}
    ratings = ratings_data.get("ratings", {})
    if not isinstance(ratings, dict):
        ratings = {}

    current = ratings.get(tool_id, {})
    if not isinstance(current, dict):
        current = {}
    old_score = float(current.get("score", 0.0))
    count = int(current.get("count", 0))

    new_count = count + 1
    new_score = (old_score * count + rating) / new_count if new_count > 0 else float(rating)

    ratings[tool_id] = {"score": round(new_score, 2), "count": new_count}
    ratings_data["ratings"] = ratings
    save_simple_yaml(ratings_file, ratings_data, ordered_keys=["ratings"])

    print(f"Rated {tool_id}: {new_score} (from {count} ratings)")
    return 0
```

- [ ] **Step 4: 实现 `log_action` 函数**

紧接 `rate_tool` 之后插入：

```python
def log_action(
    root: Path,
    operation: str,
    description: str,
    result: str,
    tool_id: str = "",
    rating: int | None = None,
) -> int:
    """Append an action entry to action-log.md."""
    ensure_harness_root(root)
    log_file = root / ACTION_LOG_PATH
    log_file.parent.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"## {timestamp}",
        "",
        f"- **操作**: {operation}",
        f"- **说明**: {description}",
        f"- **结果**: {result}",
        f"- **使用工具**: {tool_id if tool_id else '无'}",
    ]
    if rating is not None:
        lines.append(f"- **评分**: {rating}")
    else:
        lines.append("- **评分**: N/A")
    lines.append("")

    with log_file.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return 0
```

- [ ] **Step 5: Commit**

```bash
git add src/harness_workflow/core.py
git commit -m "feat: implement tool-search, tool-rate, and action-log in core"
```

---

## Task 4: 在 cli.py 中注册 tool-search 和 tool-rate 命令

**Files:**
- Modify: `src/harness_workflow/cli.py`

- [ ] **Step 1: 导入新函数**

在 `from harness_workflow.core import (` 块中，添加：

```python
    search_tools,
    rate_tool,
    log_action,
```

- [ ] **Step 2: 注册子命令解析器**

在 `suggest_parser = subparsers.add_parser("suggest", ...)` 之后，插入：

```python
    tool_parser = subparsers.add_parser("tool-search", help="Search local tool index by keywords.")
    tool_parser.add_argument("keywords", nargs="+", help="Keywords to search for.")
    tool_parser.add_argument("--root", default=".", help="Repository root.")

    rate_parser = subparsers.add_parser("tool-rate", help="Rate a tool and update cumulative average.")
    rate_parser.add_argument("tool_id", help="Tool ID to rate.")
    rate_parser.add_argument("rating", type=int, help="Rating from 1 to 5.")
    rate_parser.add_argument("--root", default=".", help="Repository root.")
```

- [ ] **Step 3: 处理命令分发**

在 `if args.command == "suggest":` 块之后，插入：

```python
    if args.command == "tool-search":
        root = Path(args.root)
        match = search_tools(root, args.keywords)
        if match is None:
            print("No matching tool found.")
            return 0
        print(f"Matched: {match['tool_id']}")
        print(f"Catalog: {match['catalog']}")
        print(f"Description: {match['description']}")
        print(f"Score: {match['score']}")
        return 0
    if args.command == "tool-rate":
        return rate_tool(Path(args.root), args.tool_id, args.rating)
```

- [ ] **Step 4: Commit**

```bash
git add src/harness_workflow/cli.py
git commit -m "feat: register tool-search and tool-rate CLI commands"
```

---

## Task 5: 创建 Tools 层索引和评分文件

**Files:**
- Create: `.workflow/tools/index/keywords.yaml`
- Create: `.workflow/tools/index/missing-log.yaml`
- Create: `.workflow/tools/ratings.yaml`

- [ ] **Step 1: 创建 keywords.yaml**

创建 `.workflow/tools/index/keywords.yaml`，示例内容：

```yaml
tools:
  - tool_id: "agent"
    keywords: ["subagent", "agent", "派发任务", "独立视角", "测试", "验收", "诊断"]
    catalog: "catalog/agent.md"
    description: "启动 subagent 执行独立任务"

  - tool_id: "git-commit"
    keywords: ["git", "commit", "提交代码", "保存变更"]
    catalog: "catalog/git.md"
    description: "将代码变更提交到 Git 仓库"
```

- [ ] **Step 2: 创建 missing-log.yaml**

创建 `.workflow/tools/index/missing-log.yaml`：

```yaml
# 记录本地索引和 skill hub 均未命中的查询，用于后续优化索引
queries: []
```

- [ ] **Step 3: 创建 ratings.yaml**

创建 `.workflow/tools/ratings.yaml`：

```yaml
ratings:
  agent:
    score: 4.5
    count: 2

  git-commit:
    score: 5.0
    count: 1
```

- [ ] **Step 4: Commit**

```bash
git add .workflow/tools/index/keywords.yaml .workflow/tools/index/missing-log.yaml .workflow/tools/ratings.yaml
git commit -m "feat: add tool index, ratings, and missing-log scaffolding"
```

---

## Task 6: 测试 tool-search 和 tool-rate 命令

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 在测试类中添加工具层测试**

在 `tests/test_cli.py` 末尾（或合适位置）添加：

```python
    def test_tool_search_finds_match_by_keywords(self) -> None:
        self.run_cli("init", "--root", str(self.repo))
        keywords_path = self.repo / ".workflow" / "tools" / "index" / "keywords.yaml"
        keywords_path.parent.mkdir(parents=True, exist_ok=True)
        keywords_path.write_text(
            "tools:\n"
            "  - tool_id: test-tool\n"
            '    keywords: ["test", "run", "execute"]\n'
            '    catalog: "catalog/test.md"\n'
            '    description: "A test tool"\n',
            encoding="utf-8",
        )
        result = self.run_cli("tool-search", "run", "test", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Matched: test-tool", result.stdout)
        self.assertIn("A test tool", result.stdout)

    def test_tool_search_returns_none_when_no_match(self) -> None:
        self.run_cli("init", "--root", str(self.repo))
        result = self.run_cli("tool-search", "nonexistent", "keyword", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("No matching tool found", result.stdout)

    def test_tool_rate_updates_cumulative_average(self) -> None:
        self.run_cli("init", "--root", str(self.repo))
        result = self.run_cli("tool-rate", "test-tool", "5", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        ratings_path = self.repo / ".workflow" / "tools" / "ratings.yaml"
        self.assertTrue(ratings_path.exists())
        text = ratings_path.read_text(encoding="utf-8")
        self.assertIn("test-tool:", text)
        self.assertIn("5.0", text)
        self.assertIn("count: 1", text)

        # Rate again to verify cumulative average
        result = self.run_cli("tool-rate", "test-tool", "3", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        text = ratings_path.read_text(encoding="utf-8")
        self.assertIn("count: 2", text)
```

- [ ] **Step 2: 运行测试**

```bash
PYTHONPATH=src python3 -m pytest tests/test_cli.py::HarnessCliTest::test_tool_search_finds_match_by_keywords -v
PYTHONPATH=src python3 -m pytest tests/test_cli.py::HarnessCliTest::test_tool_search_returns_none_when_no_match -v
PYTHONPATH=src python3 -m pytest tests/test_cli.py::HarnessCliTest::test_tool_rate_updates_cumulative_average -v
```

Expected: 3 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli.py
git commit -m "test: add tool-search and tool-rate CLI tests"
```

---

## Task 7: 将本次实现注册为 req-21 的变更

**Files:**
- Create: `.workflow/flow/requirements/req-21-批量建议合集（3条）/changes/chg-01-工具层重构/change.md`
- Create: `.workflow/flow/requirements/req-21-批量建议合集（3条）/changes/chg-01-工具层重构/plan.md`

- [ ] **Step 1: 创建 change.md**

```markdown
# Change: chg-01

## Title

工具层重构：基础角色、工具索引、评分与操作日志

## Goal

实现设计文档 `docs/superpowers/specs/2026-04-16-tool-layer-refactor-design.md` 中定义的全部内容。

## Scope

**包含**：
- `base-role.md` 及加载顺序修改
- `keywords.yaml`、`ratings.yaml`、`missing-log.yaml`
- `tool-search`、`tool-rate` CLI 命令
- `action-log.md` 写入逻辑
- 对应测试

**不包含**：
- skill hub 的真实网络请求实现（当前仅预留接口）
- 重写现有 catalog 工具定义

## Acceptance Criteria

- [x] `base-role.md` 已创建并被 loader 引用
- [x] `tool-search` 能按关键词返回最匹配工具
- [x] `tool-rate` 能正确计算累计均分
- [x] 新增测试全部通过
```

- [ ] **Step 2: 创建 plan.md**

将本计划文档（`docs/superpowers/plans/2026-04-16-tool-layer-refactor.md`）的核心步骤摘要写入 `plan.md`，或创建软链接/引用。

- [ ] **Step 3: Commit**

```bash
git add .workflow/flow/requirements/req-21-批量建议合集（3条）/changes/chg-01-工具层重构/
git commit -m "docs: register tool-layer refactor as chg-01 for req-21"
```

---

## Self-Review Checklist

- [x] **Spec coverage**: 所有设计文档中的功能点（base-role、tool-search、tool-rate、action-log、索引文件）均已对应到任务
- [x] **Placeholder scan**: 无 TBD、TODO 或模糊描述
- [x] **Type consistency**: `search_tools` 返回 `dict[str, object] | None`，`rate_tool` 接收 `int`，与 CLI 和测试一致
