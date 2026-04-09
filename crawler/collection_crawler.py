"""Crawl a public XHS collection page to extract all note metadata."""

import re
import time
from typing import List, Dict, Optional

from playwright.sync_api import Page

from utils.logger import get_logger

logger = get_logger(__name__)

XHS_BASE_URL = "https://www.xiaohongshu.com"


def crawl_collection(
    page: Page,
    collection_url: str,
    scroll_times: int = 10,
    delay: float = 2.0,
) -> List[Dict]:
    """Crawl a collection page and extract all note metadata.

    Args:
        page: Authenticated Playwright Page.
        collection_url: URL of the XHS public collection.
        scroll_times: Number of scroll-down actions to load more notes.
        delay: Delay in seconds between scrolls.

    Returns:
        List of note dicts with keys: note_id, title, url, cover_image, author.
    """
    logger.info(f"Crawling collection: {collection_url}")
    page.goto(collection_url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)

    # Scroll to load all notes
    for i in range(scroll_times):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        logger.debug(f"Scroll {i + 1}/{scroll_times}")
        page.wait_for_timeout(int(delay * 1000))

        # Check if "no more" indicator appears
        no_more = page.query_selector(".no-more, .loading-end")
        if no_more:
            logger.info("Reached end of collection.")
            break

    # Extract note cards
    notes = _extract_notes(page)

    # Deduplicate by note_id
    seen = set()
    unique_notes = []
    for note in notes:
        if note["note_id"] not in seen:
            seen.add(note["note_id"])
            unique_notes.append(note)

    logger.info(f"Found {len(unique_notes)} unique notes in collection.")
    return unique_notes


def _extract_notes(page: Page) -> List[Dict]:
    """Extract note metadata from the loaded collection page."""
    notes = []

    # Try multiple selectors for different collection page layouts
    card_selectors = [
        "section.note-item",
        ".note-card",
        "a[href*='/explore/']",
        "a[href*='/discovery/item/']",
        ".feeds-container .note-item",
    ]

    cards = []
    for selector in card_selectors:
        cards = page.query_selector_all(selector)
        if cards:
            logger.debug(f"Found {len(cards)} cards with selector: {selector}")
            break

    if not cards:
        # Fallback: extract all links that look like note links
        logger.warning("No cards found with known selectors, trying link extraction...")
        return _extract_notes_from_links(page)

    for card in cards:
        try:
            note = _parse_card(card, page)
            if note:
                notes.append(note)
        except Exception as e:
            logger.debug(f"Failed to parse card: {e}")
            continue

    return notes


def _parse_card(card, page: Page) -> Optional[Dict]:
    """Parse a single note card element into a metadata dict."""
    # Try to get the link
    link_el = card.query_selector("a[href*='/explore/'], a[href*='/discovery/item/']")
    if not link_el:
        link_el = card if card.get_attribute("href") else None
    if not link_el:
        return None

    href = link_el.get_attribute("href") or ""
    note_id = _extract_note_id(href)
    if not note_id:
        return None

    url = href if href.startswith("http") else f"{XHS_BASE_URL}{href}"

    # Title
    title_el = card.query_selector(".title, .note-title, .desc")
    title = title_el.inner_text().strip() if title_el else ""

    # Cover image
    img_el = card.query_selector("img")
    cover_image = img_el.get_attribute("src") or "" if img_el else ""

    # Author
    author_el = card.query_selector(".author .name, .author-wrapper .name, .nickname")
    author = author_el.inner_text().strip() if author_el else ""

    return {
        "note_id": note_id,
        "title": title,
        "url": url,
        "cover_image": cover_image,
        "author": author,
    }


def _extract_notes_from_links(page: Page) -> List[Dict]:
    """Fallback: extract notes from all links on the page."""
    notes = []
    links = page.query_selector_all("a")
    for link in links:
        href = link.get_attribute("href") or ""
        note_id = _extract_note_id(href)
        if note_id:
            url = href if href.startswith("http") else f"{XHS_BASE_URL}{href}"
            title = link.inner_text().strip()[:100]
            notes.append({
                "note_id": note_id,
                "title": title,
                "url": url,
                "cover_image": "",
                "author": "",
            })
    return notes


def _extract_note_id(url: str) -> Optional[str]:
    """Extract note ID from a XHS URL."""
    patterns = [
        r"/explore/([a-f0-9]+)",
        r"/discovery/item/([a-f0-9]+)",
        r"noteId=([a-f0-9]+)",
        r"/note/([a-f0-9]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None
