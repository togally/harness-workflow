# req-02 Session Memory

## 执行状态

### chg-07 移除版本概念
- [x] core.py 版本常量和路径删除
- [x] 版本相关函数（~26个）删除
- [x] archive_requirement() 重写（新签名 --folder）
- [x] workflow_next() 版本引用清理（重写为 requirement-centric）
- [x] cli.py 移除 version/active/use/plan 命令
- [x] 命令文件删除（harness-version/active/use/plan.md）
- [x] .workflow/versions/ 删除
- [x] pip install -e . 重装验证

### chg-01 修复主加载链
- [x] context/index.md 更新加载规则（session-start、evaluation、team/project）

### chg-02 清理 CLI 产物目录
- [x] context/rules/ 删除

### chg-03 恢复 tools/ 工具层
- [x] .workflow/tools/ 建立（从 archive/legacy-cleanup 迁移）
- [x] catalog/ 迁移
- [x] 角色文件 ## 可用工具 更新（引用 stage-tools.md）

### chg-04 迁移 backup 目录
- [x] context/backup/ → .workflow/archive/

### chg-06 更新 lint 和测试文件
- [x] lint_harness_repo.py 更新（新目录结构）
- [x] test_harness_cli.py skip 标注（所有版本相关测试）

### chg-05 README 双语文档
- [x] README.md（英文，新六层架构说明）
- [x] README.zh.md（中文）

## 待处理捕获问题

（无）
