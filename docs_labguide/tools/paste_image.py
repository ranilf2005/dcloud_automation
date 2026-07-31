#!/usr/bin/env python3
"""Paste a clipboard image into the lab-guide site and insert the Markdown link.

Authoring helper for the multi-page Markdown lab guide under ``docs_labguide/``.
It reads an image from the system clipboard (a screenshot, or an image file you
copied in the file manager), saves it into ``docs_labguide/images/``, and — unless
``--no-insert`` is given — writes a ready ``![alt](images/<file>)`` block (plus an
italic caption if you pass ``--caption``) into the Markdown page you are editing.

Why a script instead of a plain editor paste?
----------------------------------------------
The pages are authored in ``content/<slug>.md`` but the site builder renders each
one to ``docs_labguide/<slug>.html`` (one level up). So an image link must be
written **relative to the built page** — ``images/<file>`` — NOT relative to the
Markdown file. This tool always inserts the correct ``images/<file>`` path, so you
never have to reason about it.

Target page auto-detection: by default the most recently modified
``content/*.md`` file is treated as the page you are working on. Override with
``--page <slug>`` or ``--file <path>``.

Insertion point: if the page contains a ``<!-- paste-image -->`` comment, the
image is inserted just before it; otherwise it is appended to the end of the file.

Examples
--------
    # Auto-detect the page, save + insert the pasted image:
    python tools/paste_image.py

    # Target a page, add a caption:
    python tools/paste_image.py --page lab1-hands-on --caption "CML dashboard"

    # Just save the file and print the snippet, do not edit any Markdown:
    python tools/paste_image.py --no-insert

Requires Pillow:  pip install -r tools/requirements.txt
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths — everything is anchored to docs_labguide/ (this file's parent's parent)
# --------------------------------------------------------------------------- #
DOCS_DIR = Path(__file__).resolve().parent.parent      # docs_labguide/
CONTENT_DIR = DOCS_DIR / "content"                     # the Markdown pages
IMAGES_DIR = DOCS_DIR / "images"                       # where images are saved
# Image src as used from a *built* page (docs_labguide/<slug>.html) — the images
# folder sits next to the HTML, so the src is simply images/<file>.
IMG_SRC_PREFIX = "images"

# If a page contains this marker, images are inserted just before it.
PASTE_MARKER = "<!-- paste-image -->"


# --------------------------------------------------------------------------- #
# Target page discovery
# --------------------------------------------------------------------------- #
def detect_page() -> Path | None:
    """Return the most recently modified content/*.md file."""
    pages = list(CONTENT_DIR.glob("*.md"))
    if not pages:
        return None
    return max(pages, key=lambda p: p.stat().st_mtime)


# --------------------------------------------------------------------------- #
# Clipboard
# --------------------------------------------------------------------------- #
def grab_clipboard_image():
    """Return a PIL.Image from the clipboard, or None if there isn't one.

    Handles a raw bitmap (a screenshot) and a file copied in the OS file manager.
    On Linux, falls back to wl-paste / xclip when Pillow returns None.
    """
    try:
        from PIL import Image, ImageGrab
    except ImportError:
        sys.exit(
            "Pillow is required. Install it with:\n"
            "    pip install -r tools/requirements.txt"
        )

    try:
        data = ImageGrab.grabclipboard()
    except Exception:
        data = None

    if isinstance(data, list):  # a list of file paths was copied
        for name in data:
            try:
                return Image.open(name)
            except Exception:
                continue
        return None
    if data is not None:
        return data  # already a PIL.Image

    # Linux fallback: Pillow's grabclipboard has limited X11/Wayland support.
    if sys.platform.startswith("linux"):
        for cmd in (
            ["wl-paste", "-t", "image/png"],
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
        ):
            try:
                out = subprocess.run(cmd, capture_output=True, timeout=5)
            except (FileNotFoundError, subprocess.SubprocessError):
                continue
            if out.returncode == 0 and out.stdout:
                try:
                    return Image.open(io.BytesIO(out.stdout))
                except Exception:
                    continue
    return None


# --------------------------------------------------------------------------- #
# Saving
# --------------------------------------------------------------------------- #
def next_filename(folder: Path, prefix: str, explicit: str | None) -> str:
    """Pick an output filename, auto-incrementing <prefix>-NN.png by default."""
    if explicit:
        name = explicit
        if not re.search(r"\.(png|jpg|jpeg|gif|webp)$", name, re.IGNORECASE):
            name += ".png"
        return name
    existing = {p.name for p in folder.glob(f"{prefix}-*.png")}
    n = 1
    while f"{prefix}-{n:02d}.png" in existing:
        n += 1
    return f"{prefix}-{n:02d}.png"


def save_image(image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = "PNG"
    if path.suffix.lower() in (".jpg", ".jpeg"):
        fmt = "JPEG"
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
    elif path.suffix.lower() == ".webp":
        fmt = "WEBP"
    elif path.suffix.lower() == ".gif":
        fmt = "GIF"
    image.save(path, fmt)


# --------------------------------------------------------------------------- #
# Markdown insertion
# --------------------------------------------------------------------------- #
def build_block(src: str, alt: str, caption: str | None) -> str:
    """A Markdown image, optionally followed by an italic caption line."""
    block = f"![{alt}]({src})"
    if caption:
        block += f"\n*{caption}*"
    return block


def insert_into_markdown(md_path: Path, block: str) -> bool:
    text = md_path.read_text(encoding="utf-8")
    idx = text.find(PASTE_MARKER)
    if idx != -1:
        line_start = text.rfind("\n", 0, idx) + 1
        new_text = text[:line_start] + block + "\n\n" + text[line_start:]
    else:
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        new_text = text + sep + block + "\n"
    md_path.write_text(new_text, encoding="utf-8")
    return True


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Paste a clipboard image into the Markdown lab guide.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--page", help="Page slug, e.g. lab1-hands-on (default: most recently edited).")
    parser.add_argument("--file", help="Path to the content/*.md file (overrides --page).")
    parser.add_argument("--name", help="Output filename (default: <page>-NN.png).")
    parser.add_argument("--caption", help="Optional italic caption under the image.")
    parser.add_argument("--alt", help="Image alt text (default: derived from caption/page).")
    parser.add_argument("--no-insert", action="store_true", help="Save the image but do not edit any Markdown.")
    args = parser.parse_args()

    # Resolve the target Markdown page.
    if args.file:
        md_path = Path(args.file)
        if not md_path.is_absolute():
            md_path = (Path.cwd() / md_path).resolve()
        if not md_path.exists():
            md_path = CONTENT_DIR / Path(args.file).name
    elif args.page:
        md_path = CONTENT_DIR / f"{args.page}.md"
    else:
        md_path = detect_page()
        if md_path is None:
            print("No content/*.md pages found. Use --page or --file.", file=sys.stderr)
            return 2

    page_slug = md_path.stem

    # Grab the clipboard image.
    image = grab_clipboard_image()
    if image is None:
        print(
            "No image found on the clipboard.\n"
            "Take a screenshot (or copy an image file) and run this again.",
            file=sys.stderr,
        )
        return 1

    # Save it into docs_labguide/images/.
    filename = next_filename(IMAGES_DIR, page_slug, args.name)
    out_path = IMAGES_DIR / filename
    save_image(image, out_path)

    rel_src = f"{IMG_SRC_PREFIX}/{filename}"
    alt = args.alt or args.caption or f"{page_slug} screenshot"
    print(f"Saved image  -> {out_path.relative_to(DOCS_DIR).as_posix()}  ({image.width}x{image.height})")

    block = build_block(rel_src, alt, args.caption)

    if args.no_insert:
        print("\nSnippet (not inserted; --no-insert):\n")
        print(block)
        return 0

    if not md_path.exists():
        print(f"\nPage not found ({md_path.name}); snippet not inserted:\n")
        print(block)
        return 0

    insert_into_markdown(md_path, block)
    where = "before <!-- paste-image -->" if PASTE_MARKER in md_path.read_text(encoding="utf-8") else "at end of file"
    print(f"Inserted     -> content/{md_path.name}  ({where})")
    print(f"Markdown src -> {rel_src}")
    if PASTE_MARKER not in md_path.read_text(encoding="utf-8"):
        print(f"Tip: add '{PASTE_MARKER}' where you want images to land in the page.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
