---
name: ai-daily-digest
description: |
  AI 技术日报精选工具。
  触发词：/ai-digest、ai日报、生成日报、技术日报、RSS日报、今天有什么新技术、AI精选
  功能：自动采集 92 个顶级技术 RSS 源，AI 三维度评分精选 Top N，生成中文摘要和技术趋势总结。
version: "1.0.0"
author: workbuddy-user
agent_created: true
---

# AI 技术日报精选 Skill

## 触发条件

用户说以下任何一种时，立即激活此 Skill：
- `/ai-digest`
- `ai日报`、`技术日报`、`RSS日报`
- `生成日报`、`今天有什么新技术`、`AI精选`、`每日精选`
- `帮我看看今天的技术圈`

## 执行流程

### 第一步：运行 Python 采集脚本（Bash 工具）

**注意：** 优先使用当天已有的 JSON 文件（避免重复抓取）。

```bash
# 定义输出目录（默认 ~/WorkBuddy/ai-daily-digest）
OUTPUT_DIR="$HOME/WorkBuddy/ai-daily-digest"
SKILL_DIR="$HOME/.workbuddy/skills/ai-daily-digest"
DATE=$(date +%Y-%m-%d)
JSON_FILE="${OUTPUT_DIR}/rss_raw_${DATE}.json"

if [ -f "$JSON_FILE" ]; then
  echo "使用缓存：$JSON_FILE"
else
  # 运行采集脚本，输出到指定目录
  python "${SKILL_DIR}/scripts/rss_fetch.py" --hours 24 --output-dir "$OUTPUT_DIR"
fi
```

**如果用户配置了外部 API Key（开源场景）：**
```bash
# 使用 rss_digest.py（支持 GEMINI_API_KEY / OPENAI_API_KEY）
GEMINI_API_KEY="用户的Key" python "${SKILL_DIR}/scripts/rss_fetch.py" --hours 24 --output-dir "$OUTPUT_DIR"
```

### 第二步：读取 JSON 文件内容（Read 工具）

读取 `~/WorkBuddy/ai-daily-digest/rss_raw_YYYY-MM-DD.json` 文件，解析其中的 `articles` 数组。

### 第三步：AI 评分与精选（WorkBuddy 模型直接处理）

读取 JSON 后，**直接在对话中完成以下分析**（无需外部 API）：

#### 3a. 批量评分

对每篇文章从三个维度打分（1-10）：
- **相关性**：与 AI、编程、技术趋势的关联程度
- **质量**：内容深度、原创性、可读性
- **时效性**：是否涉及新技术/新事件/新发现

同时为每篇文章打上**分类标签**（如：AI/LLM、系统编程、安全、前端、产品思考、其他）和**3个关键词**。

综合得分 = (相关性 × 0.4 + 质量 × 0.4 + 时效性 × 0.2)

#### 3b. 精选 Top N（默认 Top 8，用户可指定）

从综合得分最高的文章中选出 Top 8，为每篇生成：
- **中文标题**（翻译/意译，保留原意）
- **中文摘要**（4-6 句，结构清晰，覆盖：背景→核心观点→技术细节→价值/影响）
- **推荐理由**（一句话，说明为什么这篇值得读）

#### 3c. 趋势总结

从精选文章中归纳 **2-3 个当日宏观技术趋势**，每个趋势包含：
- 趋势名称（5-10 字）
- 背景说明（2-3 句）
- 相关文章引用（1-2 篇）

### 第四步：输出格式

生成标准 Markdown 日报，结构如下：

```markdown
# 🤖 AI 技术日报精选 · YYYY-MM-DD

> 从 92 个顶级技术 RSS 源中精选，共抓取 N 篇，AI 精选 Top 8

---

## 🔥 今日技术趋势

### 趋势一：[趋势名称]
[背景说明，2-3句]
> 相关文章：《文章标题》

### 趋势二：[趋势名称]
...

---

## 📚 精选 Top 8 · 深度解读

### 1. [中文标题]
**原标题**：[英文原标题] | **来源**：source | **时间**：时间
**分类**：标签 | **关键词**：kw1, kw2, kw3
**评分**：相关性 8 · 质量 9 · 时效性 7 = 综合 8.2

**摘要：**
[4-6句中文摘要]

**推荐理由**：[一句话]

🔗 [阅读原文](链接)

---

### 2. ...

---

## 📋 今日全量文章（N 篇）

| # | 来源 | 标题 | 评分 | 时间 |
|---|------|------|------|------|
| 1 | source | [title](link) | 8.2 | 时间 |
...

---
*生成时间：本地时间 | 数据范围：最近 24 小时*
```

### 第五步：保存日报文件（可选）

将生成的日报保存为 `digest_YYYY-MM-DD.md`，路径：
`~/WorkBuddy/ai-daily-digest/digest_YYYY-MM-DD.md`

---

## 用户可配置参数

对话时用户可以说：
- `top 5` / `精选5篇` → 调整精选数量（默认8）
- `最近48小时` / `--hours 48` → 扩大时间范围
- `只看AI相关` → 过滤分类
- `保存文件` → 额外保存 Markdown 到本地

---

## 开源用户配置说明

如果用户希望使用外部 AI API（不依赖 WorkBuddy 内置模型）：

1. 安装依赖：`pip install openai`
2. 配置环境变量：
   ```bash
   # Gemini（免费额度充足）
   export GEMINI_API_KEY=AIzaSy...
   
   # 或 DeepSeek（极低价）
   export OPENAI_API_KEY=sk-...
   export OPENAI_API_BASE=https://api.deepseek.com/v1
   
   # 或任意 OpenAI 兼容接口
   export OPENAI_API_KEY=sk-...
   export OPENAI_API_BASE=https://your-api.com/v1
   export OPENAI_MODEL=gpt-4o-mini
   ```
3. 使用完整版脚本：`python rss_digest.py --hours 24 --top-n 8 --output-dir ~/WorkBuddy/ai-daily-digest`

---

## 自动化配置

在 WorkBuddy 自动化中设置每日执行：
- **名称**：AI 技术日报
- **Prompt**：`/ai-digest` 或 `帮我生成今天的 AI 技术日报精选，Top 8`
- **调度**：每天 08:00（RRULE: `FREQ=DAILY;BYHOUR=8;BYMINUTE=0`）
- **工作目录**：`~/WorkBuddy/ai-daily-digest`（生成文件输出目录）

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `rss_fetch.py` | RSS 采集器，输出 JSON（无 AI 依赖） |
| `rss_digest.py` | 完整版（含外部 AI API 评分，开源用户使用） |

**输出文件**（生成在 `~/WorkBuddy/ai-daily-digest/` 下，不在 skill 目录中）：

| 文件 | 用途 |
|------|------|
| `rss_raw_YYYY-MM-DD.json` | 每日原始数据缓存 |
| `digest_YYYY-MM-DD.md` | 每日精选日报输出 |
