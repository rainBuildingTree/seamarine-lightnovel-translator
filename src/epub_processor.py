import asyncio
import uuid
import zipfile
import posixpath
import os
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from translator_core import translate_chunk_with_html, translate_chapter_async, annotate_image, translate_chunk_for_enhance
from dual_language import combine_dual_language
from concurrent.futures import ThreadPoolExecutor

def translate_text_for_completion(text):
    #translated_text = translate_chunk_for_enhance(text)
    #soup = BeautifulSoup(translated_html, "lxml-xml")
    return translate_chunk_for_enhance(text)  

def translate_text(text, chapter_index=0, chunk_index=0):
    html_fragment = f"<div>{text}</div>"
    translated_html = translate_chunk_with_html(html_fragment, chapter_index, chunk_index)
    soup = BeautifulSoup(translated_html, "lxml-xml")
    return soup.get_text()

def force_horizontal_writing(html_content):
    soup = BeautifulSoup(html_content, "lxml-xml")
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

def contains_japanese(text):
    return re.search(r'[\u3040-\u30FF\u4E00-\u9FFF]', text) is not None

def contains_cyrill(text):
    return re.search(r'[\u0400-\u04FF\u0500-\u052F]', text) is not None

def contains_thai(text):
    return re.search(r'[\u0E00-\u0E7F]', text) is not None

def contains_arabic(text):
    return re.search(r'[\u0600-\u06FF\u0750-\u077F]', text) is not None

def contains_hebrew(text):
    return re.search(r'[\u0590-\u05FF]', text) is not None

def contains_devanagari(text):
    return re.search(r'[\u0900-\u097F]', text) is not None

def contains_greek(text):
    return re.search(r'[\u0370-\u03FF]', text) is not None

def contains_foreign(text):
    return (contains_arabic(text) or contains_japanese(text) or contains_cyrill(text) or 
            contains_thai(text) or contains_hebrew(text) or contains_devanagari(text) or contains_greek(text))

async def translate_miscellaneous_async(input_path, output_path, progress_callback=None):
    # Read File Contents
    file_contents = {}
    with zipfile.ZipFile(input_path, 'r') as zin:
        for name in zin.namelist():
            file_contents[name] = zin.read(name)
    if progress_callback:
        progress_callback(10)

    # Find META-INF/container.xml
    container_path = 'META-INF/container.xml'
    if container_path not in file_contents:
        raise ValueError("META-INF/container.xml not found in the EPUB.")
    
    # Retrieve container_tree
    container_tree = ET.fromstring(file_contents[container_path])
    container_ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'} # ns = Namespace

    # Retrieve opf file
    opf_path = None
    rootfile = container_tree.find('.//container:rootfile', container_ns)
    if rootfile is not None:
        opf_path = rootfile.attrib.get('full-path')
    if not opf_path or opf_path not in file_contents:
        raise ValueError("OPF file not found in the EPUB.")
    
    # Get opf data
    opf_data = file_contents[opf_path]

    # Get opf data tree
    opf_tree = ET.fromstring(opf_data)
    ns = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    # Get Epub Version
    epub_version = opf_tree.attrib.get('version', '2.0')
    if epub_version.startswith('1'):
        raise ValueError("EPUB 1.0 is not supported on this program")

    # Get Metadata
    metadata_elem = opf_tree.find('opf:metadata', ns)


    # Update Metadata
    if metadata_elem is not None:
        # Translate title
        title_elem = metadata_elem.find('dc:title', ns)
        if title_elem is not None and title_elem.text:
            original_title = title_elem.text
            translated_title = translate_text(original_title, 0, 0)
            title_elem.text = translated_title
    
    # Update opf File
    opf_updated = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)
    file_contents[opf_path] = opf_updated

    # Find TOC (Table of Contents)
    toc_path = None
    manifest_elem = opf_tree.find('opf:manifest', ns)
    opf_dir = posixpath.dirname(opf_path)
    if manifest_elem is not None:
        # For EPUB2
        if epub_version.startswith('2'):
            spine = opf_tree.find('opf:spine', ns)
            toc_id = spine.attrib.get('toc', None)
            if toc_id:
                for item in manifest_elem.findall('opf:item', ns):
                    if item.attrib.get('id') == toc_id:
                        toc_href = item.attrib.get('href')
                        toc_path = posixpath.join(opf_dir, toc_href)
        # For EPUB3
        else:
            for item in manifest_elem.findall('opf:item', ns):
                if 'properties' in item.attrib and 'nav' in item.attrib['properties']:
                    toc_href = item.attrib.get('href')
                    toc_path = posixpath.join(opf_dir, toc_href)
    if progress_callback:
        progress_callback(20)
    
    # Update TOC
    if epub_version.startswith('2'): # EPUB 2.0
        if toc_path and toc_path in file_contents:
            toc_data = file_contents[toc_path]
            toc_tree = ET.fromstring(toc_data)
            ns_ncx = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
            for navPoint in toc_tree.findall('.//ncx:navPoint', ns_ncx):
                navLabel = navPoint.find('ncx:navLabel', ns_ncx)
                if navLabel is not None:
                    text_elem = navLabel.find('ncx:text', ns_ncx)
                    if text_elem is not None and text_elem.text:
                        text_elem.text = translate_chunk_for_enhance(text_elem.text) #text(text_elem.text, 0, 0)
            toc_updated = ET.tostring(toc_tree, encoding='utf-8', xml_declaration=True)
            file_contents[toc_path] = toc_updated
    else: # EPUB 3.0
        if toc_path and toc_path in file_contents:
            toc_data = file_contents[toc_path]
            toc_soup = BeautifulSoup(toc_data, 'lxml-xml')
            nav = toc_soup.find('nav', attrs={'epub:type': 'toc'})
            if nav:
                for li in nav.find_all('li'):
                    a = li.find('a')
                    if a and a.string:
                        original_text = a.string
                        translated_text = translate_chunk_for_enhance(original_text) #text(original_text, 0, 0)
                        a.string = translated_text
            toc_updated = str(toc_soup).encode('utf-8')
            file_contents[toc_path] = toc_updated
    if progress_callback:
        progress_callback(90)

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

async def translate_epub_async(input_path, output_path, max_concurrent_requests, dual_language, complete_mode, image_annotation_mode, progress_callback=None, proper_nouns=None):
    complete_mode = False
    # Read File Contents
    file_contents = {}
    with zipfile.ZipFile(input_path, 'r') as zin:
        for name in zin.namelist():
            file_contents[name] = zin.read(name)

    # Find META-INF/container.xml
    container_path = 'META-INF/container.xml'
    if container_path not in file_contents:
        raise ValueError("META-INF/container.xml not found in the EPUB.")
    
    # Retrieve container_tree
    container_tree = ET.fromstring(file_contents[container_path])
    container_ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'} # ns = Namespace

    # Retrieve opf file
    opf_path = None
    rootfile = container_tree.find('.//container:rootfile', container_ns)
    if rootfile is not None:
        opf_path = rootfile.attrib.get('full-path')
    if not opf_path or opf_path not in file_contents:
        raise ValueError("OPF file not found in the EPUB.")
    
    # Get opf data
    opf_data = file_contents[opf_path]

    # Get opf data tree
    opf_tree = ET.fromstring(opf_data)
    ns = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    # Get Epub Version
    epub_version = opf_tree.attrib.get('version', '2.0')
    if epub_version.startswith('1'):
        raise ValueError("EPUB 1.0 is not supported on this program")

    # Get Metadata
    metadata_elem = opf_tree.find('opf:metadata', ns)


    # Update Metadata
    if metadata_elem is not None:
        language_elem = metadata_elem.find('dc:language', ns)
        if language_elem is not None:
            language_elem.text = 'ko'
        else:
            new_lang = ET.Element('{http://purl.org/dc/elements/1.1/}language')
            new_lang.text = 'ko'
            metadata_elem.append(new_lang)
        
        # Update Identifier (If it does not exists, add one)
        identifier_elem = metadata_elem.find('dc:identifier', ns)
        new_id = str(uuid.uuid4())
        if identifier_elem is not None:
            identifier_elem.text = new_id
        else:
            new_identifier = ET.Element('{http://purl.org/dc/elements/1.1/}identifier')
            new_identifier.text = new_id
            metadata_elem.append(new_identifier)
        
        # Inject Contributer
        contributor_elem = metadata_elem.find('dc:contributor', ns)
        if contributor_elem is None:
            new_contrib = ET.Element('{http://purl.org/dc/elements/1.1/}contributor')
            new_contrib.text = '귀여운 시마린'
            metadata_elem.append(new_contrib)
    
    # Update opf File
    opf_updated = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)
    file_contents[opf_path] = opf_updated

    # Find TOC (Table of Contents)
    manifest_elem = opf_tree.find('opf:manifest', ns)
    opf_dir = posixpath.dirname(opf_path)

    # Find all chapters
    chapter_files = []
    if manifest_elem is not None:
        for item in manifest_elem.findall('opf:item', ns):
            media_type = item.attrib.get('media-type', '')
            properties = item.attrib.get('properties', '')
            # Exclude items with 'nav' property
            if 'nav' in properties:
                continue
            if media_type in ['application/xhtml+xml', 'text/html']:
                href = item.attrib.get('href')
                chapter_path = posixpath.join(opf_dir, href) if opf_dir else href
                if chapter_path in file_contents:
                    chapter_files.append(chapter_path)
                    
    # Preserve original chapter HTMLs
    original_chapter_htmls = {}
    for chap in chapter_files:
        original_chapter_htmls[chap] = file_contents[chap].decode('utf-8')
    
    for chap, html in original_chapter_htmls.items():
        original_filename = posixpath.basename(chap)
        name, ext = os.path.splitext(original_filename)
        new_filename = f"{name}_original{ext}"
        new_path = posixpath.join('originals', new_filename)
        file_contents[new_path] = html.encode('utf-8')
            
    # Substitute proper nouns
    if proper_nouns:
        # Longer proper nouns first
        proper_nouns = dict(sorted(proper_nouns.items(), key=lambda item: len(item[0]), reverse=True))
        for chap in chapter_files:
            try:
                content = file_contents[chap].decode('utf-8')
                for jp, ko in proper_nouns.items():
                    content = content.replace(jp, ko)
                file_contents[chap] = content.encode('utf-8')
            except Exception as e:
                if progress_callback:
                    progress_callback(0)

    # Translate Chapters
    
    async def wrap_translate(idx, chap_path):
        html = file_contents[chap_path].decode('utf-8')
        translated_html = await translate_chapter_async(html, idx + 1, executor, semaphore)
        return chap_path, translated_html
    
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    executor = ThreadPoolExecutor(max_concurrent_requests)
    total_chapters = len(chapter_files)

    tasks = []
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
        print(f"Processing chapter: {chap}")
        print(f"type of original_chapter_htmls[{chap}]: {type(original_chapter_htmls.get(chap))}")
        print(f"type of results[{chap}]: {type(results.get(chap))}")
        if dual_language:
            original_html = original_chapter_htmls[chap]
            translated_html = results[chap]
            combined_html = combine_dual_language(original_html, translated_html)
            updated_html = force_horizontal_writing(combined_html)
            file_contents[chap] = updated_html.encode('utf-8')
        else:
            updated_html = force_horizontal_writing(results[chap])
            file_contents[chap] = updated_html.encode('utf-8')

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

async def translate_completion_async(input_path, output_path, max_concurrent_requests, dual_language, complete_mode, image_annotation_mode, progress_callback=None, proper_nouns=None):
    complete_mode = True

    # Read File Contents
    file_contents = {}
    with zipfile.ZipFile(input_path, 'r') as zin:
        for name in zin.namelist():
            file_contents[name] = zin.read(name)

    # Find META-INF/container.xml
    container_path = 'META-INF/container.xml'
    if container_path not in file_contents:
        raise ValueError("META-INF/container.xml not found in the EPUB.")
    
    # Retrieve container_tree
    container_tree = ET.fromstring(file_contents[container_path])
    container_ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'} # ns = Namespace

    # Retrieve opf file
    opf_path = None
    rootfile = container_tree.find('.//container:rootfile', container_ns)
    if rootfile is not None:
        opf_path = rootfile.attrib.get('full-path')
    if not opf_path or opf_path not in file_contents:
        raise ValueError("OPF file not found in the EPUB.")
    
    # Get opf data
    opf_data = file_contents[opf_path]

    # Get opf data tree
    opf_tree = ET.fromstring(opf_data)
    ns = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    # Get Epub Version
    epub_version = opf_tree.attrib.get('version', '2.0')
    if epub_version.startswith('1'):
        raise ValueError("EPUB 1.0 is not supported on this program")

    # Get Metadata
    metadata_elem = opf_tree.find('opf:metadata', ns)

    # Update opf File
    opf_updated = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)
    file_contents[opf_path] = opf_updated

    # Find TOC (Table of Contents)
    manifest_elem = opf_tree.find('opf:manifest', ns)
    opf_dir = posixpath.dirname(opf_path)

    results = {}
    # Find all chapters
    chapter_files = []
    if manifest_elem is not None:
        for item in manifest_elem.findall('opf:item', ns):
            media_type = item.attrib.get('media-type', '')
            properties = item.attrib.get('properties', '')
            # Exclude items with 'nav' property
            if 'nav' in properties:
                continue
            if media_type in ['application/xhtml+xml', 'text/html']:
                href = item.attrib.get('href')
                chapter_path = posixpath.join(opf_dir, href) if opf_dir else href
                if chapter_path in file_contents:
                    chapter_files.append(chapter_path)
                    results[chapter_path] = file_contents[chapter_path].decode('utf-8')
                    
    # Preserve original chapter HTMLs
    original_chapter_htmls = {}
    for chap in chapter_files:
        original_chapter_htmls[chap] = file_contents[chap].decode('utf-8')

    for chap, html in original_chapter_htmls.items():
        original_filename = posixpath.basename(chap)
        name, ext = os.path.splitext(original_filename)
        new_filename = f"{name}_original{ext}"
        new_path = posixpath.join('originals', new_filename)
        file_contents[new_path] = html.encode('utf-8')
    
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    executor = ThreadPoolExecutor(max_concurrent_requests)
    total_chapters = len(chapter_files)

    async def reduce_wrapper(chap):
        def reduce_japanese_in_chapter(html):
            miso_soup = BeautifulSoup(html, 'lxml-xml')
            for p in miso_soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                if contains_foreign(p.get_text()):
                    for text_node in p.find_all(string=True):
                        if contains_foreign(text_node):
                            original_text = text_node
                            attempts = 0
                            translated_text = original_text
                            while attempts < 3:
                                try:
                                    candidate = translate_text_for_completion(translated_text)
                                    if len(candidate) > 2 * len(original_text):
                                        attempts += 1
                                    elif contains_foreign(candidate):
                                        attempts += 1
                                        translated_text = candidate
                                    elif len(candidate) == 0:
                                        attempts += 1
                                    else:
                                        translated_text = candidate
                                        attempts = 3
                                except Exception as e:
                                    translated_text = original_text
                                    attempts = 3
                            text_node.replace_with(translated_text)
            return str(miso_soup)
        html = results[chap]
        new_html = await asyncio.get_running_loop().run_in_executor(executor, reduce_japanese_in_chapter, html)
        new_html = force_horizontal_writing(new_html)
        return chap, new_html
    
    reduction_tasks = [asyncio.create_task(reduce_wrapper(chap)) for chap in chapter_files]
    total_reduction = len(reduction_tasks)
    completed_reduction = 0
    for task in asyncio.as_completed(reduction_tasks):
        chap, new_html = await task
        file_contents[chap] = new_html.encode('utf-8')
        completed_reduction += 1
        if progress_callback:
            progress = (completed_reduction / total_reduction) * 90
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

async def annotate_images(input_path, output_path, max_concurrent_requests, dual_language, complete_mode, image_annotation_mode, progress_callback=None, proper_nouns=None):
    image_annotation_mode = True

    # Read File Contents
    file_contents = {}
    with zipfile.ZipFile(input_path, 'r') as zin:
        for name in zin.namelist():
            file_contents[name] = zin.read(name)

    # Find META-INF/container.xml
    container_path = 'META-INF/container.xml'
    if container_path not in file_contents:
        raise ValueError("META-INF/container.xml not found in the EPUB.")
    
    # Retrieve container_tree
    container_tree = ET.fromstring(file_contents[container_path])
    container_ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'} # ns = Namespace

    # Retrieve opf file
    opf_path = None
    rootfile = container_tree.find('.//container:rootfile', container_ns)
    if rootfile is not None:
        opf_path = rootfile.attrib.get('full-path')
    if not opf_path or opf_path not in file_contents:
        raise ValueError("OPF file not found in the EPUB.")
    
    # Get opf data
    opf_data = file_contents[opf_path]

    # Get opf data tree
    opf_tree = ET.fromstring(opf_data)
    ns = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    # Get Epub Version
    epub_version = opf_tree.attrib.get('version', '2.0')
    if epub_version.startswith('1'):
        raise ValueError("EPUB 1.0 is not supported on this program")

    # Get Metadata
    metadata_elem = opf_tree.find('opf:metadata', ns)

    # Update opf File
    opf_updated = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)
    file_contents[opf_path] = opf_updated

    # Find TOC (Table of Contents)
    manifest_elem = opf_tree.find('opf:manifest', ns)
    opf_dir = posixpath.dirname(opf_path)

    results = {}
    # Find all chapters
    chapter_files = []
    if manifest_elem is not None:
        for item in manifest_elem.findall('opf:item', ns):
            media_type = item.attrib.get('media-type', '')
            properties = item.attrib.get('properties', '')
            # Exclude items with 'nav' property
            if 'nav' in properties:
                continue
            if media_type in ['application/xhtml+xml', 'text/html']:
                href = item.attrib.get('href')
                chapter_path = posixpath.join(opf_dir, href) if opf_dir else href
                if chapter_path in file_contents:
                    chapter_files.append(chapter_path)
                    results[chapter_path] = file_contents[chapter_path].decode('utf-8')
                    
    # Preserve original chapter HTMLs
    original_chapter_htmls = {}
    for chap in chapter_files:
        original_chapter_htmls[chap] = file_contents[chap].decode('utf-8')

    for chap, html in original_chapter_htmls.items():
        original_filename = posixpath.basename(chap)
        name, ext = os.path.splitext(original_filename)
        new_filename = f"{name}_original{ext}"
        new_path = posixpath.join('originals', new_filename)
        file_contents[new_path] = html.encode('utf-8')
    
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    executor = ThreadPoolExecutor(max_concurrent_requests)
    total_chapters = len(chapter_files)
    # 이미지 annotation 추가
    if image_annotation_mode:
        for chap in chapter_files:
            try:
                html_content = file_contents[chap].decode('utf-8')
                soup = BeautifulSoup(html_content, 'lxml-xml')

                # 모든 이미지 태그: <img> + <image> (SVG)
                all_images = soup.find_all(['img']) + soup.select('svg image')

                for img in all_images:
                    # 가능한 모든 속성 이름 시도
                    src = (
                        img.get("src") or
                        img.get("xlink:href") or
                        img.get("href") or
                        img.get("{http://www.w3.org/1999/xlink}href")
                    )

                    if not src:
                        print(f"[WARN] No valid image path in tag in {chap}")
                        continue

                    # 상대경로로 변환
                    chapter_dir = posixpath.dirname(chap)
                    image_path = posixpath.join(chapter_dir, src) if chapter_dir else src
                    image_path = posixpath.normpath(image_path)
                    print(f"[INFO] Resolving image path: {image_path}")

                    # 이미지가 EPUB 내부에 존재할 경우만 처리
                    if image_path in file_contents:
                        with zipfile.ZipFile(input_path, 'r') as zf:
                            image_bytes = zf.read(image_path)
                            annotation = annotate_image(image_bytes)
                            new_p = soup.new_tag("p")
                            new_p.append('[[이미지 텍스트:')
                            for i, line in enumerate(annotation.strip().split('\n')):
                                new_p.append(soup.new_tag("br"))
                                new_p.append(line)
                            new_p.append(']]')
                            img.insert_after(new_p)
                    else:
                        print(f"[WARN] Image not found in EPUB: {image_path}")

                # 결과 저장
                file_contents[chap] = str(soup).encode('utf-8')

            except Exception as e:
                print(f"[ERROR] Failed to process {chap}: {e}")
    
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