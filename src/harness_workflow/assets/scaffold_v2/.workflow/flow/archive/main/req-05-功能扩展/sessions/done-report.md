# req-05 done 阶段回顾报告

## 执行摘要

req-05「功能扩展」实现了 4 项功能、7 个变更，横跨 `core.py`、`backup.py`、`cli.py`、`README.md`、`README.zh.md`。所有变更已完成并通过 Python assertion 验证。

**关键成果**：
- kimicli 成为第 4 个受支持平台，`harness install` 默认全选
- `harness archive` 自动以 git branch 名为 folder，并支持交互式需求选择
- 归档时完整迁移 sessions + state.yaml 到归档目录
- 归档后自动生成 `artifacts/requirements/` 下的需求摘要文档
- README 双语更新

---

## 六层检查结果

### 第一层：Context（上下文层）
- [x] **角色行为**：executing 阶段以开发者角色直接执行，与角色定义一致
- [x] **经验文件**：harness.md 中已有 pipx inject 和 python3 经验；development.md 中已有大文件重写和并行状态迁移经验，本轮无新增需沉淀的泛化经验
- [x] **上下文完整性**：本需求跨两个会话（上下文压缩后继续），context summary 完整传递了 chg-01/02 完成状态，chg-03~07 在新会话中顺利衔接

### 第二层：Tools（工具层）
- [x] **工具使用顺畅度**：整体顺畅；pipx 环境 vs uv venv 问题出现一次（`uv run harness next` 因 .venv 缺少 yaml 模块失败），通过 `pipx inject --force` 解决
- [x] **CLI 工具适配**：`questionary.select()` 用于交互式选择，表现符合预期
- [ ] **已知遗留问题**：`uv run harness` 与 pipx 安装的 harness 使用不同 venv，需要执行 `pipx inject` 才能同步源码变更——这是开发体验摩擦点

> 建议：在 harness-workflow 开发文档中增加「本地开发验证」说明：源码变更后需运行 `pipx inject harness-workflow . --force` 才能使 `harness` 命令加载最新代码。

### 第三层：Flow（流程层）
- [x] **阶段完整性**：requirement_review（需求分析 + 4 次用户问答澄清）→ planning（7 个变更的 change.md + plan.md）→ executing（全部实现 + 验证）→ done
- [ ] **testing/acceptance 跳过**：本项目 WORKFLOW_SEQUENCE 为 `executing → done`，跳过了 testing/acceptance 阶段。7 个变更通过 Python assertion 验证了关键断言，但未执行独立的测试/验收 subagent
- [x] **流程顺畅度**：上下文压缩一次（chg-01/02 完成后进入新会话），交接顺利，无卡顿

> 注：harness-workflow 本身的 WORKFLOW_SEQUENCE 不包含 testing/acceptance，这是设计选择而非流程异常。建议后续需求评估是否将 testing/acceptance 纳入 WORKFLOW_SEQUENCE（参见「遗留问题」）。

### 第四层：State（状态层）
- [x] **runtime.yaml 一致性**：stage 从 executing 正确推进到 done，active_requirements 含 req-05
- [x] **需求状态一致性**：state/requirements/req-05-功能扩展.yaml 存在，stage=executing（尚未归档，归档后会迁移至归档目录 state.yaml）
- [x] **状态记录完整性**：7 个变更均有 session-memory.md，关键决策已记录

### 第五层：Evaluation（评估层）
- [ ] **testing/acceptance 独立性**：未执行独立 testing/acceptance subagent（同第三层说明，WORKFLOW_SEQUENCE 设计如此）
- [x] **代码断言验证**：通过 `uv run --with pyyaml python -c "..."` 执行了覆盖所有 AC 关键点的断言
- [x] **验收标准达成度**：
  - kimicli AC：ALL_PLATFORMS 含 kimi ✅，PLATFORM_CONFIGS kimi source 正确 ✅，Hard Gate 含 .kimi 路径 ✅
  - 归档默认 folder：git branch 读取正确（main → archive/main/）✅
  - 交互式选择：archive nargs="?" ✅，enter req_id 可选 ✅
  - 归档迁移：sessions + state.yaml 移动逻辑正确 ✅
  - 制品仓库：_extract_section 章节提取正确 ✅，generate_requirement_artifact 输出路径正确 ✅

### 第六层：Constraints（约束层）
- [x] **边界约束**：所有变更均在 change.md 定义范围内，未扩大范围
- [x] **风险扫描**：本轮无高风险操作（shutil.move 用于本地文件迁移，可 git 回滚）
- [x] **硬门禁遵守**：每个 /harness-next 均先读取三个必读文件后执行

---

## 工具层适配发现

### CLI 摩擦点
- `uv run harness` 与 `pipx inject` 版本不同步 → 每次源码变更后需手动 `pipx inject --force`
  > 建议：开发文档添加说明；或考虑 Makefile 目标 `make dev` 自动执行 inject

### 无新 MCP 适配需求

---

## 经验沉淀情况

本轮无需新增泛化经验（harness.md 中已有 pipx 和 python3 经验），pipx/uv 混用问题是已知模式的重复。

---

## 流程完整性评估

| 阶段 | 状态 | 说明 |
|------|------|------|
| requirement_review | ✅ 完整 | 需求文档含背景/目标/范围/AC，用户 4 次确认 |
| planning | ✅ 完整 | 7 个变更的 change.md + plan.md 全部生成 |
| executing | ✅ 完整 | 7 个变更全部实现，assertions 通过 |
| testing | ⚠️ 未运行 | WORKFLOW_SEQUENCE 无此阶段 |
| acceptance | ⚠️ 未运行 | WORKFLOW_SEQUENCE 无此阶段 |

---

## 遗留问题与注意事项

1. **WORKFLOW_SEQUENCE 无 testing/acceptance**：harness 工具本身的 CLI 没有这两个阶段，导致自身需求无法走完整流程。后续可评估是否增加这两个阶段到 WORKFLOW_SEQUENCE。

2. **pipx inject 开发体验**：每次修改 core.py 后需 `pipx inject harness-workflow . --force`，建议补充开发文档或 Makefile。

3. **interactive archive 与 done-state 的 AC 差异**：requirement.md AC 说明「传入 req-id 时弹出列表预选中」，但实现中 `harness archive req-05` 在 done reqs 列表中查找 req-05 预选 —— 若 req-05 尚未到 done 阶段则找不到，会触发「无可归档需求」提示。这是符合设计意图的行为，但可能让用户困惑。建议在文档中说明。

---

## 下一步行动

- **立即**：运行 `harness archive req-05` 归档本需求（验证 chg-03~06 的完整流程）
- **后续**：考虑在 WORKFLOW_SEQUENCE 中增加 testing/acceptance（新建需求）
- **后续**：补充开发文档中 pipx inject 的说明
