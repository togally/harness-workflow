---
id: sug-20
title: "tools/harness_update.py 过渡态清理（改为 harness_install.py 别名）"
status: pending
created_at: 2026-04-23
priority: low
---

req-33 chg-01 为避免破坏 test_update_repo_* import，保留了 tools/harness_update.py 作为 helper 入口，内部已委托给 install_repo。长远建议：tools/harness_update.py 直接改为 tools/harness_install.py 的 alias 或 re-export，保持入口最少。
