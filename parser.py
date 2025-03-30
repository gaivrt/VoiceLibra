import os
import subprocess
import shutil
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def convert_to_epub(input_path: str) -> str:
    """
    Convert the given ebook file to EPUB format using Calibre's ebook-convert if needed.
    Returns the path to the EPUB file (which may be the original if it was already EPUB).
    """
    # If input is already .epub, return it
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".epub":
        return input_path
    # Check that Calibre's ebook-convert is available
    if not shutil.which("ebook-convert"):
        raise FileNotFoundError("Calibre's ebook-convert tool is not found. Please install Calibre to convert e-books.")
    # Define output epub path
    output_path = os.path.splitext(input_path)[0] + ".epub"
    try:
        # Run the conversion
        subprocess.run(["ebook-convert", input_path, output_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Conversion to EPUB failed: {e.stderr.decode('utf-8', errors='ignore')}")
    return output_path

def parse_epub(epub_path: str):
    """
    Parse the given EPUB file and extract chapters.
    Returns a tuple (book_title, chapters) where chapters is a list of dict {title, text}.
    """
    book = epub.read_epub(epub_path)
    # Attempt to get book title from metadata
    title = None
    metadata_titles = book.get_metadata('DC', 'title')
    if metadata_titles:
        title = metadata_titles[0][0]
    # Iterate over document items (chapters)
    chapters = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        # Skip items that are likely not content (like nav or css)
        # EPUB nav (table of contents) is typically ITEM_NAV or type 'toc'
        if item.get_name().endswith("nav.xhtml") or item.get_name().endswith("nav.htm"):
            continue
        # Get raw HTML content
        content = item.get_content()
        if not content:
            continue
        # Parse HTML content to extract text
        soup = BeautifulSoup(content, "html.parser")
        # Remove scripts, styles if any
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        text = text.strip()
        if not text:
            continue
        # Determine chapter title: use item title if exists in metadata or first heading
        chapter_title = None
        # Check if this item has a title in the EPUB Spine/TOC
        # ebooklib's get_metadata for 'title' doesn't apply to chapters easily, so find first header tag as title
        header = soup.find(['h1', 'h2', 'h3', 'h4', 'h5'])
        if header:
            chapter_title = header.get_text().strip()
        if not chapter_title:
            # Fallback: use file name or generic "Chapter X"
            chapter_title = f"Chapter {len(chapters) + 1}"
        chapters.append({"title": chapter_title, "text": text})
    # If no chapters found (maybe plain text?), treat entire text as one chapter
    if not chapters:
        # In case the EPUB had no clear chapter splits, just use full text
        full_text = ""
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            if item.get_name().endswith("nav.xhtml") or item.get_name().endswith("nav.htm"):
                continue
            content = item.get_content()
            if content:
                soup = BeautifulSoup(content, "html.parser")
                for tag in soup(["script", "style"]):
                    tag.decompose()
                text = soup.get_text(separator="\n").strip()
                full_text += text + "\n"
        full_text = full_text.strip()
        if full_text:
            chapters = [{"title": title or "Chapter 1", "text": full_text}]
    return title, chapters
