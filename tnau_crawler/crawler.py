#!/usr/bin/env python3
"""
TNAU Agritech Portal — Production-Grade Async Crawler
======================================================
Crawls https://agritech.tnau.ac.in and builds a structured knowledge base.

Features:
  - Async I/O via asyncio + aiohttp  (fast, non-blocking)
  - Full folder-hierarchy preservation
  - PDF download + HTML save + Markdown conversion
  - Table extraction to CSV
  - Per-page metadata JSON
  - Master index.csv  (Title, URL, Category, Crop, Language, File Type)
  - Respects robots.txt + polite delay
  - Resumable — saves state after every page
  - Domain filtering (agritech.tnau.ac.in only)
  - Skip social media / YouTube / ads / large images
  - Live progress bar with tqdm

Usage:
  python crawler.py                     # fresh crawl
  python crawler.py --resume            # resume interrupted crawl
  python crawler.py --concurrency 4     # gentler (4 workers)
  python crawler.py --delay 2.0         # 2-second polite delay
  python crawler.py --max-pages 1000    # stop after 1 000 pages
  python crawler.py --verbose           # debug logging

Output (inside knowledge_base/):
  html/        raw HTML  (URL path preserved)
  markdown/    converted Markdown
  pdfs/        all PDF files
  tables/      per-page CSV tables
  metadata/    per-page JSON
  index.csv    master index
  crawler.log  detailed log
  .state.json  checkpoint (hidden)
"""

# ── Standard library ─────────────────────────────────────────────────────────
import argparse
import asyncio
import csv
import hashlib
import json
import logging
import re
import signal
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import unquote, urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

# ── Third-party ───────────────────────────────────────────────────────────────
import aiofiles
import aiohttp
from bs4 import BeautifulSoup, Comment
from markdownify import markdownify as _md_convert
from tqdm import tqdm

# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

BASE_URL        = "https://agritech.tnau.ac.in"
ALLOWED_DOMAIN  = "agritech.tnau.ac.in"
START_URL       = BASE_URL + "/"

OUTPUT_DIR      = Path("knowledge_base")
HTML_DIR        = OUTPUT_DIR / "html"
MD_DIR          = OUTPUT_DIR / "markdown"
PDF_DIR         = OUTPUT_DIR / "pdfs"
TABLE_DIR       = OUTPUT_DIR / "tables"
META_DIR        = OUTPUT_DIR / "metadata"
STATE_FILE      = OUTPUT_DIR / ".state.json"
INDEX_FILE      = OUTPUT_DIR / "index.csv"
LOG_FILE        = OUTPUT_DIR / "crawler.log"

# Defaults (overridden by CLI args)
DEFAULT_CONCURRENCY = 6
DEFAULT_DELAY       = 1.5    # polite seconds between requests per worker
TIMEOUT_TOTAL       = 30     # seconds per request
TIMEOUT_CONNECT     = 10
MAX_RETRIES         = 3
RETRY_BASE_WAIT     = 2.0    # exponential backoff: 2^retry seconds
MAX_IMAGE_BYTES     = 1_048_576    # 1 MB — skip larger images
MAX_PDF_BYTES       = 60_000_000   # 60 MB — skip absurdly large PDFs

USER_AGENT = (
    "TNAU-KnowledgeBase-Crawler/2.0 "
    "(Tamil Nadu Agricultural University research crawler; "
    "polite bot; contact agritech.tnau.ac.in)"
)

# ── Skip lists ────────────────────────────────────────────────────────────────

SKIP_DOMAINS: frozenset = frozenset({
    # Social media
    "facebook.com", "fb.com", "m.facebook.com",
    "twitter.com", "x.com",
    "instagram.com",
    "linkedin.com",
    "pinterest.com",
    "reddit.com",
    # Video / streaming
    "youtube.com", "youtu.be",
    "vimeo.com",
    # Google ads & tracking
    "doubleclick.net", "googleadservices.com",
    "googlesyndication.com", "google-analytics.com",
    "ads.google.com", "googletagmanager.com",
    # Messaging
    "whatsapp.com", "wa.me",
    "telegram.org", "t.me",
    # Share widgets
    "addthis.com", "sharethis.com",
    "disqus.com",
    # Other irrelevant
    "amazon.com", "flipkart.com",
})

SKIP_EXTENSIONS: frozenset = frozenset({
    # Images (handled separately with size limit)
    ".jpg", ".jpeg", ".png", ".gif", ".bmp",
    ".webp", ".svg", ".ico", ".tif", ".tiff",
    # Video / audio
    ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv",
    ".mp3", ".wav", ".ogg", ".flac", ".aac",
    # Archives
    ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2",
    # Executables
    ".exe", ".dmg", ".apk", ".msi", ".deb", ".rpm",
    # Fonts / CSS / JS (not content)
    ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
    # Presentation (no easy text extraction without extra libs)
    ".ppt", ".pptx",
    # Legacy Excel (use .xlsx if you add openpyxl later)
    ".xls",
})

# ═════════════════════════════════════════════════════════════════════════════
# AGRI TAXONOMY  (crop & category detection)
# ═════════════════════════════════════════════════════════════════════════════

CROPS: List[str] = [
    # Cereals & millets
    "paddy", "rice", "wheat", "maize", "corn", "sorghum", "jowar",
    "bajra", "pearl millet", "ragi", "finger millet", "barnyard millet",
    "kodo millet", "foxtail millet", "little millet",
    # Cash crops
    "cotton", "sugarcane", "jute", "tobacco",
    # Oilseeds
    "groundnut", "sunflower", "sesame", "gingelly", "castor",
    "mustard", "rapeseed", "linseed", "safflower", "soybean",
    # Fruits
    "banana", "mango", "coconut", "papaya", "guava", "sapota",
    "grapes", "pomegranate", "watermelon", "muskmelon", "jackfruit",
    "fig", "avocado", "pineapple", "strawberry", "jamun",
    "lemon", "lime", "orange", "citrus", "amla", "tamarind",
    "custard apple", "wood apple",
    # Vegetables
    "tomato", "onion", "potato", "brinjal", "eggplant",
    "chilli", "capsicum", "pepper",
    "okra", "bhendi", "ladyfinger",
    "drumstick", "moringa",
    "cabbage", "cauliflower", "carrot", "radish", "beetroot",
    "bitter gourd", "ridge gourd", "bottle gourd", "snake gourd",
    "ivy gourd", "cucumber", "pumpkin", "ash gourd",
    "spinach", "fenugreek leaves", "amaranthus", "curry leaf",
    "cluster bean", "long bean", "french bean",
    # Root & tuber
    "tapioca", "cassava", "yam", "colocasia", "elephant foot yam",
    # Pulses
    "blackgram", "black gram", "greengram", "green gram",
    "redgram", "red gram", "pigeon pea", "tur",
    "chickpea", "bengal gram", "cowpea", "lentil", "horsegram",
    # Spices
    "turmeric", "ginger", "garlic", "coriander", "cumin",
    "fennel", "cardamom", "clove", "nutmeg", "cinnamon",
    # Flowers
    "jasmine", "rose", "chrysanthemum", "marigold",
    "crossandra", "tuberose", "gerbera", "anthurium",
    # Plantation
    "rubber", "coffee", "tea", "cocoa", "arecanut", "cashew",
    "neem", "teak", "eucalyptus", "casuarina", "bamboo",
    # Livestock
    "cattle", "cow", "buffalo", "sheep", "goat", "pig",
    "poultry", "chicken", "duck", "turkey", "quail",
    # Fisheries
    "fish", "prawn", "shrimp", "crab", "mussel", "oyster",
    # Others
    "silkworm", "mushroom",
]

CATEGORIES: Dict[str, List[str]] = {
    "crop_production": [
        "crop", "paddy", "wheat", "maize", "cereal", "pulse",
        "oilseed", "cultivation", "kharif", "rabi", "sowing",
        "transplanting", "harvesting", "yield", "agronomy",
    ],
    "horticulture": [
        "horticulture", "vegetable", "fruit", "flower", "spice",
        "plantation", "orchard", "nursery", "grafting", "pruning",
    ],
    "animal_husbandry": [
        "animal", "livestock", "cattle", "buffalo", "dairy",
        "poultry", "sheep", "goat", "pig", "veterinary",
        "breeding", "feed", "fodder",
    ],
    "fisheries": [
        "fish", "aqua", "fisheries", "shrimp", "prawn", "crab",
        "mariculture", "inland fisheries", "pond", "aquaculture",
    ],
    "soil_management": [
        "soil", "fertilizer", "fertilisation", "nutrient", "compost",
        "organic", "manure", "biofertilizer", "micronutrient", "liming",
        "soil health", "soil fertility",
    ],
    "plant_protection": [
        "pest", "disease", "insect", "fungal", "fungicide",
        "weed", "herbicide", "spray", "pesticide", "bio-control",
        "integrated pest", "ipm", "nematode", "mite", "thrips",
    ],
    "farm_machinery": [
        "machinery", "equipment", "tractor", "implement",
        "mechanization", "thresher", "sprayer", "drip",
        "irrigation", "pump", "harvester",
    ],
    "post_harvest": [
        "post-harvest", "postharvest", "storage", "processing",
        "grading", "value addition", "packaging", "drying",
        "milling", "cold storage",
    ],
    "agro_forestry": [
        "forestry", "agroforestry", "tree", "timber", "wood",
        "plantation crop", "silviculture",
    ],
    "sericulture": ["silk", "silkworm", "sericulture", "mulberry", "reeling"],
    "schemes_subsidies": [
        "scheme", "subsidy", "government", "policy", "programme",
        "program", "loan", "insurance", "pm kisan", "nabard",
    ],
    "research_technology": [
        "research", "variety", "seed", "technology", "innovation",
        "hybrid", "genotype", "breeding", "biotechnology", "tnau",
    ],
    "general": [],
}

# ═════════════════════════════════════════════════════════════════════════════
# LOGGING
# ═════════════════════════════════════════════════════════════════════════════

def _setup_logging(verbose: bool) -> logging.Logger:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)-8s] %(message)s"
    level = logging.DEBUG if verbose else logging.INFO

    handlers = [
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
    # Only add stderr handler if not verbose (tqdm owns the terminal)
    if verbose:
        handlers.append(logging.StreamHandler(sys.stderr))

    logging.basicConfig(level=level, format=fmt, handlers=handlers)
    # Silence noisy libraries
    for lib in ("aiohttp", "chardet", "charset_normalizer", "urllib3"):
        logging.getLogger(lib).setLevel(logging.WARNING)
    return logging.getLogger("tnau")


logger = logging.getLogger("tnau")

# ═════════════════════════════════════════════════════════════════════════════
# URL UTILITIES
# ═════════════════════════════════════════════════════════════════════════════

def normalize_url(url: str, base: str = "") -> Optional[str]:
    """Resolve relative URLs, strip fragment, lowercase scheme+host."""
    try:
        if base:
            url = urljoin(base, url.strip())
        p = urlparse(url)
        if p.scheme not in ("http", "https"):
            return None
        return urlunparse((
            p.scheme.lower(),
            p.netloc.lower(),
            p.path or "/",
            p.params,
            p.query,
            "",          # drop fragment
        ))
    except Exception:
        return None


def _in_skip_domain(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in SKIP_DOMAINS)


def is_allowed_url(url: str) -> bool:
    """True if the URL should be fetched (domain + extension check)."""
    try:
        p = urlparse(url)
        if p.netloc.lower() != ALLOWED_DOMAIN:
            return False
        suffix = Path(p.path).suffix.lower()
        if suffix in SKIP_EXTENSIONS:
            return False
        return True
    except Exception:
        return False


def is_pdf_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(".pdf")


def url_to_local(url: str, base_dir: Path, new_suffix: str = "") -> Path:
    """
    Map URL path → local file path, preserving folder hierarchy.

    https://agritech.tnau.ac.in/agriculture/paddy.html
      → base_dir/agriculture/paddy.html

    https://agritech.tnau.ac.in/horticulture/  (directory)
      → base_dir/horticulture/index.html

    https://agritech.tnau.ac.in/page.php?cat=3  (query string)
      → base_dir/page_q_<hash>.html
    """
    p = urlparse(url)
    path = unquote(p.path).lstrip("/")

    # Incorporate query string as safe hash suffix to avoid collisions
    if p.query:
        q_hash = hashlib.md5(p.query.encode()).hexdigest()[:8]
        stem = Path(path).stem or "index"
        ext  = Path(path).suffix or ".html"
        path = str(Path(path).parent / f"{stem}_q{q_hash}{ext}")

    # Sanitize each path component
    parts = [
        re.sub(r'[<>:"|?*\x00-\x1f\\]', "_", part)
        for part in Path(path).parts
    ]

    if not parts:
        local = base_dir / "index.html"
    elif path.endswith("/") or not Path(parts[-1]).suffix:
        # Directory URL → index.html inside that folder
        local = base_dir.joinpath(*parts) / "index.html"
    else:
        local = base_dir.joinpath(*parts)

    if new_suffix:
        local = local.with_suffix(new_suffix)

    return local


# ═════════════════════════════════════════════════════════════════════════════
# ROBOTS.TXT HANDLER
# ═════════════════════════════════════════════════════════════════════════════

class RobotsHandler:
    """Parse robots.txt once at startup, then gate every URL against it."""

    def __init__(self):
        self._rp = RobotFileParser()
        self._loaded = False
        self._crawl_delay = 0.0

    async def load(self, session: aiohttp.ClientSession) -> None:
        robots_url = f"{BASE_URL}/robots.txt"
        try:
            async with session.get(
                robots_url,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    text = await resp.text(errors="replace")
                    self._rp.parse(text.splitlines())
                    cd = self._rp.crawl_delay(USER_AGENT)
                    self._crawl_delay = float(cd) if cd else 0.0
                    logger.info(
                        f"robots.txt loaded — crawl-delay hint: {self._crawl_delay}s"
                    )
                else:
                    logger.warning(
                        f"robots.txt returned {resp.status} — treating as fully allowed"
                    )
        except Exception as exc:
            logger.warning(f"Could not load robots.txt: {exc}")
        finally:
            self._loaded = True

    def can_fetch(self, url: str) -> bool:
        if not self._loaded:
            return True
        try:
            return bool(self._rp.can_fetch(USER_AGENT, url))
        except Exception:
            return True

    def delay(self, user_default: float) -> float:
        """Return the effective polite delay (max of robots hint and user setting)."""
        return max(self._crawl_delay, user_default)


# ═════════════════════════════════════════════════════════════════════════════
# CRAWLER STATE  (checkpoint / resume)
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class CrawlerState:
    visited: Set[str]          = field(default_factory=set)
    queued:  Set[str]          = field(default_factory=set)
    failed:  Dict[str, int]    = field(default_factory=dict)   # url → fail count
    stats:   Dict[str, int]    = field(default_factory=lambda: {
        "pages_crawled":    0,
        "pdfs_downloaded":  0,
        "tables_extracted": 0,
        "errors":           0,
        "skipped":          0,
        "bytes_saved":      0,
    })

    # ── Persistence ───────────────────────────────────────────────────────

    def save(self) -> None:
        """Atomic write: write to .tmp then rename."""
        tmp = STATE_FILE.with_suffix(".tmp")
        payload = {
            "visited": sorted(self.visited),
            "queued":  sorted(self.queued),
            "failed":  self.failed,
            "stats":   self.stats,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        tmp.replace(STATE_FILE)

    @classmethod
    def load(cls) -> "CrawlerState":
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, encoding="utf-8") as fh:
                    data = json.load(fh)
                s = cls(
                    visited=set(data.get("visited", [])),
                    queued=set(data.get("queued", [])),
                    failed=data.get("failed", {}),
                    stats=data.get("stats", {}),
                )
                logger.info(
                    f"Resuming — {len(s.visited)} visited, "
                    f"{len(s.queued)} queued, "
                    f"{s.stats.get('pages_crawled', 0)} pages crawled"
                )
                return s
            except Exception as exc:
                logger.warning(f"Could not read state file: {exc} — starting fresh")
        return cls()


# ═════════════════════════════════════════════════════════════════════════════
# CONTENT ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════

_TAMIL_RANGE   = ("஀", "௿")
_DEVANAGARI    = ("ऀ", "ॿ")
_TELUGU        = ("ఀ", "౿")

def detect_language(text: str) -> str:
    if not text:
        return "English"
    sample = text[:5000]
    n = len(sample)

    def _ratio(lo: str, hi: str) -> float:
        return sum(1 for c in sample if lo <= c <= hi) / max(n, 1)

    if _ratio(*_TAMIL_RANGE) > 0.04:
        return "Tamil"
    if _ratio(*_DEVANAGARI) > 0.04:
        return "Hindi"
    if _ratio(*_TELUGU) > 0.04:
        return "Telugu"
    return "English"


def detect_crop(text: str) -> str:
    """Return the most-mentioned crop, or 'General'."""
    low = text.lower()
    hits: Dict[str, int] = {}
    for crop in CROPS:
        n = len(re.findall(r"\b" + re.escape(crop) + r"\b", low))
        if n:
            hits[crop] = n
    if not hits:
        return "General"
    return max(hits, key=hits.__getitem__).title()


def detect_category(url: str, title: str, text: str) -> str:
    """Score each category against URL + title + first 3000 chars of body."""
    combined = (url + " " + title + " " + text[:3000]).lower()
    scores: Dict[str, int] = {}
    for cat, keywords in CATEGORIES.items():
        if cat == "general":
            continue
        score = sum(combined.count(kw) for kw in keywords)
        if score:
            scores[cat] = score
    return max(scores, key=scores.__getitem__) if scores else "general"


def clean_text(soup: BeautifulSoup) -> str:
    """Strip boilerplate and return plain text."""
    for tag in soup.find_all(
        ["script", "style", "nav", "footer",
         "iframe", "noscript", "aside", "header"]
    ):
        tag.decompose()
    for cmt in soup.find_all(string=lambda t: isinstance(t, Comment)):
        cmt.extract()
    return " ".join(soup.get_text(separator=" ").split())


def extract_headings(soup: BeautifulSoup) -> List[str]:
    return [
        tag.get_text(strip=True)
        for tag in soup.find_all(["h1", "h2", "h3", "h4"])
        if tag.get_text(strip=True)
    ][:60]


def extract_tables(soup: BeautifulSoup) -> List[List[List[str]]]:
    tables = []
    for tbl in soup.find_all("table"):
        rows = []
        for tr in tbl.find_all("tr"):
            row = [
                cell.get_text(separator=" ", strip=True)
                for cell in tr.find_all(["td", "th"])
            ]
            if any(row):
                rows.append(row)
        if len(rows) > 1:   # skip single-row tables (usually layout tables)
            tables.append(rows)
    return tables


def extract_links(
    soup: BeautifulSoup, page_url: str
) -> Tuple[List[str], List[str]]:
    """
    Returns (follow_links, pdf_links).
    follow_links — HTML pages on our domain to queue
    pdf_links    — PDFs on our domain to download
    """
    follow, pdfs = [], []
    seen: Set[str] = set()

    for a in soup.find_all("a", href=True):
        raw = a["href"].strip()
        if not raw or raw.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        # Skip obvious social / ad patterns
        if _in_skip_domain(raw):
            continue
        skip_kws = (
            "facebook", "twitter", "youtube", "instagram",
            "whatsapp", "linkedin", "doubleclick", "googleapis",
        )
        if any(kw in raw.lower() for kw in skip_kws):
            continue

        url = normalize_url(raw, base=page_url)
        if not url or url in seen:
            continue
        seen.add(url)

        if not is_allowed_url(url):
            continue

        if is_pdf_url(url):
            pdfs.append(url)
        else:
            follow.append(url)

    return follow, pdfs


def to_markdown(html_str: str, page_url: str) -> str:
    """Convert HTML to clean Markdown."""
    soup = BeautifulSoup(html_str, "lxml")

    # Remove boilerplate
    for tag in soup.find_all(
        ["script", "style", "nav", "footer",
         "iframe", "noscript", "aside", "header",
         "form", "button"]
    ):
        tag.decompose()
    for cmt in soup.find_all(string=lambda t: isinstance(t, Comment)):
        cmt.extract()

    # Prefer main content element
    main = (
        soup.find("main")
        or soup.find(id=re.compile(r"(main|content|article|body)", re.I))
        or soup.find(class_=re.compile(r"(main[-_]?content|article|entry)", re.I))
        or soup.find("article")
        or soup.body
        or soup
    )

    md = _md_convert(
        str(main),
        heading_style="ATX",
        bullets="-",
        strip=["img", "script", "style"],
    )

    # Collapse excessive blank lines
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return f"# Source: {page_url}\n\n{md}"


# ═════════════════════════════════════════════════════════════════════════════
# ASYNC FILE I/O
# ═════════════════════════════════════════════════════════════════════════════

async def awrite(path: Path, content) -> int:
    """Write bytes or str to path asynchronously, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        async with aiofiles.open(path, "wb") as fh:
            await fh.write(content)
        return len(content)
    else:
        encoded = content.encode("utf-8")
        async with aiofiles.open(path, "w", encoding="utf-8") as fh:
            await fh.write(content)
        return len(encoded)


async def awrite_json(path: Path, obj: dict) -> None:
    await awrite(path, json.dumps(obj, ensure_ascii=False, indent=2))


async def awrite_table_csv(path: Path, rows: List[List[str]]) -> None:
    """Write a 2D list as CSV, async."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for row in rows:
        escaped = ['"' + cell.replace('"', '""') + '"' for cell in row]
        lines.append(",".join(escaped))
    await awrite(path, "\n".join(lines) + "\n")


# ═════════════════════════════════════════════════════════════════════════════
# MASTER INDEX  (index.csv)
# ═════════════════════════════════════════════════════════════════════════════

INDEX_FIELDS = ["Title", "URL", "Category", "Crop", "Language", "File Type"]


class IndexManager:
    """Thread-safe (asyncio-safe) append-only CSV index."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._seen: Set[str] = set()
        self._init()

    def _init(self) -> None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        if not INDEX_FILE.exists():
            with open(INDEX_FILE, "w", newline="", encoding="utf-8") as fh:
                csv.DictWriter(fh, fieldnames=INDEX_FIELDS).writeheader()
        else:
            # Pre-load existing URLs to skip duplicates on resume
            try:
                with open(INDEX_FILE, encoding="utf-8") as fh:
                    for row in csv.DictReader(fh):
                        self._seen.add(row.get("URL", ""))
            except Exception:
                pass

    async def add(self, entry: Dict[str, str]) -> None:
        url = entry.get("URL", "")
        if url in self._seen:
            return
        async with self._lock:
            if url in self._seen:
                return
            self._seen.add(url)
            # Synchronous write is fast; no need for aiofiles here
            with open(INDEX_FILE, "a", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=INDEX_FIELDS)
                w.writerow({k: entry.get(k, "") for k in INDEX_FIELDS})


# ═════════════════════════════════════════════════════════════════════════════
# MAIN CRAWLER
# ═════════════════════════════════════════════════════════════════════════════

class TNAUCrawler:
    """
    Async crawler that:
    1. Maintains a shared asyncio.Queue of URLs to visit
    2. Runs N concurrent workers (controlled by a Semaphore)
    3. Each worker: fetch → parse → save → enqueue new URLs → delay
    4. Saves checkpoint after every page; resumable on restart
    """

    def __init__(self, args: argparse.Namespace):
        self.args       = args
        self.state      = CrawlerState.load() if args.resume else CrawlerState()
        self.robots     = RobotsHandler()
        self.index      = IndexManager()
        self.semaphore  = asyncio.Semaphore(args.concurrency)
        self.queue: asyncio.Queue = asyncio.Queue()
        self._stop      = False
        self._pbar: Optional[tqdm] = None
        self._save_interval = 25   # checkpoint every N pages

        for d in (HTML_DIR, MD_DIR, PDF_DIR, TABLE_DIR, META_DIR):
            d.mkdir(parents=True, exist_ok=True)

    # ── Entry point ──────────────────────────────────────────────────────────

    async def run(self) -> None:
        session_timeout = aiohttp.ClientTimeout(
            total=TIMEOUT_TOTAL,
            connect=TIMEOUT_CONNECT,
        )
        connector = aiohttp.TCPConnector(
            limit=self.args.concurrency + 4,
            ssl=False,
            enable_cleanup_closed=True,
            keepalive_timeout=30,
        )
        headers = {
            "User-Agent":      USER_AGENT,
            "Accept":          "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
            "Accept-Encoding": "gzip, deflate",
        }

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=session_timeout,
            headers=headers,
        ) as session:
            await self.robots.load(session)

            # Determine effective delay (respect robots.txt hint)
            self._delay = self.robots.delay(self.args.delay)
            logger.info(f"Effective polite delay: {self._delay:.1f}s per worker")

            # Seed queue: from state (resume) + start URL
            seeds = list(self.state.queued - self.state.visited)
            if not seeds:
                seeds = [START_URL]
            for url in seeds:
                await self.queue.put(url)
                self.state.queued.add(url)

            # Progress bar — total unknown (or max_pages if set), show throughput
            self._pbar = tqdm(
                total=self.args.max_pages or None,
                unit="pg",
                desc="TNAU crawl",
                dynamic_ncols=True,
                colour="green",
            )
            self._pbar.set_postfix(queue=0, pdfs=0, errors=0)

            # Spawn workers
            workers = [
                asyncio.create_task(self._worker(session, wid))
                for wid in range(self.args.concurrency)
            ]

            try:
                await self.queue.join()
            except asyncio.CancelledError:
                pass

            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

        if self._pbar is not None:
            self._pbar.close()

        self.state.queued.clear()
        self.state.save()
        self._print_summary()

    # ── Worker coroutine ─────────────────────────────────────────────────────

    async def _worker(self, session: aiohttp.ClientSession, wid: int) -> None:
        while not self._stop:
            try:
                url = await asyncio.wait_for(self.queue.get(), timeout=8.0)
            except asyncio.TimeoutError:
                # Queue temporarily empty — stay alive, more URLs may appear
                continue
            except asyncio.CancelledError:
                break

            try:
                await self._dispatch(session, url)
            except asyncio.CancelledError:
                self.queue.task_done()
                raise
            except Exception as exc:
                logger.error(f"[W{wid}] Unhandled error on {url}: {exc}")
                self.state.stats["errors"] += 1
            finally:
                self.queue.task_done()

            await asyncio.sleep(self._delay)

    # ── URL dispatcher ───────────────────────────────────────────────────────

    async def _dispatch(self, session: aiohttp.ClientSession, url: str) -> None:
        if url in self.state.visited:
            return

        # Max-pages guard
        if self.args.max_pages and (
            self.state.stats["pages_crawled"]
            + self.state.stats["pdfs_downloaded"]
        ) >= self.args.max_pages:
            self._stop = True
            return

        if not self.robots.can_fetch(url):
            logger.debug(f"robots.txt blocked: {url}")
            self.state.visited.add(url)
            self.state.stats["skipped"] += 1
            return

        async with self.semaphore:
            if is_pdf_url(url):
                await self._handle_pdf(session, url)
            else:
                await self._handle_page(session, url)

        # Update progress bar
        if self._pbar is not None:
            s = self.state.stats
            self._pbar.set_postfix(
                queue=self.queue.qsize(),
                pdfs=s["pdfs_downloaded"],
                errors=s["errors"],
                refresh=False,
            )
            self._pbar.update(1)

        # Periodic checkpoint
        total = s["pages_crawled"] + s["pdfs_downloaded"]
        if total % self._save_interval == 0:
            self.state.save()

    # ── HTML page handler ─────────────────────────────────────────────────────

    async def _handle_page(self, session: aiohttp.ClientSession, url: str) -> None:
        body, status, ctype = await self._fetch(session, url)
        if body is None:
            return

        self.state.visited.add(url)

        # If server redirected to a PDF
        if "pdf" in ctype.lower():
            await self._handle_pdf(session, url)
            return

        if "html" not in ctype.lower() and ctype:
            logger.debug(f"Non-HTML content ({ctype}) at {url}, skipping")
            return

        # ── Decode ────────────────────────────────────────────────────────
        try:
            html_str = body.decode("utf-8", errors="replace")
        except Exception:
            html_str = body.decode("latin-1", errors="replace")

        soup = BeautifulSoup(html_str, "lxml")

        # ── Extract ───────────────────────────────────────────────────────
        title_tag = soup.find("title")
        title     = title_tag.get_text(strip=True)[:300] if title_tag else url
        text      = clean_text(BeautifulSoup(html_str, "lxml"))   # fresh parse
        headings  = extract_headings(soup)
        tables    = extract_tables(soup)
        lang      = detect_language(text)
        crop      = detect_crop(title + " " + text[:4000])
        category  = detect_category(url, title, text)

        # ── Discover links ────────────────────────────────────────────────
        follow_links, pdf_links = extract_links(soup, url)

        for link in follow_links:
            if link not in self.state.visited and link not in self.state.queued:
                self.state.queued.add(link)
                await self.queue.put(link)

        for pdf_url in pdf_links:
            if pdf_url not in self.state.visited and pdf_url not in self.state.queued:
                self.state.queued.add(pdf_url)
                await self.queue.put(pdf_url)

        # ── Save HTML ─────────────────────────────────────────────────────
        html_path = url_to_local(url, HTML_DIR)
        if not html_path.suffix:
            html_path = html_path.with_suffix(".html")
        bytes_html = await awrite(html_path, html_str)

        # ── Save Markdown ──────────────────────────────────────────────────
        md_path = url_to_local(url, MD_DIR, ".md")
        await awrite(md_path, to_markdown(html_str, url))

        # ── Save Tables ────────────────────────────────────────────────────
        table_stem = url_to_local(url, TABLE_DIR).stem
        table_base = url_to_local(url, TABLE_DIR).parent
        for idx, table in enumerate(tables, 1):
            tbl_path = table_base / f"{table_stem}_table_{idx:02d}.csv"
            await awrite_table_csv(tbl_path, table)

        # ── Save Metadata ──────────────────────────────────────────────────
        meta = {
            "url":             url,
            "title":           title,
            "crawled_at":      datetime.now(timezone.utc).isoformat(),
            "http_status":     status,
            "content_type":    ctype,
            "content_bytes":   len(body),
            "language":        lang,
            "category":        category,
            "crop":            crop,
            "file_type":       "HTML",
            "headings":        headings,
            "table_count":     len(tables),
            "links_found":     len(follow_links),
            "pdf_links_found": len(pdf_links),
            "word_count":      len(text.split()),
            "local_html":      str(html_path.relative_to(OUTPUT_DIR)),
            "local_markdown":  str(md_path.relative_to(OUTPUT_DIR)),
        }
        await awrite_json(url_to_local(url, META_DIR, ".json"), meta)

        # ── Update index ───────────────────────────────────────────────────
        await self.index.add({
            "Title":     title,
            "URL":       url,
            "Category":  category,
            "Crop":      crop,
            "Language":  lang,
            "File Type": "HTML",
        })

        self.state.stats["pages_crawled"]    += 1
        self.state.stats["tables_extracted"] += len(tables)
        self.state.stats["bytes_saved"]      += bytes_html

        logger.debug(
            f"✓ [{status}] {url}  "
            f"({len(text.split())} words, {len(tables)} tables, "
            f"{len(follow_links)} links, {len(pdf_links)} PDFs)"
        )

    # ── PDF handler ───────────────────────────────────────────────────────────

    async def _handle_pdf(self, session: aiohttp.ClientSession, url: str) -> None:
        body, status, ctype = await self._fetch(session, url)
        if body is None:
            return

        self.state.visited.add(url)

        if len(body) > MAX_PDF_BYTES:
            logger.warning(
                f"PDF too large ({len(body)/1e6:.1f} MB), skipping: {url}"
            )
            return

        # Infer title from filename
        raw_name = Path(urlparse(url).path).stem
        title    = re.sub(r"[_\-]+", " ", raw_name).strip().title() or "Untitled"

        # Infer category/crop from URL + filename
        text_hint  = url + " " + title
        category   = detect_category(url, title, text_hint)
        crop       = detect_crop(text_hint)

        # ── Save PDF ───────────────────────────────────────────────────────
        pdf_path = url_to_local(url, PDF_DIR, ".pdf")
        bytes_pdf = await awrite(pdf_path, body)

        # ── Save Metadata ──────────────────────────────────────────────────
        meta = {
            "url":          url,
            "title":        title,
            "crawled_at":   datetime.now(timezone.utc).isoformat(),
            "http_status":  status,
            "file_size_kb": len(body) // 1024,
            "language":     "Unknown",   # would need PDF text extraction
            "category":     category,
            "crop":         crop,
            "file_type":    "PDF",
            "local_path":   str(pdf_path.relative_to(OUTPUT_DIR)),
        }
        await awrite_json(url_to_local(url, META_DIR, ".json"), meta)

        # ── Update index ───────────────────────────────────────────────────
        await self.index.add({
            "Title":     title,
            "URL":       url,
            "Category":  category,
            "Crop":      crop,
            "Language":  "Unknown",
            "File Type": "PDF",
        })

        self.state.stats["pdfs_downloaded"] += 1
        self.state.stats["bytes_saved"]     += bytes_pdf

        logger.debug(f"📄 PDF [{status}] {url} ({len(body)//1024} KB)")

    # ── HTTP fetch with retry ─────────────────────────────────────────────────

    async def _fetch(
        self,
        session: aiohttp.ClientSession,
        url: str,
        attempt: int = 0,
    ) -> Tuple[Optional[bytes], int, str]:
        """
        Fetch URL; returns (body_bytes, http_status, content_type).
        Returns (None, status, ctype) on skip/failure.
        """
        try:
            async with session.get(url) as resp:
                status = resp.status
                ctype  = resp.headers.get("Content-Type", "")

                if status == 200:
                    clen = int(resp.headers.get("Content-Length", 0))

                    # Skip large images before streaming
                    if "image/" in ctype and clen > MAX_IMAGE_BYTES:
                        logger.debug(f"Skip large image ({clen} B): {url}")
                        return None, status, ctype

                    body = await resp.read()

                    # Double-check images after read (Content-Length absent)
                    if "image/" in ctype and len(body) > MAX_IMAGE_BYTES:
                        return None, status, ctype

                    return body, status, ctype

                # Handle redirects manually to keep domain filter
                elif status in (301, 302, 303, 307, 308):
                    loc = resp.headers.get("Location", "")
                    if loc:
                        redir = normalize_url(loc, base=url)
                        if (
                            redir
                            and redir not in self.state.visited
                            and redir not in self.state.queued
                            and is_allowed_url(redir)
                        ):
                            self.state.queued.add(redir)
                            await self.queue.put(redir)
                    return None, status, ctype

                elif status == 429:
                    wait = int(resp.headers.get("Retry-After", 15))
                    logger.warning(f"Rate-limited, waiting {wait}s: {url}")
                    await asyncio.sleep(wait)
                    if attempt < MAX_RETRIES:
                        return await self._fetch(session, url, attempt + 1)

                elif status >= 500 and attempt < MAX_RETRIES:
                    wait = RETRY_BASE_WAIT ** attempt
                    logger.debug(f"HTTP {status}, retry {attempt+1}: {url}")
                    await asyncio.sleep(wait)
                    return await self._fetch(session, url, attempt + 1)

                else:
                    logger.debug(f"HTTP {status}: {url}")
                    if status not in (403, 404, 410):
                        self.state.stats["errors"] += 1

                return None, status, ctype

        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            if attempt < MAX_RETRIES:
                wait = RETRY_BASE_WAIT ** attempt
                logger.debug(f"Retry {attempt+1}/{MAX_RETRIES} ({exc}): {url}")
                await asyncio.sleep(wait)
                return await self._fetch(session, url, attempt + 1)

            logger.warning(f"Failed after {MAX_RETRIES} retries: {url} — {exc}")
            self.state.failed[url] = attempt + 1
            self.state.stats["errors"] += 1
            return None, 0, ""

    # ── Summary ───────────────────────────────────────────────────────────────

    def _print_summary(self) -> None:
        s  = self.state.stats
        mb = s["bytes_saved"] / 1_048_576

        lines = [
            "",
            "═" * 62,
            "  TNAU Agritech Crawler — COMPLETED",
            "═" * 62,
            f"  Pages crawled       : {s['pages_crawled']:,}",
            f"  PDFs downloaded     : {s['pdfs_downloaded']:,}",
            f"  Tables extracted    : {s['tables_extracted']:,}",
            f"  Errors / skipped    : {s['errors']:,} / {s['skipped']:,}",
            f"  Total bytes saved   : {mb:.1f} MB",
            f"  Unique URLs visited : {len(self.state.visited):,}",
            "",
            f"  Output directory    : {OUTPUT_DIR.resolve()}",
            f"  Master index        : {INDEX_FILE}",
            f"  Log file            : {LOG_FILE}",
            "═" * 62,
        ]
        print("\n".join(lines))
        for line in lines:
            logger.info(line.strip())


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="crawler.py",
        description=(
            "Production-grade async crawler for https://agritech.tnau.ac.in\n"
            "Builds a structured knowledge base with HTML, Markdown, PDFs,\n"
            "extracted tables, metadata JSON, and a master index.csv."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crawler.py                        Fresh crawl (recommended first run)
  python crawler.py --resume               Pick up where we left off
  python crawler.py --concurrency 3        3 workers — gentler on server
  python crawler.py --delay 2.5            2.5 s delay between requests
  python crawler.py --max-pages 500        Stop after 500 pages/PDFs
  python crawler.py --verbose              Print debug logs to console
        """,
    )
    p.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint (.state.json)",
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        metavar="N",
        help=f"Parallel workers (default: {DEFAULT_CONCURRENCY})",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        metavar="SECS",
        help=f"Polite delay in seconds between requests (default: {DEFAULT_DELAY})",
    )
    p.add_argument(
        "--max-pages",
        type=int,
        default=0,
        metavar="N",
        help="Stop after N pages+PDFs (0 = unlimited)",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level console logging",
    )
    return p


# ═════════════════════════════════════════════════════════════════════════════
# GRACEFUL SHUTDOWN
# ═════════════════════════════════════════════════════════════════════════════

_crawler_ref: Optional[TNAUCrawler] = None


def _handle_signal(sig, frame):
    print(
        f"\n\n⚠️  Signal {sig} received — saving checkpoint and exiting...",
        file=sys.stderr,
    )
    if _crawler_ref is not None:
        _crawler_ref._stop = True
        try:
            _crawler_ref.state.save()
            print(
                f"✓ State saved to {STATE_FILE}\n"
                f"  Resume with: python crawler.py --resume",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"⚠️  Could not save state: {e}", file=sys.stderr)
    sys.exit(0)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

async def _main() -> None:
    global _crawler_ref

    args = _build_parser().parse_args()
    _setup_logging(args.verbose)

    print("═" * 62)
    print("  TNAU Agritech Portal Crawler  v2.0")
    print("═" * 62)
    print(f"  Target      : {BASE_URL}")
    print(f"  Output      : {OUTPUT_DIR.resolve()}")
    print(f"  Workers     : {args.concurrency}")
    print(f"  Delay       : {args.delay}s (+ robots.txt hint)")
    print(f"  Max pages   : {args.max_pages or 'unlimited'}")
    print(f"  Resume      : {'Yes — loading checkpoint' if args.resume else 'No — fresh start'}")
    print("═" * 62 + "\n")

    crawler = TNAUCrawler(args)
    _crawler_ref = crawler

    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    await crawler.run()


if __name__ == "__main__":
    asyncio.run(_main())
