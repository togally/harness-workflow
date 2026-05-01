# CHANGELOG

## 1.0.1 (2026-05-01)

req-57：多项目工作区路书 + .workflow 本地化（minor 增量）。

### Major Features

**req-57 / chg-01：多项目工作区检测 + AUTO 多段聚合**
- 新增 `WorkspaceDetector`（priority=5，先于 MavenMultiModuleDetector）
- 触发条件：root 无项目文件（pom/package/pyproject/Cargo/go.mod/gradle）+ 顶层 ≥2 个子目录各有项目文件
- `_scan_stack` / `_scan_layout` / `_scan_scripts` 按 sub-project 分段：
  - 每段标题 `### {dir} ({stack-label})`，stack-label 自动识别（Java/Maven、Node/Vue、Node/React、Node、Go、Python、Rust）
  - layout 路径加 sub-project 前缀（`frontend/src/main.ts`）
  - scripts 按 sub-project 列脚本
- 实证：uav workspace（4 sub-project：2 Vue + 2 Maven）端到端识别正确

**req-57 / chg-02：sub-project domain 路径调整**
- 每个 sub-project 当顶级 domain，domain 名直接用目录名（保留大小写 + 短横线，不规范化）
- `_scan_domain_files` 扫整个 sub-project 子树（IGNORE_DIRS 过滤）
- 200 文件上限防爆：超出截断 + 末尾提示"还有 X 个文件未列"（uav 实证：Yh-platform 2869 → 截断 200 + 提示 2669）
- 内部不递归（OQ-3：只到 sub-project 层为叶子）

**req-57 / chg-05：硬门禁十 §1 升级（路书读法泛化到所有 stage）**
- 1.0.0 版只说"任务入场即读路书"，没明列哪些 stage 角色 / 哪些工件，下游实测 analyst 看到任务直接 grep 全仓代码（跳过术语 → code-map 关键词索引 → domain README → KEY_FILES 的导航链）
- §1 升级：明列 7 个 stage 角色（analyst / planning / executing / testing / acceptance / regression / done）+ 5 类工件（requirement.md / change.md / plan.md / regression diagnosis / bugfix.md）+ 5 步导航（read overview → 关键词命中 domain → 读 README → 读 code/data-model/notes → **禁止跳过 1-4 直接 grep**）
- live + scaffold_v2 mirror 双写 byte-identical（硬门禁五）
- contract 测试 15 个（TC-01..05 覆盖标题 / 7 stage / 5 工件 / 5 步关键词 / mirror byte-identical）

**req-57 / chg-03：.workflow/ 整体本地化（行为反转）**
- **Breaking 行为反转**：1.0.0 写 `!.workflow/`（强制不忽略）→ 1.0.1 反转为 `.workflow/`（整体忽略）
- 函数 `_ensure_workflow_dir_gitignore` → `_ensure_workflow_dir_ignored`（旧名 alias 保留）
- 三态边界（OQ-5）：
  - (a) 无 .gitignore → 新建仅含 `.workflow/`
  - (b) 已含精确 `.workflow/` → 跳过（幂等无 noise）
  - (c) 只含模糊 `.work*` → 追加 `.workflow/` + stdout 提示"请检查冗余"
- 清除 1.0.0 遗留的 `!.workflow/` negation
- 工具自仓 dogfooding：根 `.workflow/` 一并 `git rm --cached -r`（1269 文件 untrack）；`scaffold_v2/.workflow/` 模板继续 git 管理（84 文件）

### Migration Guide

下游已 commit `.workflow/` 的项目升级 1.0.1 后跑：

```bash
pipx upgrade harness-workflow
cd your-project
git rm --cached -r .workflow/      # 从 git 移除（工作树文件保留）
harness install                    # 自动写 .gitignore 加 .workflow/
git commit -am "feat: harness 1.0.1 — .workflow/ localized"
```

### Design Decisions（OQ 裁决记录）

- **OQ-1 = 带栈标签**：`### {dir} ({stack})` 显著提高路书可读性
- **OQ-2 = 直接用目录名**：保留大小写 + 短横线，匹配用户实际目录路径
- **OQ-3 = 只到 sub-project 层**：防 domain 数量爆炸，等真实反馈再迭代
- **OQ-4 = 工具自仓也迁移**：行为一致原则；scaffold_v2 模板例外保留
- **OQ-5 = 三态边界**：详见 chg-03

### Known Issues（非阻塞）

- pre-existing：`test_dogfood_06_petmall_runbook_existence` 失败（依赖本仓 `artifacts/main/project/README.md`，artifacts/ 被 .gitignore 排除文件本不在 git 里）— 与 1.0.1 改动无关

### 事故记录

- 实施过程中误执行 `git checkout feature/req-53-playbook -- :/` 把 chg-01..03 改动全部回滚（worktree 重置回基线分支）；test_workspace_mode.py 因为是 untracked 文件得以保留；所有改动重做并验证通过。教训记入 `.workflow/context/experience/risk/known-risks.md`。

---

## 1.0.0 (2026-04-30)

First stable release of harness-workflow with full Playbook (路书) support.

### Breaking Changes（chg-D 精简命令体系）
- 删除 `harness install --playbook-only` flag：install 默认装路书骨架（不再可选）
- 删除 `harness install --skip-playbook` flag：路书是 1.0.0 标配
- install 不再输出 `[ASSISTANT INSTRUCTION]` 强指令提示——改由 `harness playbook-refresh` 触发
- agent 想填路书：主动跑 `harness playbook-refresh` → 命令输出强指令 → agent 接力填

### Major Features

**req-55: 项目路书 Playbook 体系**
- 4-file top-level playbook skeleton: overview.md / architecture.md / runbook.md / code-map.md
- Per-domain 4-file kit: README.md / code.md / data-model.md / notes.md
- Path locked at `artifacts/project/playbooks/` (OQ-1=B)
- Idempotent skeleton rendering

**req-56: 路书引擎升级**
- Java/Maven multi-module nested project support (chg-A recursive scan)
- LLM content filling phase (`harness install` / `harness playbook-refresh`)
- Segment-level read-only semantics (AUTO / LLM two-namespace)
- `harness playbook-check` drift detection (10 check types)

**chg-A: 路书改进**
- Maven nested module recursive detection
- `harness install` strong-instruction hint sentence for agent follow-up

**chg-B: 清掉 kimi/qoder LLM provider**
- 仅保留 cc (Claude Code) / codex provider
- NoopProvider fallback polished

**chg-C: 产品规范完善 + 1.0.0 发版准备**
- **三分类区段规范**: AUTO (脚本维护) / LLM (模型填充) / USER (人工维护)
- **新增 USER:* 区段**: RECENT_CHANGES / PENDING_DECISIONS / HISTORY
  - `playbook-check` 永不报漂移；只校验 marker 配对
- **新增 LLM:* 区段**: PROJECT_NAME / COMPONENT_RELATIONS / KEY_DEPENDENCIES /
  QUICK_START / TEST_COMMANDS / DEPLOY_STEPS / FAQ /
  ENTRY_POINTS / CONFIG_FILES / TEST_DIRS /
  KEY_FILES / DEPENDENCIES / DATA_STRUCTURES / DB_TABLES / DATA_FLOW / CROSS_DOMAIN_NOTES
- **构建产物忽略**: refresh 扫描跳过 target/ build/ dist/ logs/ node_modules/ 等目录
- **强指令提示句升级**: 明确列出所有 LLM:* 区段名 + 禁止碰 USER/AUTO 区段
- **base-role.md §4 重写**: 三分类完整定义 + 合规/违规示例
- **playbook-layout.md §6 扩展**: 区段类型规范文档
- 版本号 bump: 0.2.0 → 1.0.0

**硬门禁十一: 上下文规模管理**
- 上下文 ≥ 300k tokens 触发 compact / clear 决策规则

### Test Coverage

- Total: 1063 passed (baseline 1043 + 20 new chg-C tests)
- New test files:
  - `tests/test_skeleton_section_classification.py` (10 TC)
  - `tests/test_user_section_semantics.py` (5 TC)
  - `tests/test_ignore_build_artifacts.py` (5 TC)

### chg-F（1.0.0 收尾补丁）

**bug 修复**
- install 嵌套防护：在含祖先 `.workflow/` 的子目录跑 `harness install` 会 warn + exit 0；加 `--force-nested` 跳过检查
- D-03 用 IGNORE_DIRS：`playbook-check` D-03 模块目录漂移检测跳过 logs/ build/ target/ 等构建产物目录（原误报修复）
- C-01/C-04 扫描范围限定：只扫真正的路书文件（overview/architecture/runbook/code-map + domains/*/*），跳过 `.workflow/` 路径（harness skill 文件中的示例 marker 不再误报）

**命令清单全量**
- `COMMAND_DEFINITIONS` 补 8 个缺失命令（validate/trivial/migrate/tool-search/tool-rate/feedback/pad），`/harness-*` slash commands 全齐（26 个）

**删 `--no-llm` flag（冗余）**
- `harness install` / `harness playbook-refresh` 删除 `--no-llm` flag
- CI=true 自动跳过 LLM + NoopProvider auto-detect fallback 已覆盖该场景
- `playbook/init.py` / `harness_playbook_refresh.py` 函数签名同步更新

**harness-manager.md 命令清单同步**
- 新增承载层维护类（pad）+ 辅助功能类扩展（trivial/migrate/validate/tool-search/tool-rate/feedback/init）
- scaffold_v2 mirror 字节级一致（diff -q clean）

**新增测试**
- `tests/test_install_nested_guard.py`（3 TC）
- `tests/test_d03_ignore_dirs.py`（3 TC）
- `tests/test_check_scope_limited.py`（3 TC）

### Verified On

- dogfood: harness-workflow repo itself (Python project)
- PetMallPlatform: 36-domain Java/Maven multi-module project
  - AUTO:LAYOUT: 0 build artifact entries (target/ build/ logs/ excluded)
  - 148 playbook files created correctly
  - Strong hint sentence lists all LLM section names
