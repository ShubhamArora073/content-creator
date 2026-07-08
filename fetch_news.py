"""
Fetches latest updates from Anthropic and Kubernetes sources.
Run daily via cron or manually before content creation.

Usage:
    python fetch_news.py
    # or via cron: 0 8 * * * cd ~/Downloads/content_creator && .venv/bin/python fetch_news.py
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

import defusedxml.ElementTree as ET

NEWS_FILE = Path(__file__).parent / "latest_news.json"

SOURCES = [
    {
        "name": "Simon Willison",
        "url": "https://simonwillison.net/atom/everything/",
        "type": "rss",
        "category": "ai",
    },
    {
        "name": "AI News (Buttondown)",
        "url": "https://buttondown.com/ainews/rss",
        "type": "rss",
        "category": "ai",
    },
    {
        "name": "Claude Code Releases",
        "url": "https://github.com/anthropics/claude-code/releases.atom",
        "type": "rss",
        "category": "ai",
    },
    {
        "name": "Kubernetes Blog",
        "url": "https://kubernetes.io/feed.xml",
        "type": "rss",
        "category": "devops",
    },
    {
        "name": "CNCF Blog",
        "url": "https://www.cncf.io/blog/feed/",
        "type": "rss",
        "category": "devops",
    },
]


def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ContentCreator/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  Failed to fetch {url}: {e}")
        return None


def parse_rss(xml_text, source_name, category, max_items=5):
    items = []
    try:
        root = ET.fromstring(xml_text)
        # Handle both RSS and Atom feeds
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        # Try RSS format
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            description = item.findtext("description", "").strip()[:300]
            if title:
                items.append({
                    "title": title,
                    "link": link,
                    "date": pub_date,
                    "description": description,
                    "source": source_name,
                    "category": category,
                })

        # Try Atom format if RSS found nothing
        if not items:
            for entry in root.findall("atom:entry", ns)[:max_items]:
                title = entry.findtext("atom:title", "", ns).strip()
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                pub_date = entry.findtext("atom:published", "", ns).strip()
                summary = entry.findtext("atom:summary", "", ns).strip()[:300]
                if title:
                    items.append({
                        "title": title,
                        "link": link,
                        "date": pub_date,
                        "description": summary,
                        "source": source_name,
                        "category": category,
                    })
    except ET.ParseError as e:
        print(f"  Parse error for {source_name}: {e}")
    return items


def parse_github_releases(json_text, source_name, category, max_items=5):
    items = []
    try:
        releases = json.loads(json_text)
        for release in releases[:max_items]:
            items.append({
                "title": f"{release.get('name', release.get('tag_name', 'Unknown'))}",
                "link": release.get("html_url", ""),
                "date": release.get("published_at", ""),
                "description": (release.get("body", "") or "")[:300],
                "source": source_name,
                "category": category,
            })
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  Parse error for {source_name}: {e}")
    return items


def fetch_all():
    all_items = []
    for source in SOURCES:
        print(f"Fetching {source['name']}...")
        raw = fetch_url(source["url"])
        if not raw:
            continue

        if source["type"] == "rss":
            items = parse_rss(raw, source["name"], source["category"])
        elif source["type"] == "github_releases":
            items = parse_github_releases(raw, source["name"], source["category"])
        else:
            continue

        all_items.extend(items)
        print(f"  Got {len(items)} items")

    return all_items


def main():
    print(f"Fetching news at {datetime.now().isoformat()}")
    items = fetch_all()

    output = {
        "fetched_at": datetime.now().isoformat(),
        "total_items": len(items),
        "items": items,
    }

    NEWS_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved {len(items)} items to {NEWS_FILE}")

    # Print summary
    by_category = {}
    for item in items:
        cat = item["category"]
        by_category.setdefault(cat, []).append(item)

    print("\nSummary:")
    for cat, cat_items in by_category.items():
        print(f"  {cat}: {len(cat_items)} items")
        for item in cat_items[:3]:
            print(f"    - {item['title']}")


if __name__ == "__main__":
    main()
