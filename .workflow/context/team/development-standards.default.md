# Development Standards (Default Template)

> 本文件是新项目的默认开发规范模板。当项目没有 `development-standards.md` 或文件为空时，各角色 `before-task` 阶段自动回退加载此模板。

## 通用代码风格约束

### 命名规范
- 变量和函数：使用有意义的命名，优先 `camelCase`（JavaScript/TypeScript）或 `snake_case`（Python/Go）
- 类名：使用 `PascalCase`
- 常量：使用 `UPPER_SNAKE_CASE`
- 文件名：使用短横线分隔（kebab-case）或与框架约定一致

### 注释要求
- 公共 API 添加文档注释（JSDoc、GoDoc 等）
- 复杂逻辑添加解释性注释
- 禁止注释掉的无用代码

### 错误处理原则
- 同步函数优先返回错误值，异步函数优先使用 try/catch
- 错误信息应包含上下文，避免裸露的原始异常

## 通用安全准则

### 输入校验
- 所有外部输入必须验证类型、范围、格式
- 避免直接拼接用户输入到命令或查询中

### 防注入
- SQL/NoSQL 查询使用参数化查询或 ORM
- 命令执行避免 shell 拼接，优先使用 API

### 敏感信息处理
- 禁止硬编码密钥、Token、密码
- 使用环境变量或密钥管理服务

## 通用测试要求

### 单元测试覆盖率
- 核心业务逻辑覆盖率 > 70%
- 公共 API 覆盖率 100%

### 集成测试边界
- 数据库操作层需要集成测试验证
- 外部服务调用需要 mock 或 integration test

## 通用构建与部署

### 构建命令
- 使用项目已有的构建工具（npm、maven、go build 等）
- 确保 CI/CD 流水线可复现

### 测试命令
- 单元测试：`npm test`、`mvn test`、`go test`
- 集成测试：使用专门的 test:integration 脚本

## 自动生成说明

当检测到项目根目录存在以下标志性文件时，可触发自动生成项目专属规范：
- `package.json` → Node.js/TypeScript 项目
- `pom.xml` → Java/Maven 项目
- `go.mod` → Go 项目
- `Cargo.toml` → Rust 项目
- `pyproject.toml` → Python 项目

自动生成的内容将包含：
- 项目使用的编程语言和框架
- 目录结构约定
- 从现有代码中提取的代码风格
- 项目特有的构建/测试命令
- 项目已有的 linter/formatter 配置
