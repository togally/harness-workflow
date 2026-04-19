# Session Memory: req-12 / chg-02

## 变更目标
更新 README 中的 suggest 命令说明，验证批量转换功能，并归档 req-12。

## 执行日志

- [x] Step 1: 在临时项目创建多个 suggest，执行 `harness suggest --apply-all` 验证
- [x] Step 2: 验证所有 pending suggest 被正确转为 req
- [x] Step 3: 更新 `README.md`，在 suggest 示例中增加 `--apply-all`
- [x] Step 4: 同步 `scaffold_v2`（README.md）
- [x] Step 5: `pipx inject harness-workflow . --force` 重新安装
- [ ] Step 6: 生成 done-report 并归档 req-12（待 done 阶段执行）

## 产出文件
- `README.md`
- `src/harness_workflow/assets/scaffold_v2/README.md`

## 关键决策
- 临时项目验证采用 `harness init` 创建干净项目，创建 2 条 suggest 后执行 `--apply-all`，成功转为 req-01 和 req-02
- 安装验证通过 `which harness` 确认 CLI 可用

## 遇到的问题
- 无

## 下一步
- 等待 req-12 进入 done 阶段后生成 done-report 并归档
