# 贡献指南 (Contributing Guide)

感谢您考虑为 AI Daily Digest 贡献力量！🎉

## 🚀 如何贡献

### 报告 Bug

发现 Bug？请先搜索 [Issue 列表](https://github.com/huangds/ai-daily-digest/issues)，确认没有被报告过。

如果确定是新的 Bug，请创建 Issue 并包含以下信息：

- **问题描述**：清晰描述遇到的问题
- **复现步骤**：一步步说明如何复现
- **预期行为**：期望的正确行为
- **实际行为**：实际发生的情况
- **环境信息**：操作系统、Python 版本、依赖版本
- **日志/截图**：如果有错误信息或截图，请一并提供

### 提议新功能

有好的想法？请先创建 Issue 讨论，说明：

- **功能描述**：详细描述建议的功能
- **使用场景**：为什么需要这个功能
- **实现思路**：如果有具体的实现思路，请一并说明

### 提交代码

1. **Fork 仓库**

   ```bash
   # 克隆你的 Fork
   git clone https://github.com/你的用户名/ai-daily-digest.git
   cd ai-daily-digest
   ```

2. **创建分支**

   ```bash
   git checkout -b feat/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **编写代码**

   - 遵循现有代码风格
   - 添加必要的注释
   - 更新文档（如果需要）
   - 添加测试（如果适用）

4. **运行测试**

   ```bash
   python -m pytest tests/
   ```

5. **提交代码**

   ```bash
   git add .
   git commit -m "feat: 添加 XXX 功能"
   ```

   **提交信息规范**（遵循 [Conventional Commits](https://www.conventionalcommits.org/)）：

   - `feat`: 新功能
   - `fix`: Bug 修复
   - `docs`: 文档更新
   - `style`: 代码格式（不影响功能）
   - `refactor`: 重构
   - `test`: 测试相关
   - `chore`: 构建/工具相关

6. **推送分支**

   ```bash
   git push origin feat/your-feature-name
   ```

7. **创建 Pull Request**

   - 填写 PR 模板
   - 关联相关的 Issue
   - 等待 Code Review

## 🎯 开发指南

### 项目结构

```
ai-daily-digest/
├── config/          # 配置文件
├── scripts/          # Python 脚本
├── tests/            # 测试文件
└── example_output/   # 示例输出
```

### 添加新 RSS 源

编辑 `config/feeds.json`，添加新源：

```json
{"name": "example.com", "url": "https://example.com/feed.xml"}
```

### 代码风格

- 使用 Python 3.8+ 语法
- 遵循 [PEP 8](https://pep8.org/) 代码规范
- 使用类型注解（Type Hints）
- 函数/方法添加文档字符串（Docstring）

### 测试

运行测试：

```bash
python -m pytest tests/ -v
```

添加新测试：在 `tests/` 目录下创建 `test_*.py` 文件。

## 📝 文档更新

如果修改了功能或添加了新功能，请同步更新：

- `README.md`
- `SKILL.md`（如果涉及 Skill 功能变更）
- 代码示例

## 🔨 Code Review 流程

1. 所有 PR 需要经过至少 1 位维护者审核
2. 审核通过后，维护者会合并代码
3. 如果有修改意见，请在 PR 中回复并及时修改

## 💬 行为准则

请阅读并遵守我们的 [行为准则](CODE_OF_CONDUCT.md)。

## ❓ 有问题？

- 查看 [Issue 列表](https://github.com/huangds/ai-daily-digest/issues)
- 新建 Issue 提问
- 联系维护者：[@huangds](https://github.com/huangds)

---

再次感谢您的贡献！🙏
