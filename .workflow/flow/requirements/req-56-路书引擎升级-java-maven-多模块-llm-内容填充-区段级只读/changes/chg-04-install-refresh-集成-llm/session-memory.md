# Session Memory — chg-04（install / refresh 集成 LLM）

## 1. Current Goal

把 chg-03（LLM provider 抽象层）落地的 `auto_detect_provider()` 集成到 `init_playbook`（install 路径）与 `playbook_refresh`（refresh 路径），调 LLM 填充骨架业务内容（5 类 LLM 区段：OVERVIEW_DESC / TECH_DECISIONS / DOMAIN_DESC / KEYWORDS / CODE_MAP_KEYWORDS）。让 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） 维度 C "首装看到有意义初稿"诉求落地（OQ-2 = C2 全程可选 + 默认开启 local / `--no-llm` 关闭 CI / env CI=true 自动 off）。LLM 调用失败时静默 fallback Noop（不阻塞主流程）。

## 2. Context Chain

- Level 0: 主 agent（harness-manager）→ analysis stage 编排
- Level 1: Subagent-L1（analyst / opus）→ req-56（路书引擎升级——Java/Maven + LLM + 区段级只读）analysis stage
- Level 2（计划中 executing / sonnet）：执行本 chg-04

## 3. Completed Tasks（analysis stage 拆分阶段）

- [x] 读 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） analysis.md §4.3 候选 C2 全程可选 + reg-01 decision.md §5 OQ-2 default-pick = C2
- [x] 读 chg-03 落地的 `LLMProvider` API 设计（4 method + auto_detect_provider 工厂）
- [x] 读 req-55（项目路书Playbook体系-项目地图+代码导航） chg-03 `init.py::init_playbook` 与 chg-04 `playbook_refresh` 主入口
- [x] 拆分本 chg：5 类 LLM 区段 + init/refresh 集成 + cli `--no-llm` flag + ensure_no_real_llm autouse fixture + 5 + 1 + 1 dogfood TC
- [x] 双 marker 系统设计（AUTO + LLM 命名空间分离）写入 change.md 风险 R-17 缓解
- [x] PetMallPlatform-like fixture 严格按 reg-01 regression.md §3 维度 A 原始证据 A-3 描述构造（5 顶层模块 + 父 pom.xml `<modules>` + spring-boot-maven-plugin + app/logs 噪声目录）

## 4. Results（analysis stage 产物）

| 产物路径 | 说明 |
|---------|------|
| `change.md` | 本 chg 范围 / 依赖 / AC / 风险 |
| `plan.md` | 11 步执行 + §4 测试用例设计（5 + 1 集成 + 1 dogfood TC，含 PetMallPlatform 完整 pipeline）|
| `session-memory.md` | 本文件 |

## 5. Issues / Bugs

无。

## 6. default-pick 决策清单（本 chg 范围内）

无（reg-01 decision.md §5 OQ-2 已 default-pick = C2 全程可选；OQ-3 已 default-pick = 自动检测；OQ-5 已 default-pick = A worktree fixture——本 chg 直接继承）。

## 7. 下一步

- analysis stage 退出 → 等用户拍板 → executing 实施
- 等 chg-03（LLM provider 抽象层）落地后 executing；可能与 chg-05（区段级只读语义 + check 兼容）紧接
