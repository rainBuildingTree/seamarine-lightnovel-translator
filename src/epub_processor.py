import asyncio
import uuid
from ebooklib import epub
from ebooklib.epub import EpubHtml
from bs4 import BeautifulSoup
from translator_core import translate_chunk_with_html, translate_chapter_async
from dual_language import combine_dual_language

dual_language_mode = True
def set_dual_language_mode(set):
    global dual_language_mode
    dual_language_mode = set

def translate_text(text, chapter_index=0, chunk_index=0):
    html_fragment = f"<div>{text}</div>"
    translated_html = translate_chunk_with_html(html_fragment, chapter_index, chunk_index)
    soup = BeautifulSoup(translated_html, "html.parser")
    return soup.get_text()


def translate_toc_entry(entry, chapter_index=0, chunk_index=0):
    if hasattr(entry, 'title'):
        entry.title = translate_text(entry.title, chapter_index, chunk_index)
        return entry
    elif isinstance(entry, tuple) and len(entry) == 2:
        link, subitems = entry
        link.title = translate_text(link.title, chapter_index, chunk_index)
        new_subitems = [translate_toc_entry(sub, chapter_index, chunk_index) for sub in subitems]
        return (link, new_subitems)
    else:
        return entry


async def translate_epub_async(input_path, output_path, max_concurrent_requests, dual_language, progress_callback=None):
    """
    Translates an EPUB file from Japanese to Korean.

    Progress updates:
      - After the first LLM (chapter) response: ~10%
      - As chapters are translated: progress increases from 10% to 90%
      - After file writing is complete: 100%

    :param input_path: Path to the input EPUB file.
    :param output_path: Path to write the translated EPUB file.
    :param max_concurrent_requests: Maximum number of concurrent translation requests.
    :param progress_callback: (Optional) A callback function receiving a percentage (0-100).
    :return: The output path.
    """
    # Set dual language flag
    global dual_language_mode
    dual_language_mode = dual_language
    # Read the original EPUB and copy all items to the translated_book.
    book = epub.read_epub(input_path)
    translated_book = epub.EpubBook()

    translated_book.toc = book.toc
    translated_book.spine = book.spine

    for item in book.get_items():
        new_uid = item.get_id()
        new_item = epub.EpubItem(
            uid=new_uid,
            file_name=item.file_name,
            media_type=item.media_type,
            content=item.content
        )
        translated_book.add_item(new_item)
        
    toc_item = translated_book.get_item_with_id("toc.ncx")
    if toc_item:
        toc_item.id = "ncx"

    translated_book.set_identifier(f'{uuid.uuid4()}')

    # Translate book title.
    metadata_title = book.get_metadata('DC', 'title')
    if metadata_title:
        original_title = metadata_title[0][0]
        translated_title = translate_text(original_title, chapter_index=0, chunk_index=0)
        translated_book.set_title(translated_title)

    translated_book.set_language('ko')

    # Set cover and authors.
    cover = book.get_item_with_id('cover')
    if cover:
        translated_book.set_cover(cover.file_name, cover.content)
    creators = book.get_metadata('DC', 'creator')
    for creator in creators:
        translated_book.add_author(creator[0])
    translated_book.add_metadata('DC', 'contributor', 'SeaMarine')

    # Set TOC and spine.
    #translated_book.toc = book.toc
    #translated_book.spine = book.spine

    epub.write_epub(output_path, translated_book)
    translated_book = epub.read_epub(output_path)
    
    translated_book.toc = [translate_toc_entry(entry, chapter_index=0, chunk_index=0) for entry in translated_book.toc]

    # Get chapter items for translation.
    chapter_items = [item for item in translated_book.get_items() if isinstance(item, EpubHtml)]

    original_chapter_htmls = []
    if dual_language_mode:
        for item in chapter_items:
            original_chapter_htmls.append(item.get_content().decode('utf-8'))

    # Setup asynchronous translation using a thread pool.
    from concurrent.futures import ThreadPoolExecutor
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    executor = ThreadPoolExecutor(max_concurrent_requests)

    total_chapters = len(chapter_items)
    tasks = []

    async def wrap_translate(idx, html):
        translated_html = await translate_chapter_async(html, idx + 1, executor, semaphore)
        return idx, translated_html

    for idx, item in enumerate(chapter_items):
        html = item.get_content().decode('utf-8')
        tasks.append(asyncio.create_task(wrap_translate(idx, html)))

    completed = 0
    results = {}
    # As each chapter translation completes, update progress.
    for task in asyncio.as_completed(tasks):
        idx, translated_html = await task
        results[idx] = translated_html
        completed += 1
        if progress_callback:
            # Progress increases from 10% to 90% based on completed chapters.
            progress = 10 + (completed / total_chapters) * 80
            progress_callback(progress)

    if progress_callback:
        progress_callback(90)

    for idx in range(total_chapters):
        if dual_language_mode:
            original_html = original_chapter_htmls[idx]
            translated_html = results[idx]
            combined_html = combine_dual_language(original_html, translated_html)
            chapter_items[idx].set_content(combined_html.encode('utf-8'))
        else:
            chapter_items[idx].set_content(results[idx].encode('utf-8'))

    # Set translated content for each chapter in original order.
    #for idx in range(total_chapters):
    #    chapter_items[idx].set_content(results[idx].encode('utf-8'))

    epub.write_epub(output_path, translated_book)
    if progress_callback:
        progress_callback(100)
    return output_path
