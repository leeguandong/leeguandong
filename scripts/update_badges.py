#!/usr/bin/env python3
"""Scrape latest stats from Google Scholar, CSDN, OpenArt and update README badges."""

import re
import os

README_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "README.md")

SCHOLAR_USER = "on_b6MMAAAAJ"
CSDN_USERNAME = "liguandong"
OPENART_USERNAME = "leeguandong"


def get_scholar_citations() -> str | None:
    """Fetch total citation count via scholarly library."""
    try:
        from scholarly import scholarly
        author = scholarly.search_author_id(SCHOLAR_USER)
        cited = author.get("citedby")
        if cited is not None:
            return str(cited)
    except Exception as e:
        print(f"[WARN] scholarly failed: {e}")
    return None


def get_csdn_followers() -> str | None:
    """Fetch follower count from CSDN using Playwright headless browser."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"https://blog.csdn.net/{CSDN_USERNAME}", timeout=30000)
            # Wait for the achievement module to load
            page.wait_for_selector(".user-profile-statistics-num", timeout=15000)
            nums = page.query_selector_all(".user-profile-statistics-num")
            # The fans count is typically the first statistics number
            for el in nums:
                text = el.inner_text().strip()
                if text and text != "暂无" and text != "0":
                    browser.close()
                    return text
            browser.close()
    except Exception as e:
        print(f"[WARN] Playwright CSDN scrape failed: {e}")
    return None


def get_openart_downloads() -> str | None:
    """Fetch total download count from OpenArt profile page."""
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        resp = requests.get(
            f"https://openart.ai/workflows/profile/{OPENART_USERNAME}",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        match = re.search(r'downloads"\s*:\s*(\d+)', resp.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"[WARN] Failed to fetch OpenArt downloads: {e}")
    return None


def update_readme(scholar: str | None, csdn: str | None, openart: str | None):
    """Update badge values in README.md."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    if scholar:
        content = re.sub(
            r"(Google%20Scholar%20Citations-)\d+(-)",
            rf"\g<1>{scholar}\2",
            content,
        )
        print(f"[OK] Google Scholar Citations -> {scholar}")

    if csdn:
        content = re.sub(
            r"(CSDN-)\d+(%20%E5%85%B3%E6%B3%A8-)",
            rf"\g<1>{csdn}\2",
            content,
        )
        print(f"[OK] CSDN Followers -> {csdn}")

    if openart:
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
