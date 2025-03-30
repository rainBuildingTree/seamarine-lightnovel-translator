import asyncio
import uuid
import zipfile
import os
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from translator_core import translate_chunk_with_html, translate_chapter_async
from dual_language import combine_dual_language

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
    soup = BeautifulSoup(html_content, "html.parser")
    head = soup.find("head")
    if head is None:
        head = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head)
        else:
            soup.insert(0, head)
    style_tag = soup.new_tag("style")
    style_tag.string = "body { writing-mode: horizontal-tb !important; }"
    head.append(style_tag)
    return str(soup)

async def translate_epub_async(input_path, output_path, max_concurrent_requests, dual_language, complete_mode, progress_callback=None, proper_nouns=None):
    global dual_language_mode
    dual_language_mode = dual_language
    file_contents = {}
    with zipfile.ZipFile(input_path, 'r') as zin:
        for name in zin.namelist():
            file_contents[name] = zin.read(name)
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
    opf_data = file_contents[opf_path]
    opf_tree = ET.fromstring(opf_data)
    ns = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }
    metadata_elem = opf_tree.find('opf:metadata', ns)
    if metadata_elem is not None:
        title_elem = metadata_elem.find('dc:title', ns)
        if title_elem is not None and title_elem.text:
            original_title = title_elem.text
            translated_title = translate_text(original_title, 0, 0)
            title_elem.text = translated_title
        language_elem = metadata_elem.find('dc:language', ns)
        if language_elem is not None:
            language_elem.text = 'ko'
        else:
            new_lang = ET.Element('{http://purl.org/dc/elements/1.1/}language')
            new_lang.text = 'ko'
            metadata_elem.append(new_lang)
        identifier_elem = metadata_elem.find('dc:identifier', ns)
        new_id = str(uuid.uuid4())
        if identifier_elem is not None:
            identifier_elem.text = new_id
        else:
            new_identifier = ET.Element('{http://purl.org/dc/elements/1.1/}identifier')
            new_identifier.text = new_id
            metadata_elem.append(new_identifier)
        contributor_elem = metadata_elem.find('dc:contributor', ns)
        if contributor_elem is None:
            new_contrib = ET.Element('{http://purl.org/dc/elements/1.1/}contributor')
            new_contrib.text = 'SeaMarine'
            metadata_elem.append(new_contrib)
    opf_updated = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)
    file_contents[opf_path] = opf_updated
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
    chapter_files = []
    if manifest_elem is not None:
        for item in manifest_elem.findall('opf:item', ns):
            media_type = item.attrib.get('media-type', '')
            if media_type in ['application/xhtml+xml', 'text/html']:
                href = item.attrib.get('href')
                chapter_path = os.path.join(opf_dir, href) if opf_dir else href
                if chapter_path in file_contents:
                    chapter_files.append(chapter_path)
    # New Feature: Replace proper nouns in chapter files if a dictionary is provided.
    if proper_nouns:
        for chap in chapter_files:
            try:
                content = file_contents[chap].decode('utf-8')
                for jp, ko in proper_nouns.items():
                    content = content.replace(jp, ko)
                file_contents[chap] = content.encode('utf-8')
            except Exception as e:
                if progress_callback:
                    progress_callback(0)
    original_chapter_htmls = {}
    if dual_language_mode:
        for chap in chapter_files:
            original_chapter_htmls[chap] = file_contents[chap].decode('utf-8')
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
            if complete_mode:
                progress = 10 + (completed / total_chapters) * 50
            else:
                progress = 10 + (completed / total_chapters) * 80
            progress_callback(progress)
    if not complete_mode and progress_callback:
        progress_callback(90)
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
    def contains_japanese(text):
        return re.search(r'[\u3040-\u30FF\u4E00-\u9FFF]', text) is not None
    if complete_mode:
        async def reduce_wrapper(chap):
            def reduce_japanese_in_chapter(html):
                miso_soup = BeautifulSoup(html, 'html.parser')
                for p in miso_soup.find_all('p'):
                    if contains_japanese(p.get_text()):
                        for text_node in p.find_all(string=True):
                            if contains_japanese(text_node):
                                original_text = text_node
                                attempts = 0
                                translated_text = original_text
                                while attempts < 3:
                                    candidate = translate_text(original_text)
                                    if contains_japanese(candidate) or len(candidate) > 2 * len(original_text):
                                        attempts += 1
                                        translated_text = candidate
                                    else:
                                        translated_text = candidate
                                        break
                                text_node.replace_with(translated_text)
                return str(miso_soup)
            html = file_contents[chap].decode('utf-8')
            new_html = asyncio.get_running_loop().run_in_executor(executor, reduce_japanese_in_chapter, html)
            new_html = await new_html
            return chap, new_html
        reduction_tasks = [asyncio.create_task(reduce_wrapper(chap)) for chap in chapter_files]
        total_reduction = len(reduction_tasks)
        completed_reduction = 0
        for task in asyncio.as_completed(reduction_tasks):
            chap, new_html = await task
            file_contents[chap] = new_html.encode('utf-8')
            completed_reduction += 1
            if progress_callback:
                progress = 60 + (completed_reduction / total_reduction) * 40
                progress_callback(progress)
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