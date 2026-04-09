"""Export interview cards to Markdown format."""

from pathlib import Path
from typing import List, Dict

from utils.logger import get_logger

logger = get_logger(__name__)


def export_to_markdown(cards: List[Dict], output_dir: str = "data/cards/markdown") -> List[str]:
    """Export all cards to individual Markdown files.

    Args:
        cards: List of card dicts.
        output_dir: Output directory for markdown files.

    Returns:
        List of file paths created.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    files = []

    for card in cards:
        note_id = card.get("note_id", "unknown")
        filepath = output_path / f"{note_id}.md"

        md = _card_to_markdown(card)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
        files.append(str(filepath))

    logger.info(f"Exported {len(files)} markdown files to {output_dir}")
    return files


def export_all_to_single_markdown(cards: List[Dict], output_file: str = "data/cards/all_cards.md") -> str:
    """Export all cards to a single Markdown file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# Interview Knowledge Cards\n\n"]
    for i, card in enumerate(cards, 1):
        lines.append(f"---\n\n")
        lines.append(_card_to_markdown(card))
        lines.append("\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    logger.info(f"Exported {len(cards)} cards to {output_file}")
    return str(output_path)


def _card_to_markdown(card: Dict) -> str:
    """Convert a single card dict to markdown text."""
    lines = []

    company = card.get("company", "") or "Unknown"
    position = card.get("position", "") or "Unknown"
    round_ = card.get("interview_round", "")
    source = card.get("source_url", "")
    title = card.get("source_title", "")

    header = f"## {company} - {position}"
    if round_:
        header += f" ({round_})"
    lines.append(header)
    lines.append("")

    if title:
        lines.append(f"> **Source**: [{title}]({source})")
    elif source:
        lines.append(f"> **Source**: [{source}]({source})")

    author = card.get("author", "")
    if author:
        lines.append(f"> **Author**: {author}")

    lines.append("")

    for j, q in enumerate(card.get("questions", []), 1):
        question = q.get("question", "")
        answer = q.get("answer", "")
        qtype = q.get("question_type", "")
        has_orig = q.get("has_original_answer", False)

        type_badge = f" `{qtype}`" if qtype else ""
        answer_badge = " *(original answer)*" if has_orig else " *(generated answer)*"

        lines.append(f"### Q{j}: {question}{type_badge}")
        lines.append("")
        lines.append(f"**Answer**{answer_badge}:")
        lines.append("")
        lines.append(answer)
        lines.append("")

    return "\n".join(lines)
