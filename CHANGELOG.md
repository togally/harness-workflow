# CHANGELOG

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
