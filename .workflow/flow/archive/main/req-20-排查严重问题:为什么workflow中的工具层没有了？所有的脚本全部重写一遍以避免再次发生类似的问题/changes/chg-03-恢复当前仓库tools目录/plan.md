# Plan: 恢复当前仓库 tools 目录

## 执行步骤

1. 确认 `.workflow/context/backup/legacy-cleanup/.workflow/tools/` 中的源文件完整（与 chg-02 使用的源相同）。
2. 在项目根目录 `.workflow/` 下创建 `tools/` 目录（若不存在）。
3. 将 backup 中的全部 `.md` 文件和 `catalog/` 子目录递归复制到 `.workflow/tools/`。
4. 验证关键文件列表：
   - `index.md`
   - `stage-tools.md`
   - `selection-guide.md`
   - `maintenance.md`
   - `catalog/_template.md` 等
5. （执行时需确认）如有必要，运行 `harness update --check` 验证 tools 目录不会被标记为待清理或待归档。

## 预期产物

- 新建/恢复的 `.workflow/tools/` 目录及其内容

## 依赖关系

- **前置依赖**：
  - chg-01 必须完成（确保 update 不会再次误清理）
  - chg-02 必须完成（确保模板与恢复内容一致，scaffold 同步逻辑不会覆盖）
- **后置依赖**：chg-04 需要基于恢复后的状态编写测试。
