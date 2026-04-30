# Session Memory — chg-02（SCRIPTS detector 注册化）

## 1. Current Goal

`harness_playbook_refresh.py::_scan_scripts` 由 if-elif 链重构为按文件类型分发的 detector 注册器（与 chg-01（推断器多语言注册化）同源 detector 模式），新增 Maven / Gradle / Cargo / .NET 4 类命令检测器，覆盖 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） 维度 B 盲点，让 Java/Maven 项目跑 `playbook-refresh` 后 runbook AUTO:SCRIPTS 区段非空。保证 req-55（项目路书Playbook体系-项目地图+代码导航）已落地 baseline TC 不被破坏。

## 2. Context Chain

- Level 0: 主 agent（harness-manager）→ analysis stage 编排
- Level 1: Subagent-L1（analyst / opus）→ req-56（路书引擎升级——Java/Maven + LLM + 区段级只读）analysis stage
- Level 2（计划中 executing / sonnet）：执行本 chg-02

## 3. Completed Tasks（analysis stage 拆分阶段）

- [x] 读 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） analysis.md §3 维度 B 根因 + 候选 B1（detector 注册化）+ B3（LLM 兜底，本 chg 不做，留 chg-04）
- [x] 读 req-55（项目路书Playbook体系-项目地图+代码导航） chg-04 落地的 `_scan_scripts`（baseline 第 153-192 行 + AUTO:SCRIPTS 区段替换语义）
- [x] 拆分本 chg：detector 注册器（与 chg-01 同源模式）+ 7 类 detector（3 baseline + 4 多语言）+ 5 + 1 TC
- [x] 与 chg-01 / chg-03 / chg-04 / chg-05 边界划清：本 chg 只动 `harness_playbook_refresh.py::_scan_scripts` + 新增 2 测试文件，不动推断器 / LLM provider / base-role

## 4. Results（analysis stage 产物）

| 产物路径 | 说明 |
|---------|------|
| `change.md` | 本 chg 范围 / 依赖 / AC / 风险 |
| `plan.md` | 10 步执行 + §4 测试用例设计（5 + 1 TC + 1 共存 TC）|
| `session-memory.md` | 本文件 |

## 5. Issues / Bugs

无。

## 6. default-pick 决策清单（本 chg 范围内）

无（reg-01 decision.md §5 已 default-pick = B1，本 chg 直接继承）。

## 7. 下一步

- analysis stage 退出 → 等用户拍板 → executing 实施
- chg-01 / chg-02 / chg-03 可并行 executing

## 8. Executing Stage 产物（chg-02 实施，2026-04-30）

### 改动文件
- `src/harness_workflow/tools/harness_playbook_refresh.py`（重构 `_scan_scripts`，新增 ScriptDetector ABC + 7 类 detector）
- `tests/test_playbook_refresh_multi_lang.py`（新增，17 TC）
- `tests/test_playbook_refresh_dogfood_multi_lang.py`（新增，1 dogfood TC）

### 自检结果
1. `grep -cE '^class .+\(ScriptDetector\)'` = 7 ✅（≥7）
2. Maven/spring-boot 引用行数 = 7 ✅（≥3）
3. Gradle 引用行数 = 15 ✅（≥2）
4. `grep -c '^def test_'` test_playbook_refresh.py=10, multi_lang=17, dogfood=1；总计 28 ✅（≥16）
5. `pytest tests/test_playbook_refresh*.py -v` = 28 passed ✅
6. `pytest tests/ -q` = 852 passed / 59 failed（基线 847 passed / 64 failed，引入 +0 fail）✅
7. `harness validate --contract artifact-placement` = exit 0 / PASS ✅

### grep 命中统计
- `mvn | maven` = 7 行
- `gradle | gradlew` = 15 行
- `cargo` = 5 行
- `dotnet | csproj` = 5 行

## 完成态

本 chg executing stage 完成 ✅
