# Change Plan — chg-02（角色索引 + role-model-map 更新）

## 1. Development Steps

### Step 1: 编辑 `role-model-map.yaml`（live）

- 在 `roles:` 下 `# ---- 开放型 / 创意型 / 综合判断型 → opus ----` 节追加一行：`  analyst: "opus"              # 需求澄清 + 变更拆分（req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））角色物理合并）`；
- 在 `requirement-review: "opus"` 与 `planning: "opus"` 两行**尾部追加注释**：` # legacy alias — route to analyst（req-40）`；
- 不动 `default: "sonnet"`、不动其他角色 key。

### Step 2: 同步 `role-model-map.yaml` mirror

- `cp .workflow/context/role-model-map.yaml src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml`；
- 跑 `diff -rq .workflow/context/role-model-map.yaml src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml` 确认无输出。

### Step 3: 编辑 `index.md`（live）

- 在"Stage 执行角色"表合并两行：
  - 旧：`| **需求分析师**（yaml key: requirement-review） | 澄清用户意图... | .workflow/context/roles/requirement-review.md | opus |`
  - 旧：`| **架构师**（yaml key: planning） | 将需求拆分为独立变更... | .workflow/context/roles/planning.md | opus |`
  - 新：`| **分析师**（yaml key: analyst） | 澄清用户意图 + 拆分变更 + 制定 plan.md；两 stage（requirement_review + planning）由同一角色执行 | .workflow/context/roles/analyst.md | opus |`
- 在合并行下方加注释行（表格下段用引用块）：
  ```
  > 原 requirement-review（需求分析师）+ planning（架构师）合并为 analyst，落地于 req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））。legacy role_key 仍在 role-model-map.yaml 保留作别名，兼容历史归档引用。
  ```

### Step 4: 同步 `index.md` mirror

- `cp .workflow/context/index.md src/harness_workflow/assets/scaffold_v2/.workflow/context/index.md`；
- 跑 `diff -rq .workflow/context/index.md src/harness_workflow/assets/scaffold_v2/.workflow/context/index.md` 确认无输出。

### Step 5: 自检 + 交接

- 跑 AC-2 / AC-3 的 grep 断言（见 2.1）；
- 更新 chg-02 `session-memory.md`：记录已完成步骤 + default-pick（I-1=A / M-1=B）；
- 更新 `artifacts/main/requirements/req-40-.../chg-02-变更简报.md`（≤ 1 页，对齐 planning.md 对人文档契约模板）；
- 按硬门禁二追加 `action-log.md` 一行。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `grep -E "^\s+analyst:\s*\"opus\"" .workflow/context/role-model-map.yaml`（命中）
- `grep -E "^\s+requirement-review:\s*\"opus\"" .workflow/context/role-model-map.yaml`（命中，legacy 别名保留）
- `grep -E "^\s+planning:\s*\"opus\"" .workflow/context/role-model-map.yaml`（命中，legacy 别名保留）
- `grep -q "legacy alias" .workflow/context/role-model-map.yaml`（命中注释）
- `grep -q "analyst" .workflow/context/index.md && grep -q "roles/analyst.md" .workflow/context/index.md`（索引表含 analyst 条目）
- `grep -q "原 requirement-review" .workflow/context/index.md`（合并注释命中）
- `diff -rq .workflow/context/role-model-map.yaml src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml`（无输出）
- `diff -rq .workflow/context/index.md src/harness_workflow/assets/scaffold_v2/.workflow/context/index.md`（无输出）

### 2.2 Manual smoke / integration verification

- 用 Python 快速加载验证：`python -c "import yaml; m=yaml.safe_load(open('.workflow/context/role-model-map.yaml')); assert m['roles']['analyst']=='opus'; assert m['roles']['requirement-review']=='opus'; assert m['roles']['planning']=='opus'; print('OK')"`；
- 肉眼复核 `index.md` Stage 执行角色表，确认 analyst 行四列完整、合并注释行在表下方。

### 2.3 AC Mapping

- AC-2（role-model-map 更新 + 兼容留痕） -> Step 1 + Step 2 + 2.1 grep/diff 断言 + 2.2 Python 加载验证；
- AC-3（index.md 角色索引更新） -> Step 3 + Step 4 + 2.1 grep/diff 断言 + 2.2 肉眼复核。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01（analyst.md 已落地，才能让 index.md / role-model-map 指向的文件路径有效）；
- **后置依赖**：chg-03（harness-manager 路由改写需要 analyst role_key 已在 role-model-map 注册）；
- **本 chg 内部顺序**：Step 1 → Step 2 → Step 3 → Step 4 → Step 5 强制串行；role-model-map 先于 index.md（yaml 是权威源，index.md 是镜像）。
