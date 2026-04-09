"""Streamlit frontend for browsing interview knowledge cards."""

import json
import streamlit as st
from pathlib import Path
from typing import List, Dict

CARDS_DIR = "data/cards"


def load_cards() -> List[Dict]:
    """Load all card JSON files."""
    cards_path = Path(CARDS_DIR)
    if not cards_path.exists():
        return []
    cards = []
    for f in sorted(cards_path.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                cards.append(json.load(fh))
        except Exception:
            continue
    return cards


def get_unique_values(cards: List[Dict], key: str) -> List[str]:
    """Get unique non-empty values for a given key across all cards."""
    values = set()
    for card in cards:
        v = card.get(key, "")
        if v:
            values.add(v)
    return sorted(values)


def get_all_question_types(cards: List[Dict]) -> List[str]:
    """Get all unique question types across all cards."""
    types = set()
    for card in cards:
        for q in card.get("questions", []):
            qt = q.get("question_type", "")
            if qt:
                types.add(qt)
    return sorted(types)


def save_user_notes(note_id: str, question_idx: int, notes: str):
    """Save user notes for a specific question."""
    filepath = Path(CARDS_DIR) / f"{note_id}.json"
    if not filepath.exists():
        return
    with open(filepath, "r", encoding="utf-8") as f:
        card = json.load(f)
    if question_idx < len(card.get("questions", [])):
        card["questions"][question_idx]["user_notes"] = notes
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)


def main():
    st.set_page_config(page_title="Interview Cards", page_icon="📚", layout="wide")
    st.title("📚 Interview Knowledge Cards")

    cards = load_cards()

    if not cards:
        st.info("No cards found. Run the pipeline first to crawl and extract interview content.")
        st.code("python main.py crawl <collection_url>", language="bash")
        return

    # --- Sidebar: Filters ---
    st.sidebar.header("Filters")

    companies = get_unique_values(cards, "company")
    selected_company = st.sidebar.selectbox(
        "Company", ["All"] + companies
    )

    positions = get_unique_values(cards, "position")
    selected_position = st.sidebar.selectbox(
        "Position", ["All"] + positions
    )

    q_types = get_all_question_types(cards)
    selected_type = st.sidebar.selectbox(
        "Question Type", ["All"] + q_types
    )

    # Filter cards
    filtered_cards = cards
    if selected_company != "All":
        filtered_cards = [c for c in filtered_cards if c.get("company") == selected_company]
    if selected_position != "All":
        filtered_cards = [c for c in filtered_cards if c.get("position") == selected_position]

    # Count questions
    total_q = sum(len(c.get("questions", [])) for c in filtered_cards)
    st.sidebar.markdown(f"**{len(filtered_cards)}** cards / **{total_q}** questions")

    # --- Sidebar: Export ---
    st.sidebar.markdown("---")
    st.sidebar.header("Export")

    if st.sidebar.button("Export Markdown"):
        from exporter.markdown_exporter import export_all_to_single_markdown
        path = export_all_to_single_markdown(filtered_cards)
        st.sidebar.success(f"Exported to {path}")
        with open(path, "r", encoding="utf-8") as f:
            st.sidebar.download_button("Download Markdown", f.read(), file_name="interview_cards.md")

    if st.sidebar.button("Export Anki CSV"):
        from exporter.anki_exporter import export_to_anki_csv
        path = export_to_anki_csv(filtered_cards)
        st.sidebar.success(f"Exported to {path}")
        with open(path, "r", encoding="utf-8") as f:
            st.sidebar.download_button("Download CSV", f.read(), file_name="anki_export.csv")

    # --- Main area: Cards ---
    for card in filtered_cards:
        company = card.get("company", "") or "Unknown"
        position = card.get("position", "") or "Unknown"
        round_ = card.get("interview_round", "")
        source_url = card.get("source_url", "")
        note_id = card.get("note_id", "")
        author = card.get("author", "")

        # Card header
        header = f"**{company}** — {position}"
        if round_:
            header += f" ({round_})"

        with st.expander(header, expanded=True):
            # Meta info row
            meta_cols = st.columns([3, 2, 2])
            with meta_cols[0]:
                if source_url:
                    st.markdown(f"🔗 [Original Post]({source_url})")
            with meta_cols[1]:
                if author:
                    st.caption(f"Author: {author}")
            with meta_cols[2]:
                st.caption(f"ID: {note_id}")

            # Questions
            questions = card.get("questions", [])
            if selected_type != "All":
                questions = [q for q in questions if q.get("question_type") == selected_type]

            for idx, q in enumerate(questions):
                question = q.get("question", "")
                answer = q.get("answer", "")
                qtype = q.get("question_type", "")
                has_orig = q.get("has_original_answer", False)
                user_notes = q.get("user_notes", "")

                type_color = {
                    "algorithm": "🟢",
                    "basics": "🔵",
                    "project": "🟠",
                    "behavioral": "🟣",
                    "system_design": "🔴",
                }.get(qtype, "⚪")

                st.markdown(f"**{type_color} Q{idx+1}: {question}** `{qtype}`")

                answer_label = "📝 Original Answer" if has_orig else "🤖 Generated Answer"
                st.markdown(f"*{answer_label}:*")
                st.markdown(answer)

                # User notes section
                notes_key = f"notes_{note_id}_{idx}"
                new_notes = st.text_area(
                    "My Notes",
                    value=user_notes,
                    key=notes_key,
                    height=68,
                    label_visibility="collapsed",
                    placeholder="Add your own notes here...",
                )
                if new_notes != user_notes:
                    save_user_notes(note_id, idx, new_notes)

                st.markdown("---")


if __name__ == "__main__":
    main()
