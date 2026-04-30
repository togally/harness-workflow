---
id: req-55
title: "项目路书(Playbook)体系——项目地图+代码导航"
created_at: 2026-04-30
operation_type: requirement
stage: analysis
---

## Goal

**问题**：AI agent 接到任务后无法精准加载相关代码——缺少"项目地图 + 代码导航"作为入口，只能依赖 grep / glob 全局扫描，既消耗上下文又不准确，且对业务术语（如 `Workspace ≠ Project` 这类业务边界）做错误推断。

**交付能力**（三件一体）：
1. **项目地图（playbook）**：`artifacts/project/playbooks/` 一套静态文档骨架（`overview.md` / `architecture.md` / `runbook.md` / `code-map.md` + `domains/<领域>/` 子文档），让 agent 通过"关键词 → 领域 → 文件清单"三跳定位代码（OQ-1 决策：与 req-51/req-52 项目级承载层保持一致）。
2. **agent 强制行为**：在 `base-role.md` 追加"代码加载规则（强制）"章节，让所有继承该规约的角色按"路书优先 + 兜底声明 + 路书只读"三条硬约束执行。
3. **路书生命周期 CLI**：扩展 `harness install` 追加路书初始化阶段；新增 `harness playbook-refresh`（HTML 注释定界自动区段刷新）/ `harness playbook-check`（漂移检测 + 健康报告 + CI 退出码）两条子命令，让路书可按项目演进自动维护，而非由 agent 各自更新导致内容失控。

## Scope

### Included（5 chg DAG）

- **chg-01（路书目录骨架契约）**：`artifacts/project/playbooks/` 目录结构定义（OQ-1=B，沿用 req-51/req-52 项目级承载规范）、4 份顶层文件（`overview.md` / `architecture.md` / `runbook.md` / `code-map.md`）写作规范、`domains/<领域>/` 4 件套（`README.md` / `code.md` / `data-model.md` / `notes.md`）字段契约、跨领域内容归属规则、HTML 注释定界 `<!-- AUTO:STACK -->` / `<!-- /AUTO:STACK -->` 等自动区段语义；本 chg 仅落骨架契约文档（写在 `.workflow/flow/playbook-layout.md`，第一节顶部显式声明"路书根目录 = `artifacts/project/playbooks/`"），并扩 `repository-layout.md` §2.1 项目级豁免章节从 3 类（constraints/experience/tools）扩到 4 类（+ playbooks）；不涉及 CLI 实现。
- **chg-02（baseRole 代码加载规则 + CLAUDE 索引）**：`.workflow/context/roles/base-role.md` 追加 `## 硬门禁十：代码加载规则` 章节（路书优先 / 兜底规则 / 项目背景加载 / 不该做的事 4 节），并在 `CLAUDE.md` 末尾追加"项目路书"索引节；本 chg 不动 CLI、不动 playbook 内容。
- **chg-03（`harness install` 追加路书初始化阶段）**：复用 `src/harness_workflow/tools/harness_install.py` 入口，在 `install_repo` 之后追加 `init_playbook` 阶段（OQ-3=A 默认追加，不修改既有内部）；命中 `artifacts/project/playbooks/` 已存在则跳过；不存在则生成 4 份顶层文件骨架 + 推断领域（OQ-4=B-modified，4 级降级链：`src/modules/* → src/domains/* → app/* → src/{pkg}/*次级模块`，命中即停，stdout 打印命中级别）+ 各 `domains/<领域>/` 4 件套；增加 `--skip-playbook` / `--playbook-only` 两 flag（互斥）；现有调用方在不传新 flag 时行为不变。
- **chg-04（`harness playbook-refresh` 子命令）**：在 `harness_workflow/tools/` 新增 `harness_playbook_refresh.py`，CLI 注册 `playbook-refresh`；只刷新 `artifacts/project/playbooks/` 内 HTML 注释定界的 `<!-- AUTO:* -->` 自动区段（技术栈 / scripts / 顶层目录树 / 各 `domains/<领域>/code.md` 文件清单 / `code-map.md` 位置字段），人工写入区一律不动；支持 `--dry-run`。
- **chg-05（`harness playbook-check` 子命令）**：新增 `harness_playbook_check.py` + CLI 注册 `playbook-check`；扫描 `artifacts/project/playbooks/` 做漂移检测（依赖新增但 `architecture.md` 未提 / scripts 新增但 `runbook.md` 未提 / 模块目录新增但 `domains/` 缺对应文件夹 / `domains/` 存在但 `code-map.md` 未登记或反之 / `code.md` 引用文件不存在 / `README.md` "依赖领域" 链接失效）+ 关键词覆盖检测（`code-map.md` 关键词为空领域）+ 未填 TODO 分组报告 + `@./` 引用路径有效性 + AUTO 区段被改但未跑 refresh 的兜底检测（OQ-5=A 路书只读软约束的事后审计闭环）；漂移返回非零 exit code 供 CI 接入。

### Excluded（明示不做）

- **不让脚本调 LLM**：所有路书生成 / 刷新 / 检测均为静态分析（文件树扫描 + 正则区段替换 + 路径存在性校验），保证可重复、可在 CI 跑、零成本。
- **不让 agent 自动维护路书**：路书是**只读资源**；agent 走兜底命中后只能用 `<!-- TODO: 待补入 code-map -->` 提示用户，禁止直接修改 `artifacts/project/playbooks/`。
- **不在路书里塞流程文档 / 输出风格 / 流程引导**：那些归 workflow（`.workflow/context/roles/*` / `.workflow/flow/stages.md`）；路书只回答"项目是什么、相关代码在哪"两件事。
- **不把代码清单塞进 `code-map.md`**：`code-map.md` 只做关键词 → 领域映射，文件清单归 `domains/<领域>/code.md`。
- **不复制同一份内容到多个 domain**：跨领域流程归调用方 `notes.md`，互相链接；真正全局的（认证 / 链路追踪 / 错误处理）放 `architecture.md`。
- **不在每个具体角色 prompt 里重复写代码加载规则**：那是 baseRole 的事（chg-02 落地点）。

## Acceptance Criteria

> 所有 AC 必须有可验证手段（文件存在性 / grep 命中 / pytest 用例 / CLI exit code），无空话条目。

- **AC-01（骨架契约文档落地）**：`.workflow/flow/playbook-layout.md` 存在；含 §1 顶层文件契约 / §2 domains 4 件套契约 / §3 跨领域归属规则 / §4 HTML 注释定界规约；grep `<!-- AUTO:` 命中 ≥ 5 处区段定义。验证：`test -f .workflow/flow/playbook-layout.md && grep -c '<!-- AUTO:' .workflow/flow/playbook-layout.md` ≥ 5。
- **AC-02（baseRole 强制章节落地）**：`.workflow/context/roles/base-role.md` 包含"代码加载规则（强制）"小节，覆盖 4 节（路书优先 / 兜底规则 / 项目背景加载 / 不该做的事），且与既有硬门禁清单（一/二/三/四/六/七/九）按统一编号风格协调（OQ-2 决策见下）。验证：`grep -c '## 硬门禁' .workflow/context/roles/base-role.md` 命中数 ≥ 8（原 7 + 新 1）。
- **AC-03（CLAUDE.md 索引节落地）**：`CLAUDE.md` 末尾含 `## 项目路书` 段，列出 4 份顶层文件 + `domains/<领域>/` 子目录指向。验证：`grep -A6 '^## 项目路书' CLAUDE.md` 输出非空且含 `code-map.md`。
- **AC-04（`harness install` 路书初始化生效）**：在干净仓库执行 `harness install`（不传 flag），完成后：(a) `artifacts/project/playbooks/overview.md` / `architecture.md` / `runbook.md` / `code-map.md` 4 件齐全；(b) `domains/` 至少含 1 个推断领域子文件夹（含 `README.md` / `code.md`）；(c) `CLAUDE.md` 末尾含项目路书索引节；(d) 已存在路书时再次执行 `harness install` 不覆盖任何文件，stdout 含 "playbook 已存在，跳过初始化"。验证：subprocess 调 `python3 -m harness_workflow.cli install --root <tmpdir>` 后断言文件存在 + 第二次跑断言无 diff。
- **AC-05（install flag 生效）**：`harness install --skip-playbook` 跳过路书阶段（原有 install_repo 行为不变，无 `artifacts/project/playbooks/` 产出）；`harness install --playbook-only` 跳过 install_repo（mirror / agent skill 不被刷写），仅执行路书初始化。验证：两条命令分别在 tmpdir 跑通 + 文件存在性断言。
- **AC-06（`harness playbook-refresh` 自动区段刷新）**：在已有路书的 fixture 上引入新 dependency / 新 script / 新 `src/modules/foo/`，跑 `harness playbook-refresh`，仅 `<!-- AUTO:* -->` 区段被替换；HTML 注释外人工写入段保持 byte-identical。验证：跑 refresh 前后对每份文件 diff，AUTO 区段外的行 zero-diff。
- **AC-07（`harness playbook-check` 漂移检测）**：构造覆盖 6 类漂移的 fixture（依赖/scripts/模块目录/`code-map.md` 互引/`code.md` 引用失效/`README.md` 依赖链接失效）+ 关键词为空领域 fixture，跑 `harness playbook-check` 命中 ≥ 6 + 1 类违规并 `exit 1`；空白健康仓库 `exit 0`。验证：pytest 7 条用例对应每类漂移。
- **AC-08（`--dry-run` 全覆盖）**：`harness install --dry-run` / `playbook-refresh --dry-run` 打印将要写入的文件路径与差异片段，不落盘；验证：跑完后 `git status` 无新增 / 修改文件。
- **AC-09（路径自检 + 项目级豁免合规）**：`artifacts/project/playbooks/` 由 `repository-layout.md` §2.1 项目级豁免章节扩 4 类（constraints/experience/tools + playbooks）覆盖（OQ-1=B 决策落地，chg-01 同步扩白名单）；`harness validate --contract artifact-placement` exit 0，`harness validate --human-docs` exit 0。
- **AC-10（dogfood 活证）**：harness-workflow 自身仓在 chg-03 完成后跑 `harness install`（dry-run 模式）不抛异常，且 `harness playbook-check --dry-run` 在 baseline 状态下 exit 0；提交前由 testing 阶段 sub-agent 跑 dogfood 子进程用例验证。
- **AC-11（pytest 全绿，零回归）**：实施完成后 `pytest tests/ -q` 全绿，且历史用例 0 fail；新增用例数 ≥ 12（每 chg ≥ 2 条，含 dogfood TC）。
- **AC-12（hardgate 链路：契约 + lint）**：新增契约 `harness validate --contract playbook-layout`（验证 chg-01 骨架契约自身字段完整 + chg-04/05 自动区段替换无错位），exit 0。

## Split Rules

### 拆分原则

1. **按交付物层次**：契约（chg-01） → 行为（chg-02） → CLI 实现按子命令（chg-03/04/05），每层独立可验证。
2. **依赖单向**：chg-01 落契约 → chg-02 / chg-03 引用契约 → chg-04 / chg-05 引用 chg-03 落地的 fixture；不允许反向依赖。
3. **粒度均衡**：每个 chg 落地代码 + 测试在 1 个 stage（≤ 1 day）完成，change.md ≤ 1 屏，plan.md ≤ 8 步。
4. **dogfood 内置**：chg-03 起每个 chg 必含一条 dogfood TC（subprocess 子进程实跑 CLI 入口），不允许只跑 unit。

### chg DAG（5 chg）

```
chg-01（路书目录骨架契约：playbook-layout.md）
   ↓
chg-02（baseRole 强制章节 + CLAUDE.md 索引节）   ← 与 chg-03 可并行（无文件冲突）
chg-03（harness install 追加路书初始化阶段）       ← 依赖 chg-01 契约
   ↓
chg-04（harness playbook-refresh 子命令）           ← 依赖 chg-03 fixture
chg-05（harness playbook-check 子命令）             ← 依赖 chg-03 fixture，可与 chg-04 并行
```

### 风险与缓解

- **风险 R-1（领域推断在本仓不适用）**：harness-workflow 自身是 `src/harness_workflow/*.py` 单包结构，没有 `src/modules/*` / `src/domains/*` / `app/*`；若推断器在本仓零命中，install 阶段会产出 0 个 domain → 路书形态不完整。**缓解**：chg-03 内置 4 级降级链（`src/modules/* → src/domains/* → app/* → src/{pkg}/*次级模块`），单包项目把 `src/{pkg}/<次级模块>/` 作 fallback 领域，命中即停 + stdout 打印命中级别（如 `domain inference: matched 'src/{pkg}/*次级模块'`），最低保证 ≥ 1 个领域骨架（OQ-4=B-modified 决策见下）。
- **风险 R-2（`--playbook-only` 切走 install_repo 引发 mirror 跳过 expectation 偏差）**：`harness install` 当前唯一同步入口是 `install_repo`，`--playbook-only` 跳过它会让用户误以为 mirror 已同步。**缓解**：`--playbook-only` 在 stdout 显式打印 "skipped install_repo (--playbook-only)"，并在 `feedback.jsonl` 留痕。
- **风险 R-3（路书"只读"约束对 agent 的强制力）**：base-role 写规则但无 hook 拦截 agent 写入。**缓解**：chg-02 在 baseRole 写"路书只读"硬约束 + chg-05 `playbook-check` 可在 CI 检出 agent 偷改（如 AUTO 区段被改但未跑 refresh 即提交）；强制阻拦交后续 req（OQ-5 决策见下）。
- **风险 R-4（`<!-- AUTO:* -->` 区段被人工破坏）**：用户手改 AUTO 区段后跑 refresh 会丢失改动。**缓解**：chg-04 refresh 实现里增加"AUTO 区段格式破损"检测，破损时 abort + 提示用户先修复定界；chg-05 `playbook-check` 把 AUTO 区段格式破损列为漂移项。

### 估算

| chg | 估算 | 关键交付 |
|-----|------|---------|
| chg-01（路书目录骨架契约） | 0.5 day | `playbook-layout.md` 契约文档 + pytest 契约用例 2 条 |
| chg-02（baseRole 代码加载规则与 CLAUDE 索引） | 0.5 day | `base-role.md` 强制章节 + `CLAUDE.md` 索引节 + grep 校验 |
| chg-03（harness install 追加路书初始化） | 1 day | `harness_install.py` 追加 + 4 件套生成器 + 推断器 + dogfood TC |
| chg-04（harness playbook-refresh 子命令） | 1 day | `harness_playbook_refresh.py` 新增 + AUTO 区段替换器 + dogfood TC |
| chg-05（harness playbook-check 子命令） | 1 day | `harness_playbook_check.py` 新增 + 7 类漂移检测 + dogfood TC |

总计：4 day（线性串行）/ 3 day（chg-04/05 并行）。
