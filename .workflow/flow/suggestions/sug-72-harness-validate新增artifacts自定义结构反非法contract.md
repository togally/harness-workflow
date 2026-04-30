---
id: sug-72
title: "harness validate 新增 contract 检测 artifacts/project 之外的 artifacts/{其他}/ 自定义结构防 AI 发明路径"
status: pending
created_at: 2026-04-30
priority: medium
---

req-53 用户原话暴露「AI 自己发明路径 `artifacts/standards/coding/`」痛点；本 req 通过 `harness pad` 强制 kind / scope 枚举封死了入口路径，但**已存在的违规目录** + **绕过 pad 直接 vim 写入的违规路径**仍无 lint 兜底。建议 `harness validate` 新增 contract `project-artifact-layout`（或同型）：扫描 `artifacts/` 下所有目录树，断言除 `artifacts/{branch}/` 对人型白名单 + `artifacts/project/{constraints,experience,tools}/` 机器型白名单之外不得存在自定义结构（如 `artifacts/standards/` / `artifacts/rules/` / `artifacts/specs/`）；命中即 ABORT 或 warn 引导用 `harness pad`。落地：复用 `_bootstrap_project_skeleton` 已知白名单 + `repository-layout.md` §2/§3 路径表作权威源。来源：req-53 done 阶段六层回顾 Constraints 层 + 用户原话痛点。
