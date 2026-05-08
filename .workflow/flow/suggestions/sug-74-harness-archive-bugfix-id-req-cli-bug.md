---
id: sug-74
title: "harness archive bugfix-id 误归档 req（CLI 参数解析 bug）"
status: pending
created_at: 2026-05-08
priority: high
---

实证：harness archive bugfix-11 --skip-revert-check 输出 'Archived requirement: req-53'，把 req-53 错误归档到 archive/harness-gstack/，原 .workflow/flow/requirements/req-53-... 17 文件被 mv 走 + runtime.yaml current_requirement / active_requirements 被反写空。CLI --help 文档说 positional 'requirement' 支持 'Requirement/bugfix title or id'，但实际识别 'bugfix-11' 失败，回退到归档某个 req（疑似首个 active 或 hash 匹配）。需修：archive_requirement 函数加 bugfix-id 显式分流；--help 文档与实现对齐。临时绕过：bugfix archive 用手工 mv 或保留在 .workflow/flow/bugfixes/ 不 archive（与 bugfix-5/7/8/10 同模式）。
