# Planning Stage Experience

> Placeholder experience file. Fill in based on actual project lessons.

## Key Constraints

<!-- Record must-follow constraints here -->

## Best Practices

<!-- Record recommended approaches here -->

## Common Mistakes

<!-- Record common errors here -->

## 经验一：功能 + bugfix 合集需求的 change 拆分范式

### 场景

req-29 同时合并 sug-01（产品级 feature：ff --auto 自主推进）与 sug-08（CLI bugfix + 数据迁移：archive 判据修复 + 一次性迁移）两条建议，拆分粒度需权衡。

### 经验内容

对"一个 feature sug + 一个 bugfix sug"合集，建议采用 **3 + 2 + 1（端到端 smoke）** 的 5-change 结构：

- **feature 侧拆 3 个 change**：
  - chg-A：数据层/数据契约（数据模型 + 契约声明文件更新，无 CLI 入口）
  - chg-B：CLI 入口层 + 主循环（依赖 chg-A 的数据层）
  - chg-C（可合并到 smoke）：独立纯函数工具（如阻塞检测、渲染器）
- **bugfix 侧合 2 个 change**：
  - chg-D：判据修复 + 单测
  - chg-E：数据迁移命令 + 幂等/冲突测试
- **整合层 1 个 smoke change**：
  - chg-F：tempdir 端到端整合，覆盖所有 AC 的集成点 + 对人文档示范

这个范式的好处：
1. 每个 change 可独立并行 executing，互相不阻塞。
2. smoke change 作为最后屏障，保证"单独通过 ≠ 整体通过"的风险被兜住。
3. chg-D 可在 feature 侧任意阶段合入，不占关键路径。

### 来源

req-29 — sug-01（ff --auto）+ sug-08（archive 判据）合集，5 个 change 并行 + 最后 smoke 收尾
