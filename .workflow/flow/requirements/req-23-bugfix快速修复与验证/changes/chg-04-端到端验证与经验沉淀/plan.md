# chg-04 Plan: 端到端验证与经验沉淀

## 执行步骤

### Step 1: 准备测试场景
- 在当前项目中找一个已知的小问题（或人为构造一个），例如：
  - `harness status` 输出格式中某个字段显示异常
  - 或某个文档中的路径引用错误
- 确保问题范围小、修复简单、可验证

### Step 2: 走完整 bugfix 流程
- `harness bugfix "测试用 bug 描述"`
- 模拟 regression 诊断：填写 `diagnosis.md` 和 `bugfix.md`
- `harness next` → executing → 修复
- `harness next` → testing → 验证
- `harness next` → acceptance → 确认
- `harness next` → done → 回顾

### Step 3: 验证 technical-director 模式切换
- 确认在整个过程中 technical-director 没有尝试加载 `planning` 角色
- 确认 stage 流转严格遵循 `regression → executing → testing → acceptance → done`

### Step 4: lint 脚本验证
- 运行 `python3 tools/lint_harness_repo.py --root . --strict-claude --strict-stage-roles`
- 确认 lint 对 `bugfix-` 目录无报错

### Step 5: 经验沉淀
- 新建 `experience/roles/bugfix.md` 或在 `experience/roles/regression.md` 中新增 bugfix 模式相关经验
- 内容至少覆盖：bugfix 与标准需求的边界、bugfix 流程中的关键注意点

### Step 6: 输出测试报告
- 在 req-23 目录下创建 `end-to-end-test-report.md`
- 记录测试步骤、验证结果、发现问题、修复动作
