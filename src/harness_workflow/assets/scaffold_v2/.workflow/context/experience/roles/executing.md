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

---

## 经验八：managed-state 幂等同步的两端判据——"未登记 vs 已登记但不匹配"必须区分

### 场景

`update_repo` 同步 scaffold 模板到目标项目时，目标文件与模板不一致的情况有两种截然不同的语义：
- A：`managed-files.json` 未登记该文件的 hash → 说明此前某个版本的 harness 根本没把它纳入 managed（漏登记 / 版本演进新增）；
- B：`managed-files.json` 已登记 hash 但与当前文件不匹配 → 说明用户在 harness 落盘后手动改过该文件。

混同这两种语义会造成死锁：原实现对所有"不匹配"统一走 `skipped modified`，A 类文件因此永远追不上新模板（hash 永远写不进去，下次 update 继续 skip）。

### 经验内容

1. **判据要显式分支**：`relative not in managed_state` ≠ `managed_state[relative] != current_hash`。前者是"adopt-as-managed"的可信任覆盖信号；后者是用户自定义，必须 `skipped modified`。
2. **写 hash 的时机要前置到 adopt 点**：不要依赖收尾阶段的 `_refresh_managed_state`"当前文件等于模板才写 hash"——这条收尾逻辑是保护用户自定义文件的，不能承担 adopt 的 hash 写入职责，否则陷入"永远不等于模板 → 永远不写 hash → 下次继续 skipped"的死锁。
3. **action 命名要自证**：新增分支记 `adopted {relative}` 而不是 `updated`，让审计者能立刻区分"模板演进首次 adopt"与"用户 force_managed 主动更新"。
4. **烟测先对比 HEAD baseline**：修复生效后在临时副本上跑 `harness update`，stdout `adopted` 条数应 > 0 且 `skipped modified` 条数下降；baseline 下同场景的 `skipped modified` 条数作为对比基数。

### 反例

- 只在 `_refresh_managed_state` 里"放宽"判据（对未登记文件无条件写 hash）——表面上修了 A 类，但实际上 `_sync_...` 根本没写模板内容到文件，`_refresh_managed_state` 写到的 hash 对应的还是旧内容，下次 update 仍然 skip。必须在 `_sync_...` 层同时覆盖 + 写 hash，不能分两处。
- 把 `LEGACY_CLEANUP_TARGETS` 当成治本工具——`LEGACY_CLEANUP_TARGETS` 只应列入"真正被废弃的历史产物路径"，不得列入任何"每次 update 都会活跃再生成"的文件（如 `experience/index.md`），否则形成"搬家 → 重建 → 下次再搬家"循环，在 `backup/legacy-cleanup/` 下累积 `-N` 递增副本。

### 来源

bugfix-3 — pipx 重装后新项目 install/update 生成数据不正确（根因 A + B）

---

## 经验九：agent 作用域收敛类修复——决策 / 生成 / 落盘三段管道必须同时接参数

### 场景

用户要求"install/update 只作用于当前选定 agent"，管道涉及三段：
- 决策层：CLI 收到 `--agent X` 或从状态层读 `active_agent`
- 生成层：`_managed_file_contents` / `_project_skill_targets` 根据作用域生成 payload
- 落盘层：`install_local_skills` / `_sync_requirement_workflow_managed_files` / `update_repo` 把 payload 写入文件系统

### 经验内容

1. **三段必须同时接参数**：只接决策层会泄漏到老行为；只接生成层会被 CLI 绕过；只接落盘层会被上游覆盖。必须一路透传 `active_agent` 或 `agent_override`/`force_all_platforms`。
2. **状态层持久化是 source of truth**：`install_agent` 调用末尾必须写 `write_active_agent(root, agent)`，消费点（`update_repo` 入口）读 `read_active_agent(root)`。不要依赖内存传参——多次 CLI 调用之间内存不共享。
3. **兼容 escape hatch 与一次性 flag 要分开**：
   - 一次性：`--agent X` 覆盖本次 run，不写状态层（`agent_override` 参数）；
   - 兼容：`--all-platforms` 强制老行为（`force_all_platforms` 参数），与 `active_agent` 无关；
   - 回退：`active_agent` 缺失时走 `enabled[]` + warning，老仓不破坏。
4. **三种场景都要有测试**：持久化 / 作用域收敛 / 迁移兼容 + 边界（compat warning / 迁移不覆盖 / 一次性 flag 不持久化）。

### 反例

- 只在 `install_agent` 写 `active_agent` 但 `update_repo` 没读 → 状态层有字段但不生效，用户以为修复了实则没有。
- 只在 `_managed_file_contents` 按 `active_agent` 裁剪但 CLI 没透传 `--all-platforms` → escape hatch 失效，多 agent 用户受影响。
- 写入点 `install_local_skills` / `_sync_requirement_workflow_managed_files` 只改一个但另一个仍硬编码 → 写入范围不一致，`.claude/skills/` 刷了但 `.codex/commands/` 还是全写。

### 来源

bugfix-3（新） — install/update 仅更新当前选定 agent（问题 1）

---

## 经验十：路径常量迁移的三件套——新常量 + 旧常量 + 迁移锚点

### 场景

六层架构成型前留下的路径常量（如 `FEEDBACK_DIR = Path(".harness")`），后续要归位到 `.workflow/state/feedback/`。直接改常量会导致：
- 新仓 OK，但老仓 `.harness/feedback.jsonl` 历史数据"消失"（实际在磁盘，但代码不读）
- `harness_export_feedback` 消费者读新路径读不到 → 历史统计归零
- git 层出现 `rm .harness/feedback.jsonl` 但用户看不到迁移提示

### 经验内容

1. **三件套同时建立**：
   - 新常量（`FEEDBACK_DIR = .workflow/state/feedback/`）：所有新写入、新读取走这里
   - 旧常量（`LEGACY_FEEDBACK_DIR = .harness/`）：仅用于 `update_repo` 迁移识别
   - 迁移锚点：`update_repo` 开头 `shutil.move` 旧→新 + 空目录 rmdir + action log + 用户提示
2. **数据连续性硬门禁**：迁移前后文件行数 ≥ 迁移前（本次 update 可能新增事件），用测试断言锁死。
3. **不覆盖已有数据**：目标新位置已有数据时拒绝 move，打 warning（极端场景：用户手工提前放了文件）。
4. **消费者同步**：所有 `Path(".harness")` 硬编码（工具脚本 / scaffold_v2 文档 / README）一次性 grep 扫清，不留死路径。
5. **git 提示**：迁移后 stdout 打印 `git rm .harness/... && git add .workflow/state/feedback/...` 引导用户 commit（sug-20 跟踪）。

### 反例

- 只改常量不加迁移：老仓跑 `harness update` 后新位置空、旧位置数据仍在，`harness feedback` 统计归零。
- 迁移但不检查新位置已存在：覆盖用户手工放置的数据，丢失。
- 代码迁移但 scaffold_v2 模板文档路径不改：新仓 install 出来 SKILL.md 写的是旧路径，新人困惑。

### 来源

bugfix-3（新） — `.harness/feedback.jsonl` 落层归位（问题 2）

---

## 经验十一：mirror→live 全量同步契约（install_repo 完整性收口）

### 场景

`install_repo` 落地多版本演进，原有 `_sync_requirement_workflow_managed_files` 只针对 `_managed_file_contents`（curated 子集 + 平台 commands/skills），但 `_scaffold_v2_file_contents` 是更全的 mirror（含 role / experience / evaluation / context/index 等）。在 managed_state 缺登记的存量项目（无 `managed-files.json`），默认走 adopt-as-managed 分支可覆盖大多数 drift；但仍存在两类残留：(1) 系统 post-install 重建文件（`_refresh_experience_index` / `_write_project_profile_if_changed` / `render_template` CLAUDE.md 等）必然 drift；(2) install_repo 未跑 mirror 全量比对作为 defense-in-depth，自检 audit 又被 pyproject 锚点锁死，存量项目漂移沉默。

### 经验内容

1. **"两段同步 + 共享白名单"契约**：
   - 段一 = `_sync_requirement_workflow_managed_files`（managed 子集，承用户保护语义：adopt-as-managed / skipped user-authored / skipped modified）；
   - 段二 = `_sync_scaffold_v2_mirror_to_live`（mirror 全量 defense-in-depth，对 missing / drift 残留补铺）；
   - 共享白名单 = 模块级 `_SCAFFOLD_V2_MIRROR_WHITELIST`，由 sync helper + `_install_self_audit` 双方消费，避免双份维护。
2. **顺序敏感**：sync helper 必须放在 `_sync_requirement_workflow_managed_files` 之后、`_write_project_profile_if_changed` 之后、`print("Update summary:")` 之前、`_install_self_audit` 之前。倒置会让 (a) 最终 actions 不进 summary 段；(b) audit 看到未 sync 的 drift 误报。
3. **白名单要包含 "post-install 系统重建" 类**：`context/experience/index.md` / `context/project-profile.md` / `CLAUDE.md` / `AGENTS.md` 这类必然与 mirror 不同的文件，必须列入白名单否则 helper 会持续误判为 user-modified（hash 已登记但被系统重写过）。
4. **非 managed 用户改动按保守策略 stderr-skip 而非静默覆盖**：未登记 hash 的 mirror 文件 + live 内容不等于 mirror → 默认 stderr 跳过（"用户可能自定义"），`--force-managed` 才覆盖；与 sug-13 / sug-14 协同保护用户改动。
5. **self-audit 触发面解锁，但保留 env escape hatch**：删除 `pyproject.toml name == "harness-workflow"` 锚点（让所有项目都跑 audit），保留 `HARNESS_DEV_REPO_ROOT` env（开发期切到本仓 audit、不污染目标项目）。
6. **测试六分支齐全**：`tests/test_install_repo_sync_contract.py` 应覆盖 fresh install zero-drift / missing 文件铺回 / user-modified 保护 / force_managed 覆盖 / 白名单豁免 / audit 触发面解锁，每条独立用例。

### 反例

- 把 sync helper 放在 `_install_self_audit` 之后：audit 永远报 drift（sync 还没跑），WARNING 噪声爆给用户。
- 把白名单常量内联到 helper 与 audit 两处：常量更新时漏改一处导致两个出口判据不一致，drift count 不对齐。
- 没把 `experience/index.md` / `project-profile.md` 列入白名单：每次 install 后 helper 都报 "skipped user-modified" + audit 报 "drift detected"，用户体验差且 stderr 噪声高。
- 删 audit pyproject 锚点时把 env 段也删了：开发期 harness-workflow 仓库自己跑 audit 会爆假阳（本仓 .workflow/ 是开发态，不一定与 mirror 完全一致）。

### 来源

req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致）） / chg-05（install_repo 末尾追加 mirror→live 全量同步） + chg-06（解锁 _install_self_audit 触发面）

---

## 经验十二：CLI 路由迁移契约——helper 跨 req 重定义入口时必须同时迁旧入口透传 + 旧测试断言

### 场景

req-33（install 吸收 update 的 CLI 职责 + harness update 契约层重定义为触发 project-reporter）
把 `update_repo` 主实现合并到 `install_repo`，但 CLI 层只做了 update --flag → install_repo
的兼容透传 hack，**没把 install 入口接到 install_repo**。reg-02 实证：
- `harness install` 仍只调 install_agent（单平台 skill 落盘），不跑 install_repo（mirror 同步 + audit）；
- `harness update --check / --force-managed / --all-platforms / --agent` 仍走 install_repo（旧 hack）；
- 单测 296 passed 全绿（因为旧测试只覆盖 update --flag → install_repo 路径），下游用户 `harness install` 跑不出 mirror 同步效果，存量项目漂移沉默。

### 经验内容

1. **helper 跨 req 重定义主入口时**：必须同时迁三件事：
   - **新入口接通**（`harness install` → install_repo）；
   - **旧入口透传 hack 移除**（`harness update --flag` 硬 fail + stderr 迁移提示）；
   - **旧测试断言迁移**（test_cli.py 中 update --flag 的断言改写为 install --flag 或硬 fail 提示）。
   只迁一件 → 单测全绿但下游用户跑不通；只迁两件 → 测试套件内部前后矛盾。
2. **硬 fail 优于静默兼容**：迁移过渡期的旧 flag 应该 stderr `请改用 harness install --{flag}` + exit 1，让用户立刻看到迁移路径，而不是静默继续走旧 hack（debug 困难）。
3. **保留 `--scan` 类正交分支**：与新主入口（install_repo）无关的辅助分支（如 `update --scan` → scan_project）应保留不删，避免把 update 子命令清空。
4. **CLI 路由测试用文件副作用代理 + stderr 模式断言**：subprocess 黑盒下，install_repo 调用证据用 stdout `"Update summary"` 行 + 文件状态变化（`--check` 不写 / `--force-managed` 覆盖 / `--all-platforms` 跨 agent）替代 monkeypatch spy，更接近真实用户使用路径。
5. **STEP-1 红用例必须明确标注期望失败原因**：不只是 `assert False`，而是 docstring 写 "current 状态 → 失败原因 → STEP-2 绿后通过"，让红 → 绿过渡过程可追溯。

### 反例

- req-33 / bugfix-1 阶段只做了 `update --flag → install_repo` 透传 hack 没接 `install → install_repo`，单测全绿但 reg-02 真跑（Yh-platform 存量项目）发现 mirror 漂移沉默——典型"测试覆盖路径与生产路径分叉"反例。
- 删除 update 子命令所有 flag 处理（含 `--scan`）→ scan_project 分支被误清，必须保留 `--scan` 单独分支。

### 来源

req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致）） / chg-07（CLI 路由修正：harness install 接 install_repo + 移除 harness update --flag 的 install_repo hack） / reg-02（CLI 路由 + packaging 双根因）实证教训。
