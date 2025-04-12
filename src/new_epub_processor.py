import asyncio
import uuid
import zipfile
import posixpath
import os
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from translator_core import (
    translate_chunk_with_html,
    translate_chapter_async,
    annotate_image,
    translate_chunk_for_enhance,
    translate_text_simple
)
from dual_language import combine_dual_language
from concurrent.futures import ThreadPoolExecutor
import string
import pycountry

# --- 유틸리티 함수들 ---

def translate_text_for_completion(text: str, language: str) -> str:
    """번역 완성 모드에서 단순 텍스트 번역 (예: enhancement 전용)."""
    return translate_chunk_for_enhance(text, language)

def translate_text(text: str, chapter_index: int = 0, chunk_index: int = 0, language: str = 'Japanese') -> str:
    """HTML 래핑 후 chunk 별 번역 후 순수 텍스트 추출."""
    html_fragment = f"<div>{text}</div>"
    translated_html = translate_chunk_with_html(html_fragment, chapter_index, chunk_index, language)
    soup = BeautifulSoup(translated_html, "lxml-xml")
    return soup.get_text()

def get_language_name(code: str, default: str) -> str:
    """ISO 코드(2자리, 3자리 등)를 이용하여 언어 이름을 반환."""
    code = code.lower()
    lang = pycountry.languages.get(alpha_2=code)
    if lang:
        return lang.name
    lang = pycountry.languages.get(alpha_3=code)
    if lang:
        return lang.name
    for lang in pycountry.languages:
        if hasattr(lang, 'bibliographic') and lang.bibliographic == code:
            return lang.name
        if hasattr(lang, 'terminology') and lang.terminology == code:
            return lang.name
    return default

def contains_japanese(text: str) -> bool:
    filtered = re.sub(r'[・ー]', '', text)
    return re.search(r'[\u3040-\u30FF\u4E00-\u9FFF]', filtered) is not None

def contains_cyrill(text: str) -> bool:
    return re.search(r'[\u0400-\u04FF\u0500-\u052F]', text) is not None

def contains_thai(text: str) -> bool:
    return re.search(r'[\u0E00-\u0E7F]', text) is not None

def contains_arabic(text: str) -> bool:
    return re.search(r'[\u0600-\u06FF\u0750-\u077F]', text) is not None

def contains_hebrew(text: str) -> bool:
    return re.search(r'[\u0590-\u05FF]', text) is not None

def contains_devanagari(text: str) -> bool:
    return re.search(r'[\u0900-\u097F]', text) is not None

def contains_greek(text: str) -> bool:
    return re.search(r'[\u0370-\u03FF]', text) is not None

def contains_english(text: str) -> bool:
    english_char_count = sum(1 for c in text if c in string.ascii_letters)
    total_alpha_count = sum(1 for c in text if c.isalpha())
    if total_alpha_count == 0:
        return False
    return english_char_count / total_alpha_count > 0.5

def contains_foreign(text: str, is_include_english: bool = False) -> bool:
    return (contains_arabic(text) or contains_japanese(text) or contains_cyrill(text) or
            (contains_english(text) if is_include_english else False) or
            contains_thai(text) or contains_hebrew(text) or contains_devanagari(text) or contains_greek(text))

# --- EPUBProcessor 클래스 ---

class EPUBProcessor:
    def __init__(self, input_path: str):
        self.input_path = input_path
        self.file_contents = self._load_epub_contents()
        self.original_file_contents = {}
    
    def _load_epub_contents(self) -> dict:
        contents = {}
        with zipfile.ZipFile(self.input_path, 'r') as zin:
            for name in zin.namelist():
                contents[name] = zin.read(name)
        return contents
    
    def save(self, output_path: str, progress_callback=None) -> str:
        with zipfile.ZipFile(output_path, 'w') as zout:
            if 'mimetype' in self.file_contents:
                zout.writestr('mimetype', self.file_contents['mimetype'], compress_type=zipfile.ZIP_STORED)
            for fname, data in self.file_contents.items():
                if fname == 'mimetype':
                    continue
                zout.writestr(fname, data, compress_type=zipfile.ZIP_DEFLATED)
        if progress_callback:
            progress_callback(100)
        return output_path
    
    def get_container_tree(self) -> ET.Element:
        container_path = 'META-INF/container.xml'
        if container_path not in self.file_contents:
            raise ValueError("META-INF/container.xml not found in the EPUB.")
        return ET.fromstring(self.file_contents[container_path])
    
    def get_opf_tree_and_path(self) -> tuple[ET.Element, str]:
        container_tree = self.get_container_tree()
        container_ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
        rootfile = container_tree.find('.//container:rootfile', container_ns)
        if rootfile is None:
            raise ValueError("rootfile not found in container.xml")
        opf_path = rootfile.attrib.get('full-path')
        if not opf_path or opf_path not in self.file_contents:
            raise ValueError("OPF file not found in the EPUB.")
        opf_tree = ET.fromstring(self.file_contents[opf_path])
        return opf_tree, opf_path
    
    def get_language(self) -> str:
        opf_tree, opf_path = self.get_opf_tree_and_path()
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        metadata_elem = opf_tree.find('opf:metadata', ns)
        if metadata_elem is None:
            raise ValueError("Metadata not found in OPF file.")

        language_elem = metadata_elem.find('dc:language', ns)
        if language_elem is not None:
            return get_language_name(language_elem.text.strip(), 'Japanese')
        return 'Japanese'


    
    def update_metadata_epub(self, lang: str = 'ko', contributor: str = '귀여운 시마린'):
        """translate_epub_async에서 사용하는 메타데이터 업데이트: 언어, identifier, contributor 추가."""
        opf_tree, opf_path = self.get_opf_tree_and_path()
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        metadata_elem = opf_tree.find('opf:metadata', ns)
        if metadata_elem is None:
            raise ValueError("Metadata not found in OPF file.")
        # 언어 업데이트
        language_elem = metadata_elem.find('dc:language', ns)
        if language_elem is not None:
            language_elem.text = lang
        else:
            new_lang = ET.Element('{http://purl.org/dc/elements/1.1/}language')
            new_lang.text = lang
            metadata_elem.append(new_lang)
        # identifier 업데이트
        identifier_elem = metadata_elem.find('dc:identifier', ns)
        new_id = str(uuid.uuid4())
        if identifier_elem is not None:
            identifier_elem.text = new_id
        else:
            new_identifier = ET.Element('{http://purl.org/dc/elements/1.1/}identifier')
            new_identifier.text = new_id
            metadata_elem.append(new_identifier)
        # contributor 추가 (없으면)
        contributor_elem = metadata_elem.find('dc:contributor', ns)
        if contributor_elem is None:
            new_contrib = ET.Element('{http://purl.org/dc/elements/1.1/}contributor')
            new_contrib.text = contributor
            metadata_elem.append(new_contrib)
        # 변경된 OPF를 다시 저장
        self.file_contents[opf_path] = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)
    
    def get_chapter_files(self, opf_tree: ET.Element, opf_path: str) -> list:
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
        }
        manifest_elem = opf_tree.find('opf:manifest', ns)
        opf_dir = posixpath.dirname(opf_path)
        chapter_files = []
        if manifest_elem is not None:
            for item in manifest_elem.findall('opf:item', ns):
                media_type = item.attrib.get('media-type', '')
                properties = item.attrib.get('properties', '')
                if 'nav' in properties:
                    continue
                if media_type in ['application/xhtml+xml', 'text/html']:
                    href = item.attrib.get('href')
                    chapter_path = posixpath.join(opf_dir, href) if opf_dir else href
                    if chapter_path in self.file_contents:
                        chapter_files.append(chapter_path)
        return chapter_files
    
    def preserve_original_chapters(self, chapter_files: list):
        """원본 챕터 HTML을 'originals/' 폴더에 저장."""
        self.original_file_contents = {}
        for chap in chapter_files:
            original_html = self.file_contents[chap].decode('utf-8')
            self.original_file_contents[chap] = self.file_contents[chap]
            original_filename = posixpath.basename(chap)
            name, ext = posixpath.splitext(original_filename)
            new_filename = f"{name}_original{ext}"
            new_path = posixpath.join('seamarine_originals', new_filename)
            self.file_contents[new_path] = original_html.encode('utf-8')
    
    def load_original_chapters(self):
        """원본 챕터 HTML을 self.original_file_contents에 로드"""
        with zipfile.ZipFile(self.input_path, 'r') as zin:
            for name in zin.namelist():
                full_file_name = posixpath.basename(name)
                filename, _ = posixpath.splitext(full_file_name)
                if filename.endswith('_original'):
                    self.original_file_contents[full_file_name] = zin.read(name)
    @staticmethod
    def force_horizontal_writing(html_content: str) -> str:
        """HTML 내에 head에 writing-mode 스타일을 추가."""
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
    
    # --- 비동기 EPUB 처리 메소드들 ---
    
    async def translate_miscellaneous_async(self, output_path: str, progress_callback=None) -> str:
        """
        EPUB의 메타데이터(예: 제목)와 목차(TOC)를 번역하는 기능.
        EPUB 버전에 따라 EPUB2/EPUB3의 TOC 업데이트 방식을 분리함.
        """
        language = self.get_language()

        opf_tree, opf_path = self.get_opf_tree_and_path()
        ns = {'opf': 'http://www.idpf.org/2007/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}
        metadata_elem = opf_tree.find('opf:metadata', ns)
        if metadata_elem is not None:
            title_elem = metadata_elem.find('dc:title', ns)
            if title_elem is not None and title_elem.text:
                original_title = title_elem.text
                translated_title = translate_text_simple(original_title, language)
                title_elem.text = translated_title
        self.file_contents[opf_path] = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)
        if progress_callback:
            progress_callback(10)
        
        # TOC 업데이트
        manifest_elem = opf_tree.find('opf:manifest', ns)
        epub_version = opf_tree.attrib.get('version', '2.0')
        opf_dir = posixpath.dirname(opf_path)
        toc_path = None
        if manifest_elem is not None:
            if epub_version.startswith('2'):
                spine = opf_tree.find('opf:spine', ns)
                toc_id = spine.attrib.get('toc', None) if spine is not None else None
                if toc_id:
                    for item in manifest_elem.findall('opf:item', ns):
                        if item.attrib.get('id') == toc_id:
                            toc_href = item.attrib.get('href')
                            toc_path = posixpath.join(opf_dir, toc_href)
                            break
            else:
                for item in manifest_elem.findall('opf:item', ns):
                    if 'properties' in item.attrib and 'nav' in item.attrib['properties']:
                        toc_href = item.attrib.get('href')
                        toc_path = posixpath.join(opf_dir, toc_href)
                        break
        if progress_callback:
            progress_callback(20)
        
        if toc_path and toc_path in self.file_contents:
            if epub_version.startswith('2'):
                toc_data = self.file_contents[toc_path]
                toc_tree = ET.fromstring(toc_data)
                ns_ncx = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
                for navPoint in toc_tree.findall('.//ncx:navPoint', ns_ncx):
                    navLabel = navPoint.find('ncx:navLabel', ns_ncx)
                    if navLabel is not None:
                        text_elem = navLabel.find('ncx:text', ns_ncx)
                        if text_elem is not None and text_elem.text:
                            text_elem.text = translate_text_simple(text_elem.text, language)
                updated_toc = ET.tostring(toc_tree, encoding='utf-8', xml_declaration=True)
                self.file_contents[toc_path] = updated_toc
            else:
                toc_data = self.file_contents[toc_path]
                toc_soup = BeautifulSoup(toc_data, 'lxml-xml')
                nav = toc_soup.find('nav', attrs={'epub:type': 'toc'})
                if nav:
                    for li in nav.find_all('li'):
                        a = li.find('a')
                        if a and a.string:
                            original_text = a.string
                            translated_text = translate_text_simple(original_text, language)
                            a.string = translated_text
                updated_toc = str(toc_soup).encode('utf-8')
                self.file_contents[toc_path] = updated_toc
        if progress_callback:
            progress_callback(90)
        self.save(output_path, progress_callback)
        if progress_callback:
            progress_callback(100)
        return output_path
    
    # 1. translate_epub_async 함수에서 dual_language 처리를 제거합니다.
    async def translate_epub_async(
        self, output_path: str, max_concurrent_requests: int,
        complete_mode: bool,
        progress_callback=None, proper_nouns: dict = None
    ) -> str:
        """
        EPUB 전체 본문 번역 작업.
        - 메타데이터(언어, identifier, contributor) 업데이트
        - manifest에서 챕터 추출 및 원본 챕터 보존
        - proper_nouns 치환 (있다면)
        - 각 챕터를 translate_chapter_async로 번역 후 force_horizontal_writing 적용
        """
        language = self.get_language()

        self.update_metadata_epub()  # 기본 메타데이터 업데이트
        
        opf_tree, opf_path = self.get_opf_tree_and_path()
        chapter_files = self.get_chapter_files(opf_tree, opf_path)
        self.preserve_original_chapters(chapter_files)
        
        if proper_nouns:
            # proper_nouns가 있다면 길이가 긴 단어부터 먼저 치환
            proper_nouns = dict(sorted(proper_nouns.items(), key=lambda item: len(item[0]), reverse=True))
            for chap in chapter_files:
                try:
                    content = self.file_contents[chap].decode('utf-8')
                    for jp, ko in proper_nouns.items():
                        content = content.replace(jp, ko)
                    self.file_contents[chap] = content.encode('utf-8')
                except Exception:
                    if progress_callback:
                        progress_callback(0)
        
        semaphore = asyncio.Semaphore(max_concurrent_requests)
        executor = ThreadPoolExecutor(max_concurrent_requests)
        total_chapters = len(chapter_files)
        
        async def wrap_translate(idx, chap_path):
            html = self.file_contents[chap_path].decode('utf-8')
            translated_html = await translate_chapter_async(html, idx + 1, executor, semaphore)
            return chap_path, translated_html
        
        tasks = [asyncio.create_task(wrap_translate(idx, chap)) for idx, chap in enumerate(chapter_files)]
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
                progress_callback(int(progress))
        
        if not complete_mode and progress_callback:
            progress_callback(90)
        
        # dual language 처리 분기 제거: 단순히 번역 결과에 force_horizontal_writing 적용
        for chap in chapter_files:
            updated_html = self.force_horizontal_writing(results[chap])
            self.file_contents[chap] = updated_html.encode('utf-8')
        
        self.save(output_path, progress_callback)
        if progress_callback:
            progress_callback(100)
        return output_path


    # 2. 새로운 dual language 적용 함수 (비동기 버전) 생성
    async def apply_dual_language_async(self, output_path: str, progress_callback=None) -> str:
        """
        별도로 원본과 번역문을 결합하여 dual language 형식의 EPUB을 만드는 함수.
        - load_original_chapters 호출하여 원본 챕터들을 로드
        - 원본 파일이 없다면 ValueError 발생
        - 각 챕터에 대해 원본과 번역문을 결합(combine_dual_language)하고 force_horizontal_writing 적용
        - 결과를 output_path에 저장
        """
        # 원본 챕터 로드: 만약 이미 preserve_original_chapters 호출 후 진행된 경우라면 해당 데이터를 사용,
        # 그렇지 않으면 load_original_chapters를 통해 로드 (파일 내 '_original' 패턴 확인)

        opf_tree, opf_path = self.get_opf_tree_and_path()
        chapter_files = self.get_chapter_files(opf_tree, opf_path)
        
        total = len(chapter_files)
        for i, chap in enumerate(chapter_files, start=1):
            if chap not in self.file_contents:
                print("WTF")
                continue
            origin_chap, ext = posixpath.splitext(posixpath.basename(chap))
            if 'seamarine_originals/'+origin_chap+'_original'+ext not in self.file_contents:
                print(f"WTF2{origin_chap+'_original'+ext}")
                continue
            original_html = self.file_contents['seamarine_originals/'+origin_chap+'_original'+ext].decode('utf-8')
            # 현재 self.file_contents에는 번역된 챕터가 있다고 가정 (translate_epub_async를 먼저 실행)
            translated_html = self.file_contents[chap].decode('utf-8')
            combined_html = combine_dual_language(original_html, translated_html)
            updated_html = self.force_horizontal_writing(combined_html)
            self.file_contents[chap] = updated_html.encode('utf-8')
            if progress_callback:
                progress_callback(int((i/total)*100))
        
        self.save(output_path, progress_callback)
        if progress_callback:
            progress_callback(100)
        return output_path
    
    async def translate_completion_async(
        self, output_path: str, max_concurrent_requests: int, progress_callback=None
    ) -> str:
        """
        번역 완성 모드 – 각 챕터 내 텍스트를 직접 축소(reduce) 처리.
        각 p, h1~h6 태그 내 텍스트에 대해 번역 후 반복 시도하여 적절한 결과 도출.
        """
        language = self.get_language()

        opf_tree, opf_path = self.get_opf_tree_and_path()
        self.file_contents[opf_path] = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)
        
        chapter_files = self.get_chapter_files(opf_tree, opf_path)
        #self.preserve_original_chapters(chapter_files)
        
        # 각 챕터 원문을 results에 저장
        results = {chap: self.file_contents[chap].decode('utf-8') for chap in chapter_files}
        executor = ThreadPoolExecutor(max_concurrent_requests)
        
        async def reduce_wrapper(chap):
            def reduce_foreign_in_chapter(html):
                soup = BeautifulSoup(html, 'lxml-xml')
                for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    if contains_foreign(p.get_text(), is_include_english=(language=='English')):
                        for text_node in p.find_all(string=True):
                            if contains_foreign(text_node, is_include_english=(language=='English')):
                                original_text = text_node
                                attempts = 0
                                translated_text = original_text
                                while attempts < 3:
                                    try:
                                        candidate = translate_text_for_completion(translated_text, language)
                                        if len(candidate) > 2 * len(original_text):
                                            attempts += 1
                                        elif contains_foreign(candidate, is_include_english=(language=='English')):
                                            attempts += 1
                                            translated_text = candidate
                                        elif len(candidate) == 0:
                                            attempts += 1
                                        else:
                                            translated_text = candidate
                                            attempts = 3
                                    except Exception:
                                        translated_text = original_text
                                        attempts = 3
                                text_node.replace_with(translated_text)
                return str(soup)
            html = results[chap]
            new_html = await asyncio.get_running_loop().run_in_executor(executor, reduce_foreign_in_chapter, html)
            new_html = self.force_horizontal_writing(new_html)
            return chap, new_html
        
        reduction_tasks = [asyncio.create_task(reduce_wrapper(chap)) for chap in chapter_files]
        total_reduction = len(reduction_tasks)
        completed_reduction = 0
        for task in asyncio.as_completed(reduction_tasks):
            chap, new_html = await task
            self.file_contents[chap] = new_html.encode('utf-8')
            completed_reduction += 1
            if progress_callback:
                progress = (completed_reduction / total_reduction) * 90
                progress_callback(int(progress))
        
        self.save(output_path, progress_callback)
        if progress_callback:
            progress_callback(100)
        return output_path
    
    async def annotate_images_async(
        self, output_path: str, max_concurrent_requests: int,
        progress_callback=None
    ) -> str:
        """
        EPUB 내의 이미지 태그(img 및 svg image)를 순회하여,
        annotate_image() 함수를 통해 이미지 설명(annotation)을 생성한 뒤,
        해당 설명을 새로운 <p> 태그로 이미지 뒤에 삽입하는 작업.
        """
        language = self.get_language()

        opf_tree, opf_path = self.get_opf_tree_and_path()
        self.file_contents[opf_path] = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)
        
        chapter_files = self.get_chapter_files(opf_tree, opf_path)
        #self.preserve_original_chapters(chapter_files)
        
        for chap in chapter_files:
            try:
                html_content = self.file_contents[chap].decode('utf-8')
                soup = BeautifulSoup(html_content, 'lxml-xml')
                # <img> 태그와 <svg> 내의 image 태그 모두 검색
                all_images = soup.find_all('img') + soup.select('svg image')
                for img in all_images:
                    src = (img.get("src") or img.get("xlink:href") or img.get("href") or
                           img.get("{http://www.w3.org/1999/xlink}href"))
                    if not src:
                        print(f"[WARN] No valid image path in tag in {chap}")
                        continue
                    chapter_dir = posixpath.dirname(chap)
                    image_path = posixpath.normpath(posixpath.join(chapter_dir, src) if chapter_dir else src)
                    print(f"[INFO] Resolving image path: {image_path}")
                    if image_path in self.file_contents:
                        image_bytes = self.file_contents[image_path]
                        annotation = annotate_image(image_bytes, language)
                        new_p = soup.new_tag("p")
                        new_p.append('[[이미지 텍스트:')
                        for line in annotation.strip().split('\n'):
                            new_p.append(soup.new_tag("br"))
                            new_p.append(line)
                        new_p.append(']]')
                        img.insert_after(new_p)
                    else:
                        print(f"[WARN] Image not found in EPUB: {image_path}")
                self.file_contents[chap] = str(soup).encode('utf-8')
            except Exception as e:
                print(f"[ERROR] Failed to process {chap}: {e}")
        
        self.save(output_path, progress_callback)
        if progress_callback:
            progress_callback(100)
        return output_path