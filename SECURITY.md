# 安全政策

## 支持的版本

我们为以下版本提供安全更新：

| 版本 | 支持状态 |
| --- | --- |
| 1.0.x | ✅ |
| < 1.0 | ❌ |

## 报告安全漏洞

我们非常重视安全问题。如果你发现了安全漏洞，请按照以下步骤报告：

### 🔒 私密报告

**请不要在公开的 GitHub Issues 中报告安全漏洞。**

请通过以下方式私密报告：

1. **GitHub Security Advisories**（推荐）
   - 访问项目的 [Security](https://github.com/your-username/mcp-projectmanage-openproject/security) 页面
   - 点击 "Report a vulnerability"
   - 填写详细信息

2. **邮件报告**
   - 发送邮件至：[your-email@example.com]
   - 主题：`[SECURITY] MCP OpenProject - 安全漏洞报告`

### 📋 报告内容

请在报告中包含以下信息：

- **漏洞描述**：详细描述安全问题
- **影响范围**：哪些版本和组件受影响
- **复现步骤**：如何重现该漏洞
- **潜在影响**：可能造成的安全风险
- **建议修复**：如果有修复建议请提供

### ⏱️ 响应时间

我们承诺：

- **24 小时内**：确认收到报告
- **72 小时内**：初步评估和响应
- **7 天内**：提供详细的修复计划
- **30 天内**：发布安全修复（如果可能）

## 🛡️ 安全最佳实践

### 部署安全

1. **API 密钥管理**
   - 使用环境变量存储 API 密钥
   - 定期轮换 API 密钥
   - 不要在代码中硬编码密钥

2. **网络安全**
   - 使用 HTTPS 进行生产部署
   - 配置适当的防火墙规则
   - 限制不必要的端口访问

3. **容器安全**
   - 使用官方基础镜像
   - 定期更新容器镜像
   - 扫描镜像漏洞

### 开发安全

1. **依赖管理**
   - 定期更新依赖包
   - 使用 `npm audit` 或 `pip-audit` 检查漏洞
   - 固定依赖版本

2. **代码安全**
   - 验证所有输入数据
   - 使用参数化查询
   - 实施适当的错误处理

3. **认证授权**
   - 实施强认证机制
   - 使用最小权限原则
   - 记录安全相关事件

## 🔍 安全扫描

项目集成了以下安全扫描工具：

- **Trivy**：容器和依赖漏洞扫描
- **CodeQL**：代码安全分析
- **Dependabot**：依赖安全更新

## 📚 安全资源

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [Python Security](https://python-security.readthedocs.io/)
- [Docker Security](https://docs.docker.com/engine/security/)

## 🏆 致谢

我们感谢所有负责任地报告安全问题的研究人员和用户。

### 安全贡献者

- 待添加...

## 📞 联系方式

如有安全相关问题，请联系：

- **安全邮箱**：[your-email@example.com]
- **PGP 密钥**：[如果有的话]

---

**最后更新**：2025-07-23
