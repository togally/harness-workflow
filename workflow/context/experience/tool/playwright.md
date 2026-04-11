# Playwright 工具使用经验

> 任务涉及 Playwright 测试时按需加载，跨阶段通用。
> 置信度：low — 新沉淀经验，验证后逐步提升。

## 核心注意事项

- 执行 Playwright 测试前确认浏览器已安装（`npx playwright install`）
- 测试超时时检查选择器和等待条件
- 异步操作需使用 `waitForSelector` 或 `waitForNavigation`

## 最佳实践

- 使用页面对象模式（Page Object Model）组织测试代码
- 截图和视频录制用于调试失败测试
- 并行测试时注意共享状态问题

## 常见错误

- 选择器过于脆弱（依赖 CSS 类名等易变属性）
- 未处理动态内容加载导致的竞态条件
- 测试未清理测试数据导致相互干扰
