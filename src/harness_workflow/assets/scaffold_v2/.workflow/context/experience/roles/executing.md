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

---

## 经验三：Legacy Cleanup 列表的修改必须配合回归测试

### 场景
req-20 中 `.workflow/tools/` 被错误地列入了 `LEGACY_CLEANUP_TARGETS`，导致所有项目运行 `harness update` 时 tools 目录被整体归档到 backup，造成数据丢失。

### 经验内容
任何对"清理/删除列表"的修改都是高风险操作，因为一旦生效就会不可逆地影响多个项目。修改前必须：

1. **三查**：谁依赖它、谁创建它、删除后会破坏什么
2. **测试覆盖**：新增回归测试，验证被清理对象不会在更新周期中被误处理
3. **区分"删除"与"移动"**：`shutil.move` 到 backup 虽然可恢复，但用户往往不知道 backup 的存在，等效于数据丢失

### 反例
将仍在活跃使用的 `.workflow/tools/` 路径加入 `LEGACY_CLEANUP_TARGETS`，没有配套测试，直到用户发现"角色文件引用的 stage-tools.md 不存在"才定位到问题。

### 来源
req-20 tools 目录误清理事件

---

## 经验四：core.py 彻底删除需要完整重构，不能依赖薄壳包装器

### 场景
req-25 需要删除 core.py，实现"项目中只允许工具层存在脚本"。初次尝试创建工具脚本包装 core.py 函数（cli.py → tool scripts → core.py），但这只是过渡方案，最终仍需将 core.py 逻辑完整提取。

### 经验内容
当需求要求"彻底删除 X"时：
1. **薄壳包装不是终点** — 只是证明了接口契约，无法满足"删除原文件"的要求
2. **必须做完整提取** — 将 core.py 的实际逻辑逐函数提取到工具脚本
3. **复杂依赖要预估工作量** — core.py 有 4277 行、70+ 函数、相互引用，重构需要较长时间
4. **分阶段验证** — 每迁移一类函数就验证 CLI 命令，不要等到最后才发现问题

### 来源
req-25 — core.py 删除与工具层重构

---

## 经验五：多层 subagent 嵌套需要协议先行

### 场景
req-25 的 chg-03 需要实现 subagent 嵌套调用机制（上层可以无限调用下层）。

### 经验内容
嵌套调用这类复杂机制：
1. **先定义协议** — 在 design.md 或 role 文件中定义清楚调用链结构、上下文传递方式、session-memory 格式
2. **再实现代码** — 协议定义清晰后，实现只是照着协议写代码
3. **协议是验证标准** — 协议定义本身就是验收标准，实现是否符合协议一目了然

### 来源
req-25/chg-03 — subagent 嵌套调用机制实现
