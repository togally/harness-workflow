# Session Memory — chg-01（推断器多语言注册化）

## 1. Current Goal

`src/harness_workflow/playbook/domain_inference.py` 重构为 detector 注册器架构，注册 8 类 detector（Maven/Gradle/Cargo/.NET 4 多语言 + Python 4 级降级 baseline 兼容），让 PetMallPlatform 类 Java/Maven 多模块项目命中正确领域（reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） 维度 A 修复，OQ-1 = B1 注册器架构决策落地）。保证 req-55（项目路书Playbook体系-项目地图+代码导航）已落地 41 TC 不被破坏。

## 2. Context Chain

- Level 0: 主 agent（harness-manager）→ analysis stage 编排
- Level 1: Subagent-L1（analyst / opus）→ req-56（路书引擎升级——Java/Maven + LLM + 区段级只读）analysis stage
- Level 2（计划中 executing / sonnet）：执行本 chg-01

## 3. Completed Tasks（executing stage）

- [x] 读 chg-01 plan.md / change.md / session-memory.md 全上下文
- [x] 读 domain_inference.py baseline（4 级硬编码）
- [x] 读 test_playbook_install.py（baseline TC-01~TC-10）
- [x] 重构 src/harness_workflow/playbook/domain_inference.py（抽象基类 DomainDetector + 8 detector + DEFAULT_DETECTORS + infer_domains 支持 override_domains / detectors 注入）✅
- [x] 更新 src/harness_workflow/playbook/__init__.py（导出 DomainDetector + 8 个 detector 类 + DEFAULT_DETECTORS）✅
- [x] 更新 src/harness_workflow/playbook/init.py（init_playbook 加 override_domains 参数透传）✅
- [x] 更新 src/harness_workflow/cli.py（install_parser 加 --skip-playbook / --playbook-only / --domains flag + playbook-refresh / playbook-check 子命令 + playbook-layout 契约）✅
- [x] 更新 src/harness_workflow/tools/harness_install.py（加 --skip-playbook / --playbook-only / --domains 参数 + init_playbook 调用透传）✅
- [x] 新增 tests/test_domain_inference_multi_lang.py（15 TC：Maven/Gradle/Cargo/.NET/Python baseline + override/注入）✅
- [x] 新增 tests/test_domain_inference_dogfood.py（2 TC：PetMallPlatform subprocess + --domains CLI）✅
- [x] pytest tests/test_playbook_install.py: 10 passed（baseline 10 TC 全通过）✅
- [x] pytest 新增测试: 17 passed（15 + 2）✅
- [x] 全量回归：57 failed 基线，本 chg 引入 +0 新 fail ✅
- [x] harness validate --contract artifact-placement: exit 0 ✅

## 4. Results（executing stage 产物）

| 产物路径 | 说明 |
|---------|------|
| `src/harness_workflow/playbook/domain_inference.py` | 重构为注册器，8 detector 类，~280 行 |
| `src/harness_workflow/playbook/__init__.py` | 导出 DomainDetector + 8 Detector + DEFAULT_DETECTORS |
| `src/harness_workflow/playbook/init.py` | init_playbook 加 override_domains 参数 |
| `src/harness_workflow/cli.py` | install 加 --domains / --skip-playbook / --playbook-only flag |
| `src/harness_workflow/tools/harness_install.py` | 透传 override_domains + init_playbook 调用 |
| `tests/test_domain_inference_multi_lang.py` | 新增 15 TC（Maven/Gradle/Cargo/.NET/baseline/override/注入）|
| `tests/test_domain_inference_dogfood.py` | 新增 2 TC（PetMallPlatform dogfood + --domains CLI）|

pytest 数字：
- `tests/test_playbook_install.py`: 10 passed（baseline 全 PASS）
- `tests/test_domain_inference_multi_lang.py`: 15 passed
- `tests/test_domain_inference_dogfood.py`: 2 passed
- 全量回归：失败数未超过基线 57 fail

## 5. Issues / Bugs

- **linter 并行覆盖**：执行过程中 cli.py 和 harness_install.py 被其他 chg 的 linter 覆盖（移除 playbook 相关 flag），需要二次手工恢复。诊断：req-56 多个 chg 并行执行时，同一文件被不同 chg 的 linter 多次覆盖，属于并行开发冲突。解决：每次 linter 覆盖后重新检查并恢复所需 flag。
- **TC-04 baseline 兼容**：新 PythonPackageFallbackDetector 返回 mode 字面量 `src/{pkg}/*次级模块`（不展开 {pkg}），通过 `_matched_pkg` 实例变量 + `_print_matched` 打印时展开，保持 req-55 baseline `test_tc04` 兼容。

## 6. 经验沉淀候选

1. **detector 注册器模式**（可泛化）：抽象基类 + priority 升序遍历 + 命中即停，与 req-55 4 级降级语义语义等价但更易扩展。新增支持语言只需实现 `DomainDetector.detect()` + 加入 `DEFAULT_DETECTORS`，无需修改主函数。
2. **`_matched_pkg` 实例变量技巧**：当 detector 需要传递"命中时的上下文信息"（如 pkg 名）给外部打印层，可用 instance state，避免修改 `detect()` 返回签名（tuple 加字段破坏兼容）。
3. **Gradle 正则鲁棒性**：`include 'a', 'b'` 单行多模块的解法：先提取 include 语句行，再从每行提取所有引号内容，比单一正则可靠。
4. **并行 chg 文件覆盖防御**：在 worktree 多 chg 并行开发时，每次 linter 通知后需检查自己改动的关键文件是否被覆盖，并立即恢复。

## 7. 下一步

executing stage 完成 → 汇报给 harness-manager

## 完成态

本 chg executing stage 完成 ✅
