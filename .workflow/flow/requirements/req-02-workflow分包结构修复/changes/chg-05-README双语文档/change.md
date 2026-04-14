# chg-05 README 双语文档

## 目标

在项目根目录创建英文 README.md（默认）和中文 README.zh.md，两文件互有跳转链接。

## 内容要求

### 必须包含
1. **项目介绍**：harness-workflow 是什么，解决什么问题
2. **六层原理**：工作流的六层架构说明（Hard Gate → 角色层 → 约束层 → 经验层 → 评估层 → 工具层）
3. **安装方式**：如何在项目中安装和初始化
4. **使用方式**：核心命令（harness requirement / next / regression 等）基本用法

### 建议包含（对项目宣传有价值）
- Badge（如适用）
- 工作流状态机图（用 ASCII 或 Mermaid 表示 stage 流转）
- 与其他 AI 工作流工具的差异点（核心价值主张）
- 支持的平台（Claude Code、Codex、Qoder）

### 格式要求
- `README.md`：英文，文件顶部有 "中文文档" 跳转链接
- `README.zh.md`：中文，文件顶部有 "English" 跳转链接
- 两文件结构对称，内容对应

## 范围

### 创建文件
- `README.md`（项目根目录）
- `README.zh.md`（项目根目录）

### 不修改
- 其他任何文件

## 验收标准

- [ ] `README.md` 存在，包含项目介绍、六层原理、安装方式、使用方式
- [ ] `README.zh.md` 存在，内容与 README.md 对应
- [ ] 两文件顶部互有跳转链接
- [ ] README.md 中的 stage 流转关系有可视化表达
- [ ] 内容准确，无与实际结构不符的描述
