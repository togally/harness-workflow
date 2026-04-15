# Session Memory: chg-03

## Change
harness archive 自动清理残留目录

## Status
✅ 已完成

## Steps
- [x] 读取 `archive_requirement` 函数
- [x] 在归档移动成功后，增加对 `flow/requirements/{req-id}/` 的残留目录检测和删除
- [x] 记录清理动作到输出日志
- [x] 临时项目测试验证：创建假需求 → `harness archive` → 残留目录被清理

## Internal Test
- [x] archive 成功后残留目录已不存在 ✅
- [x] 不存在残留时不报错 ✅
- [x] 清理动作有日志输出 ✅
