---
id: chg-03
title: "harness install 追加路书初始化阶段"
req: req-55
created_at: 2026-04-30
---

## 1. 执行步骤

1. **读上下文**：读 chg-01 落地的 `playbook-layout.md`（路书根 = `artifacts/project/playbooks/`，OQ-1=B）、`harness_install.py` 现有结构（`install_agent` + `install_repo`）、`cli.py` install 子命令注册段。
2. **建子包**：创建 `src/harness_workflow/playbook/{__init__.py, domain_inference.py, templates.py, claude_md_index.py}`。
3. **写 `domain_inference.py`**：实现 4 级降级链（**顺序**：`src/modules/*` → `src/domains/*` → `app/*` → `src/{pkg}/*次级模块`），**命中即停**；返回 `[(domain_name, source_path)]`；stdout 打印形如 `domain inference: matched 'src/{pkg}/*次级模块' (4 domains: tools, playbook, assets, hooks)`（让用户感知 fallback）；第 4 级 `{pkg}` 自动从 `pyproject.toml` `[tool.poetry] / [project] name` 或 `setup.py` 读，无配置则取 `src/` 下唯一非 `__pycache__` 子目录名（OQ-4=B-modified）。推断器永远 ≥ 1 个领域，零兜底场景才 abort + stderr。
4. **写 `templates.py`**：4 顶层文件 + `domains/<领域>/` 4 件套 string template，AUTO 区段使用 `<!-- AUTO:STACK -->` / 等标记（参考 chg-01 §4）。
5. **写 `__init__.py`**：实现 `init_playbook(root, dry_run, force, skip, only) -> int`：检测 `artifacts/project/playbooks/` 是否已存在 → 不存在则按 templates 生成；填 AUTO 区段静态分析数据；写入路径 = `{root}/artifacts/project/playbooks/`（OQ-1=B）。
6. **写 `claude_md_index.py`**：在 `CLAUDE.md` 末尾插入"项目路书"索引节（grep 检测已存在则跳过），路径全部 `artifacts/project/playbooks/`。
7. **改 `harness_install.py`**：在 `install_repo` 调用之后追加 `init_playbook(root, dry_run=args.dry_run, force=args.force_managed, skip=args.skip_playbook, only=args.playbook_only)`（OQ-3=A 默认追加）；`--skip-playbook` / `--playbook-only` 两 flag 互斥校验（同时传 → exit ≠ 0 + stderr 提示 "mutually exclusive"）；`--playbook-only` 时跳过 `install_repo` 且 stdout 显式打印 "skipped install_repo (--playbook-only); mirror not synced this run"。
8. **改 `cli.py`**：`install_parser` 加 `--skip-playbook` / `--playbook-only` 两 flag（互斥组）。
9. **改 README / SKILL.md mirror 同步**：明确"`harness install` 现含路书初始化阶段（默认开启）；`--skip-playbook` 跳过路书阶段；`--playbook-only` 仅跑路书阶段"。
10. **新增 pytest 用例 ≥ 6 条 + dogfood TC 1 条**（含 4 级降级每级 ≥ 1 fixture）。
11. **跑 pytest**：`pytest tests/test_playbook_install*.py -v` 看真实数字。
12. **dogfood 实跑**：`python3 -m harness_workflow.cli install --root <tmpdir> --dry-run` 看 stdout / exit code。
13. **harness-workflow 自身仓 dogfood**：`python3 -m harness_workflow.cli install --dry-run`，断言无异常 + 领域推断走第 4 级降级命中（`matched 'src/{pkg}/*次级模块'`） + 现有 install 默认行为产物（mirror / agent skill）依然落地 + `--skip-playbook` / `--playbook-only` 双断言。
14. **harness validate**：`harness validate --contract artifact-placement && harness validate --human-docs`。
15. **session-memory 留痕**：所有数字 + exit code。

## 2. 产物

- `src/harness_workflow/playbook/__init__.py`（新增）
- `src/harness_workflow/playbook/domain_inference.py`（新增，4 级降级链 + stdout 命中级别打印）
- `src/harness_workflow/playbook/templates.py`（新增）
- `src/harness_workflow/playbook/claude_md_index.py`（新增，路径 `artifacts/project/playbooks/`）
- `src/harness_workflow/tools/harness_install.py`（追加 init_playbook 调用 + flag 解析 + 互斥校验）
- `src/harness_workflow/cli.py`（install_parser 加 `--skip-playbook` / `--playbook-only` 互斥组）
- README.md / SKILL.md（mirror 同步行：明确"`harness install` 现含路书初始化阶段（默认开启）；`--skip-playbook` 跳过；`--playbook-only` 仅跑路书"）
- `tests/test_playbook_install.py`（新增，≥ 6 条 TC，含 4 级降级每级 ≥ 1 fixture）
- `tests/test_playbook_install_dogfood.py`（新增，1 条 dogfood TC，含双 flag 守护断言）

## 3. 依赖

- 上游：chg-01（playbook-layout.md 骨架契约）。
- 下游：chg-04（playbook-refresh 复用 templates.py + AUTO 区段标记 + domain_inference）/ chg-05（playbook-check 复用 domain_inference + AUTO 区段位置元数据）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - src/harness_workflow/tools/harness_install.py（追加 init_playbook 阶段 + 双 flag 互斥校验）
> - src/harness_workflow/cli.py（install_parser 加 `--skip-playbook` / `--playbook-only` 互斥组）
> - src/harness_workflow/playbook/*（新增子包，含 4 级降级 domain_inference + 写入 `artifacts/project/playbooks/`）
> - README.md / SKILL.md（mirror 同步行）
> - 调用链：harness install 入口 → install_agent → install_repo → init_playbook（新追加，OQ-3=A 默认）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 干净仓库跑 install 生成 4 顶层 + ≥ 1 领域 | tmpdir + subprocess install | 4 文件存在于 `artifacts/project/playbooks/` + domains/ ≥ 1 子目录 | AC-03.1 | P0 |
| TC-02 已有 playbook 二次 install 幂等 | 已有 playbook 的 tmpdir | git diff 空 | AC-03.2 | P0 |
| TC-03 `--skip-playbook` flag | tmpdir + `install --skip-playbook` | `artifacts/project/playbooks/` 不存在 + 现有 install 产物（mirror / agent skill）依然落地 | AC-03.3 | P0 |
| TC-04 `--playbook-only` flag | tmpdir + 预置 marker 文件 + `install --playbook-only` | `artifacts/project/playbooks/` 存在 + marker 文件未被刷写 + stdout 含 "skipped install_repo" | AC-03.4 | P0 |
| TC-05 `--dry-run` 不落盘 | tmpdir + `install --dry-run` | git status 无新增 | AC-03.5 | P0 |
| TC-06 双 flag 互斥校验 | `install --skip-playbook --playbook-only` | exit ≠ 0 + stderr 含 "mutually exclusive" | AC-03.4 | P0 |
| TC-07 4 级降级 level-1 modules | fixture: `src/modules/{auth,payment}/` | stdout 含 `matched 'src/modules/*' (2 domains: auth, payment)` | AC-03.7 | P0 |
| TC-08 4 级降级 level-2 domains | fixture: `src/domains/{order,user}/` | stdout 含 `matched 'src/domains/*'` | AC-03.7 | P0 |
| TC-09 4 级降级 level-3 app | fixture: `app/{web,worker}/` | stdout 含 `matched 'app/*'` | AC-03.7 | P0 |
| TC-10 4 级降级 level-4 单包次级模块 | fixture: `src/mypkg/{tools,assets}/` + `pyproject.toml [project] name = mypkg` | stdout 含 `matched 'src/{pkg}/*次级模块'` + 推出 ≥ 2 个领域 | AC-03.7 | P0 |
| TC-Dogfood-01 完整 install dogfood 实跑 | tmpdir + tmp_path fixture + subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'install', '--root', tmpdir]) | exit 0 + stdout 含 'playbook initialized' + `domain inference: matched 'src/{pkg}/*次级模块'` + runtime.yaml stage 字段存在 + feedback.jsonl 事件数 ≥ 1；现有 install 产物（mirror / agent skill）依然落地；`--skip-playbook` 时不创建 `artifacts/project/playbooks/`，`--playbook-only` 时不刷 mirror | AC-03.6 / AC-03.7 | P0 |
| TC-11 harness-workflow 自身仓 dogfood 命中第 4 级 | 本仓根 + `install --dry-run` | exit 0 + 领域推断 ≥ 1 + stdout 含 `matched 'src/{pkg}/*次级模块'`（OQ-4=B-modified 兜底） | AC-03.7 | P0 |
