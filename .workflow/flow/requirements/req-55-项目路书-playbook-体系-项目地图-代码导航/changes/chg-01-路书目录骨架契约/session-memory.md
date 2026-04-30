# Session Memory — chg-01（路书目录骨架契约）

## 1. Current Goal

落地 `.workflow/flow/playbook-layout.md` 契约底座（§1 顶部显式声明路书根 = `artifacts/project/playbooks/`，OQ-1=B 决策），并扩 `repository-layout.md` §2.1 项目级豁免章节从 3 类（constraints/experience/tools）扩到 4 类（+ playbooks），作为 req-55（项目路书(Playbook)体系——项目地图+代码导航）后续 chg 的引用基；不动 src/ / 不动 baseRole / 不生成实际 playbook 目录。

## 2. Context Chain

- Level 0: 主 agent（harness-manager） → analysis stage 编排
- Level 1: Subagent-L1（analyst / opus） → req-55 analysis stage 全流程
- 后续 Level 1 (executing / sonnet)：执行本 chg 实施

## 3. Completed Tasks

- [x] 新建 `.workflow/flow/playbook-layout.md` 含 §1-§5 共 5 节（§1 顶部第 10 行声明路书根 = `artifacts/project/playbooks/`）
- [x] 修改 `.workflow/flow/repository-layout.md` §2.1 项目级豁免：3 类 → 4 类（+ playbooks），加 OQ-1=B 注释行
- [x] 新建 `tests/test_playbook_layout_contract.py` 含 TC-01（5 节标题）/ TC-02（5 类 AUTO）/ TC-03（路书根路径）/ TC-04（§2.1 4 类豁免）
- [x] pytest 4 条全 PASS（4 passed / 0 failed）
- [x] harness validate --contract artifact-placement exit 0

## 4. Results

### 产出文件清单

| 文件 | 操作 | 说明 |
|-----|------|------|
| `.workflow/flow/playbook-layout.md` | 新增 | 路书目录骨架契约，§1-§5 共 5 节，5 类 AUTO 区段，5 条校验锚点 |
| `.workflow/flow/repository-layout.md` | 修改 §2.1 | 项目级豁免 3 类 → 4 类（+ playbooks），加 OQ-1=B 注释行 |
| `tests/test_playbook_layout_contract.py` | 新增 | 4 TC（TC-01 / TC-02 / TC-03 / TC-04）|

### grep 验证数字

- `grep -c '^## ' .workflow/flow/playbook-layout.md` = **5**（§1/§2/§3/§4/§5）
- `grep -c '<!-- AUTO:' .workflow/flow/playbook-layout.md` = **16**（表格行 + 正文引用共 16 次；含 STACK / SCRIPTS / LAYOUT / DOMAIN_FILES / DOMAIN_LIST 五类定义；≥ 5 满足 AC-01.2）
- `.workflow/flow/playbook-layout.md` 第 10 行含 `artifacts/project/playbooks/` = **命中**
- `.workflow/flow/repository-layout.md` §2.1 含 `playbooks` = **命中**，四类（constraints / experience / tools / playbooks）均存在

### pytest 结果

```
pytest tests/test_playbook_layout_contract.py -v
4 passed / 0 failed
```

### harness validate exit code

- `harness validate --human-docs`: **exit 1**（executing stage 尚未到 done，requirement.md 副本 / 交付总结.md 为 pending 状态，属正常工作流状态，非本 chg 引入问题）
- `harness validate --contract artifact-placement`: **exit 0**（`.workflow/flow/playbook-layout.md` 机器型文档落 flow/，合规）

### 自检 7 条（硬门禁九）

1. `test -f .workflow/flow/playbook-layout.md && wc -l .workflow/flow/playbook-layout.md` = **存在，241 行（≥ 80）** ✅
2. `grep -c '^## ' .workflow/flow/playbook-layout.md` = **5** ✅
3. `grep -c '<!-- AUTO:' .workflow/flow/playbook-layout.md` = **16**（含表格行 + 正文引用，五类区段全覆盖）✅
4. `head -10 .workflow/flow/playbook-layout.md | grep 'artifacts/project/playbooks/'` = **命中**（第 10 行）✅
5. `grep -A 5 '§2.1' .workflow/flow/repository-layout.md | grep -i 'playbook'` = **命中** ✅
6. `pytest tests/test_playbook_layout_contract.py -v 2>&1 | tail -10` = **4 passed / 0 failed** ✅
7. `grep -c '^def test_' tests/test_playbook_layout_contract.py` = **4** ✅

## 5. Issues / Open Questions

- `harness validate --human-docs` exit 1：这是 executing stage 的正常状态，requirement.md 副本和交付总结.md 在 done 阶段产出，不在本 chg 范围内；不影响 chg-01 验收（AC-01.4 要求的 `--contract artifact-placement` exit 0 已通过）。

## 6. 经验沉淀候选

- **候选（executing → 经验文件）**：本 chg 演示了"契约层文档骨架（playbook-layout.md）"的标准结构，可作为后续类似 req 新增契约文档的样本：
  - frontmatter（id / version / owner / created_by / created_at）
  - §1 顶部第一行显式声明根目录（路书根目录 = `artifacts/project/playbooks/`）
  - §1-§3 内容规范 + §4 AUTO 区段表（表格：区段标记 / 所在文件 / 内容来源 / 刷新触发 / 破损语义）+ §5 校验锚点清单（C-01～C-05）
  - OQ-1=B 项目级豁免扩 4 类的 repository-layout.md §2.1 修改样本（3 类 → 4 类，加注释行）
  - 沉淀位置候选：`.workflow/context/experience/roles/executing.md`（经验十六）
