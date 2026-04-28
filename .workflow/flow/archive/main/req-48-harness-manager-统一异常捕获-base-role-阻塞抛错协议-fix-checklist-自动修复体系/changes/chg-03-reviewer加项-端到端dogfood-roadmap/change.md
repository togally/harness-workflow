# Change — chg-03（reviewer 加项 + 端到端 dogfood + roadmap）

> 父需求：req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
> 角色：analyst（opus），由 executing（sonnet）按 plan.md 落地
> 依赖：chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）+ chg-02（Fix Checklist 首批 3 个 + lint 输出加 fix-checklist 指针）必须先完成

## 1. 目标

闭环防止"提示无工具"反模式未来再发生，并端到端 dogfood 验证 chg-01 协议 + chg-02 工程主菜真的能"自动修复 + 重试"。具体包含：

1. **修改 reviewer checklist + role 文档**：加新条目「新加 contract 必须配套 fix-checklist；新加硬门禁必须配套抛错协议」防止再犯；
2. **dogfood 端到端 pytest**：手动构造 3 个 contract FAIL 场景（artifact-placement / schema-audit / missing-document）→ 子进程跑 `harness next` → 观察 harness-manager 捕获 → 派发 fix-subagent → 按 checklist 修 → 复跑 lint 验证 PASS；
3. **roadmap.md 留尾输出**：列出留尾 3 个 fix-checklist + 5 个 contract 改造，建议作为 req-49 / req-50 单独落或拆 sug 池；

本 chg 是 req-48 反馈闭环的最后一环，落地后 req-48 进入 done 阶段。

## 2. 范围

### 2.1 包含

#### 2.1.1 reviewer checklist 加项

1. **修改 `.workflow/context/checklists/review-checklist.md`**：
   - 在「六层检查框架·第一层 Context」或「制品完整性检查专节·Context」位置新增高优先级条目：
     - `[ ] **抛错协议配套（高）**（req-48 / chg-03）：本 stage 新加任何 contract（validate_contract.py 新函数）必须配套 .workflow/context/checklists/fix-{error-type}.md；新加任何硬门禁（base-role.md 新段落）必须引用 error-protocol.md 的 HARNESS_BLOCK 协议；缺失视为 FAIL。`
   - 在「阶段速查表·done 阶段重点」加补丁：六层回顾 grep `validate_contract.py` 新增 `def check_*` 函数，逐一核对配套 fix-*.md 是否存在。

2. **修改 `.workflow/context/roles/reviewer.md`**：
   - 在 SOP「执行」段强调上述 checklist 项；如 reviewer.md 不存在或内容缺失，按 chg-03 实际查阅情况增量补充（不重写整文件）。

#### 2.1.2 dogfood 端到端 pytest

1. **新建 `tests/test_block_protocol_e2e.py`**：
   - fixture：`tmp_harness_repo`（tmpdir 内安装最小 .workflow/ 骨架，复用现有 `harness install` 在 tmpdir 跑通的方式）；
   - 用例 1（artifact-placement）：构造 `artifacts/main/requirements/req-99-x/planning/session-memory.md` 违规工件 → 子进程 `harness validate --contract artifact-placement` → assert exit 64 + `runtime-block.yaml` 写入；然后按 fix-artifact-placement.md 步骤手动 mv（subprocess `mkdir -p`/`mv` 调用模拟 fix-subagent）→ 复跑 contract → assert exit 0；
   - 用例 2（schema-audit）：构造 `.workflow/state/requirements/req-99/foo.yaml` 旧目录 → 子进程跑 contract → assert exit 64；fix（mv 到 archive 或迁 yaml）→ 复跑 → assert exit 0；
   - 用例 3（missing-document）：构造 runtime.yaml `stage=planning` 但 chg 子目录缺失 → 子进程跑 contract → assert exit 64；fix（按 stage 创建骨架）→ 复跑 → assert exit 0；
   - 每条用例 assert：`runtime-block.yaml` 字段完整 + stdout 含 `HARNESS_BLOCK:` + `fix-checklist:` 指针。

#### 2.1.3 roadmap.md 留尾输出（done 阶段补回写）

> 注：roadmap.md 由 done 阶段产出（与 req-46 / req-47 同款），但本 chg 明确 roadmap 内容骨架，避免 done 阶段再决策。

1. **roadmap 内容定调**（写入本 plan.md §结尾 + done 阶段六层回顾时由 done 角色 cp 出 roadmap.md）：
   - 留尾 3 个 fix-checklist：`fix-user-write-protected-zones.md` / `fix-build-cache-freshness.md` / `fix-self-audit-drift.md`；
   - 留尾 5 个 contract 改造：`role-stage-continuity` / `test-case-design-completeness` / `triggers` / `testing-no-destructive-git` / `deployment-sync`；
   - 建议路径：拆 req-49（剩余 3 个 fix-checklist + 配套 lint 改造）+ 拆 sug 池 5 个 sug（每个 contract 改造一条），按优先级渐进；
   - 优先级：user-write-protected-zones 最高（PetMall / uav 实证频次最高），其余按需。

#### 2.1.4 scaffold_v2 mirror 同步

- 同 commit 同步 `.workflow/context/checklists/review-checklist.md` 修改 + `roles/reviewer.md` 修改到 scaffold_v2 mirror（硬门禁五保护面）；
- `tests/test_block_protocol_e2e.py` 不需要 mirror（src/ 子树外）。

### 2.2 排除

- **不**新加任何 fix-checklist（5 个留尾的不在本 chg 范畴）；
- **不**改任何 contract lint（5 个留尾的不在本 chg 范畴）；
- **不**写 roadmap.md 文件本体到 `.workflow/flow/requirements/req-48-{slug}/done/`（done 阶段产出，本 chg 仅定调内容骨架）；
- **不**做反向回填 PetMall / uav 历史脏数据（按 req-48 §3.2 排除条款）。

## 3. 验收

- [ ] `.workflow/context/checklists/review-checklist.md` 含新条目「抛错协议配套（高）」+ 引用 req-48 / chg-03；
- [ ] `.workflow/context/roles/reviewer.md` 强调本条 checklist 项（如 reviewer.md 不存在按 chg-03 实际处理，记录在 session-memory.md）；
- [ ] `tests/test_block_protocol_e2e.py` 存在 + 3 用例 PASS（每用例覆盖 FAIL → fix → PASS 闭环）；
- [ ] roadmap 内容骨架在本 plan.md §4 / §5 留痕（done 阶段 cp 出 roadmap.md）；
- [ ] reviewer 文件 + checklist 同步到 scaffold_v2 mirror；
- [ ] `harness validate --contract artifact-placement` exit 0；
- [ ] `harness validate --human-docs` exit 0；
- [ ] 全量 pytest 不回归（`pytest tests/` 全 PASS）。

对应 AC：AC-06（reviewer checklist 加项 + 端到端自证）/ AC-08（分批落地与续尾 roadmap）+ AC-07（mirror 同步部分）。

## 4. 关联 sug

- 无（本 chg 是 req-48 反馈闭环，新设计）；
- roadmap.md 中可能新增 3-5 条 sug 入池（具体 sug-id 由 done 阶段分配）。
