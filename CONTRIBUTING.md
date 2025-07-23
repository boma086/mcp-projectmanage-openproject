# 贡献指南

感谢你对 MCP OpenProject 集成项目的关注！我们欢迎各种形式的贡献。

## 🚀 如何贡献

### 报告 Bug

如果你发现了 bug，请：

1. 检查 [Issues](https://github.com/your-username/mcp-projectmanage-openproject/issues) 确认问题尚未被报告
2. 使用 Bug Report 模板创建新的 issue
3. 提供详细的复现步骤和环境信息

### 建议新功能

如果你有新功能的想法：

1. 检查 [Issues](https://github.com/your-username/mcp-projectmanage-openproject/issues) 确认功能尚未被建议
2. 使用 Feature Request 模板创建新的 issue
3. 详细描述功能的用途和实现方案

### 提交代码

1. **Fork 项目**
2. **创建功能分支**：`git checkout -b feature/amazing-feature`
3. **提交更改**：`git commit -m 'Add some amazing feature'`
4. **推送分支**：`git push origin feature/amazing-feature`
5. **创建 Pull Request**

## 📋 开发指南

### 环境设置

```bash
# 克隆项目
git clone https://github.com/your-username/mcp-projectmanage-openproject.git
cd mcp-projectmanage-openproject

# 启动 OpenProject
docker-compose up -d

# 选择一个解决方案进行开发
cd http-solution  # 或其他解决方案
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 代码规范

#### Python 代码

- 使用 **Black** 进行代码格式化
- 使用 **flake8** 进行代码检查
- 使用 **isort** 进行导入排序
- 遵循 **PEP 8** 规范

```bash
# 格式化代码
black src/
isort src/

# 检查代码
flake8 src/
```

#### TypeScript 代码

- 使用 **Prettier** 进行代码格式化
- 使用 **ESLint** 进行代码检查
- 遵循 **TypeScript** 最佳实践

```bash
# 格式化代码
npm run format

# 检查代码
npm run lint
```

### 测试

- 为新功能添加测试
- 确保所有测试通过
- 保持测试覆盖率

```bash
# 运行测试
pytest tests/
npm test
```

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat(http): add project report generation
fix(fastmcp): resolve initialization race condition
docs: update installation instructions
```

## 🎯 开发优先级

### 高优先级
1. **HTTP 解决方案优化** - 已测试通过，需要持续改进
2. **FastMCP 问题修复** - 解决版本兼容性问题
3. **文档完善** - 改进使用指南和 API 文档

### 中优先级
1. **FastAPI 解决方案实现** - 基于 FastAPI 的新实现
2. **测试覆盖率提升** - 添加更多测试用例
3. **性能优化** - 提升响应速度和资源使用

### 低优先级
1. **TypeScript 解决方案实现** - Node.js 版本实现
2. **监控和日志** - 添加详细的监控功能
3. **部署工具** - Docker 和 K8s 部署支持

## 🔍 代码审查

所有 Pull Request 都会经过：

1. **自动化检查**：CI/CD 管道验证
2. **CodeRabbit 审查**：AI 代码审查
3. **人工审查**：维护者代码审查

请确保：
- [ ] 代码符合项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 通过了所有检查

## 📞 联系方式

如果你有任何问题：

- 创建 [Issue](https://github.com/your-username/mcp-projectmanage-openproject/issues)
- 发起 [Discussion](https://github.com/your-username/mcp-projectmanage-openproject/discussions)

## 📄 许可证

通过贡献代码，你同意你的贡献将在 [MIT License](LICENSE) 下发布。
