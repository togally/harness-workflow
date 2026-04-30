---
id: chg-01
title: "契约底座：artifacts/{branch}/project/ 豁免段 + 硬门禁五例外白名单 + scaffold_v2 mirror 同步"
requirement: req-51
operation_type: plan
---

# Change Plan

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 `.workflow/flow/repository-layout.md`（live）

**变更点 A：§1 三大子树语义总览段尾追加**（约第 25 行 `artifacts/{branch}/` 那一行后插入注脚）：

> 注：`artifacts/{branch}/project/{constraints,experience,tools}/` 三类项目级机器型文档由 req-51（项目级规则-经验-工具支持从制品引入）显式豁免本表"不出现机器型文档"原则；详见 §2 白名单新增段与 §3 顶部豁免说明段。豁免范围**仅限**这三类，其他机器型文档（requirement.md / change.md / plan.md / session-memory.md / yaml / 报告类等）严禁入 artifacts/ 不变。

**变更点 B：§2 对人文档白名单段尾**（紧接现有"其他对人产物 兜底"行后）追加新段：

```markdown
### 2.1 项目级机器型豁免段（req-51（项目级规则-经验-工具支持从制品引入）OQ-1 = B-modified）

`artifacts/{branch}/project/{constraints,experience,tools}/` 是 req-51 显式开放的项目级承载层，**仅限**以下三类文档存入：

| 子树 | 语义 | 产出者 | 消费者 |
|------|------|--------|--------|
| `artifacts/{branch}/project/constraints/` | 项目独有规则 / 边界约束 | 下游用户（项目团队） | 全部 stage 角色（按 §3 加载链项目级覆盖全局） |
| `artifacts/{branch}/project/experience/` | 项目独有经验沉淀（roles / tool / risk / regression / stage 五分类同 `.workflow/context/experience/` schema） | 下游用户 + done 阶段沉淀 | stage 角色按经验加载规则匹配 |
| `artifacts/{branch}/project/tools/` | 项目独有工具 catalog / index / protocols / keywords | 下游用户 | tools-manager（按项目级覆盖全局规则匹配） |

**与全局 §1 "artifacts 不出现机器型文档"原则的关系**：本豁免**仅限**上列三类项目级机器型文档；其他机器型文档（如 requirement.md / change.md / plan.md / session-memory.md / yaml / 报告类）继续严禁入 artifacts/。豁免不放大保护面，不破坏 bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） 已立的底座。

**与 OQ-2 = A 项目级覆盖全局策略的关系**：项目级三类目录在加载链中**优先于** `.workflow/context/{constraints,experience}/` 与 `.workflow/tools/`（详见 chg-03（加载层覆盖-tools-项目级合并））；`harness validate --contract user-write-protected-zones` 对本目录自动豁免（详见 chg-02（升级保护-mirror-protected-双豁免））。

**与 mirror 同步契约（硬门禁五）的关系**：本路径**不**纳入 `src/harness_workflow/assets/scaffold_v2/` mirror 同步；`harness install` / `harness install --force-managed` / `harness update` 全流程跳过本路径（详见 chg-02）。
```

**变更点 C：§3 机器型文档权威落位段顶部插入豁免说明**（紧接 `**机器型文档**定义...` 段后）：

```markdown
> **req-51（项目级规则-经验-工具支持从制品引入）OQ-1 = B-modified 豁免说明**：以下三类项目级机器型文档由 §2.1 显式开放、由本节豁免：
> - `artifacts/{branch}/project/constraints/`
> - `artifacts/{branch}/project/experience/`
> - `artifacts/{branch}/project/tools/`
>
> 其他机器型文档（req / chg / regression / bugfix 级 requirement.md / change.md / plan.md / session-memory.md / yaml / 报告类等）继续按本节落 `.workflow/flow/requirements/` 子树，不豁免。
```

**变更点 D：§3.2 bugfix 段顶部同样插入对应豁免说明**（保持口径一致，避免 bugfix 路径被误读为也在豁免内）：

```markdown
> 注：req-51 三类项目级豁免（§2.1 / §3 顶部）**不**适用于 bugfix 子树；bugfix 机器型文档继续落 `.workflow/flow/bugfixes/` 子树。
```

### 1.2 `.workflow/context/roles/harness-manager.md`（live）

**变更点 E：硬门禁五例外白名单新增 1 条**（约第 37-48 行 `**例外白名单**` 表，在 `.workflow/context/team/` / `.workflow/context/project/` 等本项目独有子树条目附近追加）：

```markdown
- `artifacts/{branch}/project/`（req-51（项目级规则-经验-工具支持从制品引入）OQ-1 = B-modified；三类项目级机器型文档承载层 `constraints/` / `experience/` / `tools/`，跨项目语义不通用，由 §3 加载链项目级覆盖全局规则消费；硬门禁五配套豁免详见 chg-02（升级保护-mirror-protected-双豁免））
```

### 1.3 `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`（mirror）

- **完全镜像 1.1 全部变更点 A / B / C / D**，与 live 字节级一致；
- 硬门禁五要求：与 live 必须**同一 commit** ship。

### 1.4 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`（mirror）

- **完全镜像 1.2 变更点 E**，与 live 字节级一致。

### 1.5 `artifacts/main/project/`（占位）

- 新增 `artifacts/main/project/README.md`：声明本目录由 req-51 OQ-1 = B-modified 开放，三子目录承载项目级 constraints / experience / tools；
- 新增 `artifacts/main/project/constraints/.gitkeep` / `experience/.gitkeep` / `tools/.gitkeep`（空文件）。

## 2. 实施步骤（顺序 + 命令）

### Step 1：编辑 live `repository-layout.md`

- 用 Edit 工具按 1.1 变更点 A / B / C / D 顺序插入；
- 不破坏现有 §1 表 / §2 白名单表 / §3 落位表的既有行；
- 命令：（executing 阶段执行）

```bash
# 自检本次改动只改了 4 个段落
git diff .workflow/flow/repository-layout.md | grep -E "^(\+|\-)" | wc -l   # 期望：仅改动行
```

### Step 2：编辑 live `harness-manager.md`

- 用 Edit 工具按 1.2 变更点 E 在硬门禁五例外白名单段追加；
- 不破坏其他段落。

### Step 3：同 commit 编辑 mirror（硬门禁五合规）

- 完全镜像 Step 1 / Step 2 改动到 `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 与 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`；
- 自检：

```bash
diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md   # 期望 silent
diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md   # 期望 silent
```

### Step 4：创建 `artifacts/main/project/` 占位

```bash
mkdir -p artifacts/main/project/constraints artifacts/main/project/experience artifacts/main/project/tools
touch artifacts/main/project/constraints/.gitkeep artifacts/main/project/experience/.gitkeep artifacts/main/project/tools/.gitkeep
# README.md 用 Write 工具落，内容声明本目录是 req-51 项目级承载层
```

### Step 5：契约自检

```bash
harness validate --human-docs                  # exit 0
harness validate --contract all                # exit 0（确认未误伤）
grep -nE "artifacts/\{branch\}/project/" .workflow/flow/repository-layout.md   # 期望 ≥ 3 命中（§1 注脚 + §2.1 + §3 豁免说明）
grep -nE "artifacts/\{branch\}/project/" .workflow/context/roles/harness-manager.md   # 期望 ≥ 1 命中（硬门禁五例外白名单）
```

## 3. 测试用例设计（≥ 3 用例）

> regression_scope: targeted（本 chg 仅改契约文档 + scaffold_v2 mirror，破坏面收敛在 repository-layout / harness-manager 两文件 + mirror 副本）
> 波及接口清单（git diff --name-only 预估）：
> - `.workflow/flow/repository-layout.md`
> - `.workflow/context/roles/harness-manager.md`
> - `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`
> - `artifacts/main/project/README.md`（新建 + 3 个 .gitkeep）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-契约段落落地 | grep 三类豁免段在 `repository-layout.md` 中存在 | `grep -c "artifacts/{branch}/project/"` ≥ 3；含 §2.1 标题"项目级机器型豁免段"行 | AC-01 | P0 |
| TC-02-硬门禁五白名单扩展 | grep `harness-manager.md` 硬门禁五例外白名单段 | `grep -nE "artifacts/\{branch\}/project/" .workflow/context/roles/harness-manager.md` 命中 ≥ 1；位置在 `**例外白名单**` 段内（grep 上下文 -B 3 含字符串 "例外白名单"） | AC-04 | P0 |
| TC-03-scaffold mirror 同步契约 | live + mirror 字节比对 | `diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` silent；`diff -q` harness-manager.md 同源对比 silent | AC-04（mirror 同步豁免依赖契约文件本身先 mirror 同步） | P0 |
| TC-04-人文档 lint 全绿 | `harness validate --human-docs` | exit code = 0；本次改动未引入对人文档新违规 | AC-01 | P1 |
| TC-05-占位目录与 README 存在 | `artifacts/main/project/{README.md, constraints/.gitkeep, experience/.gitkeep, tools/.gitkeep}` | 5 个文件均 `os.path.exists` True；README.md 包含字符串 `req-51` 与 `OQ-1` | AC-01（路径承载） | P1 |

## 4. 验收 lint 命令字面（grep / pytest，executing 不得偷换关键词）

```bash
# L1：契约段落落地
grep -c "artifacts/{branch}/project/" .workflow/flow/repository-layout.md
grep -n "项目级机器型豁免段" .workflow/flow/repository-layout.md
grep -n "OQ-1 = B-modified" .workflow/flow/repository-layout.md

# L2：硬门禁五例外白名单扩展
grep -B 3 "artifacts/{branch}/project/" .workflow/context/roles/harness-manager.md | grep -c "例外白名单"

# L3：scaffold mirror 字节级同源
diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md
diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md

# L4：契约自检全绿
harness validate --human-docs
harness validate --contract all

# L5：占位 README + .gitkeep
test -f artifacts/main/project/README.md
test -f artifacts/main/project/constraints/.gitkeep
test -f artifacts/main/project/experience/.gitkeep
test -f artifacts/main/project/tools/.gitkeep
grep -E "req-51|OQ-1" artifacts/main/project/README.md
```

## 5. scaffold_v2 mirror 同步清单（硬门禁五）

| live 文件 | mirror 文件 | 同步动作 |
|-----------|------------|---------|
| `.workflow/flow/repository-layout.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` | 同 commit 镜像变更点 A / B / C / D |
| `.workflow/context/roles/harness-manager.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` | 同 commit 镜像变更点 E |

**mirror 同步硬门禁自检**（reviewer 阶段必跑）：

```bash
# 必须双双 silent；任一非 silent → reviewer FAIL
diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md
diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
```

**注意**：`artifacts/main/project/README.md` + 3 个 `.gitkeep` **不**纳入 mirror（artifacts/ 子树不属于硬门禁五保护面，且本 chg-01 拍板"项目级路径不进 scaffold_v2 mirror"是 OQ-4 = A 的核心要义，本 chg 自身做活证示范）。
