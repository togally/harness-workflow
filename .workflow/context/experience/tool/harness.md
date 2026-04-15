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

---

## 经验四：修改 `.workflow/` 后必须同步 `src/harness_workflow/assets/scaffold_v2/`

### 场景
req-07 在 Yh-platform 项目中发现 `harness install` 部署的模板严重过时（缺少 req-05 的 ff 模式、req-06 的时长记录等）。

### 经验内容
`harness install` 和 `harness update` 的调用链最终都会读取包内 `assets/scaffold_v2/` 中的文件来生成目标项目的 `.workflow/`。因此：

**任何对 harness-workflow 仓库 `.workflow/` 的修改，必须同步到 `src/harness_workflow/assets/scaffold_v2/`。**

同步步骤：
```bash
# 在 harness-workflow 仓库根目录执行
rm -rf src/harness_workflow/assets/scaffold_v2/.workflow
cp -R .workflow src/harness_workflow/assets/scaffold_v2/
cp WORKFLOW.md src/harness_workflow/assets/scaffold_v2/
cp CLAUDE.md src/harness_workflow/assets/scaffold_v2/

# 重新安装包
pipx inject harness-workflow . --force
```

**检查方法**：
```bash
# 在临时目录验证新安装的项目是否包含最新内容
TMPDIR=$(mktemp -d)
cd "$TMPDIR"
harness install
grep "harness ff" .workflow/flow/stages.md
```

**反例**：
req-05 和 req-06 修改了 `.workflow/flow/stages.md`、`.workflow/context/roles/done.md` 等文件，但没有同步到 `src/harness_workflow/assets/scaffold_v2/`，导致所有外部项目通过 `harness install` 拿到的都是旧模板。

### 来源
req-07 Yh-platform 验证（harness install 模板过时）
