# Session Memory — chg-03（harness install 追加路书初始化）

## 1. Current Goal

让 `harness install` 在 install_repo 之后追加 `init_playbook` 阶段（OQ-3=A 默认追加，路径 = `artifacts/project/playbooks/` OQ-1=B）；提供 `--skip-playbook` / `--playbook-only` 两互斥 flag；领域推断按 4 级降级链命中即停 + stdout 打印命中级别（OQ-4=B-modified）；零新依赖、零 LLM 调用，纯静态分析；现有调用方不传 flag 时行为不变。

## 2. Context Chain

- Level 0: 主 agent（harness-manager）→ analysis stage 编排
- Level 1: Subagent-L1（analyst / opus）→ req-55（项目路书Playbook体系-项目地图+代码导航）analysis stage
- Level 1（executing / sonnet）：执行本 chg-03（harness install 追加路书初始化）

## 3. Completed Tasks

- [x] 新建 `src/harness_workflow/playbook/` 子包（4 文件，写入路径 = `artifacts/project/playbooks/`）
  - `__init__.py`：导出 `init_playbook / infer_domains / render_skeleton`
  - `domain_inference.py`：4 级降级链 + stdout 命中级别打印 + `_read_pkg_name` pyproject/setup.py 解析
  - `skeleton.py`：4 顶层文件 + domains/{name}/ 4 件套渲染，5 类 AUTO 区段，幂等
  - `init.py`：`init_playbook(root, skip, only)` 主入口，软失败（领域推断失败 → 返回 0 + stderr WARN，不阻塞 install）
- [x] 修改 `harness_install.py`（追加 init_playbook 调用 + 双 flag 注册 + `--playbook-only` 单跑路径）
- [x] 修改 `cli.py`（install_parser 追加互斥组 `--skip-playbook` / `--playbook-only` + handler 透传）
- [x] README / SKILL.md mirror 同步行：（OQ-3=A 已在代码实现，文档同步 = TODO for chg-04/05 dogfood 后在交付总结中补）
- [x] 新增 `tests/test_playbook_install.py`（10 TC：TC-01～TC-10，含 4 级降级每级 ≥ 1 + dogfood subprocess + 双 flag + 幂等）
- [x] 全量回归通过（57 failed vs 基线 61 failed，本 chg 不引入新 fail）
- [x] harness validate --contract artifact-placement exit 0

## 4. Results

### 关键产物

| 产物路径 | 说明 |
|---------|------|
| `src/harness_workflow/playbook/__init__.py` | 新增，公开 API（init_playbook / infer_domains / render_skeleton）|
| `src/harness_workflow/playbook/domain_inference.py` | 新增，4 级降级链 + stdout 命中级别打印 |
| `src/harness_workflow/playbook/skeleton.py` | 新增，4 顶层文件 + domains 4 件套模板 + 5 类 AUTO 区段 |
| `src/harness_workflow/playbook/init.py` | 新增，`init_playbook(root, skip, only)` 主入口 |
| `src/harness_workflow/tools/harness_install.py` | 改，追加 init_playbook 调用 + 双 flag 注册 + playbook-only 单跑 |
| `src/harness_workflow/cli.py` | 改，install_parser 追加互斥组 + handler 透传 |
| `tests/test_playbook_install.py` | 新增，10 TC |

### 测试数字

- `pytest tests/test_playbook_install.py`: **10 passed / 0 failed**
- 全量回归 `pytest tests/`: **767 passed / 57 failed / 41 skipped**（基线 61 failed，本 chg 不引入新 fail，实际减少 4）
- `harness validate --contract artifact-placement`: **PASS，exit 0**

## 5. Issues / Bugs

### Issue-1：领域推断失败导致 install 返回 1（已修复）

**问题**：初始实现在 `infer_domains` 无法推断领域时，`init_playbook` 返回 1，导致所有未包含正确项目结构的临时 tmpdir 测试失败（test_cli.py / test_bugfix_13_project_skeleton_bootstrap.py 等共 20 条）。

**修复**：将 `init_playbook` 的领域推断失败逻辑从返回 1 改为返回 0 + stderr WARN（软失败语义）。路书初始化不应阻塞 install 主流程，用户可手工创建 `artifacts/project/playbooks/domains/` 结构。

**策略决策（default-pick）**：软失败（WARN + return 0），因为路书是可选增强功能，不是 install 必须成功的核心步骤。

### Issue-2：subprocess 测试 PYTHONPATH 设置

**问题**：subprocess 跑 `python3 -m harness_workflow.cli` 找不到 `harness_workflow` 模块（worktree 未安装到系统 Python）。

**修复**：在 `_run_cli` helper 中显式设置 `PYTHONPATH=<repo>/src:$PYTHONPATH`，让 subprocess 找到 worktree 的源码包。

## 6. 经验沉淀候选

### 候选一：4 级降级推断器的"软失败"原则

**场景**：项目结构检测（如领域推断）作为 install 的追加阶段，在检测失败时不应阻塞 install 主流程。

**经验**：
- 追加阶段（enhancement stage）的失败应以"软失败"语义处理（WARN + return 0），而非硬失败（ERROR + return 1）。
- 硬失败适合"缺少必要前置条件"的核心路径；软失败适合"可选增强功能无法初始化"场景。
- 判据：如果该阶段跳过后 install 仍然能完整落地核心功能（mirror 同步 + agent skill），则该阶段应软失败。

**应用范围**：任何在 install/update 阶段追加的可选功能（如路书初始化、项目扫描等）。

### 候选二：subprocess 测试的 PYTHONPATH 设置规范

**场景**：在 git worktree 中开发新功能，subprocess 测试需要 import 未安装的包。

**经验**：
- 测试 helper 的 `_run_cli()` 应在 subprocess 的 env 中追加 `PYTHONPATH=<repo>/src:$existing_PYTHONPATH`。
- 不要全局修改 `sys.path`（会影响同进程内其他测试），只在 subprocess env 中注入。
- 参考模式：`env["PYTHONPATH"] = f"{SRC_DIR}:{existing}" if existing else SRC_DIR`。

**沉淀位置候选**：`.workflow/context/experience/roles/executing.md` 经验十六（worktree subprocess 测试 PYTHONPATH 规范）。

## 7. 路径自检

| 工件类型 | 落点 | 是否合规 |
|---------|------|---------|
| playbook 子包 | `src/harness_workflow/playbook/` | ✅ 源码层，不在 scaffold_v2 mirror 同步范围 |
| 测试文件 | `tests/test_playbook_install.py` | ✅ tests/ 根目录 |
| 路书写入路径 | `{root}/artifacts/project/playbooks/` | ✅ OQ-1=B 路径，符合 repository-layout.md §2.1 |
| chg-03 session-memory | `.workflow/flow/requirements/req-55-.../changes/chg-03-.../session-memory.md` | ✅ 机器型文档落 flow/ |

硬门禁五确认：本 chg 改动全在 `src/harness_workflow/*.py`，不改 `.workflow/` 子树，无 scaffold_v2 mirror 同步责任。

## 8. 汇报字段（按 stage-role.md 统一精简汇报模板）

### 字段 1：产出（≤ 3 行）

- 新建 `src/harness_workflow/playbook/`（4 文件：`__init__.py / domain_inference.py / skeleton.py / init.py`）；改 `src/harness_workflow/tools/harness_install.py`（追加 init_playbook + 双 flag 互斥校验 + playbook-only 单跑路径）；改 `src/harness_workflow/cli.py`（install_parser 追加互斥组 + handler 透传）。
- 4 级降级推断器：Level-1 `src/modules/*` → Level-2 `src/domains/*` → Level-3 `app/*` → Level-4 `src/{pkg}/*次级模块`，命中即停 + stdout 打印命中级别（OQ-4=B-modified）；软失败语义（WARN + 0）不阻塞 install 主流程。
- 新增 `tests/test_playbook_install.py`（10 TC：4 级降级各 1 + dogfood subprocess + 幂等 + 双 flag + 互斥校验 + 骨架文件验证）。

### 字段 2：状态（单行）

- **PASS**。10 TC 全过，全量回归 57 failed（< 基线 61 failed），harness validate exit 0，硬门禁九自查 7 条全过。

### 字段 3：default-pick 决策列表

1. `init_playbook` 领域推断失败 = 软失败（WARN + return 0，不阻塞 install）——理由：路书是可选增强功能，失败不应中断 install 核心产物（mirror / agent skill）落地。
2. 互斥 flag 位于 harness_install.py 的 argparse 互斥组（而非 cli.py）——理由：harness_install.py 是实际执行入口，cli.py 同时也有互斥组作双重保护。
3. `--playbook-only` 时跳过 install_agent + install_repo——理由：按 plan.md § 7 实施，与 OQ-3=A 一致，保证单跑路书初始化的隔离性。

### 字段 5：结尾硬约束

**本阶段已结束。**
