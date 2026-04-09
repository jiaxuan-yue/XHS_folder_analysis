"""Main pipeline orchestrator for XHS Interview Card automation.

Usage:
    python main.py crawl <collection_url>   # Crawl collection and save raw notes
    python main.py process                   # Clean raw notes and save processed text
    python main.py export                    # Export cards to markdown/anki
    python main.py ui                        # Launch Streamlit UI
"""

import sys
import yaml
from pathlib import Path
from typing import Dict

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config() -> Dict:
    """Load configuration from config.yaml."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    logger.warning("config.yaml not found, using defaults.")
    return {}


def cmd_crawl(collection_url: str):
    """Crawl a collection URL: extract note list, then crawl each note."""
    config = load_config()

    from crawler.auth import ensure_logged_in
    from crawler.collection_crawler import crawl_collection
    from crawler.note_crawler import crawl_note
    from storage.json_store import save_raw_note, get_existing_note_ids

    raw_dir = config.get("storage", {}).get("raw_dir", "data/raw")
    existing_ids = get_existing_note_ids(raw_dir)

    # Authenticate and get browser context
    pw, context, page = ensure_logged_in(config)

    try:
        # Step 1: Crawl collection page for note list
        scroll_times = config.get("crawler", {}).get("scroll_times", 10)
        delay = config.get("crawler", {}).get("delay", 2)
        notes = crawl_collection(page, collection_url, scroll_times=scroll_times, delay=delay)

        # Step 2: Crawl each note for full content
        new_count = 0
        for i, note_meta in enumerate(notes):
            note_id = note_meta["note_id"]
            if note_id in existing_ids:
                logger.info(f"[{i+1}/{len(notes)}] Skipping already crawled: {note_id}")
                continue

            logger.info(f"[{i+1}/{len(notes)}] Crawling note: {note_meta['title'][:50]}...")
            note_data = crawl_note(page, note_meta["url"], delay=delay)

            # Merge metadata
            note_data["title"] = note_data["title"] or note_meta.get("title", "")
            note_data["author"] = note_data["author"] or note_meta.get("author", "")
            note_data["cover_image"] = note_meta.get("cover_image", "")

            save_raw_note(note_data, raw_dir=raw_dir)
            new_count += 1

        logger.info(f"Crawling complete. {new_count} new notes saved, {len(notes) - new_count} skipped.")

    finally:
        context.close()
        pw.stop()


def cmd_process():
    """Clean raw notes and save processed text files."""
    config = load_config()

    from storage.json_store import load_all_raw_notes, save_processed_text
    from cleaner.text_cleaner import clean_text

    raw_dir = config.get("storage", {}).get("raw_dir", "data/raw")
    processed_dir = "data/processed"

    notes = load_all_raw_notes(raw_dir)
    logger.info(f"Processing {len(notes)} raw notes...")

    for note in notes:
        note_id = note.get("note_id", "unknown")
        raw_text = note.get("text_content", "")

        if not raw_text.strip():
            logger.warning(f"Skipping note {note_id}: no text content")
            continue

        cleaned = clean_text(raw_text)
        save_processed_text(note_id, cleaned, processed_dir=processed_dir)

    logger.info(f"Processing complete. Processed text saved to {processed_dir}/")
    logger.info("Next step: the agent will read processed files and extract cards using LLM.")


def cmd_export():
    """Export cards to markdown and/or Anki CSV."""
    config = load_config()
    cards_dir = config.get("storage", {}).get("cards_dir", "data/cards")

    from extractor.llm_extractor import load_all_cards
    from exporter.markdown_exporter import export_all_to_single_markdown
    from exporter.anki_exporter import export_to_anki_csv

    cards = load_all_cards(cards_dir)
    if not cards:
        logger.warning("No cards found to export.")
        return

    export_config = config.get("export", {})
    if export_config.get("markdown", True):
        export_all_to_single_markdown(cards)
    if export_config.get("anki", True):
        export_to_anki_csv(cards)


def cmd_ui():
    """Launch the Streamlit UI."""
    import subprocess
    app_path = PROJECT_ROOT / "app.py"
    logger.info("Launching Streamlit UI...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "crawl":
        if len(sys.argv) < 3:
            print("Usage: python main.py crawl <collection_url>")
            sys.exit(1)
        cmd_crawl(sys.argv[2])
    elif command == "process":
        cmd_process()
    elif command == "export":
        cmd_export()
    elif command == "ui":
        cmd_ui()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
