---
id: chg-01
title: "推断器多语言注册化（Java/Maven + Gradle + Cargo + .NET + Python 兼容）"
req: req-56
created_at: 2026-04-30
---

## 1. 执行步骤

1. **读上下文**：读 reg-01 analysis.md §2（维度 A 根因 + 候选 A1~A4 default-pick）、req-55 chg-03 落地的 `domain_inference.py`（4 级降级链 + `_read_pkg_name` helper + stdout 命中打印）、`tests/test_playbook_install.py`（TC-07~10 4 级降级 fixture，作为 baseline 兼容验证基线）。
2. **建抽象基类**：在 `domain_inference.py` 顶部定义 `DomainDetector` 抽象基类，含 `name -> str`（detector 名）、`priority -> int`（注册排序）、`detect(root: Path) -> Optional[tuple[str, list[str]]]`（返回 `(matched_mode, domains)` 或 `None`）三个接口；用 `abc.ABC` + `@abstractmethod`（沿用 Python 标准库，零依赖）。
3. **写 4 类多语言 detector**（按 priority 顺序）：
   - **MavenMultiModuleDetector（priority=10）**：扫 `root/pom.xml`，正则提取 `<modules>` 段下的 `<module>...</module>` 列表；若 `<modules>` 不存在或为空，fallback 到"扫顶层子目录中含 `pom.xml + src/main/java/` 的目录名作为领域"；matched_mode = `maven_multi_module`。
   - **GradleMultiModuleDetector（priority=20）**：扫 `root/settings.gradle` / `root/settings.gradle.kts`，正则提取 `include` 列表（如 `include 'platform-admin', 'platform-common'`），子模块名作为领域；matched_mode = `gradle_multi_module`。
   - **CargoWorkspaceDetector（priority=30）**：扫 `root/Cargo.toml`，正则提取 `[workspace] members = [...]` 列表（支持 glob 如 `crates/*` → 展开为目录列表）；matched_mode = `cargo_workspace`。
   - **DotNetSlnDetector（priority=40）**：扫 `root/*.sln`，正则提取 `Project("...") = "ProjectName", "ProjectName/ProjectName.csproj", ...` 行的 ProjectName；matched_mode = `dotnet_sln`。
4. **写 4 类 Python detector**（priority=50/60/70/80，沿用 req-55 baseline 4 级降级语义）：
   - PythonModulesDetector：扫 `src/modules/*`，matched_mode = `src/modules/*`（沿用 baseline 字面量，保持 stdout 与 41 TC 兼容）；
   - PythonDomainsDetector：扫 `src/domains/*`；
   - AppDirDetector：扫 `app/*`；
   - PythonPackageDetector：复用 req-55 `_read_pkg_name(root)` helper，扫 `src/{pkg}/*次级模块`。
5. **重写 `infer_domains(root)` 主函数**：注册器列表（按 priority 升序排列）；遍历调每个 detector.detect(root)，第一个返回非 None 的命中即返回；全部 None 则 stderr abort（与 req-55 baseline 行为一致），返回 `('unknown', [])`。
6. **stdout 命中级别打印**：抽出 `_print_matched(mode, domains, detector_name)` helper，每个 detector 命中时调用，输出 `domain inference: matched '{mode}' ({count} domains: {names})`。
7. **`cli.py` install 子命令加 `--domains <comma-separated-list>` flag**：当传入此 flag 时，跳过推断器直接用用户指定列表，stdout 打印 `domain inference: user-provided ({count} domains: ...)`。
8. **改 `init.py`**：把推断器调用改为支持 `domains_override` 参数，从 cli flag 透传。
9. **新增 pytest 用例 ≥ 5 条**（`tests/test_domain_inference_multi_lang.py`，每条独立 fixture）：
   - TC-01 PetMallPlatform-like Maven multi-module（5 顶层模块 + 父 pom `<modules>` + `app/logs` 噪声目录）→ 断言 mode=`maven_multi_module`、domains=5 模块名（不含 logs）。
   - TC-02 Gradle multi-module（settings.gradle 含 `include` 列表 + 顶层目录）。
   - TC-03 Cargo workspace（Cargo.toml `[workspace] members` glob 与显式列表两种）。
   - TC-04 .NET sln（`*.sln` 含 ≥ 2 Project 行）。
   - TC-05 baseline Python 4 级降级兼容（沿用 req-55 TC-07~10 fixture，断言 mode 字面量与 baseline 一致）。
   - TC-06 `--domains <list>` flag override（fixture 不构造任何 detector 命中结构 + 传 `--domains a,b,c`，断言 domains=[a,b,c]）。
10. **dogfood TC**（`tests/test_domain_inference_dogfood.py::test_petmall_fixture_dogfood`）：tmp_path fixture + subprocess `python3 -m harness_workflow.cli install --root <tmp> --no-llm`（chg-04 落地后 `--no-llm` 才有效；本 chg 仅落 stub flag，主体功能在 chg-04）+ stdout 断言 `matched 'maven_multi_module'` + runtime.yaml stage 字段存在 + `feedback.jsonl` 事件数 ≥ 1。
11. **跑 pytest**：`pytest tests/test_domain_inference_multi_lang.py tests/test_playbook_install.py -v` 看真实数字。
12. **harness validate**：`harness validate --contract artifact-placement && harness validate --human-docs`。
13. **session-memory 留痕**：所有数字 + exit code + grep `pom.xml\|maven\|gradle\|cargo\|csproj` 命中数。

## 2. 产物

- `src/harness_workflow/playbook/domain_inference.py`（重构：抽象基类 + 8 detector + 注册器主函数 + `_print_matched` helper）
- `src/harness_workflow/playbook/init.py`（小改：`init_playbook` 加 `domains_override` 参数透传）
- `src/harness_workflow/cli.py`（install_parser 加 `--domains <comma-separated>` flag）
- `tests/test_domain_inference_multi_lang.py`（新增，6 TC）
- `tests/test_domain_inference_dogfood.py`（新增，1 dogfood TC）

## 3. 依赖

- 上游：req-55 chg-03（init_playbook 子包 + `_read_pkg_name` helper + 4 级降级 baseline）。
- 下游：chg-04（install/refresh 集成 LLM）使用本 chg 输出的领域名作为 LLM prompt 输入；chg-02 SCRIPTS detector 注册化与本 chg 同源 detector 模式（可参考但不依赖）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单（git diff --name-only 预估）：
> - src/harness_workflow/playbook/domain_inference.py（重构为注册器，新增 8 detector）
> - src/harness_workflow/playbook/init.py（加 domains_override 参数）
> - src/harness_workflow/cli.py（install_parser 加 --domains flag）
> - 调用链：harness install 入口 → init_playbook → infer_domains → 8 detector 注册器 → 命中即停

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 PetMallPlatform-like Maven multi-module | tmpdir + 5 顶层模块（platform-admin/common/modules/extend/demo-ui）+ 父 pom.xml `<modules>` 含 5 模块 + `app/logs` 噪声 | infer_domains 返回 `mode='maven_multi_module'` + domains=5 模块名（不含 logs）；stdout 含 `matched 'maven_multi_module'` | AC-13 | P0 |
| TC-02 Gradle multi-module | tmpdir + settings.gradle 含 `include 'mod-a', 'mod-b'` + 顶层 mod-a/mod-b 目录 | infer_domains 返回 `mode='gradle_multi_module'` + domains=['mod-a', 'mod-b'] | AC-13（同源） | P0 |
| TC-03 Cargo workspace | tmpdir + Cargo.toml `[workspace] members = ["crates/*"]` + crates/{a,b,c} 目录 | infer_domains 返回 `mode='cargo_workspace'` + domains=['a', 'b', 'c'] | AC-13（同源） | P0 |
| TC-04 .NET sln | tmpdir + Solution.sln 含 2 Project 行 + 对应顶层目录 | infer_domains 返回 `mode='dotnet_sln'` + domains=2 ProjectName | AC-13（同源） | P0 |
| TC-05 baseline Python 4 级降级兼容 | tmpdir + req-55 TC-07~10 fixture（4 套） | infer_domains 输出 mode 与 baseline byte-identical（'src/modules/*' / 'src/domains/*' / 'app/*' / 'src/{pkg}/*次级模块'） | AC-22（41 TC 不破坏） | P0 |
| TC-06 `--domains` flag override | tmpdir 无任何 detector 命中结构 + cli flag `--domains a,b,c` | init_playbook 的 domains_override 参数传入 ['a','b','c']，跳过 infer_domains | AC-13（escape hatch） | P1 |
| TC-Dogfood-01 PetMallPlatform fixture install dogfood | tmp_path + subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'install', '--root', tmpdir, '--no-llm']) | exit 0 + stdout 含 `matched 'maven_multi_module'` + runtime.yaml stage 字段存在 + feedback.jsonl 事件数 ≥ 1 + `artifacts/project/playbooks/domains/platform-admin/` 目录存在 | AC-13 / AC-21 | P0 |
