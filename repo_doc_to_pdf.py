"""
Usage:
  python repo_doc_to_pdf.py --root . --out codebook.pdf --max-bytes 800000 --wrap 100
  --root — корінь проєкту
  --out — шлях до PDF
  --max-bytes — великі файли пропускаються
  --wrap — ширина переносу рядків у символах
"""
import os, sys, argparse, textwrap, pathlib, unicodedata

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

try:
    import chardet
except Exception:
    chardet = None

# Безпечно відрубуємо TeX/MathText
mpl.rcParams["text.usetex"] = False
mpl.rcParams["mathtext.default"] = "rm"

EXCLUDE_DIRS = {
    ".git", ".venv", "__pycache__", ".idea", ".mypy_cache", ".pytest_cache",
    "node_modules", "dist", "build", ".DS_Store","input_audio","outsource","docs"
}
EXCLUDE_EXTS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".pdf",
    ".zip", ".tar", ".gz", ".7z", ".mp4", ".mov", ".mp3", ".wav"
}

EXCLUDE_FILES = {".env", "celerybeat-schedule","interview.log","history.json","agent_history.db"}

def is_text_file(path: str) -> bool:
    ext = pathlib.Path(path).suffix.lower()
    if ext in EXCLUDE_EXTS:
        return False
    try:
        with open(path, "rb") as f:
            chunk = f.read(4096)
        if not chunk:
            return True
        # справжній нуль-байт
        if b"\x00" in chunk:
            return False
        return True
    except Exception:
        return False

def detect_encoding(data: bytes) -> str:
    if chardet:
        try:
            enc = chardet.detect(data).get("encoding")
            if enc:
                return enc
        except Exception:
            pass
    return "utf-8"

def read_text(path: str, max_bytes: int) -> str:
    with open(path, "rb") as f:
        data = f.read()
    if len(data) > max_bytes:
        return f"[SKIPPED: file too large ({len(data)} bytes)]"
    enc = detect_encoding(data)
    try:
        return data.decode(enc, errors="replace")
    except Exception:
        try:
            return data.decode("utf-8", errors="replace")
        except Exception:
            return data.decode("latin-1", errors="replace")

def walk_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".tox")]
        for fn in sorted(filenames):
            if fn in EXCLUDE_FILES:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            if not is_text_file(full):
                continue
            yield rel, full

def build_tree_text(root: str) -> str:
    lines = []
    base = os.path.basename(os.path.abspath(root)) or root
    lines.append(f"{base}/")
    def _print_tree(startpath, prefix=""):
        try:
            items = sorted(
                [n for n in os.listdir(startpath)
                 if n not in EXCLUDE_DIRS and n not in EXCLUDE_FILES]
            )
        except FileNotFoundError:
            return
        for i, name in enumerate(items):
            path = os.path.join(startpath, name)
            connector = "└── " if i == len(items) - 1 else "├── "
            lines.append(prefix + connector + name)
            if os.path.isdir(path):
                extension = "    " if i == len(items) - 1 else "│   "
                _print_tree(path, prefix + extension)
    _print_tree(root)
    return "\n".join(lines)

def sanitize_text(s: str) -> str:
    """Нормалізація для Matplotlib PDF:
    - заміна всіх '$' → '＄' (U+FF04), щоб повністю вимкнути mathtext
    - дроп NULL/контрольні (крім \t \n \r), variation selectors, ZWJ/ZWNJ
    - дроп не-BMP (емодзі), щоб бекенд PDF не падав
    - маппінг деяких проблемних гліфів на ASCII
    """
    if not s:
        return s
    # повністю вимкнути mathtext
    s = s.replace('$', '＄')

    out = []
    for ch in s:
        code = ord(ch)
        if ch == '\x00':
            continue
        cat = unicodedata.category(ch)
        if cat.startswith('C') and ch not in ('\t', '\n', '\r'):
            continue
        if code in (0xFE0F, 0x200D, 0x200C):  # VS16, ZWJ, ZWNJ
            continue
        if code > 0xFFFF:  # emoji / non-BMP
            continue
        if ch in {'✓', '✔'}:
            ch = 'v'
        out.append(ch)
    return ''.join(out)

def add_text_pages(pdf: PdfPages, title: str, text: str, wrap_width=100, font_size=9, header_size=11):
    # sanitize early
    title = sanitize_text(title)
    text = sanitize_text(text)

    # A4 portrait
    page_w, page_h = 8.27, 11.69
    left_margin, right_margin, top_margin, bottom_margin = 0.5, 0.5, 0.7, 0.7
    usable_height = page_h - top_margin - bottom_margin

    # wrap text
    wrapped_lines = []
    for line in text.splitlines():
        line = sanitize_text(line.expandtabs(4))
        wrapped_lines.extend(textwrap.wrap(line, width=wrap_width, replace_whitespace=False) or [""])

    # simple line-height calc
    line_height_in = (font_size * 1.2) / 72.0
    lines_per_page = max(1, int(usable_height / line_height_in) - 4)

    # render
    for page_idx in range(0, len(wrapped_lines) or 1, lines_per_page):
        fig = plt.figure(figsize=(page_w, page_h))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        # header
        ax.text(0.5, 1 - top_margin / page_h + 0.02, title,
                ha="center", va="top", fontsize=header_size, family="monospace")
        # body
        chunk = wrapped_lines[page_idx: page_idx + lines_per_page]
        body_text = "\n".join(chunk) if chunk else ""
        ax.text(left_margin / page_w, 1 - (top_margin + 0.3) / page_h,
                body_text, ha="left", va="top", fontsize=font_size, family="monospace")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root directory")
    ap.add_argument("--out", default="codebook.pdf", help="Output PDF path")
    ap.add_argument("--max-bytes", type=int, default=800000, help="Skip files larger than this many bytes")
    ap.add_argument("--wrap", type=int, default=100, help="Characters per line for wrapping")
    args = ap.parse_args()

    tree_text = build_tree_text(args.root)
    with PdfPages(args.out) as pdf:
        add_text_pages(pdf, "PROJECT TREE", tree_text, wrap_width=args.wrap, font_size=9, header_size=12)
        for rel, full in walk_files(args.root):
            if not is_text_file(full):
                continue
            try:
                content = read_text(full, args.max_bytes)
            except Exception as e:
                content = f"[ERROR reading file: {e}]"
            add_text_pages(pdf, rel, content, wrap_width=args.wrap, font_size=8, header_size=10)

if __name__ == "__main__":
    main()