# Session Memory — chg-02（角色索引 + role-model-map 更新，analyst 注册 + legacy 别名保留）

## 1. Current Goal

- 在 `role-model-map.yaml` 注册 `analyst: "opus"` + 保留 legacy 别名；在 `index.md` 角色索引表以 analyst 条目替换原两行，并同步两份 mirror。

## 2. Current Status

- **执行完毕（2026-04-23）**：4 个文件改动全落地，AC-2 / AC-3 自证全通过，mirror diff 0。

## 3. Validated Approaches

- Step 1：Edit `.workflow/context/role-model-map.yaml`，在 opus 段首行追加 `analyst: "opus"`；在 `requirement-review` / `planning` 行尾注释追加 `legacy alias — route to analyst（req-40）`。
- Step 2：`cp` + `diff -rq` mirror OK。
- Step 3：Edit `.workflow/context/index.md`，Stage 执行角色表将原两行（requirement-review / planning）合并为单行 analyst；在表行下方加引用块注释说明合并来源。
- Step 4：`cp` + `diff -rq` mirror OK。
- Step 5：全部 AC grep 断言命中，python3 YAML load 验证通过。

## 4. default-pick 决策记录

- **I-1 = A**（index.md 策略）：合并两行为 analyst 单行 + 加注释说明废弃来源，旧条目物理移除（旧 role.md 文件物理保留由 chg-01 决定）。
- **M-1 = B**（role-model-map 策略）：保留 `requirement-review` / `planning` legacy key 作别名（同值 opus），新增 `analyst` 主 key，注释标 "legacy alias"。理由：避免 role-loading-protocol 自检对 legacy key 误报；向后兼容历史归档引用。

## 5. Failed Paths

- 无。

## 6. Next Steps

- 本 chg 已结束；chg-03（harness-manager 路由 + technical-director 流转扩展）为后续依赖本 chg 的 analyst key 注册。

## 7. Open Questions

- 无。
