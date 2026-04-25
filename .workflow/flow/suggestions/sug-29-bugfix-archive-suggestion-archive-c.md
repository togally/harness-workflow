---
id: sug-29
title: "bugfix archive + suggestion archive 同步方向 C"
status: pending
created_at: 2026-04-25
priority: medium
---

req-42（archive 重定义：对人不挪 + 摘要废止）/ chg-02（archive_requirement helper 改写）只覆盖 archive_requirement (req archive)，bugfix archive + suggestion archive 走不同代码路径未同步；bugfix-4 dogfood 暴露：archive 后机器型 _meta.yaml + state.yaml + regression/ 混在 artifacts/main/archive/bugfixes/，应迁到 .workflow/flow/archive/
