---
name: Pull Request
description: 提交 Pull Request 的模板
title: "[Type] 简短描述"
labels: []
assignees: []
body:
  - type: markdown
    attributes:
      value: |
        感谢你为 AI Daily Digest 贡献力量！请填写以下信息，帮助我们快速 Review。🚀

  - type: dropdown
    id: type
    attributes:
      label: 🏷️ PR 类型
      description: 这个 PR 属于哪种类型？
      options:
        - feat - 新功能
        - fix - Bug 修复
        - docs - 文档更新
        - style - 代码格式（不影响功能）
        - refactor - 重构
        - test - 测试相关
        - chore - 构建/工具相关
        - perf - 性能优化
    validations:
      required: true

  - type: input
    id: issue-link
    attributes:
      label: 🔗 关联的 Issue
      description: 如果这个 PR 解决了某个 Issue，请填写（例如：Closes #12）
      placeholder: "Closes #12 或 Fixes #34"

  - type: textarea
    id: description
    attributes:
      label: 📋 变更描述
      description: 详细描述这个 PR 做了什么修改
      placeholder: |
        ## 修改内容
        - 添加了 XXX 功能
        - 修复了 XXX Bug
        - 优化了 XXX 性能

        ## 实现思路
        （简要说明技术实现方案）
    validations:
      required: true

  - type: textarea
    id: testing
    attributes:
      label: ✅ 测试情况
      description: 描述你做了哪些测试，确保修改可用
      placeholder: |
        - [ ] 运行了现有测试：`python -m pytest tests/`
        - [ ] 手动测试了新功能
        - [ ] 测试了边缘情况（Edge Cases）
        - [ ] 更新了相关文档

  - type: textarea
    id: screenshots
    attributes:
      label: 📷 截图/录屏
      description: 如果涉及 UI 变更或可视化内容，请附上截图（可选）
      placeholder: "拖拽图片到此处上传"

  - type: textarea
    id: checklist
    attributes:
      label: ✅ 提交前检查清单
      description: 确认以下内容已完成
      value: |
        - [ ] 代码遵循项目代码风格
        - [ ] 添加了必要的注释
        - [ ] 更新了相关文档（README.md / SKILL.md 等）
        - [ ] 添加了测试（如果适用）
        - [ ] 所有测试通过
        - [ ] 提交信息遵循 Conventional Commits 规范
    validations:
      required: true

  - type: checkboxes
    id: terms
    attributes:
      label: ✅ 确认
      options:
        - label: 我已阅读并遵守 [行为准则](https://github.com/huangds/ai-daily-digest/blob/main/CODE_OF_CONDUCT.md)
          required: true
        - label: 我确认代码是我原创的，或已获得合法授权
          required: true
