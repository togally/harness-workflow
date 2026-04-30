---
id: sug-61
title: "/usr/local/bin/harness 历史残留二进制（pipx force install 提示 PATH 冲突）"
status: pending
created_at: 2026-04-29
priority: low
---

用户机器 /usr/local/bin/harness 还有一个非 pipx 安装的 harness 二进制（历史 brew/手装残留），导致 'pipx install --force harness-workflow' 时 shell PATH 优先命中老二进制，bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）acceptance round-2 复跑因此一度 dogfood E.1 跑出旧版行为，需用户手动 rm 老二进制 + rehash 后才落到 ~/.local/bin/harness 的最新版。建议：harness install 流程检测到 PATH 中存在多个 harness 二进制时给出告警提示用户清理；或 harness status 加 'which -a harness' 自检。来源：bugfix-11 acceptance round-2 §旁支观察 #2。
