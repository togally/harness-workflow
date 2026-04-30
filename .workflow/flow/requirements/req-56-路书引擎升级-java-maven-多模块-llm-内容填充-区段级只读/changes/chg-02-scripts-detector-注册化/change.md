---
id: chg-02
title: "SCRIPTS detector 注册化（Maven/Gradle/Cargo/.NET 命令支持）"
req: req-56
created_at: 2026-04-30
---

## 目标

`src/harness_workflow/tools/harness_playbook_refresh.py::_scan_scripts` 由硬编码 if-elif 链重构为按文件类型分发的 detector 注册器架构（与 chg-01（推断器多语言注册化）同源 detector 模式），新增 Maven / Gradle / Cargo / .NET 4 类命令检测器，覆盖 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） 维度 B 盲点，让 Java/Maven 项目跑 `harness playbook-refresh` 后 runbook AUTO:SCRIPTS 区段非空。

## 范围（Scope）

### Included

- **重构 `_scan_scripts(root: Path) -> str`**：
  - 定义 `ScriptDetector` 抽象基类（接口 `name -> str` / `applies(root: Path) -> bool` / `detect(root: Path) -> list[str]`，返回命令行列表）；
  - 注册器列表（按文件类型分发，每类独立判别）：
    - `PyProjectScriptsDetector`（沿用 baseline，扫 `pyproject.toml [project.scripts]` / `[tool.poetry.scripts]`）
    - `PackageJsonScriptsDetector`（沿用 baseline，扫 `package.json scripts`）
    - `MakefileTargetsDetector`（沿用 baseline，扫 `Makefile`）
    - **MavenLifecycleDetector（新增）**：扫 `root/pom.xml` 存在则输出 4 行 lifecycle 命令（`mvn clean install` / `mvn test` / `mvn package` / `mvn spring-boot:run` 当 `<plugins>` 段含 `spring-boot-maven-plugin` 时附加）
    - **GradleLifecycleDetector（新增）**：扫 `root/build.gradle` 或 `build.gradle.kts` 或 `gradlew` 存在则输出 `./gradlew build` / `./gradlew test` / `./gradlew bootRun`（条件附加）
    - **CargoBinDetector（新增）**：扫 `root/Cargo.toml` 存在则输出 `cargo build` / `cargo test` / `cargo run`（含 `[[bin]]` 段时）
    - **DotNetSlnDetector（新增）**：扫 `root/*.sln` 或 `root/*.csproj` 存在则输出 `dotnet build` / `dotnet test` / `dotnet run`
- **入口 `_scan_scripts` 改为遍历 detector 注册器**：每类 detector 独立 applies + detect，全部 detector 输出汇总；零命中时输出 `<!-- 未检测到脚本配置，请手工填写常用命令 -->`（baseline 行为保留）。
- **每类 detector 输出格式统一**：`- \`{cmd}\`: <一句话用途>` 或 `- \`{cmd}\``（无注释时）。
- **新增 pytest 用例 ≥ 4 条**（`tests/test_playbook_refresh_multi_lang.py`）：
  - `test_maven_scripts_detector`（fixture: pom.xml + spring-boot-maven-plugin）→ 断言输出含 `mvn clean install` / `mvn test` / `mvn package` / `mvn spring-boot:run` 4 行
  - `test_gradle_scripts_detector`（fixture: build.gradle + bootRun task）
  - `test_cargo_scripts_detector`（fixture: Cargo.toml）
  - `test_dotnet_scripts_detector`（fixture: *.sln）
  - `test_baseline_python_scripts_compat`（baseline pyproject + Makefile fixture，断言输出与 req-55 baseline byte-identical）
- **dogfood TC**（`tests/test_playbook_refresh_dogfood_multi_lang.py::test_maven_refresh_dogfood`）：tmp_path + Maven fixture + subprocess `python3 -m harness_workflow.cli playbook-refresh --root <tmp>` + stdout/runbook 断言。

### Excluded

- 不动 `_scan_stack`（baseline 已覆盖 Maven artifactId 抽取，本 chg 不重写）。
- 不动 `_scan_layout` / `_scan_domain_files` / `_scan_domain_list`（与本 chg 无关）。
- 不集成 LLM 调用（chg-04 负责）。
- 不引入 Maven SDK / Gradle Tooling API（保持零依赖，用简单正则 + 文件存在性判别）。

## 依赖

- 上游：req-55 chg-04（playbook-refresh `_scan_scripts` baseline 实现 + AUTO:SCRIPTS 区段替换 helper）。
- 下游：chg-04（install/refresh 集成 LLM）依赖本 chg 落地后 SCRIPTS 输出（LLM 在生成 runbook 业务描述时会引用 SCRIPTS 输出做上下文）。

## 验收（Acceptance）

- AC-14（Maven SCRIPTS detector 命中 lifecycle 命令）：fixture 含 `pom.xml` + spring-boot-maven-plugin → `_scan_scripts` 输出含 `mvn clean install` / `mvn test` / `mvn package` / `mvn spring-boot:run` ≥ 4 行。
- AC-15（Gradle / Cargo / .NET SCRIPTS detector 各命中 ≥ 1 命令）：3 fixture 各 1 TC，断言对应命令在输出中。
- AC-baseline（req-55 baseline 兼容）：原 pyproject / package.json / Makefile fixture 跑 `_scan_scripts` 输出与 req-55 baseline byte-identical。
- AC-22（现有 41 TC 不破坏）：`pytest tests/test_playbook_refresh.py -v` 全 PASS。
- AC-23（全量回归零引入 fail）。

## 风险与缓解

- **风险 R-10（Maven detector 检测 spring-boot 插件依赖正则脆弱）**：`<plugins>` 段嵌套深，正则可能漏识别。**缓解**：MavenLifecycleDetector 输出 `mvn spring-boot:run` 设为"条件附加"——只有 grep `<artifactId>spring-boot-maven-plugin</artifactId>` 命中才输出；未命中时仅输出 3 个 lifecycle 命令（不影响主体功能）。
- **风险 R-11（Gradle Kotlin DSL 与 Groovy DSL 检测兼容性）**：`build.gradle` 与 `build.gradle.kts` 语法不同。**缓解**：GradleLifecycleDetector 用文件存在性判别（`build.gradle` 或 `build.gradle.kts` 任一即触发），不解析 task 列表，只输出标准 lifecycle 命令；`bootRun` task 仅在 grep `org.springframework.boot` 字符串命中时附加。
