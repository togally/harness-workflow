# chg-01 执行计划

## 依赖

- 无前置变更依赖
- 依赖现有文件：`WORKFLOW.md`、`.workflow/context/index.md`

## 执行步骤

### Step 1: 创建 directors 目录和 technical-director.md
- [ ] 创建 `.workflow/context/roles/directors/` 目录
- [ ] 根据 `WORKFLOW.md` 内容编写 `technical-director.md`
- [ ] 角色定义应覆盖：编排者身份、硬门禁职责、上下文维护、ff 协调、异常处理、done 回顾、subagent 派发

### Step 2: 精简 WORKFLOW.md
- [ ] 保留全局硬门禁（读取 runtime.yaml、节点任务由 subagent 执行等）
- [ ] 保留六层架构简介
- [ ] 将主 agent 的详细职责改为引导语："主 agent 应加载技术总监角色文件后执行编排"
- [ ] 确保 `WORKFLOW.md` 仍引导到 `.workflow/context/index.md`

### Step 3: 更新 context/index.md
- [ ] 在 Step 2（加载角色文件）之前或之中，增加"顶级角色选择"步骤
- [ ] 明确开发场景下加载 `.workflow/context/roles/directors/technical-director.md`
- [ ] 确保技术总监角色加载后，再按 stage 加载具体执行角色

### Step 4: 验证
- [ ] 读取 `technical-director.md`、`WORKFLOW.md`、`context/index.md`，确认逻辑连贯
- [ ] 确认无语法错误和路径错误

### Step 5: Regression 修复（2026-04-17）
- [ ] 重构 `technical-director.md`：新增硬门禁四（完整研发流程图），明确技术总监必须维护并强制执行 stage 流转
- [ ] 细化 SOP：每个步骤增加具体检查点和校验动作
- [ ] 精简 `context/index.md`：移除经验加载/风险扫描/流转规则等职责，仅保留纯加载顺序索引
- [ ] 更新 `base-role.md`：新增"角色生命周期中的通用加载职责"章节，承接原 `index.md` 的 Step 4~7

## 产物

- `.workflow/context/roles/directors/technical-director.md`
- 更新后的 `WORKFLOW.md`
- 更新后的 `.workflow/context/index.md`
