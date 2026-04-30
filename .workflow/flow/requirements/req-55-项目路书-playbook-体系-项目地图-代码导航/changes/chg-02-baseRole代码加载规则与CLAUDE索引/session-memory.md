# Session Memory — chg-02（baseRole 代码加载规则与 CLAUDE 索引）

## 1. Current Goal

把 spec §三"代码加载规则（强制）"落到 base-role.md（新增硬门禁十）+ CLAUDE.md 末尾追加"项目路书"索引节；零侵入具体角色文件。

## 2. Context Chain

- Level 0: 主 agent（harness-manager） → analysis stage 编排
- Level 1: Subagent-L1（analyst / opus） → req-55 analysis stage
- 后续 Level 1（executing / sonnet）：执行本 chg 实施

## 3. Completed Tasks

- [x] base-role.md 头部硬门禁清单加 "硬门禁十：代码加载规则（req-55（项目路书Playbook体系）/ chg-02（baseRole代码加载规则与CLAUDE索引））"
- [x] base-role.md 新增 `## 硬门禁十：代码加载规则（强制）` 4 节（路径全部 `artifacts/project/playbooks/`）含溯源行 + OQ-2=A / OQ-5=A 提及
- [x] CLAUDE.md 追加 `## 项目路书` 索引节（路径全部 `artifacts/project/playbooks/`）
- [x] scaffold_v2 mirror 同步（硬门禁五合规）：base-role.md + CLAUDE.md 均已同步追加
- [x] tests/test_playbook_baserole_contract.py 4 条 TC PASS
- [x] harness validate --contract artifact-placement exit 0

## 4. Results

- base-role.md `^## 硬门禁` 标题计数：9（原 8 + 新增硬门禁十）
- base-role.md 硬门禁十：清单条目命中 1 + 标题行命中 1，溯源行含 OQ-2=A / OQ-5=A
- CLAUDE.md：`## 项目路书` 命中 1，`artifacts/project/playbooks` 命中 1+，4 份顶层文件名均命中
- scaffold_v2 mirror diff = 0（mirror 同步验证通过）
- pytest tests/test_playbook_baserole_contract.py：**4 passed / 0 failed**
- harness validate --contract artifact-placement：**exit 0**

## 5. Issues

无。

## 6. 经验沉淀候选

- **清单条目不存在时的精确定位**：live base-role.md 的硬门禁清单中不包含"硬门禁九"条目（仅有硬门禁一/二/三/四/六/七），派发任务指令说"在硬门禁九行后追加"但清单内无该行。实际处理：在清单末尾（硬门禁七）之后追加硬门禁九清单条目 + 硬门禁十清单条目，保持清单与详细段落的一致性。
- **中文引号在 Python 字符串字面量中的语法陷阱**：f-string / 普通字符串中包含全角引号"..."时 Python 3.14 报 SyntaxError；改为普通 ASCII 引号或去掉引号包裹即可。

## 5. Open Questions / default-pick

- OQ-1 已用户拍定 = B（`artifacts/project/playbooks/`）→ 本 chg 内所有路径已对齐。
- OQ-2 已用户拍定 = A（沿用"硬门禁 N"风格 → 新增"硬门禁十"，章节标题确认为 `## 硬门禁十：代码加载规则（强制）`）。
- OQ-5 已用户拍定 = A（仅写规则 + chg-05 漂移检测兜底，不引入 hook、不改文件系统权限）→ 硬门禁十 §4 明确写"不要修改 `artifacts/project/playbooks/` 下任何文件"。
- 详见 req 主 session-memory.md `## 9`。

---

## 完成态

本 chg executing stage 完成 ✅
