# Change

## 1. Title

对人文档端到端 smoke + req-28 自身作为首次完整示范

## 2. Goal

- 交付一个端到端 smoke 脚本（在 tempdir 走完整 req 生命周期 + 一个 bugfix 分支），断言 6 份对人文档（需求摘要 / 变更简报 / 实施说明 / 测试结论 / 验收摘要 / 交付总结）真实产出并通过 chg-05 的校验；同时让 req-28 自身在各 stage 推进时真实产出 6 份对人文档——这就是"首次完整示范"。

## 3. Requirement

- `req-28`

## 4. Scope

### Included

- 新增 `tests/test_human_docs_e2e.py`（或 `tests/smoke_human_docs.py`）：
  - 用 `tempfile.TemporaryDirectory` + `harness install` 建一个全新仓库。
  - 顺序模拟：`harness requirement "demo"` → 在 requirement_review 产 `需求摘要.md` → `harness next` → planning 产 `变更简报.md` → executing 产 `实施说明.md` → testing 产 `测试结论.md` → acceptance 产 `验收摘要.md` → done 产 `交付总结.md`。
  - 再模拟 bugfix 分支：`harness bugfix "demo-fix"` → 走完 regression→executing→done（产生 `回归简报.md` / `实施说明.md` / `交付总结.md`）。
  - 结尾调用 chg-05 的 `harness validate --human-docs --requirement <id>` 与 `--bugfix <id>`，断言全 ok。
- 在 req-28 真实推进路径上兜底：
  - planning 阶段本 change 自身也产出 `变更简报.md`（本文件同目录同名）。
  - executing 阶段 6 个 change 每个都须产出 `实施说明.md`（由后续 executing 角色负责）。
  - testing / acceptance / done 阶段按契约依次产出其他 3 份对人文档。
  - 以上由 AC-11 + AC-09 共同反向覆盖。

### Excluded

- 不跑真实的 Anthropic API / subagent 调度，smoke 用"脚本直接写对人文档 + 调 harness CLI 推进 stage"的组合绕过。
- regression 产 `回归简报.md` 的完整校验本 chg 不做深入，V1 只断言其存在。
- 不覆盖 ff 模式下的对人文档产出路径（留作 sug）。

## 5. Acceptance

- Covers requirement.md **AC-11**：req-28 自身 6 份对人文档全部真实产出；端到端 smoke 绿灯；AC-09 校验对 req-28 全 ok。
- 同时兼作 AC-07 的端到端回归验证（端到端路径打通）。

## 6. Risks

- 风险 A：smoke 用时过长（完整 req 生命周期 > 1 分钟）→ 缓解：允许 smoke 标记 `@pytest.mark.slow`，默认 CI 运行；同时提供 `--fast` 只跑 requirement→planning→done 最短链路。
- 风险 B：在 tempdir 中 harness install 依赖外部网络 → 缓解：smoke 使用 editable-install 的 harness_workflow，不重新 pip；CI 在 job 内设置 PYTHONPATH。
- 风险 C：req-28 自身的 `交付总结.md` 要到 done 阶段才能产出，chg-07 本身处在 executing 时无法完整自我验证 → 缓解：chg-07 的 smoke 在 tempdir 中走完整链路是"首次示范"的真实主体，req-28 自身的 6 份产出由各 stage 真实推进闭环。
