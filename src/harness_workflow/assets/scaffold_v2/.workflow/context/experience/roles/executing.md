# Development Stage Experience

## 经验一：薄壳脚本不代表真实依赖——追到最终执行逻辑

### 场景
检查某个目录的依赖时，发现项目内脚本只是 `from package import main` 的薄壳。

### 经验内容
当项目内脚本是薄壳（只做 import + 调用），真正的业务逻辑在已安装包里。
这时查项目内文件得不到完整信息，必须找到已安装包的实际路径：

```bash
# 方式一：pip show
pip show harness-workflow

# 方式二：python 直接找
python3 -c "import harness_workflow; print(harness_workflow.__file__)"

# 方式三：pipx venv 位置
find ~/.local/pipx/venvs -name "core.py" -path "*/harness*"
```

找到后，对该包的源码做同样的 grep/read 分析。

### 来源
req-02 versions/ 依赖分析，harness.py 是薄壳，core.py 在 pipx venv 中

---

## 经验二：并行状态系统的迁移要分阶段

### 场景
旧系统有 versions/ 状态，新系统有 state/runtime.yaml，两套并行存在。

### 经验内容
当新旧两套状态系统并行时，不能直接删旧系统——CLI 等工具可能仍在写旧系统。
正确的迁移路径：

```
阶段一：新系统建立，旧系统保留（当前状态）
阶段二：CLI 升级，写新系统的同时保持写旧系统（兼容期）
阶段三：所有读取方切换到新系统，旧系统只写不读
阶段四：旧系统停写，废除
```

跳过中间阶段会导致 CLI 命令失败或状态不一致。

### 来源
req-02 versions/ 废除分析
