---
name: xhs-interview-cards
description: Automate extraction of interview knowledge cards from Xiaohongshu (XHS) collections. Crawls public collection pages, extracts note text, cleans content, uses LLM to split questions and generate answers, saves structured JSON cards. Use when the user wants to process XHS interview collections, extract interview questions, or generate study cards from XHS bookmarks.
---

# XHS Interview Cards

Automate the pipeline: XHS Collection URL -> Crawl notes -> Clean text -> LLM extract Q&A -> JSON cards -> Streamlit UI.

Project root: `/Users/breo/Documents/code/xhs`

## Setup (first time only)

```bash
cd /Users/breo/Documents/code/xhs
source env/bin/activate
pip install -r requirements.txt
playwright install chromium
```

**IMPORTANT**: Always activate the venv before running any command:
```bash
source /Users/breo/Documents/code/xhs/env/bin/activate
```

## Pipeline Workflow

### Step 1: Crawl Collection

Run the crawler with the user's collection URL:

```bash
cd /Users/breo/Documents/code/xhs
python main.py crawl <COLLECTION_URL>
```

- Opens browser for QR login if not already logged in (user scans with XHS app)
- Session persists in `~/.xhs/browser_profile/` for future runs
- Crawled notes saved to `data/raw/<note_id>.json`
- Skips already-crawled notes automatically

### Step 2: Clean Raw Text

```bash
cd /Users/breo/Documents/code/xhs
python main.py process
```

- Reads `data/raw/*.json`, cleans text (removes ads, emoji, noise)
- Saves cleaned text to `data/processed/<note_id>.txt`

### Step 3: LLM Extract Cards (Agent Task)

This step is performed by you (the agent). For each file in `data/processed/`:

1. Read the processed text file
2. Read the corresponding raw note from `data/raw/` to get metadata (url, title, author)
3. Classify: is this interview content? Use keywords: 面经, 一面, 二面, 八股, 算法题, 笔试
4. If yes, extract structured Q&A using this prompt:

```
你是一个面试知识整理专家。请从以下小红书面经帖子中提取结构化面试信息。

要求：
1. 提取帖子提到的公司名称（如果有的话）
2. 提取岗位名称（如果有的话）
3. 将文本中的每个面试题目拆分出来
4. 对每个题目：
   - 判断题型：algorithm / basics / project / behavioral / system_design
   - 如果帖子中已包含答案，保留原始答案
   - 如果没有答案，请生成一个简洁准确的参考答案
5. 输出严格的JSON格式

输出格式：
{
  "company": "",
  "position": "",
  "interview_round": "",
  "questions": [
    {
      "question": "题目内容",
      "question_type": "basics",
      "answer": "答案内容",
      "has_original_answer": true
    }
  ]
}

帖子原文：
<paste cleaned text here>
```

5. Save the result as `data/cards/<note_id>.json` using:

```python
import sys; sys.path.insert(0, "/Users/breo/Documents/code/xhs")
from extractor.llm_extractor import save_card_json
save_card_json(card_dict, {"note_id": "<id>", "url": "<url>", "title": "<title>", "author": "<author>"})
```

### Step 4: Launch UI

```bash
cd /Users/breo/Documents/code/xhs
python main.py ui
```

Opens Streamlit at http://localhost:8501 with:
- Filter by company / position / question type
- View original post links
- Add personal notes
- Export to Markdown or Anki CSV

### Step 5: Export (optional)

```bash
cd /Users/breo/Documents/code/xhs
python main.py export
```

Generates `data/cards/all_cards.md` and `data/cards/anki_export.csv`.

## Card JSON Format

```json
{
  "note_id": "abc123",
  "source_url": "https://www.xiaohongshu.com/explore/abc123",
  "source_title": "字节一面面经",
  "author": "用户名",
  "company": "字节跳动",
  "position": "后端开发",
  "interview_round": "一面",
  "questions": [
    {
      "question": "HashMap的底层实现原理",
      "question_type": "basics",
      "answer": "HashMap基于数组+链表/红黑树...",
      "has_original_answer": false
    }
  ]
}
```

## Important Notes

- Always use absolute paths from project root `/Users/breo/Documents/code/xhs`
- The crawler uses Playwright persistent context — login once, reuse session
- If login session expires, the browser will reopen for QR scan automatically
- Notes are deduplicated by `note_id` — safe to re-run crawl on same collection
- The agent handles LLM extraction (Step 3) — no external API needed
