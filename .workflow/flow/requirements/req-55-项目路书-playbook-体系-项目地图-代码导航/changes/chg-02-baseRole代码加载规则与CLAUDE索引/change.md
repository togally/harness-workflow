---
id: chg-02
title: "baseRole 追加代码加载规则 + CLAUDE.md 项目路书索引节"
req: req-55
created_at: 2026-04-30
---

## 目标

把 spec §三的"代码加载规则（强制）"章节落到 `.workflow/context/roles/base-role.md`，让所有继承该规约的角色（含 Director / toolsManager / stage 角色）获得统一的"路书优先 / 兜底声明 / 路书只读"行为；同时在仓库根 `CLAUDE.md` 末尾追加"项目路书"索引节，让 Claude Code 入口侧也指向路书。

## 范围（Scope）

### Included

- **base-role.md 追加**：在现有硬门禁清单（一/二/三/四/六/七/九）之后追加 **`## 硬门禁十：代码加载规则（强制）`**（OQ-2=A 用户拍定：沿用既有"硬门禁 N"编号风格，新编号 = 十）。包含 4 节：
  1. 优先走路书：先读 `@./artifacts/project/playbooks/code-map.md` → 关键词匹配 → `domains/<领域>/README.md` → `code.md` → 直接读文件，禁止 grep / glob。
  2. 兜底规则：路书未命中时（关键词无匹配 / 信息缺失 / 依赖链不通）允许全局查找；兜底后必须显式声明并以 `<!-- TODO: 待补入 code-map -->` 提示用户更新路书；不擅自改路书。
  3. 项目背景加载：业务概念任务必须先读 `@./artifacts/project/playbooks/overview.md` 理解术语。
  4. 不该做的事：未读 code-map 直接 grep / 跳过路书 / 修改 `artifacts/project/playbooks/` 下任何文件（路书是只读资源，OQ-5=A 软约束 + chg-05 漂移检测兜底）。
- **CLAUDE.md 追加**：在 `# currentDate` 段或文件末尾追加 `## 项目路书` 索引节，列 4 份顶层文件 + `domains/<领域>/` 子目录指向，路径全部 `artifacts/project/playbooks/`（OQ-1=B）。
- **新增 pytest 用例 2 条**（`tests/test_baserole_playbook_section.py`）：
  - `test_baserole_has_code_loading_section`：grep `## 硬门禁十：代码加载规则` 命中。
  - `test_claude_md_has_playbook_index`：grep `^## 项目路书` 命中且后面 6 行内含 `code-map.md`。

### Excluded

- 不动 `harness_install.py` / 不新增 CLI（chg-03/04/05 负责）。
- 不生成 `artifacts/project/playbooks/` 实际目录（chg-03 负责）。
- 不动其他角色文件（`analyst.md` / `executing.md` / 等），代码加载规则**只**写在 baseRole，零侵入具体角色（spec §三"零侵入"原则）。
- 不实现"路书只读"硬强制（无 hook / 无 lint），仅写规则 + 期望 chg-05 漂移检测兜底（OQ-5 default-pick = A：本 req 阶段只写规则，不引入 hook，遗留观察 1 次真实 req 后再决定是否升级硬强制）。

## 依赖

- 上游：chg-01（路书目录骨架契约：本 chg 引用其 §1-§3 规范作为路书形态保证）。
- 下游：chg-03（install 阶段创建 `artifacts/project/playbooks/` 时，本 chg 已落地的索引节 + baseRole 规则为预设语义）。

## 验收（Acceptance）

- AC-02.1：`base-role.md` 含 `## 硬门禁十：代码加载规则` 章节，4 节齐全。
  验证：`grep -c '^### [1-4]\.' base-role.md`（在硬门禁十段内部）≥ 4 + `grep -c '^## 硬门禁' base-role.md` ≥ 8（原 7 + 新增"硬门禁十"，OQ-2=A）。
- AC-02.2：`base-role.md` 硬门禁清单（文件头）已加入"硬门禁十"。
  验证：`grep -A12 '硬门禁清单' base-role.md` 含 "硬门禁十"。
- AC-02.3：`CLAUDE.md` 含 `## 项目路书` 段，列 `code-map.md` / `overview.md` / `architecture.md` / `runbook.md` / `domains/<领域>/`，路径全部 `artifacts/project/playbooks/`（OQ-1=B）。
  验证：`grep -c '^## 项目路书' CLAUDE.md` = 1，`grep -c 'code-map.md\|overview.md\|architecture.md\|runbook.md' CLAUDE.md` ≥ 4，`grep -c 'artifacts/project/playbooks' CLAUDE.md` ≥ 4。
- AC-02.4：pytest 3 条 PASS（`tests/test_baserole_playbook_section.py`）。
- AC-02.5：`harness validate --human-docs` exit 0。

## 风险与缓解

- 风险：base-role.md 已有 7 个硬门禁，新增编号"十"是否引发用户认知混乱。
  缓解：OQ-2 default-pick = A 沿用现有"硬门禁 N"风格（见 req 主 session-memory.md）；新增段顶部加溯源注释 `> 溯源：req-55（项目路书(Playbook)体系——项目地图+代码导航）/ chg-02（baseRole 代码加载规则与 CLAUDE 索引）`。
- 风险：CLAUDE.md 修改可能与既有 `# currentDate` 段冲突。
  缓解：追加在文件末尾，不动现有段落。
