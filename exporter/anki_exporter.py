"""Export interview cards to Anki-compatible CSV format."""

import csv
from pathlib import Path
from typing import List, Dict

from utils.logger import get_logger

logger = get_logger(__name__)


def export_to_anki_csv(cards: List[Dict], output_file: str = "data/cards/anki_export.csv") -> str:
    """Export all cards to Anki CSV format.

    Each row is one question-answer pair.
    Columns: Front (question), Back (answer), Tags (company, type, position).

    Args:
        cards: List of card dicts.
        output_file: Output CSV file path.

    Returns:
        Path to the exported CSV file.
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for card in cards:
        company = card.get("company", "") or "unknown"
        position = card.get("position", "") or "unknown"
        source_url = card.get("source_url", "")

        for q in card.get("questions", []):
            question = q.get("question", "")
            answer = q.get("answer", "")
            qtype = q.get("question_type", "")

            # Build Anki tags (space-separated)
            tags = []
            if company:
                tags.append(f"company::{company}")
            if position:
                tags.append(f"position::{position}")
            if qtype:
                tags.append(f"type::{qtype}")
            tag_str = " ".join(tags)

            # Add source link to the back of the card
            back_text = answer
            if source_url:
                back_text += f"\n\n<a href='{source_url}'>Source</a>"

            rows.append({
                "Front": question,
                "Back": back_text,
                "Tags": tag_str,
            })

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Front", "Back", "Tags"], delimiter="\t")
        writer.writerows(rows)

    logger.info(f"Exported {len(rows)} Q&A pairs to Anki CSV: {output_file}")
    return str(output_path)
