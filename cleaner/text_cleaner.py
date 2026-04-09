"""Text cleaning utilities for XHS note content.

Removes ads, emoji, noise, and normalizes whitespace.
"""

import re
from typing import List

from utils.logger import get_logger

logger = get_logger(__name__)

# Common ad/promo patterns in XHS posts
AD_PATTERNS = [
    r"关注我.*",
    r"点赞.*收藏.*",
    r"私信.*咨询.*",
    r"#\S+#",  # hashtags
    r"@\S+",  # mentions
    r"(?:微信|wx|vx|WX)[\s:：]\S+",
    r"(?:公众号|gzh)[\s:：]\S+",
    r"领取.*资料.*",
    r"免费.*领取.*",
    r"戳.*链接.*",
]

# Emoji ranges (comprehensive Unicode emoji blocks)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "\u2640-\u2642"
    "\u2600-\u2B55"
    "\u200d"
    "\u23cf"
    "\u23e9"
    "\u231a"
    "\ufe0f"
    "\u3030"
    "]+",
    flags=re.UNICODE,
)


def clean_text(text: str) -> str:
    """Clean raw note text content.

    Args:
        text: Raw text extracted from an XHS note.

    Returns:
        Cleaned and normalized text.
    """
    if not text:
        return ""

    # Remove ad/promo patterns
    for pattern in AD_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove emoji
    text = EMOJI_PATTERN.sub("", text)

    # Remove excessive decorative characters
    text = re.sub(r"[⭐🔥💯✅❌🎯📌📍💡🏷️➡️⬇️🔗]{1,}", "", text)

    # Normalize numbered list markers (Chinese circled numbers → plain numbers)
    circled_nums = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
    for i, c in enumerate(circled_nums, 1):
        text = text.replace(c, f"{i}.")

    # Normalize whitespace
    text = re.sub(r"\t", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def split_into_sections(text: str) -> List[str]:
    """Split cleaned text into logical sections/questions.

    Splits on common numbered patterns like:
    1. / 1、/ 1) / Q1: / 问题1 / 一、 etc.

    Args:
        text: Cleaned text.

    Returns:
        List of text sections.
    """
    if not text:
        return []

    # Patterns that indicate start of a new question/section
    split_pattern = re.compile(
        r"(?=\n\s*(?:"
        r"\d+[\.\、\)\）:：]"  # 1. 1、 1) 1） 1: 1：
        r"|[一二三四五六七八九十]+[\.\、:：]"  # 一、 二、
        r"|Q\d+"  # Q1 Q2
        r"|问题?\s*\d+"  # 问题1 问1
        r"|面试题?\s*\d+"  # 面试题1
        r"|第[一二三四五六七八九十\d]+[题道个]"  # 第一题
        r"))",
        re.MULTILINE,
    )

    sections = split_pattern.split(text)
    # Clean up empty sections
    sections = [s.strip() for s in sections if s.strip()]
    return sections
