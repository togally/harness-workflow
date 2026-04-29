---
# reg-05 路由：诊断师按 base-role 硬门禁四 default-pick 推荐路径，
# 由主 agent 在 batched-report 后落地（参考 stage-role.md 字段 3）。
route_to: "requirement"
---

# Regression Decision — reg-05（archive 行为重定义：对人文档保留原位 + 不再生成摘要 md）

## 1. Decision Status

`confirmed`（真实问题；判决见 `analysis.md` §1）

## 2. Final Notes

诉求 A（对人 folder 不挪）+ 诉求 B（不生成摘要 .md）确认为 over-engineering + 错位修复机会，由 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））推动暴露。机器型归档去向（E-3）按方向 C 精神推断默认 `.workflow/flow/archive/`，由后续执行阶段在 chg 计划中落位即可，不阻塞本回归路由。

## 3. Follow-Up

### 3.1 三条候选方向

#### 方向 A — 对人不挪 + 摘要废止 + 机器型迁 .workflow/flow/archive/（**推荐**）

**改动量**：

- `archive_requirement` helper 改写：仅迁机器型工件（`.workflow/flow/requirements/{slug}/` → `.workflow/flow/archive/{branch}/{slug}/`，已部分实现，确认收口）；`.workflow/state/sessions/{req-id}/` + `.workflow/state/requirements/{req-id}/` legacy fallback 同样仅迁机器型（不再混入 artifacts）。
- 对人 folder（`artifacts/main/requirements/{slug}/`）**不动**——done 完成即归档态。
- `generate_requirement_artifact` 调用废止；`{req-id}-{slug}.md` 摘要文件不再生成。
- `repository-layout.md` §3 / §4 微扩"archive 时机器型 / 对人路径表"。
- pytest：archive_requirement 相关用例补对人 folder 不动 + 无摘要 .md 断言。
- 历史存量：`artifacts/main/archive/requirements/req-XX/` 树（req-02 ~ req-40）按 §4 historical 豁免**不动**；残留摘要 + req-29 孤儿 folder 由清理动作单独处理（见 §3.4）。

**可逆性**：高（helper 改写 + 文档微扩，回滚一次 git revert 即可）。

**推荐度**：★★★★★ —— 最贴用户原话（"不用归档了"）+ 完美契合方向 C 精神（关注点分离）+ 改动面最小（仅 helper + layout §3/§4）+ 不挑战已有"archive 命令"语义骨架。

#### 方向 B — 保留摘要但合并到 folder 内（次推荐）

**改动量**：

- `archive_requirement` 把摘要 .md 写进对人 folder 内（路径形如 `artifacts/main/requirements/{slug}/归档摘要.md`），不在 folder 外另起。
- 对人 folder 不挪（同方向 A）。
- 机器型迁 `.workflow/flow/archive/`（同方向 A）。
- repository-layout §2 白名单加 `归档摘要.md`。

**可逆性**：中（白名单扩 + 摘要生成路径调整）。

**推荐度**：★★ —— 摘要语义与 `交付总结.md` 重叠（done 阶段已产出，含 §效率与成本段），再加 `归档摘要.md` 是把同义信息复刻一份，违反"对人文档 ≤ 1 屏可读"契约（契约 4）；用户原话也是"不用归档了"，没说"换地方放摘要"。

#### 方向 C — archive 命令彻底废止，让 done 即归档（激进）

**改动量**：

- done 阶段完成后视为"归档态"——不再有 archive 命令；`harness archive` 子命令从 CLI 移除。
- 机器型工件不迁，留在 `.workflow/flow/requirements/`（done 状态由 yaml 标记）。
- 对人 folder 不挪（同方向 A/B）。
- 大量代码 / 文档 / 角色规约重构：`harness archive` 触发的 git commit 流程（archive: req-XX-XX commit message）/ DAG 完成度判定 / `_meta.yaml` 写入路径 / done 阶段六层回顾 / `done.md` SOP 全部要改。
- repository-layout §1 / §3 / §4 三段式分水岭重写（"archive 子树"概念会消失或重定义）。

**可逆性**：低（DAG 大改 + commit 协议改 + 角色规约改）。

**推荐度**：★ —— 改动面 5x 于方向 A，且引入"archive 命令是否还存在"二阶辩论，超出本次反馈范围（用户只说"对人文档不用归档"，没说"archive 命令废止"）。可作为长期演进备选项，但本次不取。

### 3.2 路由建议（route_to）

**推荐 `--requirement`，候选标题（≤ 30 字）**：

> `archive 重定义：对人不挪 + 摘要废止`（**推荐**，22 字，覆盖诉求 A + B 主干）

备选：

> `archive 行为方向 C 化：对人就地 + 摘要废止`（28 字）
> `archive 收敛：对人不挪机器型迁 flow archive`（25 字）

**`--bugfix` vs `--requirement` 取舍**：

| 维度 | `--bugfix` | `--requirement`（**推荐**） |
|------|-----------|---------------------------|
| 规模 | 改动面 = 1 helper + 1 layout 文档微扩 + pytest，单跑可承载 | 改动面同 bugfix，但跨"contract（layout）+ behavior（helper）+ tests + cleanup"四面 |
| DAG | 单 chg 即可（archive_requirement 改写 + layout §3 微扩 + pytest）— 但需含 cleanup chg | 推荐拆 ≥ 3 chg（chg-01 layout 契约扩 + chg-02 helper 改写 + chg-03 cleanup + pytest），方向 C 风格 |
| 上下文 | runtime.yaml 当前 current_requirement 空，可挂 bugfix 池独立运行 | 同样可独立运行（new req-42） |
| 可追溯 | bugfix 池 ID 单跑，简洁 | req 级承载更完整（含 §效率与成本，便于复盘 archive 演进史） |
| **推荐** | 次选（仅当用户偏好快闪修复） | **首选**——本回归本质是"req-41 方向 C 收尾的延伸"，开 req 显得有逻辑承接，且能容纳 layout 契约扩展 chg + cleanup chg 独立交付 |

**理由（一句话）**：本次涉及 `repository-layout.md` 契约扩展（§3 / §4 加 archive 时落位表）+ `archive_requirement` 行为重定义 + 历史冗余清理 + pytest，单一 bugfix 容纳不下"契约 + 行为 + 清理"三面正交，开 req-42 拆 ≥ 3 chg 更稳。

### 3.3 `--change` 不可路由说明

`--change` 需要 active req 挂载，但 runtime.yaml 当前 `current_requirement: ""`（已 done req-38），故不可走 `--change`，硬性排除。

### 3.4 残留冗余清理建议（路由后由执行阶段处理）

`artifacts/main/requirements/` 顶层 17 件冗余：

- 16 份 `req-XX-{slug}.md` 摘要文件（req-28 ~ req-41，全部有同名 archive 副本，确认冗余可 `git rm`）
- 1 个 `req-29-...{slug}/` 孤儿 folder（含 `交付总结.md` + `done-report.md`）：req-29 archive 副本已存在 `artifacts/main/archive/requirements/req-29-...{slug}/`，与孤儿 folder 内容做 diff 后保留任意一份；建议保留 archive 副本（与同期 req 一致），孤儿 folder `git rm -r`。

**清理时机**：作为 req-42（archive 重定义：对人不挪 + 摘要废止）的回归动作之一（独立 chg 或并入 helper 改写 chg），不在本 reg-05 阶段执行；本 reg-05 仅诊断，由后续阶段 commit。

**用户确认门**：清理 = 数据销毁动作（删 17 件文件），属硬门禁四例外条款 (i) "数据丢失风险"——执行阶段触发 `git rm` 前需用户拍板确认（与 base-role 硬门禁七豁免清单一致）；本回归阶段不触发，预留给执行 stage。

### 3.5 不修代码声明（合规边界）

本 regression 阶段**不**修改 `archive_requirement` / `repository-layout.md` / 任何代码或契约文件，仅产出诊断 + 路由建议 + 候选标题 + 清理建议；交后续 `harness regression --requirement` 路径下的 req-42 + 各 chg 执行阶段落地。
