# Change Plan

## 1. Development Steps

### Step 0：前置校验（必须）

- 确认 chg-01 ~ chg-05 全部 executing 完成、进入 testing 或更后阶段；任何一个未合入则停止。
- 在临时目录准备一个干净的沙盒仓库（`harness install` 新仓库）以避免污染当前 req-26 所在的主仓。

### Step 1：设计 smoke 剧本

本剧本按时间线描述，每步列期望产物：

1. **新建 requirement**：
   - `harness requirement "smoke demo requirement with space"`
   - 期望目录命名符合 chg-02 规则：`req-{n}-smoke-demo-requirement-with-space/`（空格转 -，带 id 前缀）。
2. **requirement_review 阶段**：
   - agent 完成 requirement.md；
   - agent 产出 `artifacts/main/requirements/{id}/需求摘要.md`（chg-05 AC-06）。
   - `harness next` 推进；核对 `.workflow/state/requirements/{id}.yaml` 的 stage 字段已更新（chg-03 AC-03）。
3. **planning 阶段**：
   - 创建至少 2 个 change；
   - 每个 change 产出 `变更简报.md`（chg-05）；
   - `harness next`。
4. **executing 阶段**：
   - 每个 change 产出 `实施说明.md`；
   - 期间执行一次 `harness rename` 修改某 change 标题，验证目录保留 chg-id 前缀、state yaml 同步（chg-02 AC-02）；
   - `harness next`。
5. **testing 阶段**：
   - 产出 `测试结论.md`（req 级）；
   - 期间触发一次 `harness regression "some user issue"`：
     - 核对 regression 目录 `reg-XX-some-user-issue/`（chg-01 AC-04）；
     - `harness regression --confirm some-user-issue`；
     - 核对 `current_regression` 仍在（chg-01 AC-01）；
     - `harness regression --testing` 能继续；
   - `harness next`。
6. **acceptance 阶段**：
   - 产出 `验收摘要.md`；
   - `harness next`。
7. **done 阶段**：
   - 产出 `交付总结.md`；
   - `harness archive`；
   - 核对归档路径 `archive/main/{req-id}-{slug}/`，无双层 main（chg-04 AC-05）。

### Step 2：落地为可重复的执行形态

- 优先形态：`tests/test_e2e_smoke.py`（pytest + subprocess 调 harness CLI，或调 python 入口函数）。
  - 对 agent 阶段的产物（需求摘要.md / 变更简报.md 等），用 mock 方式写入文件后再继续流程，保证自动化可跑；
  - 所有断言用 `pathlib` + `yaml.safe_load` 读文件检查。
- 备用形态：`artifacts/main/requirements/req-26-uav-split/changes/chg-06-.../smoke-runbook.md`（人工剧本），逐步执行并贴命令输出。

### Step 3：产出 smoke 报告

在本 change 的 executing 阶段，将一份 `smoke-report.md` 落到本 change 的 change 目录（`artifacts/main/requirements/req-26-uav-split/changes/chg-06-.../` 下）。报告包含：

- 每个 AC 的逐条核对结果（证据：路径 + 内容摘要）；
- 发现的新问题清单（如有）；
- 对本 req-26 是否可 archive 的总结判定。

### Step 4：反例核对

- `git status` 确认未改 `.workflow/flow/` 下任何历史文档；
- 未改 `artifacts/bugfixes/bugfix-2/`、`artifacts/main/bugfixes/bugfix-{3,4,5}/` 下任何文件。

## 2. Verification Steps

### 2.1 Smoke 剧本成功跑完

- 所有 7 个 stage 的对人文档都按命名表产出，路径与 AC-06 契约 2 同构；
- 所有 CLI 命令退出码为 0；
- runtime.yaml 与 stage yaml 全程一致。

### 2.2 AC 逐条对照

| AC | 证据来源 |
|----|---------|
| AC-01 | Step 1.5 regression confirm 后 --testing 能继续 |
| AC-02 | Step 1.4 rename 目录 + state yaml 同步 |
| AC-03 | Step 1.2/1.7 全链路无人工改 yaml，archive 成功 |
| AC-04 | Step 1.5 regression 目录命名 |
| AC-05 | Step 1.7 archive 路径无双层 branch |
| AC-06 | 每个 stage 的对人文档产出 |
| AC-07 | 本 change 整体 |

### 2.3 smoke-report.md 审查

- 主 agent 在 acceptance 阶段阅读 smoke-report.md，确认证据链完整。

## 3. 依赖与执行顺序

- 强依赖：chg-01 ~ chg-05 全部先于本 change 执行完成。
- 建议 executing 顺序（由主 agent 决定）：
  1. chg-01 / chg-02 / chg-03 / chg-04 / chg-05 并行或串行推进；
  2. 5 个前置 change 的 testing/acceptance 过后再进入 chg-06；
  3. chg-06 跑完则 req-26 整体可 archive。
