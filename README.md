# XHS Interview Cards - 技术架构文档

## 概述

XHS Interview Cards 是一个全自动化的小红书(小红薯)面试知识卡片提取系统，将小红书收藏集合中的面试笔记转换为结构化的知识卡片。

**核心功能流程:**
```
XHS 收藏集合 URL → 爬虫采集 → 文本清理 → LLM 分析 → 卡片生成 → Streamlit 可视化
```

**主要特性:**
- 📱 完全自动化的数据提取管道
- 🤖 基于 LLM 的心智映射与问答生成
- 💾 多格式导出 (JSON/Markdown/Anki)
- 🎨 Web UI 交互界面
- 🔐 浏览器自动化登录处理

---

## 项目结构

```
xhs/
├── main.py                    # 主程序入口及命令行接口
├── app.py                     # Streamlit Web UI
├── config.yaml                # 配置文件 (爬虫、存储、导出)
├── requirements.txt           # Python 依赖声明
│
├── crawler/                   # 爬虫模块
│   ├── auth.py               # 浏览器认证与登录处理
│   ├── collection_crawler.py # 收藏集合爬虫
│   └── note_crawler.py       # 单个笔记爬虫
│
├── storage/                   # 数据存储模块
│   └── json_store.py         # JSON 文件存储实现
│
├── cleaner/                   # 文本清理模块
│   └── [清理器实现]
│
├── extractor/                 # 数据提取模块
│   └── [LLM 提取器实现]
│
├── exporter/                  # 导出模块
│   ├── markdown_exporter.py  # Markdown 格式导出
│   └── anki_exporter.py      # Anki 格式导出
│
├── utils/                     # 工具函数
│   ├── logger.py             # 统一日志系统
│   └── retry.py              # 重试机制
│
├── data/                      # 数据存储目录
│   ├── raw/                  # 原始爬虫数据
│   ├── cards/                # 生成的卡片文件 (JSON)
│   └── logs/                 # 任务日志
│
└── .qoder/                    # AI 编程助手配置
```

---

## 技术栈

### 核心依赖

| 库 | 版本 | 用途 |
|----|------|------|
| `Playwright` | ≥1.40.0 | 浏览器自动化、网页爬虫 |
| `Streamlit` | ≥1.30.0 | Web UI 框架 |
| `PyYAML` | ≥6.0 | YAML 配置文件解析 |
| `Pydantic` | ≥2.0.0 | 数据验证与序列化 |
| `requests` | ≥2.31.0 | HTTP 网络请求 |

### 系统环境

- **Python**: 3.9+
- **操作系统**: macOS / Linux / Windows
- **浏览器**: Chromium (Playwright 自动安装)

---

## 工作流程

### 1. 爬虫阶段 (Crawler)

```bash
python main.py crawl <collection_url>
```

#### 1.1 认证模块 (`crawler/auth.py`)

**功能:**
- 初始化 Playwright 浏览器环境
- 管理浏览器 profile (保存登录状态)
- 处理登录超时和重试

**关键函数:**
- `ensure_logged_in(config)` - 确保已登录，返回 (playwright, context, page)

**配置参数:**
```yaml
auth:
  profile_dir: ~/.xhs/browser_profile    # 浏览器 profile 缓存目录
  login_timeout: 120                      # 登录超时秒数
```

#### 1.2 收藏集合爬虫 (`crawler/collection_crawler.py`)

**功能:**
- 访问小红书收藏集合页面
- 滚动加载所有笔记列表
- 提取笔记 ID 和基本信息

**工作流:**
1. 加载收藏集合 URL
2. 滚动页面以加载所有笔记 (默认 10 次滚动)
3. 提取所有笔记的 ID 和元数据
4. 返回笔记 ID 列表

**配置参数:**
```yaml
crawler:
  headless: true          # 无头模式
  scroll_times: 10        # 滚动次数
  delay: 2                # 请求间隔秒数
```

#### 1.3 单笔记爬虫 (`crawler/note_crawler.py`)

**功能:**
- 逐个访问笔记页面
- 提取笔记标题、内容、标签等
- 处理图片和媒体链接

**提取字段:**
- `note_id` - 笔记唯一标识
- `title` - 笔记标题
- `content` - 笔记正文 (HTML)
- `tags` - 笔记标签列表
- `created_at` - 发布时间
- `author` - 作者信息

**数据保存格式:**
```json
{
  "note_id": "string",
  "title": "string",
  "content": "string (html)",
  "tags": ["tag1", "tag2"],
  "created_at": "2024-01-01T12:00:00",
  "author": "string",
  "raw_html": "string (full page html)"
}
```

---

### 2. 处理阶段 (Processing)

```bash
python main.py process
```

#### 2.1 文本清理 (`cleaner/`)

**功能:**
- 移除 HTML 标签，提取纯文本
- 处理特殊字符和编码问题
- 去除冗余空白和格式化

**输入:** 原始 HTML 内容
**输出:** 清理后的纯文本

#### 2.2 LLM 提取 (`extractor/`)

**功能:**
- 将笔记文本分解为问答对
- 识别问题类型 (行为问题、技术问题、系统设计等)
- 生成或增强答案

**提示词策略:**
- 系统角色: "你是面试准备专家"
- 任务: "将以下笔记分解为结构化的问答卡片"
- 输出格式: structured JSON

**问题类型枚举:**
- `behavioral` - 行为问题
- `technical` - 技术问题
- `system_design` - 系统设计
- `behavioral_puzzle` - 行为谜题
- `knowledge` - 知识点

---

### 3. 卡片生成阶段

```bash
python main.py export
```

#### 3.1 卡片数据结构

**单张卡片 JSON 格式:**
```json
{
  "note_id": "string",
  "title": "string",
  "source_url": "string",
  "company": "string",
  "position": "string",
  "difficulty": "easy | medium | hard",
  "tags": ["tag1", "tag2"],
  "questions": [
    {
      "question_id": "string",
      "question_text": "string",
      "question_type": "behavioral | technical | system_design",
      "answer": "string",
      "keywords": ["kw1", "kw2"],
      "follow_ups": ["follow_up_1"],
      "user_notes": "string (用户笔记)"
    }
  ],
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

#### 3.2 Markdown 导出

**格式:**
```markdown
# [卡片标题]

**来源**: [公司] | [职位] | 难度: [难度级别]

## 问题 1: [问题文本]

**问题类型**: behavioral

**答案**:
[详细答案]

**关键词**: 关键词1, 关键词2

**追问**: 
- 追问1
- 追问2

---
```

**导出路径:** `data/exports/markdown/`

#### 3.3 Anki 导出

**格式:**
```
Q: [问题文本]\nTags: [tags]
A: [答案]\n\n**关键词**: [keywords]
```

**导出文件:** `data/exports/anki.apkg`

---

### 4. UI 交互阶段

```bash
python main.py ui
```

#### 4.1 Streamlit App 功能

- **浏览卡片** - 按公司、职位、难度过滤
- **编辑笔记** - 为每个问题添加个人笔记
- **统计分析** - 问题分布、学习进度
- **导出功能** - 生成 Markdown/Anki

**主要页面:**
1. Home - 卡片总览
2. Browse - 卡片浏览与过滤
3. Study - 交互式学习模式
4. Analytics - 学习统计
5. Export - 多格式导出

---

## 数据流程图

```
┌─────────────────┐
│ XHS Collection  │ (小红书收藏集合)
│      URL        │
└────────┬────────┘
         │
         ▼
    ┌────────────┐
    │ Playwright │ (浏览器自动化)
    │ Browser    │
    └────┬───────┘
         │ (Cookies/Auth)
         ▼
┌─────────────────────┐
│ Collection Crawler  │ (步骤1)
│ → Note List         │
└────────┬────────────┘
         │
         ▼
┌──────────────────────┐
│ Note Crawler Loop    │ (步骤2)
│ ∀ note_id:          │
│   HTTP GET note     │
│   Extract HTML      │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Storage: JSON Store  │ (json_store.py)
│ /data/raw/*.json     │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Text Cleaner         │ (cleaner/)
│ HTML → Plain Text    │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ LLM Extractor        │ (extractor/)
│ Text → Q&A Pairs     │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Card Generator       │
│ → Structured JSON    │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Storage: Cards       │
│ /data/cards/*.json   │
└────────┬─────────────┘
         │
    ┌────┴─────┐
    │           │
    ▼           ▼
┌────────┐  ┌──────────┐
│ App.py │  │ Exporter │
│StreamUI│  │ MD/ANKI  │
└────────┘  └──────────┘
```

---

## 配置系统

### config.yaml 完整说明

```yaml
# 爬虫配置
crawler:
  headless: true              # 是否无头模式运行
  scroll_times: 10            # 收藏集合滚动加载次数
  delay: 2                    # 请求间隔(秒)

# 认证配置
auth:
  profile_dir: ~/.xhs/browser_profile   # 浏览器 profile 保存位置
  login_timeout: 120                     # 登录超时(秒)
  save_cookies: true                     # 是否保存 cookies

# 存储配置
storage:
  type: json                  # 存储类型 (json/sqlite)
  cards_dir: data/cards       # 卡片输出目录
  raw_dir: data/raw           # 原始数据目录

# 导出配置
export:
  anki: true                  # 是否导出 Anki 格式
  markdown: true              # 是否导出 Markdown 格式
  output_dir: data/exports    # 导出输出目录

# LLM 配置 (可选)
llm:
  provider: openai            # claude / openai
  model: gpt-4-turbo
  temperature: 0.7
```

---

## 代码接口 API

### 主程序接口 (`main.py`)

#### 命令行子命令

```bash
# 1. 爬虫命令
python main.py crawl <collection_url> [--max-notes N]

# 2. 处理命令
python main.py process [--raw-dir PATH] [--llm-provider openai]

# 3. 导出命令
python main.py export [--format markdown,anki] [--output PATH]

# 4. UI 命令
python main.py ui
```

#### 加载配置

```python
from main import load_config

config = load_config()
raw_dir = config.get("storage", {}).get("raw_dir", "data/raw")
```

### 存储接口 (`storage/json_store.py`)

#### 保存原始笔记

```python
from storage.json_store import save_raw_note

save_raw_note(
    note_id="string",
    note_data={
        "title": "...",
        "content": "...",
        "html": "..."
    },
    output_dir="data/raw"
)
```

#### 获取已爬取笔记 ID

```python
from storage.json_store import get_existing_note_ids

existing_ids = get_existing_note_ids("data/raw")
# Returns: Set[str]
```

#### 加载卡片

```python
from storage.json_store import load_cards

cards = load_cards("data/cards")
# Returns: List[Dict]
```

### 爬虫接口 (`crawler/`)

#### 认证

```python
from crawler.auth import ensure_logged_in

pw, context, page = ensure_logged_in(config)
# Returns:
# - pw: Playwright 实例
# - context: BrowserContext
# - page: Page 对象 (已登录)
```

#### 爬取收藏集合

```python
from crawler.collection_crawler import crawl_collection

note_ids = crawl_collection(page, collection_url, scroll_times=10)
# Returns: List[str]
```

#### 爬取单个笔记

```python
from crawler.note_crawler import crawl_note

note_data = crawl_note(page, note_id)
# Returns: Dict with keys: title, content, tags, created_at, author
```

### 日志接口 (`utils/logger.py`)

```python
from utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Message")
logger.error("Error")
logger.warning("Warning")
```

---

## 错误处理与重试机制

### 重试装饰器 (`utils/retry.py`)

```python
from utils.retry import retry_on_exception

@retry_on_exception(max_retries=3, delay=2, backoff=1.5)
def unreliable_operation():
    # 会自动重试，延迟递增
    pass
```

**重试策略:**
- 最大重试次数: 3
- 初始延迟: 2 秒
- 退避倍数: 1.5 (2s → 3s → 4.5s)
- 适用异常: Network, Timeout, 临时服务器错误

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `LoginTimeoutError` | 登录页面交互超时 | 增加 `login_timeout` |
| `CollectionNotFoundError` | 收藏集合 URL 无效 | 验证 URL 格式 |
| `NoteExtractionError` | 笔记内容提取失败 | 检查 XHS 页面结构更新 |
| `StorageError` | 文件写入失败 | 确保目录权限 |

---

## 性能优化

### 1. 爬虫优化

- **并发爬虫**: 使用 asyncio 并发爬取多个笔记 (可选)
- **缓存策略**: 已爬取笔记跳过重复爬虫
- **滚动优化**: 根据网络速度调整 `scroll_times`

### 2. 存储优化

- **文件分片**: 大量卡片可分片存储 (按日期/公司)
- **索引缓存**: 使用 SQLite 索引加速查询
- **增量更新**: 只处理新增笔记

### 3. LLM 优化

- **批处理**: 将多个笔记合并为一个 LLM 请求
- **缓存提示词**: 复用系统提示词
- **流式输出**: 使用流式 API 减少延迟

---

## 扩展指南

### 添加新导出格式

1. 在 `exporter/` 创建新模块 `format_exporter.py`
2. 实现 `BaseExporter` 接口:

```python
from abc import ABC, abstractmethod

class BaseExporter(ABC):
    @abstractmethod
    def export(self, cards: List[Dict], output_path: str) -> None:
        pass
```

3. 在 `main.py` 中注册:

```python
exporters = {
    "markdown": MarkdownExporter(),
    "anki": AnkiExporter(),
    "custom": CustomExporter()
}
```

### 添加新数据源

1. 实现新爬虫类继承 `BaseCrawler`
2. 添加数据源特定的解析逻辑
3. 统一存储接口调用

---

## 部署与运维

### 开发环境设置

```bash
git clone <repo>
cd xhs
python -m venv env
source env/bin/activate  # macOS/Linux
# source env\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install chromium
```

### 首次运行

```bash
# 1. 交互式登录
python main.py login

# 2. 爬取数据
python main.py crawl "https://www.xiaohongshu.com/user/..."

# 3. 查看结果
python main.py ui
```

### 定期维护

- **检查日志**: `logs/` 目录查看运行日志
- **清理缓存**: `rm -rf data/raw_old` 删除过期数据
- **更新依赖**: `pip install -r requirements.txt --upgrade`
- **浏览器更新**: `playwright install chromium --with-deps`

---

## 监控与调试

### 日志等级

```python
import logging
logging.getLogger("xhs").setLevel(logging.DEBUG)
```

**等级:** DEBUG < INFO < WARNING < ERROR < CRITICAL

### 调试模式

在 `config.yaml` 中:
```yaml
debug: true
log_level: DEBUG
headless: false  # 显示浏览器窗口
```

### 性能分析

```bash
python -m cProfile -s cumtime main.py crawl <url>
```

---

## 安全与隐私

- ✅ 浏览器 profile 本地存储 (不上传凭证)
- ✅ 支持代理配置 (可选)
- ✅ 请求头伪装
- ✅ 随机延迟避免被检测
- ⚠️ 定期更新 User-Agent 和浏览器指纹

---

## 常见问题 (FAQ)

**Q: 如何登录小红书?**
A: 首次运行时会打开浏览器，手动登录即可。登录状态会被保存在 `~/.xhs/browser_profile`。

**Q: 爬虫被限制如何处理?**
A: 增加 `crawler.delay` 参数，或使用代理服务。检查 IP 是否被暂时限制。

**Q: 如何离线使用?**
A: 爬虫完成后无需网络。UI 和导出都支持离线。

**Q: 支持自定义 LLM 吗?**
A: 是的，修改 `config.yaml` 中的 `llm` 部分。

---

## 参考资源

- [Playwright 文档](https://playwright.dev)
- [Streamlit 文档](https://docs.streamlit.io)
- [Pydantic 文档](https://docs.pydantic.dev)
- [XHS API](https://xiaohongshu.com) (非官方逆向)

---

**最后更新**: 2026-04-14
**版本**: 1.0.0
**维护者**: Development Team
