#!/usr/bin/env python3
"""
RSS AI Digest - Full Version (with AI scoring, summary, trend analysis)

Supports:
  - Gemini Flash (free):    set GEMINI_API_KEY
  - OpenAI compatible:     set OPENAI_API_KEY + OPENAI_API_BASE (optional)

For WorkBuddy users: run rss_fetch.py first to generate JSON,
then let WorkBuddy AI process the JSON (no API key needed).

Usage:
  export GEMINI_API_KEY=your_key    # or
  export OPENAI_API_KEY=your_key
  python rss_digest.py --hours 24 --top-n 10
"""

import sys, io, re, json, os, ssl, socket, argparse, time
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================
# Config (can override via env vars)
# ============================================================
HOURS       = int(os.environ.get("DIGEST_HOURS", 24))
TOP_N        = int(os.environ.get("DIGEST_TOP_N", 10))
MAX_WORKERS = 10
TIMEOUT      = 15

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR  = os.path.dirname(SCRIPT_DIR)
DEFAULT_FEEDS = os.path.join(PROJECT_DIR, "config", "feeds.json")

# AI config
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL    = os.environ.get("OPENAI_MODEL", "")
GEMINI_URL     = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Categories
CATEGORIES = {
    "ai-ml":       {"emoji": "[AI]",  "label": "AI / ML"},
    "security":    {"emoji": "[SEC]", "label": "Security"},
    "engineering": {"emoji": "[ENG]", "label": "Engineering"},
    "tools":       {"emoji": "[TOOL]","label": "Tools / Open Source"},
    "opinion":     {"emoji": "[IDEA]", "label": "Opinion / Misc"},
    "other":       {"emoji": "[MISC]","label": "Other"},
}


# ============================================================
# Utility (same as rss_fetch.py)
# ============================================================
def strip_html(text):
    if not text: return ""
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<(script|style)[^>]*>.*?</(script|style)>',
                  ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    for old, new in [('&amp;','&'),('&lt;','<'),('&gt;','>'),
                     ('&quot;','"'),('&#39;',"'"),('&nbsp;',' ')]:
        text = text.replace(old, new)
    return text

def get_tag(xml, tag):
    m = re.search(rf'<{tag}[^>]*><!\[CDATA\[(.*?)\]\]></{tag}>', xml, re.DOTALL)
    if m: return m.group(1).strip()
    m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', xml, re.DOTALL)
    return strip_html(m.group(1)).strip() if m else ""

def get_attr(xml, tag, attr):
    m = re.search(rf'<{tag}[^>]*\s{attr}=["\']([^"\']+)["\'][^>]*>', xml)
    return m.group(1).strip() if m else ""

def parse_date(date_str):
    if not date_str: return None
    date_str = date_str.strip()
    try: return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except: pass
    for fmt in ["%Y-%m-%dT%H:%M:%S%z","%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f%z","%Y-%m-%dT%H:%M:%S","%Y-%m-%d"]:
        try:
            s = date_str[:25] if len(date_str) > 25 else date_str
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except: pass
    return None

def parse_feed_entries(xml_text, source_name):
    items = []
    if "<entry" in xml_text:
        for entry in re.findall(r'<entry[^>]*>(.*?)</entry>', xml_text, re.DOTALL):
            title   = get_tag(entry, 'title')
            link    = get_attr(entry, 'link', 'href')
            if not link: link = get_tag(entry, 'link')
            updated = get_tag(entry, 'updated') or get_tag(entry, 'published')
            summary = get_tag(entry, 'summary') or get_tag(entry, 'content') or ""
            items.append({"title": title, "link": link,
                          "pub_date": parse_date(updated),
                          "summary": summary[:500], "source": source_name})
    elif "<item" in xml_text:
        for item in re.findall(r'<item[^>]*>(.*?)</item>', xml_text, re.DOTALL):
            title    = get_tag(item, 'title')
            link     = get_tag(item, 'link') or ""
            guid_val = get_attr(item, 'guid', 'isPermaLink')
            if not link and guid_val not in ("true", "false"): link = guid_val
            if link and not link.startswith("http"): link = ""
            pub_date = get_tag(item, 'pubDate') or get_tag(item, 'dc:date')
            summary  = get_tag(item, 'description') or get_tag(item, 'content:encoded') or ""
            items.append({"title": title, "link": link,
                          "pub_date": parse_date(pub_date),
                          "summary": summary[:500], "source": source_name})
    return items

def fetch_feed(feed):
    result = {"name": feed["name"], "url": feed["url"], "ok": False, "items": [], "error": None}
    try:
        ctx = ssl.create_default_context()
        req = Request(feed["url"], headers={"User-Agent": "Mozilla/5.0 (RSS-Fetcher)"})
        with urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        items = parse_feed_entries(raw, feed["name"])
        result["items"] = items
        result["ok"]    = True
    except HTTPError as e: result["error"] = "HTTP %d" % e.code
    except URLError as e:  result["error"] = "URL Error: %s" % str(e.reason)
    except ssl.SSLError as e: result["error"] = "SSL Error: %s" % str(e)
    except socket.timeout:    result["error"] = "Timeout"
    except Exception as e:      result["error"] = str(e)[:200]
    return result

def load_feeds(feeds_path):
    with open(feeds_path, encoding="utf-8") as f:
        feeds = json.load(f)
    print("[Config] Loaded %d RSS feeds from %s" % (len(feeds), feeds_path), flush=True)
    return feeds

def fetch_all(feeds):
    successes, failures = [], []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(fetch_feed, f): f for f in feeds}
        for fut in as_completed(futures):
            res = fut.result()
            if res["ok"]:
                successes.append(res)
                print("  OK   %-35s -> %3d items" % (res["name"], len(res["items"])), flush=True)
            else:
                failures.append(res)
                print("  FAIL %-35s -> %s" % (res["name"], res["error"]), flush=True)
    return successes, failures

def filter_by_hours(articles, hours):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    filtered, dropped = [], 0
    for a in articles:
        if a["pub_date"] and a["pub_date"] >= cutoff: filtered.append(a)
        else: dropped += 1
    print("[Filter] Kept %d recent (within %dh), dropped %d older" % (len(filtered), hours, dropped), flush=True)
    return filtered


# ============================================================
# AI Functions
# ============================================================
def call_gemini(prompt):
    """Call Gemini Flash API."""
    url = "%s?key=%s" % (GEMINI_URL, GEMINI_API_KEY)
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048}
    }).encode("utf-8")
    req = Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return "[AI Error: %s]" % str(e)


def call_openai(prompt):
    """Call OpenAI-compatible API."""
    from urllib.request import Request as RQ
    url = OPENAI_API_BASE.rstrip("/") + "/chat/completions"
    model = OPENAI_MODEL or "gpt-4o-mini"
    payload = json.dumps({
        "model":    model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens":  2048,
    }).encode("utf-8")
    req = RQ(url, data=payload, headers={
        "Content-Type":  "application/json",
        "Authorization": "Bearer %s" % OPENAI_API_KEY,
    })
    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return "[AI Error: %s]" % str(e)


def ai_score_articles(articles, batch_size=10):
    """Score articles via AI in batches. Adds score fields to each article."""
    if not GEMINI_API_KEY and not OPENAI_API_KEY:
        print("[AI] No API key - skipping AI scoring", flush=True)
        return articles

    total = len(articles)
    for start in range(0, total, batch_size):
        batch = articles[start:start + batch_size]
        items_text = ""
        for i, a in enumerate(batch):
            items_text += "%d. [%s] %s\n   Summary: %s\n\n" % (
                i + 1, a["source"], a["title"], (a["summary"] or "")[:200])

        prompt = """You are a tech news editor. For each article below, rate on 3 dimensions (1-10, integer):
- relevance: how relevant to AI/tech community (10 = very relevant)
- quality: content depth and originality (10 = high quality)
- timeliness: how new/novel the information is (10 = very timely)

Also assign a category (ai-ml / security / engineering / tools / opinion / other)
and 3 keywords.

Output format (one line per article, no extra text):
ID | relevance | quality | timeliness | category | keywords

Articles:
%s""" % items_text

        print("[AI] Scoring batch %d-%d / %d..." % (start + 1, min(start + batch_size, total), total), flush=True)
        result = ""
        if GEMINI_API_KEY:
            result = call_gemini(prompt)
        else:
            result = call_openai(prompt)

        # Parse result
        for line in result.strip().split("\n"):
            parts = re.split(r'\s*\|\s*', line.strip())
            if len(parts) < 6: continue
            try:
                idx = int(parts[0].strip()) - 1
                if 0 <= idx < len(batch):
                    batch[idx]["relevance"]  = max(1, min(10, int(parts[1].strip())))
                    batch[idx]["quality"]     = max(1, min(10, int(parts[2].strip())))
                    batch[idx]["timeliness"]  = max(1, min(10, int(parts[3].strip())))
                    batch[idx]["category"]    = parts[4].strip()
                    batch[idx]["keywords"]    = [k.strip() for k in parts[5].split(",")[:3]]
                    batch[idx]["score"] = (
                        batch[idx]["relevance"] * 0.4 +
                        batch[idx]["quality"]    * 0.4 +
                        batch[idx]["timeliness"]  * 0.2)
            except Exception: pass

        time.sleep(1)  # rate limit

    return articles


def ai_summarize_top(articles, top_n):
    """Generate Chinese summary for top articles."""
    if not GEMINI_API_KEY and not OPENAI_API_KEY:
        return articles

    top = sorted(articles, key=lambda x: x.get("score", 0), reverse=True)[:top_n]
    for i, a in enumerate(top):
        prompt = """Please process this article and return ONLY the following (in Chinese):

1. Chinese title translation (one sentence)
2. 4-6 sentence Chinese summary (concise, informative)
3. One-sentence recommendation reason

Format:
TITLE: <Chinese title>
SUMMARY: <4-6 sentences>
REASON: <one sentence>

Article:
Title: %s
Source: %s
Summary: %s""" % (a["title"], a["source"], (a["summary"] or "")[:400])

        print("[AI] Summarizing article %d/%d: %s..." % (i + 1, top_n, a["title"][:40]), flush=True)
        result = ""
        if GEMINI_API_KEY:
            result = call_gemini(prompt)
        else:
            result = call_openai(prompt)

        a["chinese_title"] = ""
        a["chinese_summary"] = ""
        a["recommend_reason"] = ""
        for line in result.strip().split("\n"):
            if line.startswith("TITLE:"):    a["chinese_title"]     = line[6:].strip()
            if line.startswith("SUMMARY:"): a["chinese_summary"]  = line[8:].strip()
            if line.startswith("REASON:"):   a["recommend_reason"] = line[7:].strip()
        time.sleep(1)

    return articles


def ai_trend_analysis(articles, top_n):
    """Generate trend analysis from top articles."""
    if not GEMINI_API_KEY and not OPENAI_API_KEY:
        return ""

    top = sorted(articles, key=lambda x: x.get("score", 0), reverse=True)[:top_n]
    items_text = "\n".join(["- [%s] %s" % (a["source"], a["title"]) for a in top])

    prompt = """Based on the following tech articles published today, identify 2-3 major tech trends.
For each trend provide:
1. A short name (3-6 words)
2. Background context (2-3 sentences)
3. Related article IDs

Output in Chinese. Format:
TREND: <name>
BACKGROUND: <context>
RELATED: <article IDs>

Articles:
%s""" % items_text

    print("[AI] Generating trend analysis...", flush=True)
    if GEMINI_API_KEY:
        return call_gemini(prompt)
    else:
        return call_openai(prompt)


# ============================================================
# Output: Markdown Digest
# ============================================================
def generate_markdown(articles, hours, top_n, trend_text):
    """Generate full Markdown digest."""
    now = datetime.now(timezone.utc)
    lines = []
    lines.append("# 📰 AI 技术日报精选\n")
    lines.append("> 生成时间：%s  |  时间范围：最近 %d 小时  |  文章总数：%d\n" %
                (now.strftime("%Y-%m-%d %H:%M UTC"), hours, len(articles)))

    # Trend analysis
    if trend_text:
        lines.append("## 🔥 今日技术趋势\n")
        lines.append(trend_text)
        lines.append("")

    # Top N articles
    top = sorted(articles, key=lambda x: x.get("score", 0), reverse=True)[:top_n]
    lines.append("## 🏆 精选 Top %d\n" % len(top))
    for i, a in enumerate(top):
        score = a.get("score", 0)
        cat = CATEGORIES.get(a.get("category", "other"), CATEGORIES["other"])
        lines.append("### %s %d. %s\n" % (cat["emoji"], i + 1, a["chinese_title"] or a["title"]))
        lines.append("- **原标题：** %s" % a["title"])
        lines.append("- **来源：** %s" % a["source"])
        lines.append("- **综合评分：** %.1f (相关性:%d 质量:%d 时效性:%d)" %
                    (score, a.get("relevance", 0), a.get("quality", 0), a.get("timeliness", 0)))
        if a.get("keywords"):
            lines.append("- **关键词：** %s" % ", ".join(a["keywords"]))
        lines.append("- **推荐理由：** %s" % (a.get("recommend_reason", "")))
        if a.get("chinese_summary"):
            lines.append("- **摘要：** %s" % a["chinese_summary"])
        lines.append("- 🔗 [%s](%s)" % (a["title"], a["link"]))
        lines.append("")

    # Full list
    lines.append("## 📋 完整文章列表\n")
    for i, a in enumerate(articles):
        lines.append("%d. **[%s]** [%s](%s)  " %
                    (i + 1, a["source"], a["title"], a["link"]))
        if a.get("score"):
            lines.append("  *评分: %.1f*" % a["score"])
        lines.append("")

    return "\n".join(lines)


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="RSS AI Digest")
    parser.add_argument("--hours",   type=int, default=HOURS,   help="Hours to look back")
    parser.add_argument("--top-n",  type=int, default=TOP_N,    help="Number of top articles to summarize")
    parser.add_argument("--output",  type=str, default=None,          help="Output Markdown file path")
    parser.add_argument("--no-ai",  action="store_true",           help="Skip AI (output raw digest)")
    parser.add_argument("--feeds",   type=str, default=DEFAULT_FEEDS, help="Feeds config JSON path")
    args = parser.parse_args()

    # Load & fetch
    feeds = load_feeds(args.feeds)
    print("\n[Start] Fetching %d RSS feeds concurrently...\n" % len(feeds), flush=True)
    t0 = time.time()
    successes, failures = fetch_all(feeds)
    elapsed = time.time() - t0

    all_articles = []
    for res in successes:
        for item in res["items"]:
            item["source"] = res["name"]
            all_articles.append(item)

    print("\n[Stats] Success: %d/%d, Total: %d items, Time: %.1fs" %
          (len(successes), len(feeds), len(all_articles), elapsed), flush=True)

    recent = filter_by_hours(all_articles, args.hours)
    recent.sort(key=lambda x: x["pub_date"] or datetime.min.replace(tzinfo=timezone.utc),
                  reverse=True)

    # AI processing
    trend_text = ""
    if not args.no_ai:
        recent = ai_score_articles(recent)
        recent = ai_summarize_top(recent, args.top_n)
        trend_text = ai_trend_analysis(recent, args.top_n)
    else:
        print("[AI] Skipped (--no-ai)", flush=True)

    # Output
    md = generate_markdown(recent, args.hours, args.top_n, trend_text)
    if args.output:
        out_path = args.output
    else:
        out_path = os.path.join(os.getcwd(), "digest_%s.md" % datetime.now().strftime("%Y-%m-%d"))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print("\n[Done] Digest saved to: %s" % out_path, flush=True)
    print("       %d articles, Top %d summarized" % (len(recent), args.top_n), flush=True)


if __name__ == "__main__":
    main()
