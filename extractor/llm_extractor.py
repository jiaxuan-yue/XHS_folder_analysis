"""LLM-based interview content extractor.

This module provides the prompt template and helper functions for the agent's
LLM to extract structured interview Q&A from cleaned note text.

The agent reads processed text, sends it through its own LLM with the prompt
template, and saves the structured JSON output.
"""

import json
from typing import List, Dict, Optional
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

# Prompt template for the agent's LLM to extract interview cards
EXTRACTION_PROMPT = """你是一个面试知识整理专家。请从以下小红书面经帖子中提取结构化面试信息。

要求：
1. 提取帖子提到的公司名称（如果有的话）
2. 提取岗位名称（如果有的话）
3. 将文本中的每个面试题目拆分出来
4. 对每个题目：
   - 判断题型：algorithm（算法）/ basics（八股/基础）/ project（项目经验）/ behavioral（行为面试）/ system_design（系统设计）
   - 如果帖子中已包含答案，保留原始答案
   - 如果没有答案，请生成一个简洁准确的参考答案
5. 输出严格的JSON格式

输出格式：
```json
{
  "company": "公司名称（未提及则为空字符串）",
  "position": "岗位名称（未提及则为空字符串）",
  "interview_round": "面试轮次（如：一面、二面、HR面，未提及则为空字符串）",
  "questions": [
    {
      "question": "题目内容",
      "question_type": "basics",
      "answer": "答案内容",
      "has_original_answer": true
    }
  ]
}
```

帖子原文：
{content}

请仅输出JSON，不要输出其他内容。"""

# Prompt to classify if a text is interview content
CLASSIFICATION_PROMPT = """判断以下文本是否为面试经验/面经内容。

判断依据：
- 包含面试题目、面试流程描述
- 提到"面经"、"一面"、"二面"、"三面"、"HR面"、"笔试"、"八股"、"算法题"等
- 包含技术问题列表
- 描述面试经历

请仅回答 true 或 false。

文本：
{content}"""


def build_extraction_prompt(content: str) -> str:
    """Build the extraction prompt with the given content."""
    return EXTRACTION_PROMPT.format(content=content)


def build_classification_prompt(content: str) -> str:
    """Build the classification prompt with the given content."""
    return CLASSIFICATION_PROMPT.format(content=content)


def parse_extraction_result(llm_output: str) -> Optional[Dict]:
    """Parse the LLM's JSON output into a structured dict.

    Args:
        llm_output: Raw text output from the LLM.

    Returns:
        Parsed dict or None if parsing fails.
    """
    try:
        # Try to extract JSON from the output (handle markdown code blocks)
        text = llm_output.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)
    except (json.JSONDecodeError, IndexError) as e:
        logger.error(f"Failed to parse LLM extraction result: {e}")
        logger.debug(f"Raw output: {llm_output[:500]}")
        return None


def save_card_json(card: Dict, note_meta: Dict, output_dir: str = "data/cards") -> str:
    """Save an extracted card to a JSON file.

    Args:
        card: Extracted card dict from LLM (company, position, questions).
        note_meta: Note metadata (note_id, url, title, author).
        output_dir: Directory to save JSON files.

    Returns:
        Path to the saved JSON file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    note_id = note_meta.get("note_id", "unknown")
    filename = f"{note_id}.json"
    filepath = output_path / filename

    # Merge card data with note metadata
    full_card = {
        "note_id": note_id,
        "source_url": note_meta.get("url", ""),
        "source_title": note_meta.get("title", ""),
        "author": note_meta.get("author", ""),
        "company": card.get("company", ""),
        "position": card.get("position", ""),
        "interview_round": card.get("interview_round", ""),
        "questions": card.get("questions", []),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(full_card, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved card: {filepath} ({len(full_card['questions'])} questions)")
    return str(filepath)


def load_all_cards(cards_dir: str = "data/cards") -> List[Dict]:
    """Load all card JSON files from the cards directory.

    Returns:
        List of card dicts.
    """
    cards_path = Path(cards_dir)
    if not cards_path.exists():
        return []

    cards = []
    for f in sorted(cards_path.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                cards.append(json.load(fh))
        except Exception as e:
            logger.warning(f"Failed to load {f}: {e}")

    logger.info(f"Loaded {len(cards)} cards from {cards_dir}")
    return cards
