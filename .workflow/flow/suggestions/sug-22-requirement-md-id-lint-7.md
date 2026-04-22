---
id: sug-22
title: "requirement.md 裸 id 引用 lint（契约 7 硬化）"
status: pending
created_at: 2026-04-23
priority: low
---

req-34 requirement.md §2 第 7 行 req-32 chg-01 chg-02 未带 title，testing 标轻度违反契约 7。建议 requirement-review 阶段加 lint：grep 首次引用 req-NN / chg-NN 必须带括号 title 否则阻塞 next。
