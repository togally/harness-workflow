# Suggest

> **状态**: 已归档 (archived)
> **归档时间**: 2026-04-18
> **应用时间**: 2026-04-18
> **修改文件**: `.workflow/context/team/development-standards.default.md` (新建), `.workflow/context/roles/stage-role.md`

新项目采用默认开发规范，并根据项目实际情况自动生成定制化的开发规范文档。

## 背景

当前 `.workflow/context/team/development-standards.md` 是团队开发规范的存放位置，但存在以下问题：

1. **新项目空白启动**：新创建的项目没有默认开发规范，角色在 `before-task` 阶段读取时发现文件缺失或为空
2. **规范与项目脱节**：即使存在开发规范，也可能是从其他项目复制过来的，与当前项目的技术栈、框架、目录结构不匹配
3. **维护成本高**：人工编写和维护开发规范需要投入额外时间，且容易遗漏项目特有的约束

## 建议

### 1. 默认规范模板

建立一份 `context/team/development-standards.default.md` 作为基础模板，包含：
- 通用代码风格约束（命名规范、注释要求、错误处理原则）
- 通用安全准则（输入校验、防注入、敏感信息处理）
- 通用测试要求（单元测试覆盖率、集成测试边界）

当项目没有 `development-standards.md` 或文件为空时，各角色 `before-task` 阶段自动回退加载默认模板。

### 2. 自动生成机制

在 `planning` 或 `executing` 阶段引入一个可选步骤：
- 当检测到项目根目录存在 `package.json`、`pom.xml`、`go.mod`、`Cargo.toml`、`pyproject.toml` 等标志性文件时
- 由 `toolsManager` 或专门的 subagent 扫描项目技术栈、目录结构、已有代码风格
- 基于默认模板生成一份项目专属的 `development-standards.md`

生成内容应包含：
- 项目使用的编程语言和框架
- 目录结构约定（如 `src/`、`tests/`、`docs/` 的用途）
- 从现有代码中提取的代码风格（缩进、引号、导入排序等）
- 项目特有的构建/测试命令（如 `npm test`、`make build`）
- 项目已有的 linter/formatter 配置（`.eslintrc`、`.prettierrc`、`ruff.toml` 等）

### 3. 更新触发条件

以下场景应触发开发规范的重新生成或更新：
- 项目技术栈发生重大变更（新增主要框架、更换构建工具）
- 目录结构发生显著调整
- 用户在 suggest 中提出与开发规范相关的改进

### 4. 角色集成

更新 `stage-role.md` 中的"团队与项目上下文（before-task）"加载规则：
- 优先加载 `development-standards.md`
- 如不存在，加载 `development-standards.default.md` 并提示用户可考虑自动生成专属规范
