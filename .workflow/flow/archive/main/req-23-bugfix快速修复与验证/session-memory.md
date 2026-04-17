# req-23 执行日志

## 当前变更
- chg-01: 规范层更新
- chg-02: bugfix 模板与目录规范
- chg-03: 实现 `harness bugfix` 命令
- chg-04: 端到端验证与经验沉淀

## 执行进度

### planning
- [x] 完成需求范围确认（含 regression 触发的 base-role 自我介绍规则扩展）
- [x] 拆分为 4 个变更
- [x] 每个变更有 change.md + plan.md
- [x] 用户确认拆分方案
- [x] 推进到 executing

### chg-01
- [x] Step 1: 更新 `base-role.md`（新增硬门禁三：角色自我介绍规则）
- [x] Step 2: 完善 `stages.md`（新增 `regression` stage 定义，补充 bugfix 退出条件）
- [x] Step 3: 更新 `review-checklist.md`（新增角色自我介绍、bugfix 目录规范、bugfix 模式识别检查项）
- [x] Step 4: lint 验证通过

### chg-02
- [x] Step 1: 设计 bugfix.md 模板（含 id/title/created_at 头部 + 五章节主体）
- [x] Step 2: 创建 `src/harness_workflow/assets/skill/assets/templates/bugfix.md.tmpl` 及英文版 `.en.tmpl`
- [x] Step 3: 创建 `src/harness_workflow/assets/templates/bugfix.md` 静态模板
- [x] Step 4: 更新 `pyproject.toml` package-data，lint 验证通过

### chg-03
- [x] Step 1: 分析现有 CLI 结构（`cli.py`、`core.py`）
- [x] Step 2: 实现 `_next_bugfix_id` 和 `create_bugfix` 函数
- [x] Step 3: 在 `cli.py` 注册 `bugfix` subparser 并绑定处理逻辑
- [x] Step 4: 添加 CLI 单元测试 `test_bugfix_creates_workspace_and_enters_regression`
- [x] Step 5: `uv run` 本地验证通过，lint 验证通过

### chg-04
- [x] Step 1: 准备测试场景（构造模拟 bug：SKILL.md missing bugfix command）
- [x] Step 2: 走完整 bugfix 流程（regression → executing → testing → acceptance → done）
- [x] Step 3: 验证 technical-director 模式切换（未加载 planning 角色，阶段流转正确）
- [x] Step 4: lint 脚本验证（对 bugfix 目录无报错）
- [x] Step 5: 经验沉淀（更新 `experience/roles/regression.md` 经验五）
- [x] Step 6: 输出端到端测试报告 `end-to-end-test-report.md`

## 关键决策
- 采用"双模式流程图"设计：标准需求走六阶段流，bugfix 走四阶段流
- bugfix 是编排层流程模式，不新增专门的 stage 执行角色
- base-role.md 新增角色自我介绍规则，作为通用约束覆盖所有角色
- `harness bugfix` 命令直接进入 `regression` 阶段

## 遇到的问题
1. `workflow_next` 不支持 `regression` 阶段：已修复，新增 `BUGFIX_SEQUENCE` 并支持 bugfix 状态目录
2. `load_simple_yaml` 无法解析嵌套字典：已修复，支持缩进子节点同时识别列表与字典格式

## 待处理捕获问题
- 无
