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

---

## 经验六：runtime.yaml 新增字段要"load 懒回填 + save 白名单"双保

### 场景
req-28 / chg-02 给 `harness bugfix` 加 `operation_type` / `operation_target` 时，发现只在 create 时写入、不改 load/save，下一次 `harness next` 就会把字段吃掉。

### 经验内容
任何新增 runtime.yaml 字段必须同时满足两点：

1. **load 侧懒回填**：`load_requirement_runtime` 读到老格式缺字段时，基于 id / 目录推断补齐后返回，并落一次回写，保证下次 load 已是新格式。
2. **save 侧白名单**：`save_requirement_runtime` 显式 allow-list 本字段，避免 PyYAML 默认 `sort_keys=True` 或其他 save 路径丢字段。

验证方式：写一条"连续 5 次 `save(load(…))` round-trip 值不变"单测，这条能同时卡住 load 丢字段和 save 白名单漏项两种 bug。

### 来源
req-28/chg-02 — operation_type / operation_target 懒回填 + 白名单双保策略

---

## 经验七：title → path 段清洗必须在"入口层"统一下沉到同一 helper

### 场景

`harness suggest --apply` / `harness requirement` / `harness bugfix` 接到含 `/` 或超长的 raw title，`create_requirement` / `create_bugfix` 直接 `f"{id}-{raw_title}"` 拼 Path，含 `/` 被 Python 自动拆成多级嵌套目录，污染 `artifacts/` + `.workflow/state/requirements/` + `runtime.yaml`。

### 经验内容

CLI 中所有把用户可控字符串拼进 filesystem 路径段的入口，都应走同一个"入口 helper"做清洗，而不是每个 create 族函数各写一遍。原则：

1. **封装单入口 helper**：如 `_path_slug(title, max_len=60)`，复用 `slugify_preserve_unicode` + 长度上限 + `strip("-")` + 空串回退到 id-only（`req-NN` / `bugfix-NN`）。
2. **state yaml 的 title 字段保留原文**：只在 path 段用 slug，展示层 / 审计层仍用 raw title，保证可读性不丢。
3. **新增入口时同步覆盖**：新开 create_foo 族函数，必须显式调用入口 helper，并在 PR 自审 checklist 里列一条"title → path 段已下沉到 `_path_slug`"。
4. **测试层用 TDD 先红再绿**：先红证明缺陷真实存在（不同场景独立用例：单 `/` 嵌套 / 长 title 截断 / 空 title id-only 回退 / 反斜杠 / Windows 非法字符 / 多行 title），再绿证明修复生效。对已修复缺陷的补测要标注"覆盖扩展（非 TDD 先红再绿）"，避免误导后来人。
5. **同步行为变更的老断言要主动改而不是跳过**：修复生效会改变既有测试对路径的断言（如 `bugfix-1-login form validation fails` → `bugfix-1-login-form-validation-fails`）、对 sug 文件归档位置的断言（`flow/suggestions/<name>` → `flow/suggestions/archive/<name>`）等。主动修断言 + action-log 记录预期行为变更清单，全量 discover 对齐基线即通过。

### 反例

- 新开 `create_requirement` / `create_bugfix` 时直接 `f-string` 拼 raw title，忘记看同一文件里 `create_change` / `create_regression` / `rename_*` 已有 `slugify_preserve_unicode` 先例——继承链漏补是本类缺陷的首要形态。
- 只改 create 层不改 `apply_suggestion`：`apply_suggestion` 取建议首行无截断当 title 直接调 `create_requirement`，即使 `create_requirement` 有 slug 清洗，超长 title 仍可能用满 60 字符 slug，可读性低——正确做法是 `apply_suggestion` 自己在取 title 时先截断（`[:60]`）+ create_requirement 再 slug 清洗，双层兜底。

### 来源

bugfix-3 — 修复 suggest apply 与 create_requirement 的 slug 清洗与截断
