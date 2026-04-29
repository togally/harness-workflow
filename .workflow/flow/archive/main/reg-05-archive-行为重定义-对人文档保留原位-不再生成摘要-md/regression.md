# Regression Intake — reg-05（archive 行为重定义：对人文档保留原位 + 不再生成摘要 md）

## 1. Issue Title

archive 行为重定义：对人文档保留原位 + 不再生成摘要 .md

## 2. Reported Concern

用户原话（2026-04-25 截图 `artifacts/main/requirements/` 全貌）：

> 对人文档就不用归档了,直接放在 requirements 中以文件夹形式存在就行了，还有就是问一下为什么归档好还有这些文件存在

具体两点诉求：

- **诉求 A**：req 级对人文档（`artifacts/main/requirements/{slug}/` 整 folder）走完 done 后**不必再挪窝**，就地以 folder 形态保留即可，不需要再"搬到 archive/"。
- **诉求 B**：当前 `archive_requirement` 在 `artifacts/main/requirements/` 下额外生成的 `{req-id}-{slug}.md` 摘要文件**冗余**——folder 内已有 `交付总结.md`（done 阶段产出，对人 brief 角色），又在 folder 外再造一份摘要相当于重复。

## 3. Current Behavior

`src/harness_workflow/workflow_helpers.py::archive_requirement`（lines 6015~6234）当前在 `harness archive` 触发时执行四步：

1. 把 `.workflow/state/sessions/{req-id}/` 整目录搬到 `artifacts/main/archive/requirements/{slug}/sessions/`（line 6209~6216）。
2. 把 `.workflow/state/requirements/{req-id}/` 子树（含 `requirement.md` / `*-report.md` 等机器型工件）搬到 `artifacts/main/archive/requirements/{slug}/state_requirements/`（line 6179~6190；req-39+ flat layout 分支）。
3. 把 `artifacts/main/requirements/{slug}/` **整 folder** 搬到 `artifacts/main/archive/requirements/{slug}/`（line 6118~6150；非 flow 分支）；req-41+ flow req 改走 `.workflow/flow/archive/{branch}/{slug}/`（line 6110~6117）。
4. 调用 `generate_requirement_artifact`（line 5311~5387）在 `artifacts/main/requirements/` 下另写 `{req-id}-{title}.md` 摘要文件（line 6228~6234）。

实际现状盘点（grep 自证）：

- `artifacts/main/requirements/` 下目前堆放 **16 份** `req-XX-{slug}.md` 摘要文件（req-28 ~ req-41），全部由 `generate_requirement_artifact` 生成，与 `artifacts/main/archive/requirements/{slug}/` 内副本同源同义。
- `artifacts/main/requirements/req-29-...{slug}/` 残留**孤儿 folder**（含 `交付总结.md` + `done-report.md`），是历史归档遗留——对人 folder 没有跟着被搬到 archive，但摘要 .md 已生成，造成"folder 在原位 + 摘要也在 + 同一 req 的副本又在 archive 下"三处重复。
- legacy req-37 archive 下 `artifacts/main/archive/requirements/req-37-.../` 含完整旧多层结构（changes/ + 测试结论.md + 验收摘要.md + 需求摘要.md），属契约 4 §4 historical 豁免。
- flow req-41 archive 下 `artifacts/main/archive/requirements/req-41-.../` 仅 `_meta.yaml + 交付总结.md + requirement.md + state.yaml`，已无 changes / brief 子树（说明 req-41 chg-01 已清理对人侧）；机器型工件已迁 `.workflow/flow/archive/main/req-XX/`。

## 4. Expected Outcome

用户期望（含本回归补全推断）：

- **E-1 对人 folder 不挪**：`artifacts/main/requirements/{slug}/` 整 folder 在 done 完成后**就地**保留为"已归档态"，不再迁入 archive；用户可在原位置直接看到对人产物（`requirement.md` 副本 / `交付总结.md` / 决策汇总.md / SQL / runbook 等白名单内文件）。
- **E-2 不生成摘要 .md**：`generate_requirement_artifact` 产出的 `{req-id}-{slug}.md` 摘要文件**直接废止**，因为 folder 内 `交付总结.md` 已是对人摘要载体（chg-05（done.md 交付总结模板扩 §效率与成本）落地）。
- **E-3 机器型归档去向**（用户未明说，按方向 C 精神推断）：`.workflow/flow/requirements/{req-id}-{slug}/` 仍按 chg-02（CLI 路径迁移 flow layout）走 `.workflow/flow/archive/{branch}/` 落位（关注点分离）；`.workflow/state/sessions/{req-id}/` + `.workflow/state/requirements/{req-id}/` 由于 flow 路径已收纳 sessions / yaml，req-41+ 不再涉及。
- **E-4 历史存量留作 git history**：legacy `artifacts/main/archive/requirements/{req-XX}/` 树（req-02 ~ req-40）按 §4 historical 豁免不动；本次只改 req-41+ 行为，残留摘要 .md + req-29 孤儿 folder 由本回归后续陪斩清理。

## 5. Next Step

1. 进入分析 → `analysis.md` 三层根因。
2. 决策 → `decision.md` 路由建议（候选标题 ≤ 30 字 + `--bugfix` / `--requirement` 取舍）。
3. 不修代码 / 不动 `archive_requirement` / 不动 `repository-layout.md`，交后续 chg / bugfix 执行。
