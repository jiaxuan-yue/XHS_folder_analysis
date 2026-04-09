"""JSON-based storage for raw crawled data and processed cards."""

import json
from pathlib import Path
from typing import List, Dict, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


def save_raw_note(note_data: Dict, raw_dir: str = "data/raw") -> str:
    """Save raw crawled note data to a JSON file.

    Args:
        note_data: Raw note dict (note_id, title, url, text_content, author).
        raw_dir: Directory for raw data files.

    Returns:
        Path to the saved file.
    """
    output_path = Path(raw_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    note_id = note_data.get("note_id", "unknown")
    filepath = output_path / f"{note_id}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(note_data, f, ensure_ascii=False, indent=2)

    logger.debug(f"Saved raw note: {filepath}")
    return str(filepath)


def load_raw_note(note_id: str, raw_dir: str = "data/raw") -> Optional[Dict]:
    """Load a raw note by note_id."""
    filepath = Path(raw_dir) / f"{note_id}.json"
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_raw_notes(raw_dir: str = "data/raw") -> List[Dict]:
    """Load all raw note files."""
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        return []
    notes = []
    for f in sorted(raw_path.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                notes.append(json.load(fh))
        except Exception as e:
            logger.warning(f"Failed to load {f}: {e}")
    return notes


def save_processed_text(note_id: str, cleaned_text: str, processed_dir: str = "data/processed") -> str:
    """Save cleaned text to a text file for LLM processing.

    Args:
        note_id: Note identifier.
        cleaned_text: Cleaned text content.
        processed_dir: Directory for processed text files.

    Returns:
        Path to the saved file.
    """
    output_path = Path(processed_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filepath = output_path / f"{note_id}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

    logger.debug(f"Saved processed text: {filepath}")
    return str(filepath)


def get_existing_note_ids(raw_dir: str = "data/raw") -> set:
    """Get set of note_ids that have already been crawled."""
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        return set()
    return {f.stem for f in raw_path.glob("*.json")}


def get_existing_card_ids(cards_dir: str = "data/cards") -> set:
    """Get set of note_ids that already have extracted cards."""
    cards_path = Path(cards_dir)
    if not cards_path.exists():
        return set()
    return {f.stem for f in cards_path.glob("*.json")}
