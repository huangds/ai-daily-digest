# AI 技术日报精选 (AI Daily Digest)

自动采集 92 个顶级技术 RSS 源，通过 AI 三维度评分精选优质内容，生成中文技术日报。

## ✨ 功能特性

- **92 个顶级 RSS 源**：来自 Hacker News Popularity 榜单的技术博客
- **AI 三维度评分**：相关性、质量、时效性（1-10 分）
- **智能精选**：自动筛选 Top N 文章（默认 Top 8）
- **中文摘要**：AI 生成中文标题翻译和结构化摘要
- **趋势总结**：归纳当日技术圈宏观趋势
- **双重模式**：
  - **WorkBuddy 内置模型**（推荐）：无需 API Key
  - **外部 API**：支持 Gemini、DeepSeek、OpenAI 兼容接口

## 🚀 快速开始

### 方式一：通过 WorkBuddy Skill（推荐）

1. 将本 skill 放入 `~/.workbuddy/skills/ai-daily-digest/`
2. 在 WorkBuddy 对话中说：`/ai-digest` 或 `生成今天的 AI 技术日报`
3. WorkBuddy 会自动执行采集、评分、生成日报

### 方式二：命令行使用

**步骤 1：安装依赖**

```bash
pip install requests
```

**步骤 2：运行采集脚本**

```bash
# 采集最近 24 小时的资讯，输出 JSON
python scripts/rss_fetch.py --hours 24

# 输出文件：scripts/rss_raw_YYYY-MM-DD.json
```

**步骤 3：AI 评分与生成日报**

在 WorkBuddy 对话中说：`/ai-digest`，它会自动读取 JSON 并生成日报。

**或使用外部 API（开源用户）**

```bash
# 配置 API Key
export GEMINI_API_KEY="AIzaSy..."

# 运行完整版（含 AI 评分）
python scripts/rss_digest.py --hours 24 --top-n 8
```

## 📁 项目结构

```
ai-daily-digest/
├── SKILL.md                   # WorkBuddy Skill 定义
├── README.md                  # 本文档
├── LICENSE                    # MIT 开源协议
├── .env.example               # 环境变量模板
├── .gitignore                 # Git 忽略规则
├── requirements.txt           # Python 依赖
├── config/
│   └── feeds.json             # 92 个 RSS 源配置
├── scripts/
│   ├── rss_fetch.py          # 纯采集器（输出 JSON）
│   └── rss_digest.py         # AI 评分版（需外部 API）
└── example_output/            # 示例输出
    └── digest_2026-06-07.md # 示例日报
```

## 🔧 配置说明

### RSS 源配置

编辑 `config/feeds.json`，添加或修改 RSS 源：

```json
[
  {"name": "example.com", "url": "https://example.com/feed.xml"},
  ...
]
```

### AI 评分维度

- **相关性**（权重 40%）：与 AI、编程、技术趋势的关联程度
- **质量**（权重 40%）：内容深度、原创性、可读性
- **时效性**（权重 20%）：是否涉及新技术/新事件/新发现

综合得分 = (相关性 × 0.4 + 质量 × 0.4 + 时效性 × 0.2)

### 用户可配置参数

对话时可以说：
- `top 5` / `精选 5 篇` → 调整精选数量（默认 8）
- `最近 48 小时` / `--hours 48` → 扩大时间范围
- `只看 AI 相关` → 过滤分类
- `保存文件` → 额外保存 Markdown 到本地

## 🌐 外部 API 配置（可选）

如果不使用 WorkBuddy 内置模型，可以配置外部 AI API：

### Gemini（推荐，免费额度充足）

```bash
export GEMINI_API_KEY="AIzaSy..."
python scripts/rss_digest.py --hours 24
```

获取 API Key：https://aistudio.google.com/apikey

### DeepSeek（极低价）

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_API_BASE="https://api.deepseek.com/v1"
export OPENAI_MODEL="deepseek-chat"
python scripts/rss_digest.py --hours 24
```

### 任意 OpenAI 兼容接口

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_API_BASE="https://your-api.com/v1"
export OPENAI_MODEL="gpt-4o-mini"
python scripts/rss_digest.py --hours 24
```

## 📊 输出格式

生成的日报包含：

1. **今日技术趋势**：2-3 个宏观趋势，每个包含背景说明和相关文章引用
2. **精选 Top N · 深度解读**：每篇包含中文标题、摘要、推荐理由、评分
3. **今日全量文章**：表格形式展示所有文章及其评分

示例输出：`example_output/digest_2026-06-07.md`

## 🤖 自动化配置

在 WorkBuddy 中设置每日自动执行：

1. 打开自动化设置
2. 创建新任务：
   - **名称**：AI 技术日报
   - **Prompt**：`/ai-digest` 或 `帮我生成今天的 AI 技术日报精选，Top 8`
   - **调度**：每天 08:00
   - **工作目录**：`~/.workbuddy/skills/ai-daily-digest`

## 📝 依赖项

- Python 3.8+
- requests（HTTP 请求）
- openai（可选，使用外部 API 时需要）

安装：

```bash
pip install requests openai
```

## 📄 许可证

MIT License —— 可自由使用、修改和分发。

## 🙏 致谢

- RSS 源来自 [Hacker News Popularity](https://refactoringenglish.com/tools/hn-popularity/) 榜单
- 感谢所有提供优质技术内容的技术博主

## 🐛 问题反馈

遇到问题？欢迎提交 Issue 或 Pull Request！

---

**作者**：WorkBuddy User  
**版本**：1.0.0  
**更新时间**：2026-06-07
