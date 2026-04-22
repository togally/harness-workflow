# Change Plan

## 1. Development Steps

### Step 1：定位 README 合适位置

- 读 `README.md`（或仓库默认入口的 doc 文件），找到与"安装 / 升级 / 下游仓库使用"最接近的段落。
- 若不存在，则在文件末尾新增 "## 升级对人文档 / change / plan 模板" 小节。

### Step 2：写入 1~3 行提示

- 内容模板：
  ```
  ### 升级 change / plan 模板

  `harness change` 与 `harness plan` 的模板由已安装的 `harness_workflow` Python 包动态读取。下游仓库仅需升级 Python 包即可获得新模板：

      pip install -U harness-workflow

  已落盘的 change 是一次性快照，不会被自动覆盖。
  ```

### Step 3：（可选）同步 CLI help text

- 查看 `src/harness_workflow/cli.py` 里 `harness update` 子命令的 `description` 字段，如允许多行文本，追加一句："不会刷新已落盘 change 的模板；如需新模板请升级 harness_workflow Python 包。"
- 如现有字段固定为单行 / 不适合扩展，跳过本 Step 并在 executing session-memory 记录原因。

### Step 4：无新增测试

- 本 change 只动文档/help text，不写单测。在 Verification 中以 grep 做静态检查。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `grep -n "pip install -U harness-workflow" README.md` 非空。
- `grep -n "change / plan 模板" README.md`（或等价关键字）非空。
- 如动了 CLI help text，`harness update --help` 输出含升级提示。

### 2.2 Manual smoke / integration verification

- 在另一个下游仓库（或同仓库 tempdir）执行 `pip install -U harness-workflow` 后 `harness change "test"`，确认 change.md 模板与本仓库最新版本一致。

### 2.3 AC Mapping

- AC-10 -> Step 1/2 + 2.1

## 3. Dependencies & Execution Order

- 与任意其他 change 完全独立，可并行启动。
- 不阻塞 chg-07 smoke。
