---
id: bugfix-11
title: "install runtime.yaml 反写 3 bug：gstack_status 丢失 + 多重 quote + active_requirements 清空"
created_at: 2026-05-08
operation_type: bugfix
stage: regression
---

## 现场摘要

bugfix-11（install runtime.yaml 反写 3 bug：gstack_status 丢失 + 多重 quote + active_requirements 清空）触发自 req-55（gstack 和 harness 工作流融合-分支 harness-gstack 落地完毕） archive 后，用户跑 `harness install --agent claude` 验证 chg-01 端到端真活时；chg-01 vendor 推送本身工作正常（"[gstack] Pushed 46 skills to /Users/jiazhiwei/.claude/skills" 真实输出），但 install 命令对 `.workflow/state/runtime.yaml` 的状态反写带 3 个边界 bug。

### B1：runtime.yaml 字段值多重 quote 累积

- **复现命令**：`harness install --agent claude`
- **观察现象**：
  - 第 1 次：`stage_entered_at: "'2026-05-08T03:30:00.000000+00:00'"`、`locked_requirement: "''"`
  - 第 2 次：`stage_entered_at: "'''2026-05-08T03:30:00.000000+00:00'''"`、`locked_requirement: "''''''"`
  - 第 3 次（当前 runtime.yaml 实测）：`stage_entered_at: "'''2026-05-08T03:30:00.000000+00:00'''"`、`locked_requirement: "''''''"`
- **期望行为**：跑 N 次 install 后 runtime.yaml 字段值与初态一致（idempotent）。

### B2：gstack_status 字段消失

- **复现命令**：`harness install --agent claude`
- **观察现象**：runtime.yaml 完全没有 `gstack_status:` 段；chg-01 设计要求 `_write_gstack_status` 应写入 4 子字段。当前 runtime.yaml 文件实测无 `gstack_status` 段。
- **期望行为**：runtime.yaml 含 `gstack_status: {installed_skills, vendor_version, last_install, agent_kind_compatible}` 4 子字段。

### B3：active_requirements 跨 req 状态污染

- **复现命令**：archive req-55 后状态 `active_requirements: [req-54]`，紧接着跑 `harness install --agent claude`。
- **观察现象**：install 后 active_requirements 变成空列表 `[]`，跨 req 在跑的 req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束）从 active 列表丢失。
- **期望行为**：install 命令是同步契约动作，不应改写业务流转字段 `active_requirements`。

### 独立复现（regression 阶段已完成）

诊断师在 `/tmp/runtime_test/` 用最小可复现脚本（仅调 `_write_gstack_status` + `save_requirement_runtime(load_requirement_runtime(...))` 两层调用，等价 install_agent + install_repo 链路）复现 3 个 bug：

```
=== 初态 ===
stage_entered_at: "2026-05-08T03:30:00.000000+00:00"
locked_requirement: ""
active_requirements:
  - req-XX

=== 第 1 次 install_repo line 3427 之后 ===
stage_entered_at: "'2026-05-08T03:30:00.000000+00:00'"
locked_requirement: "''"
active_requirements: []
（gstack_status 段消失）

=== 第 3 次 install 完结 ===
stage_entered_at: "'''''''2026-05-08T03:30:00.000000+00:00'''''''"
locked_requirement: "''''''''''''''"
active_requirements: []
```

每跑 1 次 install，单引号字符层数 +2。3 个 bug **同源**，由同一段 round-trip 路径触发。

## 根因诊断

### 根因总览（一句话）

`install_agent` 末尾的 `_write_gstack_status`（pyyaml `yaml.dump`）和 `install_repo` 末尾的 `save_requirement_runtime(load_requirement_runtime(...))`（自家 simple_yaml writer）**不互相兼容**：pyyaml 用单引号包字符串、simple_yaml load 不剥单引号、simple_yaml save 用 json.dumps 加双引号、简易 list 解析依赖 indent 不识别 pyyaml block-seq 0 缩进——一次 install 走两遍 round-trip 同时引入 3 类污染。

### B1 root cause（多重 quote）

- 触发点 A：`src/harness_workflow/workflow_helpers.py:8369` `_write_gstack_status` 用 `yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)`。pyyaml 默认对含特殊字符（冒号 `:`、`+` 等）的字符串选 single-quoted 风格，输出 `'2026-05-08T03:30:00.000000+00:00'` 与空字符串 `''`。
- 触发点 B：`workflow_helpers.py:3427`（`_sync_requirement_workflow_managed_files` 末尾） `save_requirement_runtime(root, load_requirement_runtime(root))`。
  - `load_simple_yaml`（line 331）调 `_parse_simple_yaml_scalar`（line 307），后者只剥 `"..."` 双引号（line 316），**不剥 `'...'` 单引号**——pyyaml 写出的 `'2026-05-08T...'` 被原样读入，字符串 value 含字面单引号字符。
  - `save_simple_yaml`（line 435）末端 `_render_yaml_scalar`（line 398）对字符串走 `json.dumps`（line 403）→ 输出双引号包裹的字符串字面：`"'2026-05-08T...'"`（外层 json 双引号，内层是 pyyaml 加的字面单引号）。
- 第 2 次 install：`yaml.safe_load` 读双引号字符串得到含字面单引号的字符串 → `yaml.dump` 必须 escape 字面单引号为 `''` → 写出 `'''2026-...'''`（3 单引号代表 1 字面单引号 + 包裹 1 层）→ simple_yaml 又把它包一层双引号 → 累积放大。
- 同样链路触发 `locked_requirement` / `current_regression` 等空字符串字段：pyyaml 把空串写成 `''` → simple_yaml 读到字面 `''`（含 2 个单引号字符的字符串）→ 写成 `"''"` → 第 2 次 yaml.dump 把 2 字面单引号 escape 成 4 → `'''''',` → 双层包裹后 `"''''''"` → 6 个单引号。
- **结论**：B1 是 simple_yaml writer 与 pyyaml writer 在同一文件上交替运行造成的 round-trip 不闭合。

### B2 root cause（gstack_status 字段消失）

- `_write_gstack_status`（line 8350）确实写入了 `gstack_status` 段（脚本复现已确认 install_agent 末尾 runtime.yaml 含 `gstack_status:` 段）。
- 紧随其后的 `install_repo` 链路最末尾 line 3427 调 `save_requirement_runtime(root, load_requirement_runtime(root))`：
  - `save_requirement_runtime`（line 655）的 `ordered_keys` 白名单（line 668-685）**不包含 `gstack_status` 也不包含 `gstack_run_log`**。
  - `save_simple_yaml`（line 438）按 `ordered_keys` 遍历输出，**不在白名单的字段被静默裁剪**。
  - 结果：`_write_gstack_status` 写入的 gstack_status 段被静默丢弃。
- **结论**：B2 是 `save_requirement_runtime` 的 ordered_keys 遗漏 gstack_status / gstack_run_log 两个新增字段（chg-01 添加 schema 时漏更新 writer 白名单）。

### B3 root cause（active_requirements 清空）

- `_write_gstack_status` 用 pyyaml `yaml.dump(default_flow_style=False)` 输出 block sequence 默认形态：dash 与父 key 同缩进（无 indent 增量）：
  ```yaml
  active_requirements:
  - req-XX
  ```
- `load_simple_yaml`（line 347）识别 list item 的判定是 `current_collection_key and indent > collection_indent`：父 key `active_requirements` 在 indent=0 → `collection_indent=0`，dash 行也在 indent=0 → `indent > collection_indent` 不成立 → list item **不被识别**，循环走到 line 382 重置 `current_collection_key=""`。
- 此时 `payload["active_requirements"]` 还是初值 `[]`（line 392 进入 collection 时初始化），dash 行被当成新顶层 key 解析（但 `- req-XX` 不含 `:` → line 384 直接 continue）→ 最终 `active_requirements` = `[]`。
- 而 simple_yaml 自家 writer（`_render_yaml_value` line 419）输出 list 用 `prefix + "  - " + item`（**有 2 空格缩进**），所以 simple_yaml 写出 simple_yaml 读得回；但 pyyaml 写出的形态 simple_yaml 读不回。
- **结论**：B3 是 `load_simple_yaml` 的简易解析器**只兼容自家 writer 输出形态**，不兼容 pyyaml block-seq 0 缩进的合法 yaml；当 `_write_gstack_status` 用 pyyaml 写完后，下一次 `load_requirement_runtime` 把所有非空 list 字段读成空 list。

### 同一根因的三相

| Bug | 触发函数 | 直接原因 |
|-----|---------|---------|
| B1 | `_write_gstack_status` (8369) → `save_requirement_runtime` (3427) | pyyaml 单引号 + simple_yaml 不剥 + json.dumps 双引号包裹 |
| B2 | `_write_gstack_status` (8332) → `save_requirement_runtime` (3427) | `ordered_keys` 白名单缺 `gstack_status` / `gstack_run_log` |
| B3 | `_write_gstack_status` (8369) → `load_requirement_runtime` (next call) | pyyaml block-seq 0 缩进与 simple_yaml `indent > collection_indent` 解析不兼容 |

**核心症结**：`runtime.yaml` 的写盘路径分裂成 2 个不兼容的 writer（pyyaml `yaml.dump` 与自家 `save_simple_yaml`），同一文件被两个 writer 交替反写时 round-trip 不闭合。

## 影响评估

### 范围

- 直接影响：每次 `harness install --agent claude` 之后 runtime.yaml 状态被破坏，subagent 加载链 Step 1 读到的字段全部带字面单引号 / 双引号污染，`current_requirement` / `stage_entered_at` 等字段语义被破坏。
- 间接影响：
  - `harness next` / `harness status` / 任意读 runtime 的 CLI 都会读到污染字段（render_work_item_id 输出错误 title）；
  - active_requirements 被清空 → `harness archive` 后续派发链路找不到当前在跑 req → CLI 走错分支；
  - gstack_status 丢失 → chg-01 acceptance "runtime 含 4 子字段" 这条 AC 失证，`harness install --agent claude` 反复跑无法稳态收口。

### 严重度

- **P0 阻塞**：runtime.yaml 是 harness workflow 的状态权威源，这 3 bug 让 `harness install` 自身不再 idempotent，同步契约自废武功。
- 新装项目（fresh init）跑一次 install 即被污染；存量项目每跑一次 install 累积加重。

### 是否阻塞 chg-01 acceptance

是。req-55 / chg-01 的 AC（gstack_status 4 子字段写入 + install idempotent）实际未通过，archive 时 acceptance 报告为虚报。**建议 retroactive 重 archive req-55**：在本 bugfix-11 完成 + chg-01 实际过 acceptance 后，把 req-55 状态从 archived 滚回 acceptance 重跑，并在 archive commit 中追加修订说明。

### 是否需要扩散到下游清理

是：当前仓库 runtime.yaml 已被污染（外层双引号 + 内层 6 单引号），需要在 fix 落地后人工修复一次（或 fix patch 自带 self-heal：load 时按正则剥多重单引号）。

## 修复方案

### 方案 A（最小修复，分 3 fix 互不干涉）

- A1 修 B1：`_parse_simple_yaml_scalar` 增加单引号剥除逻辑（与双引号对称），并对多重 `''''''` 做 self-heal 剥层；同时 `_render_yaml_scalar` 保持现状。
- A2 修 B2：`save_requirement_runtime.ordered_keys` 白名单追加 `gstack_status` / `gstack_run_log`（同步 DEFAULT_STATE_RUNTIME 已有的 schema）。
- A3 修 B3：`load_simple_yaml` 兼容 pyyaml block-seq 形态——把 list item 识别条件从 `indent > collection_indent` 改为 `indent >= collection_indent`（前提：dash 行才算 item，不会与 sibling 顶层 key 混淆，因为 sibling 不是 dash 开头）。
- 同时把 `_write_gstack_status` 改成走 `save_requirement_runtime`（不是 yaml.dump 直写）。

**优点**：3 fix 各自独立、可分别验证、最少回归面。
**缺点**：仍保留 pyyaml writer 与 simple_yaml writer 两套，未来再加新字段、再有第二个 writer 触点时旧坑可能重现。

### 方案 B（统一 runtime.yaml writer，单一来源）

- 删除 `_write_gstack_status` 内的 `yaml.safe_load + yaml.dump` 直写路径；改为 `runtime = load_requirement_runtime(root); runtime["gstack_status"] = status; save_requirement_runtime(root, runtime)`。
- 同时把 `save_requirement_runtime.ordered_keys` 白名单补全 gstack_status / gstack_run_log。
- 确认仓库内**所有** `runtime.yaml` 写盘点都走 `save_requirement_runtime`（grep `STATE_RUNTIME_PATH` + `runtime_path.write_text`），消除 pyyaml 直写第二条路径。
- 不改 simple_yaml load/save 的 round-trip 不闭合问题（无 pyyaml 直写后，没有 round-trip 触发条件）。

**优点**：根除多 writer 不兼容；保持 simple_yaml writer 行为不变（避免触动其他 state yaml）；改动量最小化（只动 1 个直写点）。
**缺点**：当前仓库已被污染的 runtime.yaml 仍需手工修复一次。

### 方案 C（深修 + 加契约 lint）

- 方案 B 的内容；
- 加新 contract `runtime-yaml-shape`：`harness validate --contract runtime-yaml-shape` 检测 runtime.yaml 多重单引号、缺 gstack_status 字段、active_requirements 类型不为 list；CI 与 install 自检都跑。
- 加 pytest：`test_install_runtime_idempotent`，连跑 N 次 install_agent + install_repo，每次 assert runtime.yaml 文件 hash 不变（在固定输入下）。
- 加 schema-aware writer 注释：在 `save_requirement_runtime` 上方加注释 + grep guard：`grep -nE "yaml\.(dump|safe_dump).*runtime" workflow_helpers.py` 应只返回 0 命中。

**优点**：把"runtime.yaml 单一 writer"上升为契约层硬约束；防再犯。
**缺点**：本次 bugfix 范围扩大（增加 1 个 contract、1 套 pytest），交付面变宽。

### 选定方案：B（default-pick）

**决策理由**：
- B1/B2/B3 同源（同一 round-trip 路径），统一一个写盘点即同时根治 3 bug；
- 不动 simple_yaml writer 行为，最小化对其他 state yaml（requirements / bugfixes / sessions）的回归面；
- 比 A 改动小（只动 1 个函数 + 1 行白名单 + 1 次仓库 runtime 自愈），比 C 范围窄（不加 contract + pytest 套件，本 bugfix 一次落地）；
- 方案 C 的 contract / pytest 套件可作为后续 sug 推到 suggest 池跟进，不阻塞本 bugfix。

### 后续 executing 阶段动作清单

1. 改 `_write_gstack_status`（workflow_helpers.py:8350）：删除内部的 `yaml.safe_load + yaml.dump` 直写，改为 `runtime = load_requirement_runtime(root); runtime["gstack_status"] = status; if gstack_run_log: runtime["gstack_run_log"] = ...; save_requirement_runtime(root, runtime)`。
2. 改 `save_requirement_runtime.ordered_keys`（workflow_helpers.py:668-685）：在 `active_requirements` 后追加 `"gstack_status"` 和 `"gstack_run_log"`。
3. self-heal：`load_simple_yaml` / `_parse_simple_yaml_scalar` 加 `'...'` 剥层逻辑（兼容历史已被污染的 runtime.yaml；剥 N 层成对单引号直到剥不动）；不改 save 路径。这条作为 forward-compat fallback，让被污染的存量项目能恢复。
4. grep guard：`grep -nE "yaml\.(dump|safe_dump)\s*\(.+runtime" src/harness_workflow/workflow_helpers.py` 必须返回 0 命中（人工自检）。
5. 修当前仓库 `.workflow/state/runtime.yaml`：手动剥除多重单引号字段（或跑一次 fix 后的 install 让它自愈）。
6. 给 chg-01（gstack 和 harness 工作流融合 vendor 落地）的 acceptance 重测：连跑 3 次 install --agent claude，runtime.yaml 必须保持 idempotent + 含 gstack_status 段 + active_requirements 不变。

## 测试用例设计

> regression_scope: targeted
> 波及接口清单（git diff --name-only HEAD 修复后 + 修复方案波及面手工补全）：
> - src/harness_workflow/workflow_helpers.py（`_write_gstack_status` + `save_requirement_runtime` + `_parse_simple_yaml_scalar` 三处改动）
> - tests/test_install_runtime_idempotent.py（新增）
> - .workflow/state/runtime.yaml（仓库自愈，非代码改动）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 install_agent + install_repo round-trip 1 次保持 idempotent | 干净初态 runtime.yaml（无 quote 累积、无 gstack_status） + 模拟 `harness install --agent claude` | runtime.yaml 含 `gstack_status` 段（4 子字段）+ 无多重 quote + active_requirements 保留原 list | AC-B1 / AC-B2 / AC-B3 | P0 |
| TC-02 连跑 3 次 install 仍稳态 | 同 TC-01 初态，连跑 install 3 轮 | 第 3 轮后 runtime.yaml 与第 1 轮后字面一致（last_install 时间戳除外）；字段值无单引号字面字符累积 | AC-B1 | P0 |
| TC-03 _write_gstack_status 单测：写后 ordered_keys 不裁剪 | 调 `_write_gstack_status(root, {installed_skills: [...], vendor_version: ..., last_install: ..., agent_kind_compatible: True})` | runtime.yaml 含 `gstack_status:` 段 + 4 子字段；后续 `save_requirement_runtime(root, load_requirement_runtime(root))` 不丢失该段 | AC-B2 | P0 |
| TC-04 active_requirements 跨 install 保留 | runtime.yaml 含 `active_requirements: [req-54, req-55]`，跑 `install --agent claude` | install 后 active_requirements 仍为 `[req-54, req-55]`；不被清空、不被改写顺序 | AC-B3 | P0 |
| TC-05 _parse_simple_yaml_scalar self-heal 剥多重单引号 | 输入字符串 `"''''''"` / `"'''2026-05-08T03:30:00.000000+00:00'''"` | 解析为 `""` / `"2026-05-08T03:30:00.000000+00:00"`（成对剥到剥不动） | AC-B1 forward-compat | P1 |
| TC-06 load_simple_yaml 兼容 pyyaml block-seq 0 缩进 | yaml 文本 `active_requirements:\n- req-X\n- req-Y\n` | 解析为 `{"active_requirements": ["req-X", "req-Y"]}` | AC-B3 forward-compat | P1 |
| TC-07 grep guard：runtime 写盘单一 writer | grep `yaml\.(dump|safe_dump)\s*\(.+runtime` 在 workflow_helpers.py 全文 | 0 命中（修复后所有 runtime.yaml 写盘统一走 `save_requirement_runtime`） | 方案 B 不变量 | P1 |
| TC-08 仓库当前已污染 runtime 自愈回归 | 当前仓库 .workflow/state/runtime.yaml（含 6 单引号字段污染） + 一次 install --agent claude | runtime.yaml 字段值复位为干净形态；3 bug 全清 | 端到端验证 | P0 |
| TC-09 chg-01 retroactive acceptance | 修复落地后跑 chg-01 acceptance 完整链路（install 3 次 + runtime 检查） | gstack_status 4 子字段持久 + 字段无 quote 累积 + active_requirements 稳定 | chg-01 AC | P0 |
| TC-10 ordered_keys 白名单完整性 | 单测 `save_requirement_runtime` 后 `load_requirement_runtime` round-trip | DEFAULT_STATE_RUNTIME 中所有顶层 key 都在 ordered_keys 中（含 gstack_status / gstack_run_log） | AC-B2 完整性 | P1 |

## 结论

- **路由**：confirm（真实问题，3 bug 同源已复现 + 根因锁定到具体行号）
- **目标阶段**：executing（实现/写盘契约问题，非需求/设计问题）
- **推荐执行步骤**：按方案 B 的 "executing 阶段动作清单"（6 步）执行；TC-01~TC-10 的测试用例在 testing 阶段补全验证。
