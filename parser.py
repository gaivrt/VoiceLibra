import os
import subprocess
import shutil
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def should_skip_content(title: str, text: str) -> bool:
    """判断是否应该跳过这个内容"""
    # 标题关键词过滤
    skip_titles = [
        "版权信息", "copyright", "目录", "contents",
        "前言", "序言", "preface", "introduction",
        "出版信息", "publication", "致谢", "acknowledgments",
        "作者简介", "about the author", "附录", "appendix"
    ]
    
    if title:
        title_lower = title.lower()
        if any(keyword in title_lower for keyword in skip_titles):
            return True
            
    # 内容关键词过滤
    skip_content = [
        "版权所有", "copyright", "all rights reserved",
        "出版社", "publisher", "isbn", "定价",
        "本书编写", "编委会", "责任编辑"
    ]
    
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in skip_content):
        return True
        
    # 内容长度过滤(过短的可能是目录项)
    if len(text.strip()) < 100:
        return True
        
    return False

def merge_short_chapters(chapters: list, min_length: int = 1000) -> list:
    """合并过短的章节"""
    result = []
    temp_chapter = None
    
    for chapter in chapters:
        if not temp_chapter:
            temp_chapter = chapter.copy()
            continue
            
        # 如果当前章节太短，尝试与下一章节合并
        if len(temp_chapter["text"]) < min_length:
            temp_chapter["text"] = temp_chapter["text"] + "\n\n" + chapter["text"]
            temp_chapter["title"] = temp_chapter["title"]  # 保留第一个章节的标题
        else:
            result.append(temp_chapter)
            temp_chapter = chapter.copy()
            
    if temp_chapter:
        result.append(temp_chapter)
        
    return result

def get_first_paragraph(text: str, max_length: int = 200) -> str:
    """
    Extract the first meaningful paragraph from text, limited to max_length characters.
    Tries to break at sentence boundary if possible.
    """
    # Split into paragraphs (by double newlines)
    paragraphs = [p.strip() for p in text.split('\n\n')]
    # Find first non-empty paragraph
    for para in paragraphs:
        if para:
            # If paragraph is too long, try to break at sentence boundary
            if len(para) > max_length:
                # Simple sentence splitting (for Chinese and English)
                sentences = []
                current = ""
                for char in para:
                    current += char
                    if char in '。.!?！？':
                        sentences.append(current)
                        current = ""
                        if len(''.join(sentences)) >= max_length:
                            break
                if sentences:
                    return ''.join(sentences)
                # If can't break at sentence, just truncate
                return para[:max_length] + '...'
            return para
    return ""

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
    chapters = []
    
    # 获取书名
    title = None
    metadata_titles = book.get_metadata('DC', 'title')
    if metadata_titles:
        title = metadata_titles[0][0]
        
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        # 跳过导航文件
        if "nav" in item.get_name().lower():
            continue
            
        content = item.get_content()
        if not content:
            continue
            
        # 解析HTML
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
            
        # 提取标题
        chapter_title = None
        header = soup.find(['h1', 'h2', 'h3', 'h4', 'h5'])
        if header:
            chapter_title = header.get_text().strip()
            
        # 提取正文
        text = soup.get_text(separator="\n").strip()
        
        # 跳过内容检查
        if should_skip_content(chapter_title, text):
            continue
            
        # 如果没找到标题但有正文，尝试从正文开头提取
        if not chapter_title and text:
            lines = text.split('\n')
            # 查找可能的标题行(短行)
            for line in lines[:3]:  # 只检查前3行
                line = line.strip()
                if 10 < len(line) < 50:  # 标题通常是这个长度范围
                    chapter_title = line
                    text = '\n'.join(lines[lines.index(line)+1:])
                    break
                    
        if not chapter_title:
            chapter_title = f"Chapter {len(chapters) + 1}"
            
        chapters.append({
            "title": chapter_title,
            "text": text
        })
        
    # 如果整本书被当作一个章节，尝试分割
    if len(chapters) == 1 and len(chapters[0]["text"]) > 5000:
        text = chapters[0]["text"]
        new_chapters = []
        paragraphs = text.split('\n\n')
        current_chapter = {"title": "Chapter 1", "text": ""}
        
        for para in paragraphs:
            if len(current_chapter["text"]) > 3000:  # 每章大约3000字
                new_chapters.append(current_chapter)
                current_chapter = {
                    "title": f"Chapter {len(new_chapters) + 1}",
                    "text": para
                }
            else:
                current_chapter["text"] += "\n\n" + para
                
        if current_chapter["text"]:
            new_chapters.append(current_chapter)
        chapters = new_chapters
        
    # 合并过短的章节
    chapters = merge_short_chapters(chapters)
    
    return title, chapters
