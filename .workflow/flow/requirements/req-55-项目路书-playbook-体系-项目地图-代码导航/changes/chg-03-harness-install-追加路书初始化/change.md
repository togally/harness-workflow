---
id: chg-03
title: "harness install 追加路书初始化阶段"
req: req-55
created_at: 2026-04-30
---

## 目标

让 `harness install` 在完成既有 `install_repo`（mirror 同步 + agent skill 安装）之后，自动追加 `init_playbook` 阶段（OQ-3=A 默认追加、不修改既有内部）：检测 / 生成 `artifacts/project/playbooks/` 完整骨架（4 顶层 + 推断领域，OQ-1=B 路径定位）；不影响既有调用方默认行为；提供 `--skip-playbook` / `--playbook-only` 两 flag（互斥）控制开闭。

## 范围（Scope）

### Included

- **新增内部模块**：`src/harness_workflow/playbook/` 子包，含：
  - `__init__.py`：`init_playbook(root: Path, dry_run: bool, force: bool, skip: bool, only: bool) -> int` 主入口（`skip` / `only` 与 cli flag 直接对应）。
  - `domain_inference.py`：领域推断器，按 4 级降级链 **`src/modules/* → src/domains/* → app/* → src/{pkg}/*次级模块`** 顺序匹配，**命中即停**；返回 `[(domain_name, source_path)]` 列表（OQ-4=B-modified，单包项目用次级模块兜底，最低保证 ≥ 1 个领域）；stdout 打印形如 `domain inference: matched 'src/{pkg}/*次级模块' (4 domains: tools, playbook, assets, hooks)` 让用户感知 fallback 已触发。第 4 级单包兜底逻辑：`{pkg}` 自动从 `pyproject.toml` `[tool.poetry] / [project] name` 或 `setup.py` 读，无配置则取 `src/` 下唯一非 `__pycache__` 子目录名。
  - `templates.py`：4 顶层文件 + `domains/<领域>/` 4 件套的 string template，含 `<!-- AUTO:* -->` 区段标记。
  - `claude_md_index.py`：在 `CLAUDE.md` 末尾插入 `## 项目路书` 索引节（已存在则跳过，幂等），路径全部 `artifacts/project/playbooks/`（OQ-1=B）。
- **修改 `harness_install.py`**：
  - 在 `install_repo` 之后调 `init_playbook(root)`（OQ-3=A 默认追加阶段）。
  - 新增 argparse flag：`--skip-playbook`（跳过路书阶段）/ `--playbook-only`（仅跑路书，跳过 install_repo），两 flag 互斥（同时传两者 → exit ≠ 0 + stderr 提示）。
  - 现有调用方不传 flag 时默认行为 = 既有 install_repo + 路书初始化（追加阶段，不破坏既有产物）。
- **修改 `cli.py`**：`install_parser` 注册 `--skip-playbook` / `--playbook-only` 两 flag（互斥组）。
- **`init_playbook` 行为**：
  - `artifacts/project/playbooks/` 已存在 → stdout 打印 "playbook 已存在，跳过初始化"，return 0。
  - 不存在 → 创建 4 顶层文件 + `domains/<领域>/` 4 件套；自动填入 AUTO 区段（技术栈 / scripts / 顶层目录树 / `code.md` 文件清单）；其他章节留 `<!-- TODO: ... -->`。
  - 文件已存在不覆盖（per-file 幂等）。
- **新增 pytest 用例（≥ 6 条，覆盖 4 级降级每级 ≥ 1 fixture）**（`tests/test_playbook_install.py`）：
  - `test_install_creates_playbook_skeleton`：tmpdir + subprocess 跑 `python3 -m harness_workflow.cli install --root <tmp>`，断言 4 顶层文件存在于 `artifacts/project/playbooks/` + `domains/` 至少 1 个领域。
  - `test_install_idempotent_on_existing_playbook`：第二次跑 install，断言 `git status`（在 tmpdir）无 diff。
  - `test_install_skip_playbook_flag`：`--skip-playbook` 后 `artifacts/project/playbooks/` 不存在。
  - `test_install_playbook_only_flag`：`--playbook-only` 后 mirror 文件未被刷新（用 marker 文件断言） + stdout 含 "skipped install_repo"。
  - `test_install_flag_mutual_exclusion`：`--skip-playbook --playbook-only` 同时传 → exit ≠ 0 + stderr 含 "mutually exclusive"。
  - `test_domain_inference_4level_fallback`：4 级降级每级 ≥ 1 条 fixture（modules / domains / app / src/{pkg}/*次级模块），stdout 命中 `matched 'src/modules/*'` 等字面量。
- **dogfood TC**（必填字段：tmpdir / subprocess 命令 / stdout 断言 / runtime 断言 / `feedback.jsonl` 断言）：
  - `tests/test_playbook_install_dogfood.py::test_install_dogfood_full_run`：harness-workflow 自身仓跑 install 应命中第 4 级降级（`src/{pkg}/*次级模块`，推出 ≥ 1 个领域），断言 stdout 含 "playbook initialized" + `matched 'src/{pkg}/*次级模块'`，`runtime.yaml` `stage` 字段存在 / `feedback.jsonl` 事件数 ≥ 1；同时断言"现有 install 默认行为产物（mirror / agent skill）依然落地"，`--skip-playbook` 时不创建 `artifacts/project/playbooks/`，`--playbook-only` 时不刷 mirror。

### Excluded

- 不实现 `playbook-refresh`（chg-04）/ `playbook-check`（chg-05）。
- 不动 `base-role.md` / `CLAUDE.md` 的 baseRole 段（chg-02 已落地）；本 chg 仅在 `CLAUDE.md` 末尾插入"项目路书"索引节（如 chg-02 已落地则跳过，幂等）。
- 不调 LLM；纯静态分析 + 模板填充。

## 依赖

- 上游：chg-01（路书目录骨架契约：本 chg 严格按其 §1-§4 生成骨架）。
- 下游：chg-04 / chg-05 复用本 chg 落地的 `init_playbook` helper（领域推断 / AUTO 区段标记 / 模板）。

## 验收（Acceptance）

- AC-03.1：在 tmpdir 跑 `harness install` 后 `artifacts/project/playbooks/{overview,architecture,runbook,code-map}.md` 4 件齐全，`domains/` ≥ 1 子文件夹（含 `README.md` + `code.md`）（OQ-1=B 路径定位）。
- AC-03.2：第二次跑 install 后无 diff（幂等）。
- AC-03.3：`--skip-playbook` 行为正确（路书目录不被创建）。
- AC-03.4：`--playbook-only` 行为正确（mirror 不被刷新）+ stdout 含 "skipped install_repo"。
- AC-03.5：`--dry-run` 不落盘（`git status` 无新增）。
- AC-03.6：dogfood TC PASS（subprocess 实跑 + stdout / runtime / feedback 断言）。
- AC-03.7：harness-workflow 自身仓 `harness install --dry-run` 在本 chg 落地后不抛异常（领域推断走 4 级降级链命中第 4 级 `src/{pkg}/*次级模块` → 推出 ≥ 1 个领域，stdout 含 `matched 'src/{pkg}/*次级模块'`）；同时断言 `--skip-playbook` 时不创建 `artifacts/project/playbooks/`、`--playbook-only` 时不刷 mirror。

## 风险与缓解

- 风险 R-1：领域推断在本仓 `src/harness_workflow/*.py` 单包结构零命中。
  缓解：4 级降级链最后一级 `src/{pkg}/*次级模块` 兜底，把 `src/harness_workflow/{tools, playbook, assets, hooks}` 这类次级目录作为 fallback 领域；命中即停 + stdout 打印命中级别（`domain inference: matched 'src/{pkg}/*次级模块' (...)`）；推断器永远 ≥ 1 个领域（OQ-4=B-modified）。
- 风险 R-2：`--playbook-only` 被误用导致 mirror 未同步引发同步契约（硬门禁五）违反。
  缓解：`--playbook-only` stdout 显式打印 "skipped install_repo (--playbook-only); mirror not synced this run"，并在 `feedback.jsonl` 事件留痕。
- 风险 R-3：与 req-51 / req-52 既有 install 行为冲突（OQ-3）。
  缓解：默认行为 = `install_repo` 全跑完后**追加** `init_playbook`，不修改 `install_repo` 内部逻辑；新 flag 只控制是否跳过 / 单跑。详见 OQ-3 default-pick = A。
