# Regression Intake — reg-01（chg-03/04 Java/Maven项目盲点 + LLM填骨架决策反转）

> 关联：req-55（项目路书Playbook体系——项目地图+代码导航）/ chg-03（harness install 追加路书初始化）/ chg-04（harness playbook-refresh 子命令）。
> 触发场景：req-55 已 done verdict=PASS，但 dogfood 真实在用户 Java/Maven 项目 PetMallPlatform 上跑 `harness install --playbook-only` 暴露 4 维度叠加产品问题。

## 1. Issue Title

chg-03 推断器 Java/Maven 项目盲点 + chg-04 SCRIPTS 检测器 Maven 命令盲点 + spec "不调 LLM" 决策反转 + OQ-5 路书"只读"约束语义松动（4 维度叠加产品问题）。

## 2. Reported Concern（症状一句话）

req-55 落地的路书引擎（chg-03 init_playbook + chg-04 playbook-refresh）默认按 Python/JS 项目结构建模，**不识别** Java/Maven 多模块项目的"顶层平级 platform-* 模块根 + pom.xml `<modules>`"惯例，导致：(a) 领域推断错把 `app/logs` 这种日志目录当成业务领域；(b) `runbook.md` AUTO:SCRIPTS 区段空（不知 Maven 命令）；用户基于此 dogfood 反馈进一步反转 spec §四"不调 LLM"决策为"chg-03/04 调 LLM 填骨架内容"，连带使 OQ-5"路书只读"硬约束的边界需要重新界定。

## 3. Current Behavior（4 维度症状原始证据）

### 维度 A：chg-03 推断器 Java/Maven 盲点

**原始证据 A-1（grep 代码 0 处提及 Java/Maven）**：

```bash
$ cd /Users/jiazhiwei/claudeProject/workspace2/harness-workflow-req53-playbook && \
  grep -n "pom.xml\|maven\|Maven\|build.gradle\|gradle" src/harness_workflow/playbook/domain_inference.py
（无任何输出，0 命中）
```

**原始证据 A-2（4 级降级模式枚举确认）**：`src/harness_workflow/playbook/domain_inference.py` 第 78-134 行 4 级降级链定义：
- Level 1: `src/modules/*`
- Level 2: `src/domains/*`
- Level 3: `app/*`
- Level 4: `src/{pkg}/*` 次级模块

**全部 4 级假设 Python/JS/Node 单仓项目结构**，无任何 Java/Maven 多模块识别（`<modules>` / `pom.xml` / 顶层平级模块根目录扫描）。

**原始证据 A-3（dogfood 复现，注入 PetMallPlatform-like fixture）**：

```python
# 模拟 PetMallPlatform 真实结构
root.mkdir(platform-admin / platform-common / platform-modules / platform-extend / platform-demo-ui)
root / "pom.xml".write_text('<project><modules><module>platform-admin</module></modules></project>')
root / "app" / "logs".mkdir()
root / "app" / "temp".mkdir()
infer_domains(root)
# stdout: domain inference: matched 'app/*' (2 domains: logs, temp)
# 返回: mode=app/*, domains=['logs', 'temp']
```

`platform-admin / platform-common / platform-modules / platform-extend / platform-demo-ui` **5 个真业务模块完全被忽略**，命中 Level 3 `app/*` 后**命中即停**，得到错误的"领域 = `logs / temp`"。与用户报告的 PetMallPlatform 真实输出一致（`matched 'app/*' (1 domains: logs)`）。

### 维度 B：chg-04 SCRIPTS 检测器 Maven 盲点

**原始证据 B-1（grep `_scan_scripts` 实现，0 处 Maven 命令）**：

```bash
$ grep -n "pom.xml\|mvn\|Maven\|build.gradle\|gradle\|Gradle\|cargo\|csproj" \
  src/harness_workflow/tools/harness_playbook_refresh.py
87:    """扫描 pyproject.toml / package.json / go.mod / pom.xml / Cargo.toml 提取技术栈。"""
133:    # Java: pom.xml
134:    pom = root / "pom.xml"
138:        lines.append(f"- Java/Maven: {art_m.group(1) if art_m else 'project'}")
```

只有 `_scan_stack`（第 86-150 行）会从 `pom.xml` 抽 `artifactId` 写技术栈名；**`_scan_scripts`（第 153-192 行）只扫**：
- `pyproject.toml [project.scripts]`（Python）
- `package.json scripts`（Node）
- `Makefile` targets

**0 处** mention `mvn clean install` / `mvn test` / `mvn package` / `mvn spring-boot:run`，**0 处** Gradle 命令检测，**0 处** Cargo `[bin]` 段检测，**0 处** .NET / `dotnet` 命令检测。Maven 项目跑完 `playbook-refresh` 后 `runbook.md` AUTO:SCRIPTS 区段输出 `<!-- 未检测到脚本配置，请手工填写常用命令 -->`（即用户报告的"AUTO:SCRIPTS 完全空"症状）。

### 维度 C：spec "不调 LLM" 决策反转（用户拍板）

**原始证据 C-1（spec 原文）**：`artifacts/feature-req-55-playbook/.../inputs/initial-spec.md` 第 324 行 `### 实现要点` 段：

```
- **不调 LLM**，纯静态分析，保证可重复、可在 CI 跑
```

**原始证据 C-2（requirement.md Excluded 段镜像）**：`requirement.md` 第 30-31 行：

```
### Excluded（明示不做）
- **不让脚本调 LLM**：所有路书生成 / 刷新 / 检测均为静态分析（文件树扫描 + 正则区段替换 + 路径存在性校验），保证可重复、可在 CI 跑、零成本。
```

**反转决策**（用户基于 dogfood 真实结果）：chg-03 init_playbook + chg-04 playbook-refresh **应当调 LLM** 来扫描填充骨架内容（`overview.md` 业务定义 / `domains/*/README.md` 领域职责 / `code-map.md` 关键词 / `architecture.md` 技术决策摘要等用户最关心的"对人内容"），用户可手工查看修改。

**理由**（用户视角推断）：纯静态填出来骨架 90% 内容是 `<!-- TODO: ... -->`，对人不友好；用户希望首装就能看到有意义的初稿（即使 LLM 拼凑、可手工修改），不要被迫从空白开始。

### 维度 D：OQ-5 路书"只读"约束语义松动

**原始证据 D-1（base-role.md 硬门禁十 第 4 节原文）**：`/Users/jiazhiwei/claudeProject/workspace2/harness-workflow-req53-playbook/.workflow/context/roles/base-role.md` 第 394-399 行：

```
### 4. 不该做的事
- 不要修改 `artifacts/project/playbooks/` 下任何文件（OQ-5=A：本 req 仅写规则 + chg-05 `playbook-check` 漂移检测兜底，不引入 PreToolUse hook）
```

**矛盾点**：既然 LLM 填的内容用户**要修改**（维度 C 的反转结论），那"不要修改 `artifacts/project/playbooks/` 下任何文件"的硬门禁就不能继续按字面义生效——需要细化到"`<!-- AUTO:* -->` 区段只读（脚本/LLM 生成，agent 不动）；区段外人写区域用户可改、agent 默认不改但用户 explicit 指示后可改"的**区段级只读语义**。

**原始证据 D-2**：chg-05 playbook-check 实现的"AUTO 区段哈希漂移检测"（OQ-5 兜底）只覆盖 AUTO 区段，**对区段外人写区域无检测**——技术现状已经天然支持区段级只读，只是 base-role.md 文字尚未对应。

## 4. 影响范围（Reach）

| 维度 | 受影响项目类型 | 受影响场景 | 严重性 |
|------|--------------|----------|--------|
| A | Java/Maven 多模块（顶层平级模块根） | `harness install --playbook-only` 一开就错领域 | **P0**（产品在主流企业 Java 栈上不可用） |
| A | Gradle / Kotlin / .NET 多模块（推测同源问题） | 同 A | P1（未实测但模式同源） |
| B | Java/Maven / Gradle / Cargo / .NET 项目 | `playbook-refresh` 后 runbook 空 | P1（用户需手工补，但功能上未崩） |
| C | 全部用户（spec 决策面） | install 首装体验 / refresh 后内容质量 | **P0**（决策反转影响 chg-03/04 实现路径） |
| D | 全部用户（base-role 硬门禁面） | "路书只读"硬约束语义不清 → agent 写入边界争议 | P1（与 C 互锁，需同步修订） |

**用户面**：
- **直接受影响**：所有用 Java/Maven 多模块的企业用户（Spring Boot / 微服务架构常态）；
- **间接受影响**：所有用 Gradle / Kotlin / Cargo / .NET 多模块的用户（同源问题，仅未实测）；
- **不受影响**：纯 Python / 纯 Node 单包项目（chg-03 推断器对这两类有 Level 1/2/4 命中，chg-04 SCRIPTS 对这两类有完整支持）。

## 5. Severity / Priority

- **维度 A：P0**（产品在主流企业 Java 栈上推断错误，"领域 = logs"对路书核心价值"项目地图 + 代码导航"完全反向）；
- **维度 B：P1**（功能未崩，但 SCRIPTS 区段空对 runbook 的"项目客观存在的命令"承诺打折扣）；
- **维度 C：P0**（spec 重大决策反转，影响 chg-03/04 整体实现策略 + 验收标准重构）；
- **维度 D：P1**（与 C 互锁，单独不阻塞但需配套修订）。

**整体严重性 = P0**（4 维度叠加，不能仅修 A 不修 C/D）。

## 6. Expected Outcome（用户期望）

1. **维度 A**：chg-03 推断器扩展到能识别 Java/Maven 多模块项目的"顶层平级 `platform-*` 模块根"或"`pom.xml <modules>` 字段"或"`pom.xml + src/main/java/` Maven 标准约定"；扩展后 PetMallPlatform 跑 `harness install --playbook-only` 应得出 `domains=['platform-admin', 'platform-common', 'platform-modules', 'platform-extend', 'platform-demo-ui']`。
2. **维度 B**：chg-04 SCRIPTS 检测器扩展到能扫 `pom.xml` / `build.gradle` / `Cargo.toml [bin]` / `*.csproj`，按文件类型注册化分发；至少 Maven lifecycle（`mvn clean install` / `mvn test` / `mvn package` / `mvn spring-boot:run`）能识别。
3. **维度 C**：chg-03 init_playbook 与 chg-04 playbook-refresh 引入 LLM 调用层，在首装 / refresh 时填充骨架内容（业务定义 / 领域职责 / 关键词 / 技术决策摘要等）；CI 模式下显式 `--no-llm` 跳过；spec / requirement.md "不调 LLM" 决策反转留 history。
4. **维度 D**：base-role.md 硬门禁十"路书只读"语义细化为**区段级只读**（`<!-- AUTO:* -->` 区段只读，区段外可改）；chg-05 playbook-check 兼容新语义（AUTO 区段哈希漂移仍检，区段外不检）。

## 7. Next Step

- **诊断师**：完成本 issue 的根因分析（4 个独立维度）+ 影响半径估算 + 修复方案候选 → 写 `analysis.md`。
- **路由决策**：根据 4 维度真实性 + 修复体量 + 对 req-55 baseline 的影响，给出 R1（单 reg 修）/ R2（多 reg 平行）/ R3（转新 chg）/ R4（转新 req）/ R5（reject）路由建议 → 写 `decision.md`。
- **不在本 stage 修代码**：诊断师只诊断 + 路由，不直接改代码 / 改 chg-01~05 已落地的契约 / 测试。
