---
id: bugfix-13
title: "install时自动创建artifacts-project骨架与索引模板"
created_at: 2026-04-30
operation_type: bugfix
stage: regression
verdict: real-issue
route: executing
---

# 诊断报告

## 1. 真伪判断

**真实问题**。req-52（硬编码 main 路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-04 的落地半截工程：项目级覆盖**读路径** + **stderr 日志**已接通 install_repo，但**写盘骨架自举**漏了一步，导致全新用户仓零可发现性 / 项目级覆盖能力对存量项目失效。

## 2. 主导根因

`install_repo()`（`src/harness_workflow/workflow_helpers.py` L3745-L4145）的项目级合并循环（L3781-L3806）只走 `if _main_project.exists()` 读分支；**主路径不存在时**（典型场景：全新用户仓 / 从未跑过本仓）只是 `_log_project_level_load(hits=0)` 默默放过，没有"骨架自举"。

scaffold_v2 mirror 按契约**不含** `artifacts/` 任何文件（仅含 `.workflow/` 树；`_SCAFFOLD_V2_MIRROR_WHITELIST` 含 "artifacts/project/" + "/project/" 双兜底，**正是为了**防止 mirror sync 反向覆盖用户在 artifacts/project/ 的写入）。所以 mirror 同步链路**也不会**顺手把骨架建出来——这条路**不能走**（破契约）。

唯一正确的修复方向：**install_repo 显式 bootstrap**，模板放 `assets/templates/project-skeleton/`（mirror 外），调用 `write_if_missing`（幂等天然，已有用户文件 100% 保留）。

## 3. 主 agent 4 条结论独立复核

| # | 主 agent 结论 | 复核命令 / 依据 | 复核结果 |
|---|--------------|----------------|---------|
| 1 | 自身仓 `artifacts/project/` 已存在（README + 6 份 index.md + 3 份 .gitkeep） | `find artifacts/project -maxdepth 3 -type f` | ✅ 命中 7 文件：README.md / 5 份 experience/*/index.md / 1 份 constraints/index.md / 3 份 .gitkeep（注：`tools/` 只有 .gitkeep 无 index.md，符合 `_load_project_level_index` scope_map 仅枚举 6 scope 的设计） |
| 2 | scaffold_v2 mirror 不含 `artifacts/project/` 模板 | `find src/.../scaffold_v2 -name "*project*"` + `find src/.../scaffold_v2 -type d` | ✅ scaffold_v2 树仅含 `.workflow/` 子树，无 `artifacts/`；`*project*` 命中仅为 `.workflow/context/project/project-overview.md`（与 artifacts/project/ 无关） |
| 3 | install_repo 没有"创建 artifacts/project/ 骨架"逻辑 | 通读 `install_repo()` L3745-L4145 + `grep "artifacts/project/" workflow_helpers.py` | ✅ 命中点：L172-L208 mirror 白名单 + L3781-L3806 读路径 + L3432 注释；**无任何**写盘代码 |
| 4 | "artifacts/ 不入 mirror" 是契约不可破 | `_SCAFFOLD_V2_MIRROR_WHITELIST` L172-L208 + 注释 + `repository-layout.md` §2.1 引用链 | ✅ 双兜底 "artifacts/project/" + "/project/" 明文豁免，护契约；`req-51 chg-02 / req-52 chg-02` 提交链已固化 |

4/4 全部成立。

## 4. Fix Plan（不重）

### 4.1 OQ-A：模板放哪？

- A. **新增 `src/harness_workflow/assets/templates/project-skeleton/` 独立模板树（README.md + 6 份 index.md + 3 份 .gitkeep，1:1 复刻自身仓 `artifacts/project/`），install 时按目录结构 `write_if_missing` 拷贝**
- B. 硬编码字符串模板写在 `workflow_helpers.py`（无新文件，但模板内容混在 src/ 里，不利后续维护与版本对齐）
- C. 复用现有 `assets/templates/`（`{name}.tmpl` 格式 + `render_template`），把 6 份 index.md 拆成 6 个 .tmpl + 1 个 README.tmpl + 3 个 .gitkeep 走 render

**default-pick：A**。理由：
- 模板**结构性强**（目录树 = 三个一级目录 + 子目录 + 7 份文件），整树 `_copy_tree`-style 推送比逐文件 render 更直观；
- 内容**几乎纯 markdown frontmatter + 表格**，无需变量替换（除 `created_by` 字段可保留 req-52 / chg-03 字面，无 repo_name / date 注入需求）；
- 与现有 `assets/templates/*.tmpl` 路径并列**不冲突**——前者按文件名平铺，project-skeleton 走子目录树，互不交叉；
- 候选 B 把 markdown 嵌在 .py 字符串里，违反"内容与代码分离"原则，长期维护差；
- 候选 C 强行套 .tmpl + render_template，但本场景**无变量**，render 是空操作，徒增复杂度。

### 4.2 OQ-B：写盘逻辑放哪？

- A. **`install_repo()` 入口段（`_migrate_workflow_dir` + `_ensure_workflow_dir_gitignore` 之后、项目级合并循环 L3777 之前）插一段 `_bootstrap_project_skeleton(root, check=check)` 调用**；force_skill / force_managed / agent_override 均**不影响**该 bootstrap（独立于 install / update 委托路径）
- B. 抽到 `init_repo()` 内（与 `.workflow/` 骨架并列）
- C. 仅在 `if not force_skill:` install 专属分支内调用（update 委托路径跳过）

**default-pick：A**。理由：
- bootstrap 与 install / update 路径**正交**——存量项目首次升级到含本 fix 的版本时，走 update 委托路径也应顺手补齐项目级骨架（A 覆盖 install + update 双路径）；
- 候选 B 让 init_repo 兼管 artifacts/，但 init_repo 历史职责是 `.workflow/` 写盘，扩职越界；
- 候选 C 让 update 路径丢失 bootstrap，存量项目永远建不出骨架，违背"项目级覆盖能力对存量项目也生效"的设计意图。

### 4.3 OQ-C：写盘 idempotent 策略

- A. **逐文件 `write_if_missing(path, content, created, skipped)`**（已有 helper，L2150-L2156，path.exists() 即 skip，**字节级保留**用户改动）
- B. 每次 install 强制覆盖（违反 user-write-protected-zones 契约，严禁）
- C. `check=True` 时只 dry-run + actions.append，`check=False` 时按 A

**default-pick：A + C 组合**。理由：
- A 是 install_repo 既有的"幂等天然"模式（参考 init_repo 内 write_if_missing 注释 L3870），用户哪怕已经写入 `constraints/my-rule.md` 或 `experience/roles/index.md`（含自定义条目）都**不会被覆盖**；
- C 把 dry-run 路径独立处理，与现有 `if check:` 分支风格对齐（L3891-L3905）；
- 候选 B 直接破"用户写保护"硬门禁（bugfix-8 / chg-01 落地），是禁手。

### 4.4 OQ-D：README.md 内容应该写啥（用户视角）

**default-pick**：1:1 复刻自身仓 `artifacts/project/README.md` 现有内容（已经写得很完整，含三段：用途 / 子目录结构 / OQ-A = D-modified 双轨过渡 / 契约引用 4 条）。**无需重新设计**——本仓自身就是最权威的范本。

如果未来需要给用户更友好的 onboarding，可在该 README 顶端补一节"## 快速上手"（"想加项目独有规则 → 写到 constraints/your-rule.md，并在 constraints/index.md 表格新增一行；想加 analyst 角色经验覆盖 → 写到 experience/roles/your-exp.md，并在 experience/roles/index.md 新增一行"）——但本 bugfix-13 不引入新内容，先复刻保持一致；如有补充需求，记 sug 后续 req 处理。

### 4.5 实施步骤草图

```
Step 1 (executing 阶段)：
  - 在 src/harness_workflow/assets/templates/ 下新建 project-skeleton/ 子目录
  - 复刻 7 份文件（保留 frontmatter + 表格 + 注释）：
    * README.md（来自 artifacts/project/README.md）
    * constraints/index.md
    * constraints/.gitkeep
    * experience/{roles,tool,risk,regression,stage}/index.md（5 份）
    * experience/.gitkeep
    * tools/.gitkeep

Step 2：
  - 在 workflow_helpers.py 加 helper：
    def _bootstrap_project_skeleton(root: Path, check: bool) -> list[str]:
        """req-52 chg-04 缺口补 / bugfix-13：在 install_repo 中创建
        artifacts/project/ 骨架（幂等 write_if_missing）。"""
        skeleton_root = PACKAGE_FS_ROOT / "assets" / "templates" / "project-skeleton"
        target_root = root / "artifacts" / "project"
        created, skipped = [], []
        if check:
            for src in skeleton_root.rglob("*"):
                if src.is_file():
                    rel = src.relative_to(skeleton_root)
                    dst = target_root / rel
                    if not dst.exists():
                        created.append(f"would create {dst.relative_to(root).as_posix()}")
            return created
        for src in skeleton_root.rglob("*"):
            if src.is_file():
                rel = src.relative_to(skeleton_root)
                dst = target_root / rel
                content = src.read_text(encoding="utf-8")
                write_if_missing(dst, content, created, skipped)
        print(
            f"[install_repo] project skeleton: created {len(created)} files / skipped {len(skipped)} files",
            file=sys.stderr,
        )
        return created

Step 3：
  - 在 install_repo() L3776（_ensure_workflow_dir_gitignore(root) 之后，
    "---- req-52 / chg-04（接入主流程）" 注释段之前）插：
    skeleton_actions = _bootstrap_project_skeleton(root, check=check)
    actions.extend(skeleton_actions)

Step 4 (testing 阶段)：
  - 新增 tests/test_bugfix_13_project_skeleton_bootstrap.py（详见 §测试用例设计）
  - 跑完整 lint 命令字面（详见 §完成判据）
```

## 5. 路由方向

**confirm + executing**。理由：
- 真实实现层 bug，非误判 / 非需求范围遗漏；
- 修复方案明确（4 个 OQ 都有 default-pick + 理由），无需回 analysis；
- 范围有限（src/ 1 个 helper + 1 处 install_repo 内插点 + 7 份模板文件 + 1 份测试文件），可直接进 executing。

## 测试用例设计

> regression_scope: targeted  # 改 full 触发 testing 全量回归（默认 targeted）
> 波及接口清单（git diff --name-only 自动生成 + 修复方案人工补全）：
> - src/harness_workflow/workflow_helpers.py（install_repo + 新增 _bootstrap_project_skeleton）
> - src/harness_workflow/assets/templates/project-skeleton/**（新增树，10 文件含 README + 6 index.md + 3 .gitkeep）
> - tests/test_bugfix_13_project_skeleton_bootstrap.py（新增）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-fresh-repo-bootstrap | tmpdir fresh repo（无 artifacts/）→ `python3 -m harness_workflow.cli install`（子进程真跑） | exit=0；`artifacts/project/{constraints,experience/{roles,tool,risk,regression,stage},tools}/` 9 目录 + 6 份 `index.md` + 1 份 `README.md` + 3 份 `.gitkeep` 全部存在；stderr 含 `project skeleton: created 10 files` | AC-01 | P0 |
| TC-02-idempotent-second-install | TC-01 同 tmpdir，再次跑 `harness install` | exit=0；stderr 含 `created 0 files / skipped 10 files`；7 份核心文件字节级保留（`stat -c %Y` 时间戳不变 / md5 一致） | AC-02 | P0 |
| TC-03-preserve-user-rule | tmpdir 先写 `artifacts/project/constraints/my-rule.md` 含 "USER_CONTENT" 字符串 → `harness install` | `my-rule.md` 字节级保留；同时 `constraints/index.md` 等 6 份骨架被新建 | AC-03 | P0 |
| TC-04-preserve-user-edited-index | tmpdir 先写 `artifacts/project/experience/roles/index.md` 含 "MY_CUSTOM_ENTRY" 一行 → `harness install` | 自定义 index.md **不被覆盖**（write_if_missing 命中 skip）；其他 5 份 index.md 仍按模板新建 | AC-04 | P0 |
| TC-05-check-mode-no-write | tmpdir fresh repo → `python3 -m harness_workflow.cli install --check` | exit=0；`artifacts/` 目录**不存在**；stdout / stderr 含 `would create artifacts/project/...` 计数；二次 ls 仍空 | AC-05 | P1 |
| TC-06-update-path-also-bootstraps | tmpdir 先 init_repo（仅 .workflow/）→ `python3 -m harness_workflow.cli update`（走 install_repo(force_skill=True) 委托路径） | bootstrap 仍生效（OQ-B = A 决定 update 路径也补骨架），骨架被创建 | AC-06 | P1 |
| TC-07-mirror-whitelist-still-protects | TC-01 后再写 `artifacts/project/constraints/another.md` → 第三次 `harness install --force-managed` | mirror→live sync 不覆盖；用户写入保留；白名单 "artifacts/project/" + "/project/" 双兜底未受影响 | AC-07 | P1 |
| TC-08-load-index-still-works | TC-04 后跑 `_load_project_level_index(tmpdir, "experience-roles")` → 解析自定义 index.md | 命中 1 行（path=…，title=…，scope=experience-roles，when_load=…，source="main"）；与 req-52 / chg-03 索引懒加载语义一致 | AC-08 | P1 |
| TC-09-no-regression-req52-e2e | 跑 `tests/test_req52_e2e_log.py -v` 全套（TC-01 zero-files / TC-02 main-path-hit） | 全绿；stderr 日志格式不变（`from artifacts/project/{scope}/` 行数 / 字面） | AC-09 | P0 |
| TC-10-no-regression-req51 | 跑 `tests/test_req51_project_level_protection.py -v` 全套 | 全绿；用户写入项目级文件保护契约不破 | AC-10 | P0 |
| TC-11-contract-all-pass | `python3 -m harness_workflow.cli validate --contract all` 在 TC-01 后 tmpdir | exit=0，无 ERROR 行 | AC-11 | P0 |
| TC-12-user-write-protected-pass | `python3 -m harness_workflow.cli validate --contract user-write-protected-zones` 在 TC-04 后 tmpdir（用户已写自定义 index.md） | exit=0；不报"artifacts/project/ 写入违反保护区"；若报警 → executing 阶段需补白名单豁免（兜底） | AC-12 | P0 |

每个波及接口至少 1 条用例（_bootstrap_project_skeleton 直接覆盖 TC-01~05 + TC-08；install_repo 接入点覆盖 TC-01 / TC-06；模板树覆盖 TC-01）。`regression_scope: targeted` 默认；破坏面限定在 install / update 写盘 + 项目级加载链局部，不需要 full 回归。

## 7. 完成判据（lint 命令字面）

```
pytest tests/test_bugfix_13_project_skeleton_bootstrap.py -v
pytest tests/test_req51_project_level_protection.py tests/test_req52_e2e_log.py tests/test_install_whitelist_business_zones.py -v
pytest tests/ -k "install" -v
python3 -m harness_workflow.cli validate --contract all
python3 -m harness_workflow.cli validate --contract user-write-protected-zones
```

全部 exit=0 / 全绿 / 无 ERROR 行 = 完成。

## 8. default-pick 决策清单

| OQ | 决策 | 理由 |
|----|------|------|
| OQ-A 模板放哪 | A：新增 `assets/templates/project-skeleton/` 独立模板树 | 结构性强 + 与 mirror 物理隔离 + 无变量无须 render |
| OQ-B 写盘逻辑放哪 | A：install_repo 入口段（覆盖 install + update 双路径） | 存量项目首次升级也补齐骨架 |
| OQ-C 幂等策略 | A + C：write_if_missing + check 模式 dry-run | 现有 helper 天然幂等 + 不破用户写保护 |
| OQ-D README 内容 | 1:1 复刻自身仓 README.md | 自身仓即权威范本，无需重设计 |

`required-inputs.md`：无阻塞（4 个 OQ 全部按 default-pick 推进，executing 直接消费即可）。
