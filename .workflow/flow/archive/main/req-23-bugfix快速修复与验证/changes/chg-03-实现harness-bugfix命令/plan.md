# chg-03 Plan: 实现 `harness bugfix` 命令

## 执行步骤

### Step 1: 分析现有 CLI 结构
- 读取 `src/harness_workflow/cli.py` 和 `core.py`
- 找到 `harness requirement` 命令的实现路径
- 确认 ID 生成逻辑（如何生成 req-22 这样的 ID）

### Step 2: 复用并扩展目录创建逻辑
- 复用 `requirement` 命令的目录创建、状态初始化逻辑
- 差异点：
  - 目标目录改为 `.workflow/flow/bugfixes/`
  - 状态文件改为 `.workflow/state/bugfixes/bugfix-{id}.yaml`
  - 初始 stage 为 `regression`（而非 `requirement_review`）
  - 使用 `bugfix.md` 模板而非 `requirement.md` 模板

### Step 3: 实现 `bugfix` CLI 命令
- 新增 `bugfix` subparser
- 参数：`title`（位置参数）
- 行为：创建目录 → 复制模板 → 创建状态文件 → 更新 `runtime.yaml`

### Step 4: 单元测试
- 添加 CLI 测试：验证 `harness bugfix` 的目录结构和状态更新
- 确保不影响现有 `harness requirement` 测试

### Step 5: 安装与验证
- 运行 `uv pip install -e .` 重新安装
- 本地执行 `harness bugfix "测试 bugfix 命令"` 验证行为
