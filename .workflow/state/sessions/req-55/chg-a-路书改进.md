# chg-A 路书改进 session memory

## 修改文件清单

### 修改文件
1. `src/harness_workflow/playbook/domain_inference.py` — `MavenMultiModuleDetector` 增加递归 nested pom 处理：
   - 新增 `_MAX_DEPTH = 5`
   - 新增 `_extract_modules_from_pom(pom_path)` — 从 pom 提取 `<modules>` 子模块列表
   - 新增 `_is_aggregator_pom(pom_path)` — 判断 `<packaging>pom</packaging>`
   - 新增 `_resolve_modules(parent_dir, module_names, depth)` — 递归展开聚合模块
   - `detect()` 调用 `_resolve_modules()` 处理顶层子模块列表

2. `src/harness_workflow/playbook/init.py` — `init_playbook` 增加 LLM 区段未填充提示句：
   - LLM 填充后记录 `llm_filled` 标志（只有非 NoopProvider 才标记 True）
   - 新增 `_check_has_todo_placeholders(root)` — 检查路书 TODO 占位（备用）
   - 新增 `_print_noop_fill_hint(root)` — 输出 Claude Code + Codex 两段提示句
   - `init_playbook` 在 `written > 0` 且未填充时调用提示输出

### 新增文件
3. `tests/test_domain_inference_nested_maven.py` — 3 TC：
   - TC-01: 单层叶子模块（4 模块全 jar，baseline 行为）
   - TC-02: nested pom 递归（4 个顶层 + 1 聚合带 7 子 = 10 domains，platform-modules 被展开消失）
   - TC-03: max_depth=5 防无限循环（6 层深 fixture，不 RecursionError）

4. `tests/test_install_post_message.py` — 3 TC：
   - TC-01: no_llm=True → stdout 含 "Claude Code 提示" + "Codex 提示"
   - TC-02: mock 真实 LLM provider（非 Noop） → stdout 不含提示
   - TC-03（bonus）: NoopProvider fallback → stdout 含提示

## 真实 PetMallPlatform 运行结果

### 命令
```
cd /Users/jiazhiwei/claudeProject/workspace/PetMallPlatform
rm -rf artifacts/project/playbooks
PYTHONPATH=.../harness-workflow-req53-playbook/src python3 -m harness_workflow.cli install --root . --playbook-only --no-llm
```

### 真实 domain 清单（36 个，超出预期 10 是因为 platform-common 也是 pom 聚合，有 24 个子模块）
```
domain inference: matched 'maven_multi_module' (36 domains: platform-admin,
platform-common-bom, platform-common-social, platform-common-core, platform-common-doc,
platform-common-excel, platform-common-idempotent, platform-common-job, platform-common-log,
platform-common-mail, platform-common-mybatis, platform-common-oss, platform-common-ratelimiter,
platform-common-redis, platform-common-satoken, platform-common-security, platform-common-sms,
platform-common-web, platform-common-translation, platform-common-sensitive, platform-common-json,
platform-common-encrypt, platform-common-tenant, platform-common-websocket, platform-common-sse,
platform-common-log-sls, platform-common-log-trace, platform-monitor-admin, platform-snailjob-server,
platform-generator, platform-job, platform-system, platform-workflow, platform-mall, platform-member, platform-app)
```

**关键验证**：
- `platform-modules` NOT in list（聚合展开消失）✓
- `platform-common` NOT in list（聚合展开消失）✓
- `platform-extend` NOT in list（它的 pom 也是 packaging=pom 聚合，platform-monitor-admin + platform-snailjob-server 来自它）✓
- `platform-app, platform-generator, platform-job, platform-mall, platform-member, platform-system, platform-workflow` ALL present ✓

### 末尾提示句 stdout
```
[playbook] LLM 区段未填充（NoopProvider / --no-llm）。当前 agent 可手动接力：

  Claude Code 提示：
    请阅读 artifacts/project/playbooks/overview.md / architecture.md / domains/*/README.md，
    根据项目实际情况（pom.xml / README.md / 主要源码目录）填写所有 <!-- LLM:* --> 区段内的 TODO 占位。
    填写遵循硬门禁十 §4：只改 LLM 区段的 TODO 内容，不动区段标记和 AUTO 区段。

  Codex 提示：
    请使用 read_file 读 artifacts/project/playbooks/overview.md 等路书文件，
    根据 pom.xml 和源码结构生成 LLM 区段内容（≤ 3 句 / 区段），保持区段标记不变。
    填好后用 apply_patch 写回。
```

## pytest 结果

### 新增测试
- `test_domain_inference_nested_maven.py`: 3 passed / 0 failed
- `test_install_post_message.py`: 3 passed / 0 failed
- `test_domain_inference_multi_lang.py`: 15 passed / 0 failed
- `test_domain_inference_dogfood.py`: 2 passed / 0 failed
- **总计新增相关: 23 passed / 0 failed**

### 回归测试
- `test_playbook_install.py` + `test_playbook_refresh.py` + `test_playbook_refresh_multi_lang.py`
  + `test_playbook_refresh_dogfood_multi_lang.py` + `test_install_refresh_llm_integration.py`
  + `test_petmall_fixture_dogfood.py`
- **45 passed / 0 failed**

## 偏离说明

1. **domain 数量 36 ≠ 预期 10**：预期基于任务描述（父 4 模块 + platform-modules 7 子），但实际 PetMallPlatform 中 `platform-common` 和 `platform-extend` 也是 `packaging=pom` 聚合（各有多个子模块），递归全部展开，结果 36 个。这是递归逻辑正确运行的预期效果，非 bug。

2. **init.py 修改位置**：提示句输出在 `init.py` 的 `init_playbook` 函数末尾，而非 `harness_install.py`，因为 `init_playbook` 才是知道"LLM 是否真正填充"的层级，比 CLI 层更准确。

## session-memory 落档路径

`.workflow/state/sessions/req-55/chg-a-路书改进.md`（即本文件）
