---
id: chg-04
title: trivial 测试降级（1 unit test）+ trivial-guard 自动升级护栏 + done 精简
req: req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）
trivial: false
---

# chg-04（trivial 测试降级 + trivial-guard 兜底护栏 + done 精简版）

## 1. Goal

把 trivial 通道的测试要求从"13 TC + 5 合规扫描"降级到"1 unit test + 全量 pytest 不挂"，同时 CLI 在 executing → done 流转点自动跑 trivial-guard，超标时自动升级到 bugfix 通道，并产出 ≤ 200 字 done 阶段交付总结（跳六层回顾）。

## 2. Scope

### In-Scope

1. **trivial 通道测试硬规则**：在 `evaluation/testing.md` 加 §trivial 模式段：
   - 仅要求新增 1 个 unit test 断言 fix 行为；
   - 全量 pytest 不挂（trivial-guard 自动校验）；
   - **跳过**：13 TC 设计审查 / 5 合规扫描 / acceptance dimension 评分 / done 六层回顾；
   - testing stage 在 trivial 通道**不存在**（TRIVIAL_SEQUENCE 无 testing），由 trivial-guard 在 executing → done 流转点兜底。
2. **trivial-guard CLI 实现**：新增 `harness validate --trivial-guard` 子命令：
   - 跑 `git diff --shortstat` → 验证 ≤ 10 行 + ≤ 2 文件；
   - 跑全量 `pytest`（quiet 模式）→ 验证 exit 0；
   - 跑 `git diff` grep `^\+(import |from .* import)` → 验证无新增 import；
   - 跑 `harness validate --contract all` → 验证 exit 0；
   - 任一失败 → exit 非 0 + stdout 输出 `trivial 通道护栏触发：{原因}`。
3. **harness next 在 executing → done 自动跑 trivial-guard**：
   - 当 task_type=trivial 或 chg 级 trivial=true 时，从 executing 流转到 done 前先调 `harness validate --trivial-guard`；
   - 失败 → runtime stage 切回 executing + task_type 升级为 bugfix（task_type=trivial → bugfix；chg 级 trivial=true → false）+ stdout echo 升级提示句 `trivial-guard 触发自动升级：从 trivial 通道 → bugfix 通道`；
   - 成功 → 流转到 done。
4. **done 阶段精简版（trivial 模式）**：在 `.workflow/context/roles/done.md` 加 §trivial 模式段：
   - 跳过六层回顾（不做 Layer-1 ~ Layer-6 各项扫描）；
   - 仅产出 ≤ 200 字 `交付总结.md`（落 `artifacts/{branch}/requirements/{req-id}-{slug}/交付总结.md`），3 段固定结构（**问题 / 修复 / 验证** ≤ 60 字 / 段）；
   - 经验沉淀检查（轻量版）：仅记录 trivial 通道使用心得（≤ 50 字），不强制写 experience/。
5. **trivial 模式交付总结模板**：新增 `.workflow/flow/requirements/_templates/trivial-交付总结.md`：
   ```markdown
   # 交付总结（trivial）

   ## 问题
   <!-- ≤ 60 字 -->

   ## 修复
   <!-- ≤ 60 字 + 改动文件清单 -->

   ## 验证
   <!-- ≤ 60 字 + pytest passed 数 -->
   ```
   scaffold_v2 mirror 同步。
6. **runtime.yaml 升级路径状态保留**：trivial-guard 触发升级时，runtime.yaml 加 `upgraded_from: trivial`（或 `chg_upgraded_from: {chg-id}: trivial`）字段留痕，便于事后审计；done 阶段六层回顾扫此字段时跳过 trivial 任务（已升级的不算 trivial 周期）。

### Out-of-Scope

- dogfood 活证（chg-05）；
- reviewer 加项（chg-05）；
- `harness validate --contract all` 扩展覆盖 trivial 通道路径（chg-05）。

## 3. Acceptance（对应 req-49 AC）

- AC-04（trivial-guard 自动跑 + 阈值超标 / pytest 红 → runtime stage 切回 executing 续走 BUGFIX_SEQUENCE + echo 升级提示句）；
- AC-05（trivial 通道 done stage 产 ≤ 200 字 `交付总结.md` 落正确路径 + 跳六层回顾）；
- AC-N4（trivial 测试降级硬规则：1 unit test + 全量 pytest 不挂 + 跳过 13 TC / 5 合规扫描 / acceptance / 六层回顾）。

## 4. Dependencies

- 前置：chg-01（TRIVIAL_SEQUENCE）+ chg-02（validate_trivial_eligibility 可被 trivial-guard 复用部分判据）+ chg-03（trivial-spec.md 模板 + chg 级 trivial flag）；
- 后续：chg-05（dogfood 活证 trivial-guard 升级路径 + reviewer 加项 trivial 边界检查）。

## 5. Risk

- **风险**：trivial-guard 全量 pytest 在大仓库可能跑 ≥ 30 秒，与"trivial = ≤ 5 分钟"目标冲突。**缓解**：trivial-guard 接受 `--fast` flag（仅跑改动文件相关 test 模块）；default-pick D-13 = A 全量保险，用户可通过 `--fast` 提速但责任自担。
- **风险**：trivial-guard 升级路径（trivial → bugfix）可能丢失已产出的 trivial-spec.md（与 bugfix.md 模板不一致）。**缓解**：升级时 trivial-spec.md 转 bugfix.md（保留 3 段内容，扩展为 bugfix 模板），不删除原数据；新增 helper `migrate_trivial_to_bugfix(req_dir)`。
- **风险**：done 跳六层回顾可能漏掉重要回顾点。**缓解**：六层回顾本就针对"≥ planning + executing + testing + acceptance"的复杂 req 设计，trivial 通道无 planning / testing / acceptance，自然无需对应层；保留 State 层校验（usage-log entries 数）作为最低兜底。
