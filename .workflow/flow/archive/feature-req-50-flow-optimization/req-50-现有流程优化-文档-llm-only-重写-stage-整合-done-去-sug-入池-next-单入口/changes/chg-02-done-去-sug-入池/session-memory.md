---
req_id: req-50
chg_id: chg-02
title: done 阶段去掉 sug 入池职责
ts: 2026-04-28T00:00:00+00:00
---

## §改动文件清单

| 文件 | 操作 |
|------|------|
| `.workflow/context/roles/done.md` | 删 sug 入池相关段落，新增软提示段 |
| `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md` | mirror 同步（cp，diff=0） |
| `.workflow/context/experience/roles/done.md` | 追加「done 阶段不主动入池」经验段 |

## §核心变更

**删除内容：**
- `### Step 6` 标题中「与建议转 suggest 池」部分
- Step 6 内「提取 done-report.md 改进建议，自动创建 suggest 文件」一行
- `## 建议转 suggest 池` 整段（4 步提取/过滤/创建/记录）
- `## 退出条件` 中「done-report.md 中的改进建议已提取（如有）」一条
- `## 完成前必须检查` 第 1 条（改进建议已提取并写入 suggest 池）
- `## 禁止的行为` 中「不得遗漏 done-report.md 中的改进建议提取」

**保留内容：**
- done 阶段六层回顾 SOP 完整保留
- 经验沉淀验证（Step 4）保留
- 交付总结产出模板保留
- `harness suggest` CLI 主动入口能力保留（改为可选）

**新增内容：**
- `## 允许的行为`：「（可选）通过 `harness suggest` CLI 入口创建 sug 文件——仅在用户主动请求时」
- `## 改进点处置（req-50 / chg-02）` 软提示段
- `experience/roles/done.md`：「经验：done 阶段不主动入池（req-50 / chg-02）」新段

✅
