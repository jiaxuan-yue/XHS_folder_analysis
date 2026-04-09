"""Crawl individual XHS note pages to extract text content."""

import time
from typing import Dict, Optional

from playwright.sync_api import Page

from utils.logger import get_logger

logger = get_logger(__name__)


def crawl_note(page: Page, note_url: str, delay: float = 2.0) -> Dict:
    """Crawl a single note page and extract its text content.

    Args:
        page: Authenticated Playwright Page.
        note_url: Full URL of the note.
        delay: Delay after page load to ensure content renders.

    Returns:
        Dict with keys: url, title, text_content, author, note_id.
    """
    logger.info(f"Crawling note: {note_url}")
    page.goto(note_url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(int(delay * 1000))

    result = {
        "url": note_url,
        "title": "",
        "text_content": "",
        "author": "",
        "note_id": "",
    }

    # Extract title
    title_selectors = [
        "#detail-title",
        ".title",
        ".note-title",
        "h1",
    ]
    for sel in title_selectors:
        el = page.query_selector(sel)
        if el:
            text = el.inner_text().strip()
            if text:
                result["title"] = text
                break

    # Extract main text content
    content_selectors = [
        "#detail-desc .note-text",
        "#detail-desc",
        ".note-content .content",
        ".note-text",
        ".desc",
    ]
    for sel in content_selectors:
        el = page.query_selector(sel)
        if el:
            text = el.inner_text().strip()
            if text:
                result["text_content"] = text
                break

    # If still no content, try grabbing all text from note detail area
    if not result["text_content"]:
        detail = page.query_selector(".note-detail, .note-container, #noteContainer")
        if detail:
            result["text_content"] = detail.inner_text().strip()

    # Extract author
    author_selectors = [
        ".author-container .username",
        ".user-nickname",
        ".name",
        ".author .name",
    ]
    for sel in author_selectors:
        el = page.query_selector(sel)
        if el:
            text = el.inner_text().strip()
            if text:
                result["author"] = text
                break

    # Extract note_id from URL
    import re
    for pattern in [r"/explore/([a-f0-9]+)", r"/discovery/item/([a-f0-9]+)", r"/note/([a-f0-9]+)"]:
        m = re.search(pattern, note_url)
        if m:
            result["note_id"] = m.group(1)
            break

    content_len = len(result["text_content"])
    logger.info(f"Extracted note '{result['title'][:50]}...' ({content_len} chars)")
    return result
