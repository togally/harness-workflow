# Change

## 1. Title

角色索引 + role-model-map 更新（analyst 注册 + legacy 别名保留）

## 2. Goal

- 在 `.workflow/context/index.md` 角色索引表注册 `analyst` 条目（合并原 `requirement-review` / `planning` 两条），并在 `.workflow/context/role-model-map.yaml` 新增 `analyst: "opus"` + 保留两 legacy key 作别名指 opus，使 harness-manager 派发时能查到 analyst → opus 映射，同时向后兼容历史归档文档对 legacy key 的引用。

## 3. Requirement

- `req-40`（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））

## 4. Scope

### Included

- **`.workflow/context/index.md`** 角色索引表改写（default-pick I-1 = A 合并 + 注释）：
  - "Stage 执行角色"小节把原 `需求分析师（requirement-review）` + `架构师（planning）` 两行合并为单行 `分析师（analyst）`（职责：需求澄清 + 变更拆分，model = opus，文件路径 `.workflow/context/roles/analyst.md`）；
  - 在合并行下方加注释行：`> 原 requirement-review（需求分析师）+ planning（架构师）合并为 analyst，落地于 req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））。legacy role_key 仍在 role-model-map.yaml 保留作别名，兼容历史归档引用。`
- **`.workflow/context/role-model-map.yaml`** 改写（default-pick M-1 = B 保留别名）：
  - 新增 `analyst: "opus"`；
  - 保留 `requirement-review: "opus"` + `planning: "opus"` 两条，添加 YAML 注释说明 "# legacy alias — route to analyst（req-40）"；
  - 不改 `default: "sonnet"`。
- **mirror 同步**：
  - `src/harness_workflow/assets/scaffold_v2/.workflow/context/index.md`
  - `src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml`
- 涉及文件路径：
  - live：`.workflow/context/index.md` + `.workflow/context/role-model-map.yaml`
  - mirror：`src/harness_workflow/assets/scaffold_v2/.workflow/context/index.md` + `src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml`

### Excluded

- **不动** `requirement-review.md` / `planning.md` 两 role.md 文件本身（保留作 legacy，由 chg-01 新建的 analyst.md 逻辑吸收职责；两文件物理保留兼容归档引用）；
- **不改** harness-manager.md 派发路由（归属 chg-03）；
- **不改** technical-director.md 流转协议（归属 chg-03）；
- **不废弃** legacy role key（废弃动作留到后续 req 按抽检结果决策）。

## 5. Acceptance

- Covers requirement.md **AC-2**（role-model-map 更新 + 兼容留痕）：
  - `grep -E "^\s+analyst:\s*\"opus\"" .workflow/context/role-model-map.yaml` 命中；
  - `grep -E "^\s+requirement-review:\s*\"opus\"" .workflow/context/role-model-map.yaml` 命中（legacy 别名保留）；
  - `grep -E "^\s+planning:\s*\"opus\"" .workflow/context/role-model-map.yaml` 命中（legacy 别名保留）；
  - `grep -q "legacy alias" .workflow/context/role-model-map.yaml` 命中（注释标记）；
  - `diff -rq .workflow/context/role-model-map.yaml src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml` 无输出。
- Covers requirement.md **AC-3**（index.md 角色索引更新）：
  - `.workflow/context/index.md` "Stage 执行角色"表含 `analyst` 条目行（角色名 / role_key / 文件路径 / model 四列完整）；
  - 合并注释行命中：`grep -q "原 requirement-review" .workflow/context/index.md`；
  - `diff -rq .workflow/context/index.md src/harness_workflow/assets/scaffold_v2/.workflow/context/index.md` 无输出。

## 6. Risks

- **风险 1：role-loading-protocol Step 7.5 模型自检对 legacy key 误报**。缓解：M-1 = B 方案保留 legacy key 作别名指 opus（与 analyst 同值），自检时 legacy key 仍能查到 opus，不误报；reviewer / executing 阶段 pytest 断言覆盖（chg-04）。
- **风险 2：index.md 表格合并后 CLI 或 agent 扫描逻辑断裂**。缓解：index.md 纯人读索引，CLI 与 role-loading-protocol 的权威源均是 role-model-map.yaml；合并行保持四列格式不变，仅行数减少，不破坏表格结构。
- **风险 3：历史归档文档引用 `requirement-review.md` / `planning.md` 路径失效**。缓解：chg-01 明确保留两 role.md 物理文件（不删除），归档引用路径仍有效；本 chg 只动 index 表达。
- **风险 4：mirror 未同步被硬门禁五拦截**。缓解：执行步骤强制 live 写完立刻 cp 到 mirror + 跑 `diff -rq` 自检。
