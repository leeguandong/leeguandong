#!/usr/bin/env python3
"""Scrape latest stats from Google Scholar, CSDN, OpenArt and update README badges."""

import re
import os
import requests
from bs4 import BeautifulSoup

README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

SCHOLAR_USER = "on_b6MMAAAAJ"
CSDN_USERNAME = "liguandong"
OPENART_USERNAME = "leeguandong"


def get_scholar_citations() -> str | None:
    """Fetch total citation count from Google Scholar."""
    url = f"https://scholar.google.com/citations?user={SCHOLAR_USER}&hl=en"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Citation count is in the stats table, first row, second cell
        table = soup.find("table", id="gsc_rsb_st")
        if table:
            rows = table.find_all("tr")
            if len(rows) > 1:
                cells = rows[1].find_all("td")
                if len(cells) >= 2:
                    return cells[1].text.strip()
    except Exception as e:
        print(f"[WARN] Failed to fetch Google Scholar citations: {e}")
    return None


def get_csdn_followers() -> str | None:
    """Fetch follower count from CSDN blog API."""
    url = f"https://blog.csdn.net/community/home-api/v1/get-blog-info?blogUsername={CSDN_USERNAME}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        fans = data.get("data", {}).get("fanCount")
        if fans is not None:
            return str(fans)
    except Exception as e:
        print(f"[WARN] CSDN API failed, trying page scrape: {e}")

    # Fallback: scrape the blog page
    try:
        resp = requests.get(
            f"https://blog.csdn.net/{CSDN_USERNAME}", headers=HEADERS, timeout=30
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        fans_el = soup.select_one(".user-profile-statistics-num")
        if fans_el:
            return fans_el.text.strip()
    except Exception as e:
        print(f"[WARN] Failed to scrape CSDN followers: {e}")
    return None


def get_openart_downloads() -> str | None:
    """Fetch total download count from OpenArt profile."""
    url = f"https://openart.ai/workflows/profile/{OPENART_USERNAME}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        text = resp.text
        # Try to find download count in page content or JSON data
        match = re.search(r'"totalDownloads"\s*:\s*(\d+)', text)
        if match:
            return match.group(1)
        match = re.search(r'"download_count"\s*:\s*(\d+)', text)
        if match:
            return match.group(1)
        # Try visible text pattern
        soup = BeautifulSoup(text, "html.parser")
        for el in soup.find_all(string=re.compile(r"[\d,]+\s*downloads", re.I)):
            m = re.search(r"([\d,]+)", el)
            if m:
                return m.group(1).replace(",", "")
    except Exception as e:
        print(f"[WARN] Failed to fetch OpenArt downloads: {e}")
    return None


def update_readme(scholar: str | None, csdn: str | None, openart: str | None):
    """Update badge values in README.md."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    if scholar:
        # Match: Google%20Scholar%20Citations-{number}-yellow
        content = re.sub(
            r"(Google%20Scholar%20Citations-)\d+(-)",
            rf"\g<1>{scholar}\2",
            content,
        )
        print(f"[OK] Google Scholar Citations -> {scholar}")

    if csdn:
        # Match: CSDN-{number}%20%E5%85%B3%E6%B3%A8-red
        # URL-encode the follower count for the badge
        content = re.sub(
            r"(CSDN-)\d+(%20%E5%85%B3%E6%B3%A8-)",
            rf"\g<1>{csdn}\2",
            content,
        )
        print(f"[OK] CSDN Followers -> {csdn}")

    if openart:
        # Match: OpenArt%20Downloads-{number}-green
        content = re.sub(
            r"(OpenArt%20Downloads-)\d+(-)",
            rf"\g<1>{openart}\2",
            content,
        )
        print(f"[OK] OpenArt Downloads -> {openart}")

    if content != original:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("[OK] README.md updated")
    else:
        print("[INFO] No changes needed")


def main():
    print("Fetching latest stats...")
    scholar = get_scholar_citations()
    csdn = get_csdn_followers()
    openart = get_openart_downloads()

    print(f"\nResults: Scholar={scholar}, CSDN={csdn}, OpenArt={openart}")
    update_readme(scholar, csdn, openart)


if __name__ == "__main__":
    main()
