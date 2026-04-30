---
id: chg-01
title: "契约层路径迁移：项目级承载层从 artifacts/{branch}/project/ 改为 artifacts/project/（双轨过渡）+ scaffold mirror 同步"
requirement: req-52
operation_type: plan
---

# Change Plan

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 `.workflow/flow/repository-layout.md`（live）

**变更点 A：§1 三大子树语义总览段尾注脚**（第 25 行 `artifacts/{branch}/` 行后既有注脚段）：

- 把现有注脚中的 `artifacts/{branch}/project/{constraints,experience,tools}/` 改为 `artifacts/project/{constraints,experience,tools}/`（**无 branch 维度，跟项目走**）；
- 注脚尾追加一句："legacy 路径 `artifacts/{branch}/project/` 作为加载链 fallback 兼容存量，详见 §2.1 双轨过渡段；后续 req 收口退役。"

**变更点 B：§2.1 项目级机器型豁免段重写**（约第 93-107 行）：

- 表内 3 行子树路径全部从 `artifacts/{branch}/project/...` 改为 `artifacts/project/...`；
- 表后新增"双轨过渡 fallback"子段：

```markdown
#### 双轨过渡 fallback（req-52 / chg-01）

> req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ OQ-A = D-modified：主路径迁移 + legacy 兼容。

- **主路径**：`artifacts/project/{constraints,experience,tools}/`（**无 branch 维度，跟项目走**）；新建一律入此；
- **legacy fallback**：`artifacts/{branch}/project/{constraints,experience,tools}/`（req-51 OQ-1 = B-modified 原路径）作为加载链 fallback 兼容存量；当主路径不存在但 legacy 存在时，加载链命中 legacy 并 stderr 记录 `(fallback=...)`；
- **`harness install` / `update` 主流程行为**：两条路径**均**不被 mirror 覆盖（`_SCAFFOLD_V2_MIRROR_WHITELIST` 含 `artifacts/project/` + `artifacts/{branch}/project/` 双条目，详见 chg-02）；
- **退役计划**：legacy 路径在后续 req（一次大版本归档）统一退役为只读，不在 req-52 内删除。
```

**变更点 C：§3 顶部豁免说明段重写**（约第 119-124 行）：

- 把现有三 bullet 路径全部从 `artifacts/{branch}/project/...` 改为 `artifacts/project/...`；
- bullet 后追加一句："legacy 路径 `artifacts/{branch}/project/{constraints,experience,tools}/` 由 §2.1 双轨过渡 fallback 描述兼容；本节落位表以主路径 `artifacts/project/` 为权威。"

**变更点 D：§3.2 bugfix 段顶部豁免说明**（保持口径一致）：

- 现有"req-51 三类项目级豁免（§2.1 / §3 顶部）**不**适用于 bugfix 子树"行不动，仅在末尾追加："（req-52 / chg-01 路径迁移到 `artifacts/project/` 后，本豁免范围语义不变。）"

### 1.2 `.workflow/context/roles/harness-manager.md`（live）

**变更点 E：硬门禁五例外白名单段**（约第 48 行现有 `artifacts/{branch}/project/` 条目）：

- 把现有 `artifacts/{branch}/project/` 条目拆为 2 条：
  ```markdown
  - `artifacts/project/`（req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-01（契约层路径迁移-无branch项目级-双轨过渡）OQ-A = D-modified；项目级机器型文档承载层主路径，跟项目走不跟 branch；硬门禁五配套豁免详见 chg-02（src硬编码main全面去除-branch-aware））
  - `artifacts/{branch}/project/`（legacy fallback，req-51（项目级规则-经验-工具支持从制品引入）OQ-1 = B-modified 原路径，由 req-52 OQ-A 双轨过渡兼容；后续 req 收口退役）
  ```

### 1.3 `.workflow/context/roles/role-loading-protocol.md`（live）

**变更点 F：Step 7.6 项目级承载路径段**（约第 131-141 行）：

- "项目级承载路径"段第一句：`artifacts/{branch}/project/{constraints,experience,tools}/` 改为 `artifacts/project/{constraints,experience,tools}/`（双轨过渡，详见 §2.1）；
- "加载顺序"表内"阶段 2"路径从 `artifacts/{branch}/project/constraints/...` 改为 `artifacts/project/constraints/...`；
- 表后新增 fallback 段：
  ```markdown
  #### fallback（req-52 / chg-01 双轨过渡）

  - 主路径 `artifacts/project/` 不存在 → fallback 到 legacy `artifacts/{branch}/project/`；命中后 agent 在首条输出追加 `（fallback=artifacts/{branch}/project/）` 提示用户后续 req 将退役 legacy 路径；
  - 主路径 + legacy 均不存在 → 静默跳过，不报错（与 task_context_index 回退语义一致）。
  ```

### 1.4 `.workflow/context/roles/tools-manager.md`（live）

**变更点 G：Step 2.0 项目级合并段**（约第 16-43 行）：

- "读取全局" 块内 `project_keywords / project_ratings / project_catalog / project_protocols` 4 个变量路径从 `artifacts/{branch}/project/tools/...` 改为 `artifacts/project/tools/...`；
- 表内"项目级路径（以 main 分支为例）"列改为"项目级路径（主路径无 branch）"，4 行 path 改为 `artifacts/project/tools/index/keywords.yaml` / `ratings.yaml` / `catalog/` / `protocols/`；
- "全部缺失"行从 `artifacts/main/project/tools/` 改为 `artifacts/project/tools/`；
- 输出说明行 `**catalog**` 字段路径示例从 `artifacts/main/project/tools/catalog/{tool_id}.md` 改为 `artifacts/project/tools/catalog/{tool_id}.md`；
- 段尾追加 fallback：legacy `artifacts/{branch}/project/tools/` 路径作为加载链 fallback。

### 1.5 scaffold_v2 mirror 同步（4 份）

- `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`：完全镜像 1.1 全部变更点 A / B / C / D；
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`：完全镜像 1.2 变更点 E；
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md`：完全镜像 1.3 变更点 F；
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md`：完全镜像 1.4 变更点 G；
- 硬门禁五要求：与 live **同一 commit** ship。

### 1.6 `artifacts/project/` 占位

- 新建 `artifacts/project/README.md`：声明本目录由 req-52 / chg-01 OQ-A = D-modified 开放，三子目录承载项目级 constraints / experience / tools；含 legacy fallback 说明；
- 新建 `artifacts/project/constraints/.gitkeep` / `experience/.gitkeep` / `tools/.gitkeep`（空文件）。

## 2. 实施步骤（顺序 + 命令）

### Step 1：编辑 live `repository-layout.md`

- 用 Edit 工具按 1.1 变更点 A / B / C / D 顺序修改；
- 不破坏现有 §1 表 / §2 白名单表 / §3 落位表的既有行；
- 自检：

```bash
grep -nE "artifacts/project/" .workflow/flow/repository-layout.md   # 期望 ≥ 3 命中
grep -nE "artifacts/\{branch\}/project/" .workflow/flow/repository-layout.md   # 期望 ≥ 2 命中（fallback 描述）
grep -n "双轨过渡" .workflow/flow/repository-layout.md   # 期望 ≥ 1 命中
```

### Step 2：编辑 live `harness-manager.md`

- 用 Edit 工具按 1.2 变更点 E 在硬门禁五例外白名单段拆为 2 条；
- 自检：

```bash
grep -B 3 "artifacts/project/" .workflow/context/roles/harness-manager.md | grep -c "例外白名单"   # ≥ 1
grep -nE "artifacts/project/|artifacts/\{branch\}/project/" .workflow/context/roles/harness-manager.md   # 期望 ≥ 2
```

### Step 3：编辑 live `role-loading-protocol.md`

- 用 Edit 工具按 1.3 变更点 F 改 Step 7.6；
- 自检：

```bash
grep -nE "artifacts/project/\{constraints,experience,tools\}" .workflow/context/roles/role-loading-protocol.md   # 期望 ≥ 1
grep -n "fallback（req-52" .workflow/context/roles/role-loading-protocol.md   # 期望 ≥ 1
```

### Step 4：编辑 live `tools-manager.md`

- 用 Edit 工具按 1.4 变更点 G 改 Step 2.0；
- 自检：

```bash
grep -nE "artifacts/project/tools/" .workflow/context/roles/tools-manager.md   # 期望 ≥ 4（keywords / ratings / catalog / protocols）
```

### Step 5：同 commit 编辑 4 份 scaffold_v2 mirror（硬门禁五合规）

- 完全镜像 Step 1 ~ Step 4 改动到 `src/harness_workflow/assets/scaffold_v2/...` 4 份 mirror；
- 自检：

```bash
diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md   # silent
diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md   # silent
diff -q .workflow/context/roles/role-loading-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md   # silent
diff -q .workflow/context/roles/tools-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md   # silent
```

### Step 6：创建 `artifacts/project/` 占位

```bash
mkdir -p artifacts/project/constraints artifacts/project/experience artifacts/project/tools
touch artifacts/project/constraints/.gitkeep artifacts/project/experience/.gitkeep artifacts/project/tools/.gitkeep
# README.md 用 Write 工具落，含 req-52 / chg-01 引用 + legacy fallback 说明
```

### Step 7：契约自检全绿

```bash
harness validate --human-docs                  # exit 0
harness validate --contract all                # exit 0（确认未误伤）
```

## 3. 测试用例设计（≥ 3 用例）

> regression_scope: targeted（本 chg 仅改契约文档 + scaffold_v2 mirror，破坏面收敛）
> 波及接口清单（git diff --name-only 预估）：
> - `.workflow/flow/repository-layout.md`
> - `.workflow/context/roles/harness-manager.md`
> - `.workflow/context/roles/role-loading-protocol.md`
> - `.workflow/context/roles/tools-manager.md`
> - `src/harness_workflow/assets/scaffold_v2/` 下 4 份 mirror
> - `artifacts/project/README.md`（新建）+ 3 个 .gitkeep

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-契约段落落地（repository-layout） | grep `artifacts/project/` 与 `双轨过渡` 在 `repository-layout.md` 中存在 | `grep -c "artifacts/project/"` ≥ 3；含 §2.1 "双轨过渡 fallback（req-52 / chg-01）"标题行 | AC-01 | P0 |
| TC-02-硬门禁五双轨白名单 | grep `harness-manager.md` 硬门禁五例外白名单段 | `grep -nE "artifacts/project/" .workflow/context/roles/harness-manager.md` 命中 ≥ 1；`grep -nE "artifacts/\{branch\}/project/" .workflow/context/roles/harness-manager.md` 命中 ≥ 1（legacy fallback 条目）；位置在 `**例外白名单**` 段内 | AC-01 / AC-08 | P0 |
| TC-03-role-loading-protocol fallback 描述 | grep `role-loading-protocol.md` Step 7.6 段 | `grep -nE "artifacts/project/\{constraints,experience,tools\}" .workflow/context/roles/role-loading-protocol.md` ≥ 1；`grep -n "fallback（req-52" .workflow/context/roles/role-loading-protocol.md` ≥ 1 | AC-01 / AC-02 | P0 |
| TC-04-tools-manager 路径同步 | grep `tools-manager.md` Step 2.0 项目级合并段 | `grep -cE "artifacts/project/tools/" .workflow/context/roles/tools-manager.md` ≥ 4（keywords / ratings / catalog / protocols 4 行） | AC-01 | P0 |
| TC-05-scaffold mirror 字节级同步 | live + mirror 4 份比对 | `diff -q` 4 对全 silent | AC-08 | P0 |
| TC-06-人文档 lint 全绿 | `harness validate --human-docs` | exit code = 0；本次改动未引入对人文档新违规 | AC-08 | P1 |
| TC-07-占位目录与 README 存在 | `artifacts/project/{README.md, constraints/.gitkeep, experience/.gitkeep, tools/.gitkeep}` | 4 个文件均 `os.path.exists` True；README.md 包含字符串 `req-52` 与 `OQ-A` 与 `跟项目走` | AC-01 | P1 |

## 4. 验收 lint 命令字面（grep / pytest，executing 不得偷换关键词）

```bash
# L1：契约段落落地（repository-layout.md）
grep -c "artifacts/project/" .workflow/flow/repository-layout.md
grep -n "双轨过渡 fallback（req-52 / chg-01）" .workflow/flow/repository-layout.md
grep -n "OQ-A = D-modified" .workflow/flow/repository-layout.md

# L2：硬门禁五例外白名单双轨条目
grep -B 3 "artifacts/project/" .workflow/context/roles/harness-manager.md | grep -c "例外白名单"
grep -nE "artifacts/project/" .workflow/context/roles/harness-manager.md
grep -nE "artifacts/\{branch\}/project/" .workflow/context/roles/harness-manager.md

# L3：role-loading-protocol Step 7.6 fallback
grep -nE "artifacts/project/\{constraints,experience,tools\}" .workflow/context/roles/role-loading-protocol.md
grep -n "fallback（req-52" .workflow/context/roles/role-loading-protocol.md

# L4：tools-manager Step 2.0 路径同步
grep -cE "artifacts/project/tools/" .workflow/context/roles/tools-manager.md

# L5：scaffold mirror 字节级同源（4 对）
diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md
diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
diff -q .workflow/context/roles/role-loading-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md
diff -q .workflow/context/roles/tools-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md

# L6：契约自检全绿
harness validate --human-docs
harness validate --contract all

# L7：占位 README + .gitkeep
test -f artifacts/project/README.md
test -f artifacts/project/constraints/.gitkeep
test -f artifacts/project/experience/.gitkeep
test -f artifacts/project/tools/.gitkeep
grep -E "req-52|OQ-A|跟项目走" artifacts/project/README.md
```

## 5. scaffold_v2 mirror 同步清单（硬门禁五）

| live 文件 | mirror 文件 | 同步动作 |
|-----------|------------|---------|
| `.workflow/flow/repository-layout.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` | 同 commit 镜像变更点 A / B / C / D |
| `.workflow/context/roles/harness-manager.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` | 同 commit 镜像变更点 E |
| `.workflow/context/roles/role-loading-protocol.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md` | 同 commit 镜像变更点 F |
| `.workflow/context/roles/tools-manager.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md` | 同 commit 镜像变更点 G |

**mirror 同步硬门禁自检**（reviewer 阶段必跑）：

```bash
# 必须四对全 silent；任一非 silent → reviewer FAIL
diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md
diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
diff -q .workflow/context/roles/role-loading-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md
diff -q .workflow/context/roles/tools-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md
```

**注意**：`artifacts/project/README.md` + 3 个 `.gitkeep` **不**纳入 mirror（artifacts/ 子树不属于硬门禁五保护面，且 chg-01（req-51 契约底座）已活证示范）。
