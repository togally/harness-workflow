# Session Memory — bugfix-13（install时自动创建artifacts-project骨架与索引模板）

## 1. Current Goal

bugfix-13：`harness install` 时自动在用户仓创建 `artifacts/project/` 骨架与 README 模板，确保 dogfood 测试在 fresh repo 也能通过。

## 2. Context Chain

- Level 0: 主 agent（harness-manager）→ executing stage
- Level 1: Subagent-L1（executing / Sonnet）→ 本 session

## executing stage

### Round 1

实施 bugfix-13 主体：

- `src/harness_workflow/workflow_helpers.py`：install 流程中新增 `artifacts/project/` 骨架创建逻辑
- `src/harness_workflow/assets/templates/project-skeleton/README.md`：新建模板文件
- `artifacts/project/README.md`：自身仓同步创建
- `src/harness_workflow/assets/templates/project-skeleton/constraints/.gitkeep` 等骨架目录

### Round 2（contract-7 误伤修复）

**问题**：`tests/test_req51_project_level_dogfood.py::test_dogfood_04_validate_all` FAIL

根因：`artifacts/project/README.md` line 21 含 `req-51` 裸 id 无 title，违反 contract-7（首次引用 id 必须 `{id}（{title}）`）。同一行含 "legacy fallback" 字样与 req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-04 后语义不一致。

**修改文件**：2 个文件，各 1 行

1. `artifacts/project/README.md` line 21
2. `src/harness_workflow/assets/templates/project-skeleton/README.md` line 21

**修订内容**：

```
# before
- **legacy fallback**：`artifacts/{branch}/project/`（req-51 OQ-1 = B-modified 原路径）作为加载链 fallback 兼容存量；

# after
- **branch-path 兼容路径**：`artifacts/{branch}/project/`（req-51（项目级规则-经验-工具支持从制品引入）OQ-1 = B-modified 原路径）作为加载链兼容存量；
```

**5 判据 stdout**：

```
# 判据 1：README 裸 id 扫描（grep PCRE）
3:> 本目录由 req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-01（契约层路径迁移-无branch项目级-双轨过渡）OQ-A = D-modified 开放。
21:- **branch-path 兼容路径**：`artifacts/{branch}/project/`（req-51（项目级规则-经验-工具支持从制品引入）OQ-1 = B-modified 原路径）作为加载链兼容存量；
---check1-exit:0
（注：grep PCRE 有部分 id 匹配误报（partial match），Python check_contract_7 验证 0 violations）

# 判据 2：legacy fallback 计数
0
---check2-exit:1

# 判据 3：diff 两 README silent
---check3-exit:0

# 判据 4：test_dogfood_04_validate_all
tests/test_req51_project_level_dogfood.py::test_dogfood_04_validate_all PASSED [100%]
1 passed in 2.16s

# 判据 5：全 suite fail 数
51 failed, 755 passed, 40 skipped, 1 warning, 17 subtests passed in 139.39s (0:02:19)
```

Python 权威验证（check_contract_7）：`violations: 0`

---

## Done Stage Six-Layer Review（2026-04-30T03:37+，Subagent-L1 done / opus）

> 主 agent（done / opus）六层回顾，每层 1 行；与 acceptance verdict（PASS / 0 未达标项）并列生效，不重审。

- **Context 层**：regression（opus）/ executing（sonnet）/ acceptance（sonnet）三角色行为符合预期；executing 经验十五（同型病兜底清单方法论）已在 bugfix-12 沉淀；testing.md §R1 越界抽样未触发；本周期无新经验需补，旁支教训进 sug 池。
- **Tools 层**：`write_if_missing` + `_bootstrap_project_skeleton` + `harness validate --contract user-write-protected-zones` 工具链顺畅；CLI 部署链路提示 `pipx install --force` 同步是运维事项，非工具适配缺口。
- **Flow 层**：完整走 regression → executing（× 2，Round 2 contract-7 误伤修复）→ testing（合并 acceptance，符合 req-31 / chg-04）→ acceptance → done 五段；无跳阶段无短路；testing/acceptance 合并 entry 是设计契约，非异常。
- **State 层**：runtime.yaml `current_requirement=bugfix-13 / stage=done` ✅；`state/bugfixes/bugfix-13....yaml` `stage=done / status=done / completed_at=2026-04-30` ✅；usage-log entries 数 = 4 ≥ 派发次数 4（容差 0），State 层 grep 校验 PASS。
- **Evaluation 层**：testing 独立性=PASS（subagent 独立 paste lint stdout）但**虚报基线 52 failed=baseline**实测 +1（同型病第 6 次复发），主 agent 独立核查 `pytest --tb=no -q | tail -5` 抓出后 round-2 修 README line 21 才回到 51 failed=755 passed；acceptance 独立性=PASS（A.1~A.9 全 PASS / 0 未达标项 / verdict 不重审）；硬门禁九本周期触发 1 次（testing 虚报 → 主 agent 抓出 + 二次派发修复），与 sug-69 / sug-70 同源同型，建议合并升级。
- **Constraints 层**：契约 7 / 硬门禁六全过；mirror 白名单 "artifacts/project/" + "/project/" 双兜底未动；`_SCAFFOLD_V2_MIRROR_WHITELIST` / `_merge_project_level_files` / `_load_project_level_index` 未动；scope 枚举（6 experience-* + constraints）未动；范围红线无越界；`harness validate --contract all` exit=1 全部为预存在历史 contract-7 violations，与本 bugfix-13 改动无关。

**verdict 综合**：本 bugfix-13 done 阶段六层全过，acceptance verdict PASS / 0 未达标项不重审；同型病第 6 次复发已记入 sug 入池建议（合并到既有 sug-69/70 专项 req，不本周期新增）。**本阶段已结束。**

