---
id: chg-02
title: "SCRIPTS detector 注册化（Maven/Gradle/Cargo/.NET 命令支持）"
req: req-56
created_at: 2026-04-30
---

## 1. 执行步骤

1. **读上下文**：读 reg-01 analysis.md §3（维度 B 根因 + 候选 B1+B3，default-pick = B1 detector 注册化）、req-55 chg-04 落地的 `harness_playbook_refresh.py::_scan_scripts`（第 153-192 行 baseline 实现）、`tests/test_playbook_refresh.py`（baseline TC 作为兼容验证基线）。
2. **抽出 ScriptDetector 抽象基类**：在 `harness_playbook_refresh.py` 顶部 `_scan_scripts` 之前定义 `ScriptDetector` 抽象基类，含 `name -> str` / `applies(root: Path) -> bool` / `detect(root: Path) -> list[str]` 三接口；用 `abc.ABC` + `@abstractmethod`（沿用 chg-01 同源模式）。
3. **写 3 类 baseline detector**（沿用 req-55 行为）：
   - `PyProjectScriptsDetector`：从 `pyproject.toml [project.scripts]` / `[tool.poetry.scripts]` 抽 entrypoint，输出 `- \`{name}\`: {target}`。
   - `PackageJsonScriptsDetector`：从 `package.json scripts` 字段抽 npm script，输出 `- \`npm run {name}\`: {cmd}`。
   - `MakefileTargetsDetector`：从 `Makefile` 抽 target，输出 `- \`make {target}\``。
4. **写 4 类多语言 detector**（reg-01 维度 B 修复）：
   - `MavenLifecycleDetector`：applies = `(root / 'pom.xml').exists()`；detect 返回固定 3 行（`mvn clean install` / `mvn test` / `mvn package`） + 条件附加 `mvn spring-boot:run`（仅当 grep `<artifactId>spring-boot-maven-plugin</artifactId>` 命中时）。
   - `GradleLifecycleDetector`：applies = `(root / 'build.gradle').exists() or (root / 'build.gradle.kts').exists() or (root / 'gradlew').exists()`；detect 返回 `./gradlew build` / `./gradlew test` + 条件附加 `./gradlew bootRun`（grep `org.springframework.boot` 命中时）。
   - `CargoBinDetector`：applies = `(root / 'Cargo.toml').exists()`；detect 返回 `cargo build` / `cargo test` + 条件附加 `cargo run`（含 `[[bin]]` 段时）。
   - `DotNetSlnDetector`：applies = 任一 `*.sln` 或 `*.csproj` 文件存在；detect 返回 `dotnet build` / `dotnet test` / `dotnet run`。
5. **重写 `_scan_scripts(root)` 主函数**：注册器列表（7 detector）；遍历调每个 `detector.applies(root)` 命中则调 `detect(root)` 收集所有行；汇总输出；零命中时输出 baseline 字面量 `<!-- 未检测到脚本配置，请手工填写常用命令 -->`（与 req-55 baseline 兼容）。
6. **新增 pytest 用例 ≥ 4 条**（`tests/test_playbook_refresh_multi_lang.py`，每条独立 fixture）：
   - TC-01 Maven lifecycle（fixture: pom.xml 含 spring-boot-maven-plugin）→ 4 行 mvn 命令。
   - TC-02 Gradle lifecycle（fixture: build.gradle + spring-boot 字符串）→ 3 行 gradlew 命令（含 bootRun）。
   - TC-03 Cargo bin（fixture: Cargo.toml + `[[bin]]`）→ 3 行 cargo 命令。
   - TC-04 .NET sln（fixture: Solution.sln）→ 3 行 dotnet 命令。
   - TC-05 baseline Python compat（fixture: pyproject.toml [project.scripts] + Makefile）→ 输出与 baseline byte-identical（用 req-55 baseline 输出做断言对照）。
7. **dogfood TC**（`tests/test_playbook_refresh_dogfood_multi_lang.py::test_maven_refresh_dogfood`）：tmp_path + 完整路书骨架（runbook.md 含 AUTO:SCRIPTS 区段） + pom.xml fixture + subprocess `python3 -m harness_workflow.cli playbook-refresh --root <tmp>` + 断言：(a) exit 0；(b) runbook AUTO:SCRIPTS 区段含 ≥ 4 行 mvn 命令；(c) runtime.yaml stage 字段存在；(d) feedback.jsonl 事件数 ≥ 1。
8. **跑 pytest**：`pytest tests/test_playbook_refresh*.py -v` 看真实数字（含 baseline TC 与新 TC）。
9. **harness validate**：`harness validate --contract artifact-placement && harness validate --human-docs`。
10. **session-memory 留痕**：所有数字 + exit code + grep `mvn\|gradle\|cargo\|dotnet` 命中数。

## 2. 产物

- `src/harness_workflow/tools/harness_playbook_refresh.py`（重构 `_scan_scripts` 为注册器 + 7 detector + ScriptDetector 抽象基类）
- `tests/test_playbook_refresh_multi_lang.py`（新增，5 TC）
- `tests/test_playbook_refresh_dogfood_multi_lang.py`（新增，1 dogfood TC）

## 3. 依赖

- 上游：req-55 chg-04（playbook-refresh baseline + AUTO:SCRIPTS 区段替换 helper）。
- 下游：chg-04（install/refresh 集成 LLM）使用本 chg 落地后的 SCRIPTS 输出作为 LLM prompt 上下文（让 LLM 描述 runbook 时引用真实命令而非泛化）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - src/harness_workflow/tools/harness_playbook_refresh.py（重构 _scan_scripts，新增 7 detector）
> - 调用链：harness playbook-refresh → playbook_refresh → _scan_scripts → 7 detector 注册器 → 输出汇总 → AUTO:SCRIPTS 区段替换

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 Maven lifecycle detector | tmpdir + pom.xml 含 spring-boot-maven-plugin | _scan_scripts 输出含 mvn clean install / mvn test / mvn package / mvn spring-boot:run 4 行 | AC-14 | P0 |
| TC-02 Gradle lifecycle detector | tmpdir + build.gradle 含 org.springframework.boot 字符串 | _scan_scripts 输出含 ./gradlew build / ./gradlew test / ./gradlew bootRun 3 行 | AC-15 | P0 |
| TC-03 Cargo bin detector | tmpdir + Cargo.toml 含 `[[bin]]` 段 | _scan_scripts 输出含 cargo build / cargo test / cargo run 3 行 | AC-15 | P0 |
| TC-04 .NET sln detector | tmpdir + Solution.sln + Project.csproj | _scan_scripts 输出含 dotnet build / dotnet test / dotnet run 3 行 | AC-15 | P0 |
| TC-05 baseline Python scripts compat | tmpdir + pyproject [project.scripts] + Makefile | _scan_scripts 输出与 req-55 baseline byte-identical（含 entrypoint + make targets） | AC-22 | P0 |
| TC-06 多语言 detector 共存 | tmpdir + pom.xml + package.json + Makefile（混合项目） | _scan_scripts 输出含 Maven lifecycle + npm scripts + make targets 全部行（无相互排斥） | AC-14/15 | P1 |
| TC-Dogfood-01 Maven refresh dogfood | tmp_path + 完整路书骨架（runbook.md 含 AUTO:SCRIPTS） + pom.xml + subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'playbook-refresh', '--root', tmpdir]) | exit 0 + runbook.md AUTO:SCRIPTS 区段含 ≥ 4 行 mvn 命令 + runtime.yaml stage 字段存在 + feedback.jsonl 事件数 ≥ 1 | AC-14 / AC-21 | P0 |
