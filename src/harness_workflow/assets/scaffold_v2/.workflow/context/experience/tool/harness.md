# Harness Tool Experience

## 经验一：安装环境使用 pipx inject 而非 pip install

### 场景
req-02/chg-07 重写 core.py 后需要重新安装包，pip install 失败。

### 经验内容
macOS Homebrew Python 遵守 PEP 668 externally-managed-environment，直接 `pip install -e .` 会报错。
通过 pipx 安装的包需用 `pipx inject` 更新：

```bash
# 错误：pip install -e .  → "externally managed environment"
# 正确：
pipx inject harness-workflow . --force
# 或者完整重装：
pipx reinstall harness-workflow
```

### 来源
req-02/chg-07 pipx 重装验证

---

## 经验二：python 命令在 macOS 上默认不可用，用 python3

### 场景
验证安装结果时运行 `python -c "import harness_workflow"` 报 command not found。

### 经验内容
macOS 系统默认只有 `python3`，没有 `python` 别名。所有 CLI 脚本和验证命令应使用 `python3`。

```bash
# 错误：python -c "..."
# 正确：python3 -c "..."
```

### 来源
req-02/chg-07 验证步骤

---

## 经验三：超大文件重写用 subagent，不要在主对话中逐段编辑

### 场景
req-02/chg-07 需要从 core.py（4092 行）删除 26 个函数、重写多个函数。

### 经验内容
对超过 1000 行的大规模重写任务，在主对话内逐段 Edit 会导致上下文膨胀和遗漏。
正确做法：dispatch general-purpose subagent，提供：
- 精确的函数名列表（增/删/改）
- 新实现的完整代码
- 预期的行数变化作为验证标准

Subagent 完成后主对话只做验证，不重复读整个文件。

### 来源
req-02/chg-07 core.py 949 行删减
