---
id: bugfix-8-acceptance-report
stage: acceptance
verdict: PASS
date: 2026-04-28
---

# Bugfix Acceptance Report — bugfix-8

**标题**：用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁
**验收官**：acceptance（sonnet）
**日期**：2026-04-28
**verdict：PASS**

---

## 1. 验收范围

5 chg 落地产物：
- chg-01：真清理 usage-reporter.md（build/ + dogfood + managed-files.json + LEGACY_CLEANUP_TARGETS 兜底）
- chg-02：`_SCAFFOLD_V2_MIRROR_WHITELIST` 17→20 条（+flow/bugfixes / experience/regression / experience/risk）
- chg-03：install_repo 入口 stderr + skip 分支防御性 `if not force_managed` / `else` WARNING
- chg-04：`validate_contract.py` 新增 `_is_dev_repo`（三层探测）+ `check_user_write_protected_zones` + 注册 contract + cli choices + install_repo 末尾接入
- chg-05：`validate_contract.py` 新增 `check_build_cache_freshness` + 注册 contract + cli choices

---

## 2. 验收结果摘要

| chg | 核心 AC | 判定 |
|-----|---------|------|
| chg-01 | 三处删除 + managed-files 摘除 + LEGACY_CLEANUP_TARGETS 兜底 | PASS |
| chg-02 | 白名单 20 条已含 3 新路径；TC-02 全 PASS | PASS |
| chg-03 | 入口 stderr 透传确认 + 两处防御性分支 + TC-03 PASS | PASS |
| chg-04 | `_is_dev_repo` 三层实现 + 保护区扫描 + dev mode dogfood exit 0；`_install_self_audit` 未替换（非阻塞） | 部分 PASS（主体 PASS） |
| chg-05 | build-cache-freshness contract 注册 + TC PASS；本仓 build/ 含 1 stale artifacts-layout.md（pre-existing） | 部分 PASS（主体 PASS） |

---

## 3. 关键验证证据

1. **AC-01-a/b 文件删除**：`ls build/lib/.../usage-reporter.md` → No such file；`.workflow/context/roles/` 无该文件
2. **AC-01-c managed-files**：python3 json 读取 managed_files keys 无 usage-reporter 命中
3. **AC-02-a 白名单**：workflow_helpers.py 行 203-207 含 3 条新路径（含 chg-02 注释）
4. **AC-03-a/b 防御代码**：行 3773 入口 stderr；行 3406/3510 双处 `if not force_managed` + else WARNING
5. **AC-04-a/b/c/d 硬门禁**：validate_contract.py 行 907 `_is_dev_repo`（三层实现）；dogfood `harness validate --contract user-write-protected-zones` exit=0
6. **AC-05-a/b/c lint**：validate_contract.py 行 998 `check_build_cache_freshness`；cli choices 含 `build-cache-freshness`
7. **22 tests PASS**：test_install_whitelist_business_zones.py (3) + test_install_force_managed_defense.py (4) + test_user_write_protected_zones.py (10) + test_build_cache_freshness.py (5) = 22 passed in 2.60s
8. **全量回归**：688 passed + 13 pre-existing + 0 新增 fail
9. **退出前 validate**：`harness validate --human-docs` exit=0；`harness validate --contract artifact-placement` exit=0

---

## 4. 遗留事项（不阻塞 done）

| # | 描述 | 严重性 | 建议处理 |
|---|------|--------|---------|
| 1 | `_install_self_audit` 未替换为 `_is_dev_repo` 三层探测（仍用 env 单通道） | 低 | 作为后续优化 sug 记录 |
| 2 | build/ 含 stale `artifacts-layout.md`（pre-existing，非 bugfix-8 引入） | 低 | 用户 `rm -rf build/` 后自然消除 |
| 3 | testing subagent 红线违规经验沉淀 | 低 | done 阶段写入 regression.md 经验十七 |

---

## 5. 路由决策

**verdict: PASS → done**
