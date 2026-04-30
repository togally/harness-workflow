---
id: chg-01
title: "推断器多语言注册化（Java/Maven + Gradle + Cargo + .NET + Python 兼容）"
req: req-56
created_at: 2026-04-30
---

## 目标

`src/harness_workflow/playbook/domain_inference.py` 由硬编码 4 级降级链重构为 detector 注册器架构（OQ-1 = B1 决策），覆盖 PetMallPlatform 类 Java/Maven 多模块项目（reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） 维度 A 修复），同源覆盖 Gradle / Cargo workspace / .NET sln，保留 req-55 baseline 4 级 Python detector 优先级行为一致。

## 范围（Scope）

### Included

- **重构 `domain_inference.py` 为注册器模式**：
  - 定义 `DomainDetector` 抽象基类（接口 `name -> str` / `priority -> int` / `detect(root: Path) -> Optional[tuple[str, list[str]]]`）；
  - 注册顺序按 priority 升序，命中即停（与 req-55 4 级降级语义一致）：
    - priority=10：`MavenMultiModuleDetector`（扫顶层 `pom.xml <modules>` 字段，提取子模块名为领域，fallback：扫顶层目录下含 `pom.xml + src/main/java/` 的子目录）
    - priority=20：`GradleMultiModuleDetector`（扫顶层 `settings.gradle` / `settings.gradle.kts` 含 `include` 列表 + 顶层平级模块根目录）
    - priority=30：`CargoWorkspaceDetector`（扫顶层 `Cargo.toml [workspace] members` 字段）
    - priority=40：`DotNetSlnDetector`（扫顶层 `*.sln` Project 行 + 顶层 `<ProjectName>/` 平级目录）
    - priority=50：`PythonModulesDetector`（沿用 req-55 baseline `src/modules/*`）
    - priority=60：`PythonDomainsDetector`（沿用 `src/domains/*`）
    - priority=70：`AppDirDetector`（沿用 `app/*`）
    - priority=80：`PythonPackageDetector`（沿用 `src/{pkg}/*次级模块`，单包兜底）
- **`infer_domains(root)` 主函数**：遍历注册器，调每个 detector，命中即返回 `(matched_mode, domains)`；零命中时 stderr abort（与 req-55 baseline 一致）。
- **stdout 命中级别打印**：每个 detector 命中时打印形如 `domain inference: matched 'maven_multi_module' (5 domains: platform-admin, platform-common, platform-modules, platform-extend, platform-demo-ui)`，让用户感知命中哪类 detector。
- **last-resort `--domains <list>` flag**：在 `cli.py` install 子命令加 `--domains <comma-separated-list>`，命中时跳过推断器直接用用户指定列表。
- **新增 pytest 用例 ≥ 5 条**（`tests/test_domain_inference_multi_lang.py`）：
  - `test_petmall_like_maven_modules`（PetMallPlatform 类 fixture）
  - `test_gradle_multi_module_settings_include`（Gradle 多模块）
  - `test_cargo_workspace_members`（Cargo workspace）
  - `test_dotnet_sln_projects`（.NET 多项目）
  - `test_baseline_python_4level_compat`（req-55 baseline Python 4 级降级兼容，沿用 TC-07~10 fixture）
  - `test_domains_flag_overrides_inference`（`--domains` flag 跳过推断）
- **dogfood TC**（`tests/test_domain_inference_dogfood.py::test_petmall_fixture_dogfood`）：tmp_path fixture + subprocess `python3 -m harness_workflow.cli install --root <tmp> --no-llm` + stdout 断言 + runtime / feedback 断言。

### Excluded

- 不实现 SCRIPTS detector 重构（chg-02 负责）。
- 不集成 LLM 调用（chg-03 / chg-04 负责）。
- 不动 `skeleton.py` 模板（领域命名传递沿用 req-55 实现）。
- 不引入 lxml / 第三方 XML 解析库（保持 req-55 "零新依赖"承诺，用简单正则解析 pom.xml `<modules>`）。

## 依赖

- 上游：req-55 chg-03（init_playbook 子包基础设施 + 4 级降级 baseline 行为）作为兼容性基线。
- 下游：chg-04（install/refresh 集成 LLM）依赖本 chg 落地的 6 类 detector 命中输出（领域名将作为 LLM prompt 输入）。

## 验收（Acceptance）

- AC-13（PetMallPlatform-like fixture 推断器命中正确）：fixture 跑 `infer_domains(root)` 返回 `mode='maven_multi_module'` + 5 模块；stdout 含 `matched 'maven_multi_module'`。
- AC-baseline（req-55 4 级降级兼容）：原 4 级降级 fixture（TC-07~10）跑新 `infer_domains` 输出与 baseline byte-identical（modes 名沿用 `src/modules/*` / `src/domains/*` / `app/*` / `src/{pkg}/*次级模块`）。
- AC-23（全量回归零引入 fail）：`pytest tests/test_playbook_install.py -v` 全 PASS（含 baseline TC-07~10）。

## 风险与缓解

- **风险 R-5（推断器重构破坏 req-55 4 级降级语义）**：注册器排序错可能让新 detector 抢先命中 Python 项目，破坏 baseline。**缓解**：4 类 Python detector priority 50/60/70/80（最低优先级），优先级排序后于 Java/Maven 等多模块 detector；新增专门的"baseline 兼容 TC"沿用 req-55 TC-07~10 fixture 验证。
- **风险 R-9（pom.xml 简单正则解析 robustness）**：复杂 BOM / 父 pom 嵌套结构正则可能漏。**缓解**：MavenMultiModuleDetector 设 fallback 路径——若正则未匹配 `<modules>`，则扫顶层目录下含 `pom.xml + src/main/java/` 的子目录作为领域；双路径覆盖 Aggregator pom 与单纯多模块两种场景。
