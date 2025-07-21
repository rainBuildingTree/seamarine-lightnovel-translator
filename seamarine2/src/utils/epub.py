from __future__ import annotations

import os
import posixpath
import zipfile
import lxml.etree as ET
import pycountry
import uuid
from bs4 import BeautifulSoup
import html
from xml.dom import minidom
import io


NAMESPACES = {
    'xmlns': 'urn:oasis:names:tc:opendocument:xmlns:container',
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'ncx': 'http://www.daisy.org/z3986/2005/ncx/',
    'xhtml': 'http://www.w3.org/1999/xhtml',
    'epub': 'http://www.idpf.org/2007/ops'
}
for prefix, url in NAMESPACES.items():
    ET.register_namespace(prefix, url)

class BrokenEpubError(Exception):
    pass
class UnsupportedEpubError(Exception):
    pass
class Epub:
    def __init__(self, file_path: str):
        self._file_path: str = file_path
        self._file_contents: dict[str, bytes] = {}

        self._opf_path: str | None = None
        self._opf_dir: str | None = None

        self._opf_root: ET.Element | None = None
        self._version: str | None = None
        self._metadata: ET.Element | None = None
        self._manifest: ET.Element | None = None
        self._spine: ET.Element | None = None

        self._contents: dict[str, bytes] = {}
        self._original_contents: dict[str, bytes] = {}
        self._container_tree: ET.Element[str]
        self._opf_tree: ET.Element[str]
        self._version: str
        self._metadata: ET.Element[str]
        self._identifier: ET.Element[str]
        self._title: ET.Element[str]
        self._language: ET.Element[str]
        self._contributors: list[ET.Element[str]]
        self._creators: list[ET.Element[str]]
        self._dates: list[ET.Element[str]]
        self._metas: list[ET.Element[str]]
        self._metas: list[ET.Element[str]]
        self._cover: ET.Element[str]
        self._manifest: ET.Element[str]
        self._opf_dir: str
        self._toc_path: str
        self._spine: ET.Element[str]
        self._toc_id: str
        self._chapter_files: list[str] = []
        self._image_files: list[str] = []
        self._style_files: list[str] = []
        self._ns: dict[str, str] = {
            "container": "urn:oasis:names:tc:opendocument:xmlns:container",
            "opf": "http://www.idpf.org/2007/opf",
            "dc": "http://purl.org/dc/elements/1.1/"
        }

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File Not Found: {file_path}")
        
        _, ext = os.path.splitext(os.path.basename(file_path))
        if ext.lower() != ".epub":
            raise ValueError(f"Only .epub Files Are Supported (Got: {ext})")
        
        self._file_path: str = file_path
        self._contents: dict[str, bytes] = {}
        self._original_contents: dict[str, bytes] = {}

        try:
            with zipfile.ZipFile(file_path, 'r') as zin:
                for name in zin.namelist():
                    self._contents[name] = zin.read(name)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except zipfile.BadZipFile:
            raise zipfile.BadZipFile("Incorrect EPUB Format Or Corrupted Zip Archive")
        except Exception:
            raise

        container_path = "META-INF/container.xml"
        if container_path not in self._contents:
            raise BrokenEpubError("META-INF/container.xml Not Found")
        
        self._container_tree: ET.Element[str] = ET.fromstring(self._contents[container_path])
        self._container_ns: dict[str, str] = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}

        rootfile = self._container_tree.find(".//container:rootfile", self._container_ns)
        if rootfile == None:
            raise BrokenEpubError(".//container:rootfile Not Found")
        
        self._opf_path = rootfile.attrib.get("full-path")
        if not self._opf_path or self._opf_path not in self._contents:
            raise BrokenEpubError(f"{self._opf_path} Not Found")
        
        opf_bytes = self._contents.get(self._opf_path)
        print(opf_bytes.decode())
        self._opf_tree: ET.Element[str] = ET.fromstring(opf_bytes)
        self._ns = {
            "container": "urn:oasis:names:tc:opendocument:xmlns:container",
            "opf": "http://www.idpf.org/2007/opf",
            "dc": "http://purl.org/dc/elements/1.1/"
        }
        
        self.version = self._opf_tree.attrib.get("version", "2.0")
        if self.version.startswith('1'):
            raise UnsupportedEpubError("EPUB 1.X Or Below Is Not Supported On This Library")
        
        self._metadata: ET.Element[str] = self._opf_tree.find("opf:metadata", self._ns)
        self._identifier: ET.Element[str] = self._metadata.find("dc:identifier", self._ns)
        self._title: ET.Element[str] = self._metadata.find("dc:title", self._ns)
        self._language: ET.Element[str] = self._metadata.find("dc:language", self._ns)
        self._contributors: list[ET.Element[str]] = self._metadata.findall("dc:contributor", self._ns)
        self._creators: list[ET.Element[str]] = self._metadata.findall("dc:creator", self._ns)
        self._dates: list[ET.Element[str]] = self._metadata.findall("dc:date", self._ns)
        self._metas: list[ET.Element[str]] = self._metadata.findall("meta")
        self._metas: list[ET.Element[str]] = self._metadata.findall("opf:meta") if self._metas == None else self._metas
        self._cover: ET.Element[str] = next(
            (meta for meta in self._metas if meta.attrib.get("name") == "cover"),
            None
        )

        self._manifest: ET.Element[str] = self._opf_tree.find("opf:manifest", self._ns)
        self._opf_dir: str = posixpath.dirname(self._opf_path)

        self._toc_path: str | None = None
        if self.version.startswith("2"):
            self._spine = self._opf_tree.find("opf:spine", self._ns)
            self._toc_id = self._spine.attrib.get("toc", None)
        else:
            self._spine = None
            self._toc_id = None
        
        self._chapter_files: list[str] = []
        self._image_files: list[str] = []
        self._style_files: list[str] = []
        
        for item in self._manifest.findall("opf:item", self._ns):
            media_type = item.attrib.get("media-type", "")
            properties = item.attrib.get("properties", "")
            path = posixpath.join(self._opf_dir, item.attrib.get("href", ""))
            if "nav" in properties:
                continue
            elif "html" in media_type:
                self._chapter_files.append(path)
            elif media_type.startswith("image"):
                self._image_files.append(path)
            elif "css" in media_type:
                self._style_files.append(path)
            elif 'properties' in item.attrib and 'nav' in item.attrib['properties']:
                self._toc_path = path
            elif self._toc_id != None and item.attrib.get("id") == self._toc_id:
                self._toc_path = path
        
        self.toc_data = self._contents[self._toc_path]
        
        self._original_contents = {}
        self._preserve_original_chapters()

    def save(self, save_path):
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with zipfile.ZipFile(save_path, 'w') as zout:
                if 'mimetype' in self._contents:
                    zout.writestr('mimetype', self._contents['mimetype'], compress_type=zipfile.ZIP_STORED)
                for fname, data in self._contents.items():
                    if fname == 'mimetype':
                        continue
                    zout.writestr(fname, data, compress_type=zipfile.ZIP_DEFLATED)
        except Exception as e:
            raise e
    
    def get_language(self) -> str:
        opf_tree, _ = self._get_opf_tree_and_path()
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        metadata_elem = opf_tree.find('opf:metadata', ns)
        if metadata_elem is None:
            raise ValueError("Metadata not found in OPF file.")

        language_elem = metadata_elem.find('dc:language', ns)
        if language_elem is not None:
            return self._get_language_name(language_elem.text.strip(), '')
        return ''
    
    def get_original_language(self) -> str:
        opf_tree, _ = self._get_opf_tree_and_path()
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        metadata_elem = opf_tree.find('opf:metadata', ns)
        if metadata_elem is None:
            raise ValueError("Metadata not found in OPF file.")
        
        original_lang_elem = metadata_elem.find("opf:meta", ns)
        if original_lang_elem is not None:
            return original_lang_elem.text
        else:
            return self.get_language()
    
    def update_title(self, new_title: str):
        self._metadata.set(f"{{{self._ns["dc"]}}}language", new_title)

    def update_read_direction(self, direction: str = "ltr"):
        opf_tree, self._opf_path = self._get_opf_tree_and_path()
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        spine_elem = opf_tree.find('opf:spine', ns)
        spine_elem.attrib["page-progression-direction"] = direction
        self._contents[self._opf_path] = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)

    
    def update_metadata_epub(self, lang: str = 'ko', contributor: str = None):
        opf_tree, self._opf_path = self._get_opf_tree_and_path()
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        metadata_elem = opf_tree.find('opf:metadata', ns)
        if metadata_elem is None:
            raise ValueError("Metadata not found in OPF file.")
 
        language_elem = metadata_elem.find('dc:language', ns)
        if language_elem is not None:
            if metadata_elem.find('opf:meta', ns) is None:
                original_lang = ET.Element('{http://www.idpf.org/2007/opf}meta')
                original_lang.attrib["name"] = "seamarine original lang"
                original_lang.attrib["content"] = self._get_language_name(language_elem.text)
                metadata_elem.append(original_lang)
            language_elem.text = lang
        else:
            new_lang = ET.Element('{http://purl.org/dc/elements/1.1/}language')
            new_lang.text = lang
            metadata_elem.append(new_lang)

        identifier_elem = metadata_elem.find('dc:identifier', ns)
        new_id = str(uuid.uuid4())
        if identifier_elem is not None:
            identifier_elem.text = new_id
        else:
            new_identifier = ET.Element('{http://purl.org/dc/elements/1.1/}identifier')
            new_identifier.text = new_id
            metadata_elem.append(new_identifier)

        if contributor:
            sm_contrib = ET.Element('{http://www.idpf.org/2007/opf}meta')
            sm_contrib.attrib["name"] = "Translated By"
            sm_contrib.attrib["content"] = contributor
            metadata_elem.append(sm_contrib)

        self._contents[self._opf_path] = ET.tostring(opf_tree, encoding='utf-8', xml_declaration=True)

    def get_chapter_files(self) -> list:
        opf_tree, self._opf_path = self._get_opf_tree_and_path()
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
        }
        manifest_elem = opf_tree.find('opf:manifest', ns)
        opf_dir = posixpath.dirname(self._opf_path)
        chapter_files = []
        if manifest_elem is not None:
            for item in manifest_elem.findall('opf:item', ns):
                media_type = item.attrib.get('media-type', '')
                properties = item.attrib.get('properties', '')
                if 'nav' in properties:
                    continue
                if 'html' in media_type:
                    href = item.attrib.get('href')
                    chapter_path = posixpath.join(opf_dir, href) if opf_dir else href
                    if chapter_path in self._contents:
                        chapter_files.append(chapter_path)
        return chapter_files
    
    def load_original_chapters(self):
        """원본 챕터 HTML을 self.original_file_contents에 로드"""
        with zipfile.ZipFile(self._file_path, 'r') as zin:
            for name in zin.namelist():
                full_filename = posixpath.basename(name)
                filename, _ = posixpath.splitext(full_filename)
                if filename.endswith('_original'):
                    self._original_contents[full_filename] = zin.read(name)
    
    def override_original_chapter(self):
        try:
            self.load_original_chapters()
            for chapter in self._chapter_files:
                bn, ext = posixpath.splitext(posixpath.basename(chapter))
                original_path = posixpath.join("seamarine_originals", f"{bn}_original{ext}")
                self._contents[chapter] = self._contents[original_path]
        except Exception:
            print("error in override")
            raise
            

    def apply_pn_dictionary(self, dictionary: dict[str, str]):
        chapter_files = self.get_chapter_files()
        dictionary = dict(sorted(dictionary.items(), key=lambda item: len(item[0]), reverse=True))
        chapter_files = self.get_chapter_files()
        for chap in chapter_files:
            content = self._contents[chap].decode('utf-8')

            for t_from, t_to in dictionary.items():
                escaped_ko = html.escape(t_to)  # < → &lt;, > → &gt; 등 처리
                content = content.replace(t_from, escaped_ko)

            self._contents[chap] = content.encode('utf-8')

    def apply_pn_dictionary_to_toc(self, dictionary: dict[str, str]):
        dictionary = dict(sorted(dictionary.items(), key=lambda item: len(item[0]), reverse=True))
        content = self._contents[self._toc_path].decode('utf-8')
        for t_from, t_to in dictionary.items():
            escaped_to = html.escape(t_to)
            content = content.replace(t_from, escaped_to)
        self._contents[self._toc_path] = content.encode('utf-8')

    def force_horizontal_writing(self, html_content: str) -> str:
        """HTML 내에 head에 writing-mode 스타일을 추가."""
        print(2)
        print(html_content)
        soup = BeautifulSoup(html_content, "lxml-xml")
        print(3)
        head = soup.find("head")
        print(4)
        if head is None:
            print(5)
            head = soup.new_tag("head")
            print(6)
            if soup.html:
                print(7)
                soup.html.insert(0, head)
                print(8)
            else:
                print(9)
                soup.insert(0, head)
                print(10)
        style_tag = soup.new_tag("style")
        style_tag.string = "body { writing-mode: horizontal-tb !important; }"
        head.append(style_tag)
        return str(soup)
    
    def apply_dual_language(self):
        for chapter_file in self._chapter_files:
            bn, ext = posixpath.splitext(posixpath.basename(chapter_file))
            original_path = posixpath.join("seamarine_originals", f"{bn}_original{ext}")
            original_html = self._contents[original_path]
            translated_html = self._contents[chapter_file]
            merged_html = self._combine_dual_language(original_html, translated_html)
            self._contents[chapter_file] = self.force_horizontal_writing(merged_html)
            
    
    def _combine_dual_language(self, original_html, translated_html):
        """
        원본 HTML의 기본 구조(헤드 등)는 그대로 두고, body 내의 <p> 태그만
        원문과 번역문을 결합하여 dual language로 처리합니다.
        
        만약 body 태그나 <p> 태그가 제대로 매칭되지 않으면 fallback으로 
        번역본 전체를 별도의 컨테이너로 추가합니다.
        """
        soup_original = BeautifulSoup(original_html, 'lxml-xml')
        soup_translated = BeautifulSoup(translated_html, 'lxml-xml')
        
        # body 태그 가져오기
        original_body = soup_original.body
        translated_body = soup_translated.body
        
        if original_body is None or translated_body is None:
            # body 태그가 없으면 fallback: 전체 번역본을 반환
            return translated_html
        
        original_p_tags = [
            p for p in original_body.find_all('p') 
            if p.get('title') != "SeaMarine Annotation"
        ]
        translated_p_tags = translated_body.find_all('p')
        
        # <p> 태그가 하나도 없거나 개수가 다르면 fallback 처리
        if not original_p_tags or not translated_p_tags or len(original_p_tags) != len(translated_p_tags):
            #return str(soup_original)
            return translated_html
        # <p> 태그가 있는 경우, 각 <p> 태그를 dual language로 변경
        for orig_tag, trans_tag in zip(original_p_tags, translated_p_tags):
            # 새 <p> 태그 생성, 원본 태그의 속성 그대로 복사
            new_tag = soup_original.new_tag("p")
            new_tag.attrs = orig_tag.attrs.copy()
            # 원본 내용 추가 (내부 HTML 유지)
            new_tag.append(BeautifulSoup(orig_tag.decode_contents(formatter=None), "html.parser"))
            # 구분자 추가 (예: <br>)
            new_tag.append(soup_original.new_tag("br"))
            # 번역 내용 추가 (내부 HTML 유지)
            new_tag.append(BeautifulSoup(trans_tag.decode_contents(formatter=None), "html.parser"))
            # 원본 <p> 태그를 새 태그로 교체
            orig_tag.replace_with(new_tag)
        
        return str(soup_original)

    def _load_epub_contents(self):
        with zipfile.ZipFile(self._file_path, 'r') as zin:
            for name in zin.namelist():
                self._contents[name] = zin.read(name)

    def _preserve_original_chapters(self):
        """원본 챕터 HTML을 'seamarine_originals/' 폴더에 저장."""
        chapter_files = self.get_chapter_files()
        self._original_contents = {}
        for chap in chapter_files:
            original_html = self._contents[chap].decode('utf-8')
            original_filename = posixpath.basename(chap)
            name, ext = posixpath.splitext(original_filename)
            new_filename = f"{name}_original{ext}"
            new_path = posixpath.join('seamarine_originals', new_filename)
            if new_path in self._contents.keys():
                continue
            self._original_contents[chap] = self._contents[chap]
            self._contents[new_path] = original_html.encode('utf-8')
    
    def _get_language_name(self, code: str, default: str) -> str:
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
    
    def _get_container_tree(self) -> ET.Element:
        container_path = 'META-INF/container.xml'
        if container_path not in self._contents:
            raise ValueError("META-INF/container.xml not found in the EPUB.")
        return ET.fromstring(self._contents[container_path])
    
    def _get_opf_tree_and_path(self) -> tuple[ET.Element, str]:
        container_tree = self._get_container_tree()
        container_ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
        rootfile = container_tree.find('.//container:rootfile', container_ns)
        if rootfile is None:
            raise ValueError("rootfile not found in container.xml")
        self._opf_path = rootfile.attrib.get('full-path')
        if not self._opf_path or self._opf_path not in self._contents:
            raise ValueError("OPF file not found in the EPUB.")
        opf_tree = ET.fromstring(self._contents[self._opf_path])
        return opf_tree, self._opf_path
    
class Container:
    class BrokenError(Exception):
        pass

    class Rootfile:
        def __init__(self, full_path: str = None, media_type: str = "application/oebps-package+xml", element: ET.Element = None):
            self._full_path: str = full_path
            self._media_type: str = media_type
            self.element: ET.Element = element
            
        @classmethod
        def from_element(cls, rootfile_element: ET.Element):
            full_path = rootfile_element.attrib.get("full-path")
            media_type = rootfile_element.attrib.get("media-type")

            if not all([full_path, media_type]):
                missing = [attr for attr, val in [("full-path", full_path), ("media-type", media_type)] if not val]
                raise Container.BrokenError(f"Missing required attribute(s) in <rootfile>: {', '.join(missing)}")
            
            return cls(full_path, media_type, rootfile_element)
        
        @classmethod
        def new(cls, full_path: str, media_type: str = "application/oebps-package+xml"):
            if not full_path:
                raise ValueError("full_path must be provided")
            
            element = ET.Element(
                f"{{{NAMESPACES['xmlns']}}}rootfile",
                attrib={"full-path": full_path, "media-type": media_type}
            )
            return cls(full_path, media_type, element)
        
        @property
        def full_path(self):
            return self._full_path
        @full_path.setter
        def full_path(self, value):
            self._full_path = value
            self.element.attrib["full-path"] = value

        @property
        def media_type(self):
            return self._media_type
        @media_type.setter
        def media_type(self, value):
            self._media_type = value
            self.element.attrib["media-type"] = value

        def __str__(self) -> str:
            return ET.tostring(self.element, encoding="utf-8").decode("utf-8")
    

    def __init__(self, tree: ET.ElementTree, version: str, rootfile: 'Container.Rootfile'):
        self.tree = tree
        self.version = version
        self.rootfile = rootfile

    @classmethod
    def from_xml(cls, container_xml: bytes | str | ET.Element | ET.ElementTree):
        if isinstance(container_xml, (bytes, str)):
            root = ET.fromstring(container_xml)
            tree = ET.ElementTree(root)
        elif isinstance(container_xml, ET.Element):
            tree = ET.ElementTree(container_xml)
        elif isinstance(container_xml, ET.ElementTree):
            tree = container_xml
        else:
            raise TypeError(f"Unsupported container_xml type: {type(container_xml)}")
        
        root = tree.getroot()
        version = root.attrib.get("version", "1.0")
        
        rootfile_element = root.find(".//xmlns:rootfile", NAMESPACES)
        if rootfile_element is None:
            raise cls.BrokenError("Missing <rootfile> element in container.xml.")
        
        rootfile = cls.Rootfile.from_element(rootfile_element)
        return cls(tree, version, rootfile)
    
    @classmethod
    def new(cls, rootfile_path: str, version: str = "1.0"):
        if not rootfile_path:
            raise ValueError("rootfile_path must be provided")

        root = ET.Element(f"{{{NAMESPACES['xmlns']}}}container", attrib={"version": version})
        rootfiles = ET.SubElement(root, f"{{{NAMESPACES['xmlns']}}}rootfiles")
        
        rootfile = cls.Rootfile.new(full_path=rootfile_path)
        rootfiles.append(rootfile.element)
        
        tree = ET.ElementTree(root)
        return cls(tree, version, rootfile)
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "rootfile": {
                "full-path": self.rootfile.full_path,
                "media-type": self.rootfile.media_type
            }
        }
        
    def __str__(self) -> str:
        rough_string = ET.tostring(self.tree.getroot(), encoding="utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml()
    
    def __bytes__(self) -> bytes:
        buffer = io.BytesIO()
        self.tree.write(buffer, encoding="utf-8", xml_declaration=True)
        return buffer.getvalue()
    
    def __eq__(self, other):
        return isinstance(other, Container) and self.to_dict() == other.to_dict()
    
    def save(self, path: str, encoding: str = "utf-8", xml_declaration: bool = True):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.tree.write(path, encoding=encoding, xml_declaration=xml_declaration)