#!/usr/bin/env python3
"""
RSS Daily Fetcher - Pure Data Edition
Fetches RSS feeds from config/feeds.json, filters articles from the last N hours,
and outputs structured JSON for AI processing.

Usage:
  python rss_fetch.py                     # default 24h
  python rss_fetch.py --hours 48          # last 48 hours
  python rss_fetch.py --output out.json   # custom output path
  python rss_fetch.py --print             # output to stdout
  python rss_fetch.py --feeds custom.json
"""

import sys, io, re, json, os, ssl, socket, argparse
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
MAX_WORKERS = 12
TIMEOUT     = 15
SUMMARY_MAX = 500

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_FEEDS = os.path.join(PROJECT_DIR, "config", "feeds.json")


# ============================================================
# Utility functions
# ============================================================
def strip_html(text):
    if not text:
        return ""
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<(script|style)[^>]*>.*?</(script|style)>',
                  ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    for old, new in [('&amp;',  '&'), ('&lt;',  '<'), ('&gt;',  '>'),
                     ('&quot;', '"'), ('&#39;', "'"), ('&nbsp;', ' ')]:
        text = text.replace(old, new)
    return text


def get_tag(xml, tag):
    m = re.search(rf'<{tag}[^>]*><!\[CDATA\[(.*?)\]\]></{tag}>', xml, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', xml, re.DOTALL)
    if m:
        return strip_html(m.group(1)).strip()
    return ""


def get_attr(xml, tag, attr):
    m = re.search(rf'<{tag}[^>]*\s{attr}=["\']([^"\']+)["\'][^>]*>', xml)
    if m:
        return m.group(1).strip()
    return ""


def parse_date(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    try:
        return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except Exception:
        pass
    for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
        try:
            s = date_str[:25] if len(date_str) > 25 else date_str
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
    return None


# ============================================================
# RSS Parsing
# ============================================================
def parse_feed_entries(xml_text, source_name):
    items = []
    if "<entry" in xml_text:
        for entry in re.findall(r'<entry[^>]*>(.*?)</entry>', xml_text, re.DOTALL):
            title   = get_tag(entry, 'title')
            link    = get_attr(entry, 'link', 'href')
            if not link:
                link = get_tag(entry, 'link')
            updated = get_tag(entry, 'updated') or get_tag(entry, 'published')
            summary = get_tag(entry, 'summary') or get_tag(entry, 'content') or ""
            items.append({
                "title":    title,
                "link":     link,
                "pub_date": parse_date(updated),
                "summary":  summary[:SUMMARY_MAX],
                "source":   source_name,
            })
    elif "<item" in xml_text:
        for item in re.findall(r'<item[^>]*>(.*?)</item>', xml_text, re.DOTALL):
            title    = get_tag(item, 'title')
            link     = get_tag(item, 'link') or ""
            guid_val = get_attr(item, 'guid', 'isPermaLink')
            if not link and guid_val not in ("true", "false"):
                link = guid_val
            if link and not link.startswith("http"):
                link = ""
            pub_date = get_tag(item, 'pubDate') or get_tag(item, 'dc:date')
            summary  = get_tag(item, 'description') or get_tag(item, 'content:encoded') or ""
            items.append({
                "title":    title,
                "link":     link,
                "pub_date": parse_date(pub_date),
                "summary":  summary[:SUMMARY_MAX],
                "source":   source_name,
            })
    return items


# ============================================================
# Network
# ============================================================
def fetch_feed(feed):
    result = {"name": feed["name"], "url": feed["url"],
              "ok": False, "items": [], "error": None}
    try:
        ctx = ssl.create_default_context()
        req = Request(feed["url"], headers={"User-Agent": "Mozilla/5.0 (RSS-Fetcher)"})
        with urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        items = parse_feed_entries(raw, feed["name"])
        result["items"] = items
        result["ok"]    = True
    except HTTPError as e:
        result["error"] = "HTTP %d" % e.code
    except URLError as e:
        result["error"] = "URL Error: %s" % str(e.reason)
    except ssl.SSLError as e:
        result["error"] = "SSL Error: %s" % str(e)
    except socket.timeout:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)[:200]
    return result


# ============================================================
# Main workflow
# ============================================================
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
        if a["pub_date"] and a["pub_date"] >= cutoff:
            filtered.append(a)
        else:
            dropped += 1
    print("[Filter] Kept %d recent articles (within %dh), dropped %d older" % (len(filtered), hours, dropped), flush=True)
    return filtered


def build_output(articles, successes, failures, hours):
    articles.sort(key=lambda x: x["pub_date"] or datetime.min.replace(tzinfo=timezone.utc),
                  reverse=True)
    for i, a in enumerate(articles):
        a["id"] = i + 1
        a["title"] = (a["title"] or "")[:300]
        if a["pub_date"]:
            a["pub_date"] = a["pub_date"].isoformat()
    return {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "hours":          hours,
        "total_articles": len(articles),
        "sources_ok":     len(successes),
        "sources_fail":   len(failures),
        "failed_sources": [{"name": f["name"], "url": f["url"], "error": f["error"]}
                          for f in failures],
        "articles":       articles,
    }


def main():
    parser = argparse.ArgumentParser(description="RSS Daily Fetcher")
    parser.add_argument("--hours",  type=int, default=24,
                        help="Hours to look back (default: 24)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output JSON file path")
    parser.add_argument("--print",  action="store_true",
                        help="Print to stdout instead of file")
    parser.add_argument("--feeds", type=str, default=DEFAULT_FEEDS,
                        help="Path to feeds config JSON")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Directory for output files (default: WorkBuddy/ai-daily-digest)")
    args = parser.parse_args()

    feeds = load_feeds(args.feeds)

    print("\n[Start] Fetching %d RSS feeds concurrently...\n" % len(feeds), flush=True)
    t0 = datetime.now()
    successes, failures = fetch_all(feeds)
    elapsed = (datetime.now() - t0).total_seconds()

    all_articles = []
    for res in successes:
        for item in res["items"]:
            item["source"] = res["name"]
            all_articles.append(item)

    print("\n[Stats] Success: %d/%d, Total items: %d, Time: %.1fs" %
          (len(successes), len(feeds), len(all_articles), elapsed), flush=True)

    recent  = filter_by_hours(all_articles, args.hours)
    output = build_output(recent, successes, failures, args.hours)

    if args.print:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if args.output:
            out_path = args.output
        else:
            out_dir = args.output_dir or os.path.join(
                os.path.expanduser("~"), "WorkBuddy", "ai-daily-digest")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(
                out_dir, "rss_raw_%s.json" % datetime.now().strftime("%Y-%m-%d"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print("\n[Done] Output saved to: %s" % out_path, flush=True)
        print("       %d articles, %d/%d sources OK" %
              (output["total_articles"], output["sources_ok"],
               output["sources_ok"] + output["sources_fail"]),
              flush=True)


if __name__ == "__main__":
    main()
