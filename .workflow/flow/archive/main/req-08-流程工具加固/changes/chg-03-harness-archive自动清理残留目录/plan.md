# Plan: chg-03

## Steps

1. 读取 `core.py` 中的归档相关函数（搜索 `archive` 关键词）
2. 找到需求移动到 archive 后的逻辑位置
3. 增加清理逻辑：
   - `residual = root / ".workflow" / "flow" / "requirements" / req_dir_name`
   - 如果 `residual.exists()`，则 `shutil.rmtree(residual)`
   - 记录动作如 `cleaned residual flow/requirements/{req-id}/`
4. 确保清理动作在归档成功后才执行
5. 测试：在一个临时项目或 Yh-platform 中创建一个假需求并归档，验证残留目录被清理

## Artifacts

- 更新后的 `core.py`

## Dependencies

- 无
