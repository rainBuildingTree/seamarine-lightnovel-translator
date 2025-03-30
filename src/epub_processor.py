import asyncio
import uuid
import zipfile
import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from translator_core import translate_chunk_with_html, translate_chapter_async
from dual_language import combine_dual_language

# Global flag for dual language mode.
dual_language_mode = True

def set_dual_language_mode(mode):
    global dual_language_mode
    dual_language_mode = mode

def translate_text(text, chapter_index=0, chunk_index=0):
    html_fragment = f"<div>{text}</div>"
    translated_html = translate_chunk_with_html(html_fragment, chapter_index, chunk_index)
    soup = BeautifulSoup(translated_html, "html.parser")
    return soup.get_text()

def force_horizontal_writing(html_content):
    """
    Injects a CSS rule into the HTML content to enforce horizontal text (left-to-right, top-to-bottom).
    """
    soup = BeautifulSoup(html_content, "html.parser")
    head = soup.find("head")
    if head is None:
        # If there's no <head>, create one and insert at the beginning of <html>
        head = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head)
        else:
            # Fallback: insert at the very top.
            soup.insert(0, head)
    # Create a <style> tag with our desired writing mode.
    style_tag = soup.new_tag("style")
    style_tag.string = "body { writing-mode: horizontal-tb !important; }"
    head.append(style_tag)
    return str(soup)

async def translate_epub_async(input_path, output_path, max_concurrent_requests, dual_language, progress_callback=None):
    """
    Translates an EPUB file by reading it as a ZIP archive, updating metadata,
    translating chapter content, and then writing a new EPUB file.
    
    Assumptions:
      - The EPUB has a standard structure with META-INF/container.xml,
        an OPF file, and a TOC (NCX) file.
      - Chapters are identified via manifest items with media types "application/xhtml+xml" or "text/html".
      - Other assets (like images) remain unchanged.
    
    Additionally, the chapter HTML is modified so that text is rendered horizontally
    (left-to-right, top-to-bottom) by injecting a CSS style.
    
    :param input_path: Path to the input EPUB file.
    :param output_path: Path where the translated EPUB will be saved.
    :param max_concurrent_requests: Maximum concurrent translation tasks.
    :param dual_language: Whether to combine original and translated text.
    :param progress_callback: Optional callback for progress updates (0-100).
    :return: The output_path.
    """
    global dual_language_mode
    dual_language_mode = dual_language

    # Read all files from the input EPUB into a dictionary.
    file_contents = {}
    with zipfile.ZipFile(input_path, 'r') as zin:
        for name in zin.namelist():
            file_contents[name] = zin.read(name)
    
    # --- Locate the OPF file via META-INF/container.xml ---
    container_path = 'META-INF/container.xml'
    if container_path not in file_contents:
        raise ValueError("META-INF/container.xml not found in the EPUB.")
    
    container_tree = ET.fromstring(file_contents[container_path])
    container_ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
    opf_path = None
    rootfile = container_tree.find('.//container:rootfile', container_ns)
    if rootfile is not None:
        opf_path = rootfile.attrib.get('full-path')
    if not opf_path or opf_path not in file_contents:
        raise ValueError("OPF file not found in the EPUB.")
    
    # --- Parse and update the OPF file (metadata) ---
    opf_data = file_contents[opf_path]
    opf_tree = ET.fromstring(opf_data)
    ns = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }
    metadata_elem = opf_tree.find('opf:metadata', ns)
    if metadata_elem is not None:
        # Translate the title.
        title_elem = metadata_elem.find('dc:title', ns)
        if title_elem is not None and title_elem.text:
            original_title = title_elem.text
            translated_title = translate_text(original_title, 0, 0)
            title_elem.text = translated_title

        # Set language to Korean.
        language_elem = metadata_elem.find('dc:language', ns)
        if language_elem is not None:
            language_elem.text = 'ko'
        else:
            new_lang = ET.Element('{http://purl.org/dc/elements/1.1/}language')
            new_lang.text = 'ko'
            metadata_elem.append(new_lang)

        # Update identifier.
        identifier_elem = metadata_elem.find('dc:identifier', ns)
        new_id = str(uuid.uuid4())
        if identifier_elem is not None:
            identifier_elem.text = new_id
        else:
            new_identifier = ET.Element('{http://purl.org/dc/elements/1.1/}identifier')
            new_identifier.text = new_id
            metadata_elem.append(new_identifier)

        # Add a contributor "SeaMarine" if not already present.
        contributor_elem = metadata_elem.find('dc:contributor', ns)
        if contributor_elem is None:
            new_contrib = ET.Element('{http://purl.org/dc/elements/1.1/}contributor')
            new_contrib.text = 'SeaMarine'
            metadata_elem.append(new_contrib)

    # Write back the updated OPF.
    opf_updated = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)
    file_contents[opf_path] = opf_updated

    # --- Update the TOC (NCX) file if available ---
    toc_path = None
    manifest_elem = opf_tree.find('opf:manifest', ns)
    opf_dir = os.path.dirname(opf_path)
    if manifest_elem is not None:
        for item in manifest_elem.findall('opf:item', ns):
            media_type = item.attrib.get('media-type', '')
            if media_type in ['application/x-dtbncx+xml', 'application/x-dtbncx+xml; charset=utf-8']:
                toc_href = item.attrib.get('href')
                toc_path = os.path.join(opf_dir, toc_href) if opf_dir else toc_href
                break
    if toc_path and toc_path in file_contents:
        toc_data = file_contents[toc_path]
        toc_tree = ET.fromstring(toc_data)
        ns_ncx = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
        for navPoint in toc_tree.findall('.//ncx:navPoint', ns_ncx):
            navLabel = navPoint.find('ncx:navLabel', ns_ncx)
            if navLabel is not None:
                text_elem = navLabel.find('ncx:text', ns_ncx)
                if text_elem is not None and text_elem.text:
                    text_elem.text = translate_text(text_elem.text, 0, 0)
        toc_updated = ET.tostring(toc_tree, encoding='utf-8', xml_declaration=True)
        file_contents[toc_path] = toc_updated

    # --- Identify chapter files (HTML/XHTML) from the manifest ---
    chapter_files = []
    if manifest_elem is not None:
        for item in manifest_elem.findall('opf:item', ns):
            media_type = item.attrib.get('media-type', '')
            if media_type in ['application/xhtml+xml', 'text/html']:
                href = item.attrib.get('href')
                chapter_path = os.path.join(opf_dir, href) if opf_dir else href
                if chapter_path in file_contents:
                    chapter_files.append(chapter_path)
    
    original_chapter_htmls = {}
    if dual_language_mode:
        for chap in chapter_files:
            original_chapter_htmls[chap] = file_contents[chap].decode('utf-8')
    
    # --- Asynchronously translate chapter content ---
    from concurrent.futures import ThreadPoolExecutor
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    executor = ThreadPoolExecutor(max_concurrent_requests)
    
    total_chapters = len(chapter_files)
    tasks = []
    
    async def wrap_translate(idx, chap_path):
        html = file_contents[chap_path].decode('utf-8')
        translated_html = await translate_chapter_async(html, idx + 1, executor, semaphore)
        return chap_path, translated_html
    
    for idx, chap in enumerate(chapter_files):
        tasks.append(asyncio.create_task(wrap_translate(idx, chap)))
    
    completed = 0
    results = {}
    for task in asyncio.as_completed(tasks):
        chap_path, translated_html = await task
        results[chap_path] = translated_html
        completed += 1
        if progress_callback:
            progress = 10 + (completed / total_chapters) * 80  # Progress from 10% to 90%
            progress_callback(progress)
    
    if progress_callback:
        progress_callback(90)
    
    # --- Update chapter files with translated content and force horizontal writing ---
    for chap in chapter_files:
        if dual_language_mode:
            original_html = original_chapter_htmls[chap]
            translated_html = results[chap]
            combined_html = combine_dual_language(original_html, translated_html)
            updated_html = force_horizontal_writing(combined_html)
            file_contents[chap] = updated_html.encode('utf-8')
        else:
            updated_html = force_horizontal_writing(results[chap])
            file_contents[chap] = updated_html.encode('utf-8')
    
    # --- Write the updated files into a new EPUB archive ---
    # Write the mimetype file first with no compression.
    with zipfile.ZipFile(output_path, 'w') as zout:
        if 'mimetype' in file_contents:
            zout.writestr('mimetype', file_contents['mimetype'], compress_type=zipfile.ZIP_STORED)
        for fname, data in file_contents.items():
            if fname == 'mimetype':
                continue
            zout.writestr(fname, data, compress_type=zipfile.ZIP_DEFLATED)
    
    if progress_callback:
        progress_callback(100)
    return output_path
