import xml.etree.ElementTree as ET
import uuid
from typing import Type, TypeVar

# --- 네임스페이스 URI 정의 ---
# 이제 접두사는 동적으로 결정되므로, URI만 상수로 정의합니다.
OPF_NS_URI = "http://www.idpf.org/2007/opf"
DC_NS_URI = "http://purl.org/dc/elements/1.1/"
XML_NS_URI = "http://www.w3.org/XML/1998/namespace"


def _parse_nsmap(element: ET.Element) -> dict[str, str]:
    """
    루트 요소에서 네임스페이스 선언을 파싱하여 접두사:URI 맵을 생성합니다.
    기본 네임스페이스는 'default'라는 접두사로 처리합니다.
    """
    nsmap = {k: v for k, v in element.attrib.items() if k.startswith('xmlns:')}
    nsmap = {k.split(':', 1)[1]: v for k, v in nsmap.items()}
    if 'xmlns' in element.attrib:
        nsmap['default'] = element.attrib['xmlns']
    return nsmap

def _parse_nsmap_from_file(filepath: str) -> dict:
    nsmap = {}
    for event, (prefix, uri) in ET.iterparse(filepath, events=['start-ns']):
        if prefix == '':
            nsmap['default'] = uri
        else:
            nsmap[prefix] = uri
    return nsmap

# --- 기반 클래스 (네임스페이스 처리 강화) ---

class _ElementWrapper:
    """XML ET.Element를 래핑하는 모든 클래스의 최상위 기반 클래스입니다."""
    def __init__(self, element: ET.Element, nsmap: dict[str, str]):
        if not isinstance(element, ET.Element):
            raise TypeError(f"Expected ET.Element, but got {type(element).__name__}")
        self.element: ET.Element = element
        self.nsmap: dict[str, str] = nsmap
        
        # 자주 사용하는 네임스페이스의 접두사를 인스턴스 변수로 저장
        self.opf_prefix = next((p for p, u in nsmap.items() if u == OPF_NS_URI), None)
        self.dc_prefix = next((p for p, u in nsmap.items() if u == DC_NS_URI), None)

    def _get_qname(self, local_name: str, ns_uri: str) -> str:
        """URI와 로컬 이름으로 정규화된 태그 이름(QName)을 생성합니다. (예: dc:creator, ns0:item)"""
        # nsmap에서 URI에 해당하는 접두사를 찾습니다.
        prefix = next((p for p, u in self.nsmap.items() if u == ns_uri), None)
        
        # 접두사가 있고, 'default'가 아니면 "prefix:local_name" 형식을 반환합니다.
        if prefix and prefix != 'default':
            return f"{prefix}:{local_name}"
        
        # 기본 네임스페이스이거나, 네임스페이스 맵에 없는 경우 로컬 이름만 반환합니다.
        return local_name
        
    def attr(self, attr_name: str, ns_uri: str = None) -> str | None:
        """네임스페이스 URI를 사용하여 속성을 가져옵니다."""
        if ns_uri:
            return self.element.get(f"{{{ns_uri}}}{attr_name}")
        return self.element.get(attr_name)

    def set_attr(self, attr_name: str, value: str, ns_uri: str = None):
        """네임스페이스 URI를 사용하여 속성을 설정합니다."""
        if ns_uri:
            # lxml과 달리 ElementTree는 속성 설정 시 Clark 표기법만 사용
            self.element.set(f"{{{ns_uri}}}{attr_name}", value)
        else:
            self.element.set(attr_name, value)
            
    def _find_and_wrap(self, tag: str, wrapper_class): # -> T | None 부분도 제거
        """자식 요소를 찾아 래퍼 클래스로 감싸 반환합니다."""
        el = self.element.find(tag, self.nsmap)
        return wrapper_class(el, self.nsmap) if el is not None else None

    def _find_all_and_wrap(self, tag: str, wrapper_class): # -> list[T] 부분도 제거
        """모든 자식 요소를 찾아 래퍼 클래스 리스트로 감싸 반환합니다."""
        return [wrapper_class(el, self.nsmap) for el in self.element.findall(tag, self.nsmap)]

class _HasId(_ElementWrapper):
    @property
    def id(self) -> str | None: return self.attr("id")
    @id.setter
    def id(self, value: str): self.set_attr("id", value)

class _HasContent(_ElementWrapper):
    @property
    def content(self) -> str | None: return self.element.text
    @content.setter
    def content(self, value: str): self.element.text = value

class _HasDirAndLang(_ElementWrapper):
    @property
    def direction(self) -> str | None: return self.attr("dir")
    @direction.setter
    def direction(self, value: str): self.set_attr("dir", value)
    @property
    def language(self) -> str | None: return self.attr("lang", XML_NS_URI)
    @language.setter
    def language(self, value: str): self.set_attr("lang", value, XML_NS_URI)

class _DCMESElement(_HasId, _HasContent): pass
class _OptionalDublinCore(_DCMESElement, _HasDirAndLang): pass


# --- OPF Package 클래스 및 중첩 클래스 ---

class Package(_HasId, _HasDirAndLang):
    class Metadata(_ElementWrapper):
        class Meta(_HasId, _HasDirAndLang, _HasContent):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)
            @property
            def meta_property(self) -> str | None: return self.attr("property")
            @meta_property.setter
            def meta_property(self, value: str): self.set_attr("property", value)
            @property
            def refines(self) -> str | None: return self.attr("refines")
            @refines.setter
            def refines(self, value: str): self.set_attr("refines", value)
            @property
            def scheme(self) -> str | None: return self.attr("scheme")
            @scheme.setter
            def scheme(self, value: str): self.set_attr("scheme", value)
            @property
            def name(self) -> str | None: return self.attr("name")
            @name.setter
            def name(self, value: str): self.set_attr("name", value)
            @property
            def content(self) -> str | None: return self.attr("content") or self.element.text
            @content.setter
            def content(self, value: str):
                if self.attr("content") is not None: self.set_attr("content", value)
                else: self.element.text = value
        
        class Identifier(_DCMESElement):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)
        class Title(_OptionalDublinCore):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)
        class Language(_DCMESElement):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)
        
        class Contributor(_OptionalDublinCore):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)
            @property
            def file_as(self) -> str | None: return self.attr("file-as", OPF_NS_URI)
            @file_as.setter
            def file_as(self, value: str): self.set_attr("file-as", value, OPF_NS_URI)
            @property
            def role(self) -> str | None: return self.attr("role", OPF_NS_URI)
            @role.setter
            def role(self, value: str): self.set_attr("role", value, OPF_NS_URI)
        
        class Creator(Contributor):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)

        class Date(_OptionalDublinCore):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)

        class Subject(_OptionalDublinCore):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)
            @property
            def authority(self) -> str | None: return self.attr("authority", OPF_NS_URI)
            @authority.setter
            def authority(self, value: str): self.set_attr("authority", value, OPF_NS_URI)
            @property
            def term(self) -> str | None: return self.attr("term", OPF_NS_URI)
            @term.setter
            def term(self, value: str): self.set_attr("term", value, OPF_NS_URI)

        class Type(_OptionalDublinCore):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)

        def __init__(self, element: ET.Element, nsmap: dict):
            super().__init__(element, nsmap)
            if not self.dc_prefix: raise ValueError("Dublin Core namespace not found in the document.")
            dc_tag = f"{self.dc_prefix}:" if self.dc_prefix != 'default' else ''
            
            self.identifiers = self._find_all_and_wrap(f"{dc_tag}identifier", self.Identifier)
            self.titles = self._find_all_and_wrap(f"{dc_tag}title", self.Title)
            self.languages = self._find_all_and_wrap(f"{dc_tag}language", self.Language)
            self.contributors = self._find_all_and_wrap(f"{dc_tag}contributor", self.Contributor)
            self.creators = self._find_all_and_wrap(f"{dc_tag}creator", self.Creator)
            self.dates = self._find_all_and_wrap(f"{dc_tag}date", self.Date)
            self.subjects = self._find_all_and_wrap(f"{dc_tag}subject", self.Subject)
            self.types = self._find_all_and_wrap(f"{dc_tag}type", self.Type)
            self.metas = self._find_all_and_wrap("meta", self.Meta)
        
        def _add_dc_element(self, tag_name, wrapper_class, content, **kwargs):
            # qname을 만드는 부분은 삭제하거나 주석 처리
            # qname = self._get_qname(tag_name, DC_NS_URI)
            
            # ▼▼▼ Clark 표기법으로 SubElement 생성 ▼▼▼
            el = ET.SubElement(self.element, f"{{{DC_NS_URI}}}{tag_name}")
            el.text = content
            
            new_obj = wrapper_class(el, self.nsmap)
            for key, value in kwargs.items():
                if value is not None:
                    ns_uri = OPF_NS_URI if key in ["file-as", "role", "authority", "term"] else None
                    if ns_uri:
                        new_obj.set_attr(key, value, ns_uri)
                    else:
                        new_obj.set_attr(key, value)
            
            list_name = f"{tag_name}s"
            if hasattr(self, list_name):
                getattr(self, list_name).append(new_obj)
            return new_obj

        def add_creator(self, name: str, role: str = None, file_as: str = None):
            return self._add_dc_element("creator", self.Creator, name, role=role, file_as=file_as)

    class Manifest(_HasId):
        class Item(_HasId):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)
            @property
            def fallback(self) -> str | None: return self.attr("fallback")
            @fallback.setter
            def fallback(self, value: str): self.set_attr("fallback", value)
            @property
            def href(self) -> str | None: return self.attr("href")
            @href.setter
            def href(self, value: str): self.set_attr("href", value)
            @property
            def media_overlay(self) -> str | None: return self.attr("media-overlay")
            @media_overlay.setter
            def media_overlay(self, value: str): self.set_attr("media-overlay", value)
            @property
            def media_type(self) -> str | None: return self.attr("media-type")
            @media_type.setter
            def media_type(self, value: str): self.set_attr("media-type", value)
            @property
            def properties(self) -> list[str]:
                prop_str = self.attr("properties")
                return prop_str.split() if prop_str else []
            @properties.setter
            def properties(self, value: list[str]):
                prop_str = " ".join(value)
                if prop_str: self.set_attr("properties", prop_str)
                elif "properties" in self.element.attrib: del self.element.attrib["properties"]
        
        def __init__(self, element: ET.Element, nsmap: dict):
            super().__init__(element, nsmap)
            tag = self._get_qname("item", OPF_NS_URI)
            self.items = self._find_all_and_wrap(tag, self.Item)
        
        def add_item(self, href, media_type, item_id = None, properties = None):
            if item_id is None: item_id = f"item-{uuid.uuid4().hex[:8]}"
            
            # tag를 만드는 부분은 삭제하거나 주석 처리
            # tag = self._get_qname("item", OPF_NS_URI)
            
            # ▼▼▼ Clark 표기법으로 SubElement 생성 ▼▼▼
            el = ET.SubElement(self.element, f"{{{OPF_NS_URI}}}item", id=item_id, href=href, media_type=media_type)
            
            new_item = self.Item(el, self.nsmap)
            if properties: new_item.properties = properties
            self.items.append(new_item)
            return new_item

    class Spine(_HasId):
        class ItemRef(_HasId):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)
            @property
            def idref(self) -> str | None: return self.attr("idref")
            @idref.setter
            def idref(self, value: str): self.set_attr("idref", value)
            @property
            def linear(self) -> str: return self.attr("linear") or "yes"
            @linear.setter
            def linear(self, value: str): self.set_attr("linear", value)
            @property
            def properties(self) -> list[str]:
                prop_str = self.attr("properties")
                return prop_str.split() if prop_str else []
            @properties.setter
            def properties(self, value: list[str]):
                prop_str = " ".join(value)
                if prop_str: self.set_attr("properties", prop_str)
                elif "properties" in self.element.attrib: del self.element.attrib["properties"]

        def __init__(self, element: ET.Element, nsmap: dict):
            super().__init__(element, nsmap)
            tag = self._get_qname("itemref", OPF_NS_URI)
            self.itemrefs = self._find_all_and_wrap(tag, self.ItemRef)
        @property
        def page_progression_direction(self) -> str | None: return self.attr("page-progression-direction")
        @page_progression_direction.setter
        def page_progression_direction(self, value: str): self.set_attr("page-progression-direction", value)
        @property
        def toc(self) -> str | None: return self.attr("toc")
        @toc.setter
        def toc(self, value: str): self.set_attr("toc", value)
        
        def add_itemref(self, idref, linear = True):
            # tag를 만드는 부분은 삭제하거나 주석 처리
            # tag = self._get_qname("itemref", OPF_NS_URI)

            # ▼▼▼ Clark 표기법으로 SubElement 생성 ▼▼▼
            el = ET.SubElement(self.element, f"{{{OPF_NS_URI}}}itemref", idref=idref)

            if not linear: el.set("linear", "no")
            new_itemref = self.ItemRef(el, self.nsmap)
            self.itemrefs.append(new_itemref)
            return new_itemref

    class Guide(_ElementWrapper):
        class Reference(_ElementWrapper):
            def __init__(self, element: ET.Element, nsmap: dict): super().__init__(element, nsmap)
            @property
            def type_attr(self) -> str | None: return self.attr("type")
            @type_attr.setter
            def type_attr(self, value: str): self.set_attr("type", value)
            @property
            def title(self) -> str | None: return self.attr("title")
            @title.setter
            def title(self, value: str): self.set_attr("title", value)
            @property
            def href(self) -> str | None: return self.attr("href")
            @href.setter
            def href(self, value: str): self.set_attr("href", value)
            
        def __init__(self, element: ET.Element, nsmap: dict):
            super().__init__(element, nsmap)
            tag = self._get_qname("reference", OPF_NS_URI)
            self.references = self._find_all_and_wrap(tag, self.Reference)

    def __init__(self, tree: ET.ElementTree, nsmap: dict):
        self.tree = tree
        root = tree.getroot()
        if not root.tag.endswith("package"):
             raise ValueError("Root element is not <package>")
        
        super().__init__(root, nsmap)

        if not self.opf_prefix:
            raise ValueError("OPF namespace not found in the document.")
        
        # ▼▼▼ _get_qname을 사용하여 동적으로 태그 이름 생성 ▼▼▼
        metadata_tag = self._get_qname("metadata", OPF_NS_URI)
        manifest_tag = self._get_qname("manifest", OPF_NS_URI)
        spine_tag = self._get_qname("spine", OPF_NS_URI)
        guide_tag = self._get_qname("guide", OPF_NS_URI)

        metadata_el = root.find(metadata_tag, nsmap)
        if metadata_el is None: raise ValueError("Required <metadata> element not found.")
        self.metadata = self.Metadata(metadata_el, nsmap)

        manifest_el = root.find(manifest_tag, nsmap)
        if manifest_el is None: raise ValueError("Required <manifest> element not found.")
        self.manifest = self.Manifest(manifest_el, nsmap)

        spine_el = root.find(spine_tag, nsmap)
        if spine_el is None: raise ValueError("Required <spine> element not found.")
        self.spine = self.Spine(spine_el, nsmap)

        guide_el = root.find(guide_tag, nsmap)
        self.guide = self.Guide(guide_el, nsmap) if guide_el is not None else None
    
    @classmethod
    def from_file(cls, filepath: str):
        nsmap = _parse_nsmap_from_file(filepath)
        tree = ET.parse(filepath)
        return cls(tree, nsmap)

    def _prepare_for_writing(self):
        """출력 전, 파싱된 네임스페이스 맵을 ET에 등록하여 예쁜 출력을 보장합니다."""
        for prefix, uri in self.nsmap.items():
            if prefix != 'default':
                ET.register_namespace(prefix, uri)


    def _apply_ns_to_root(self):
        """
        루트 요소에 nsmap 기반으로 네임스페이스 속성을 정리하여 적용합니다.
        기존 xmlns 속성을 모두 제거한 후 새로 설정하여 중복을 방지합니다.
        """
        # 기존의 모든 xmlns 속성 키를 찾아서 리스트로 만듭니다.
        # attrib 딕셔너리를 직접 순회하면서 삭제하면 RuntimeError가 발생할 수 있습니다.
        keys_to_remove = [k for k in self.element.attrib if k.startswith('xmlns') or k == 'xmlns']
        
        # 찾은 키들을 삭제합니다.
        for key in keys_to_remove:
            del self.element.attrib[key]
            
        # nsmap을 기반으로 네임스페이스 속성을 새로 설정합니다.
        for prefix, uri in self.nsmap.items():
            if prefix == 'default':
                self.element.set('xmlns', uri)
            else:
                self.element.set(f'xmlns:{prefix}', uri)

    # to_string 메소드 교체
    def to_string(self, encoding="unicode", xml_declaration=True):
        self._apply_ns_to_root() # 헬퍼 메소드 호출
        return ET.tostring(self.element, encoding=encoding, xml_declaration=xml_declaration)
    
    # write_to_file 메소드 교체
    def write_to_file(self, filepath, encoding="utf-8", xml_declaration=True):
        self._apply_ns_to_root() # 헬퍼 메소드 호출
        self.tree.write(filepath, encoding=encoding, xml_declaration=xml_declaration)

    @property
    def prefix(self) -> str | None: return self.attr("prefix")
    @prefix.setter
    def prefix(self, value: str): self.set_attr("prefix", value)
    @property
    def unique_identifier(self) -> str | None: return self.attr("unique-identifier")
    @unique_identifier.setter
    def unique_identifier(self, value: str): self.set_attr("unique-identifier", value)
    @property
    def version(self) -> str | None: return self.attr("version")
    @version.setter
    def version(self, value: str): self.set_attr("version", value)


if __name__ == "__main__":
    def comprehensive_test_no_helpers(input_filepath: str, output_filepath: str):
        print(f"--- 🧪 종합 테스트 시작 (헬퍼 메소드 미사용): '{input_filepath}' ---")

        try:
            # === 1. 파일 읽기 및 초기 상태 확인 ===
            print("\n[1] 파일 읽기 및 초기 상태 확인...")
            pkg = Package.from_file(input_filepath)

            # --- 기본 정보 조회 ---
            print(f"  - Package Version: {pkg.version}")
            print(f"  - Unique Identifier: {pkg.unique_identifier}")
            
            # --- 메타데이터 조회 ---
            main_title = pkg.metadata.titles[0]
            print(f"  - 원본 Title: '{main_title.content}' (ID: {main_title.id})")

            main_creator = pkg.metadata.creators[0]
            print(f"  - 원본 Creator: '{main_creator.content}' (File-as: {main_creator.file_as}, Role: {main_creator.role})")
            
            print(f"  - 언어 수: {len(pkg.metadata.languages)}, 첫번째 언어: {pkg.metadata.languages[0].content}")
            print(f"  - Manifest 아이템 수: {len(pkg.manifest.items)}")
            print(f"  - Spine 아이템 참조 수: {len(pkg.spine.itemrefs)}")
            
            cover_meta = next((meta for meta in pkg.metadata.metas if meta.name == 'cover'), None)
            if cover_meta:
                cover_item_id = cover_meta.content
                cover_item = next((item for item in pkg.manifest.items if item.id == cover_item_id), None)
                if cover_item:
                    print(f"  - 커버 이미지: ID='{cover_item_id}', Href='{cover_item.href}'")

            # === 2. 기존 정보 수정 ===
            print("\n[2] 기존 정보 수정...")
            
            # --- 타이틀 수정 ---
            main_title.content += " [수정됨]"
            print(f"  - 수정된 Title: '{main_title.content}'")

            # --- Creator 속성 수정 ---
            main_creator.file_as = "HAYASHI, Tetsu"
            print(f"  - 수정된 Creator File-as: '{main_creator.file_as}'")
            
            # --- Package 속성 수정 ---
            pkg.direction = "rtl"
            pkg.language = "ja-JP"
            print(f"  - Package 속성 설정: dir='{pkg.direction}', xml:lang='{pkg.language}'")
            
            # --- Manifest 아이템 속성 수정 ---
            first_item = pkg.manifest.items[0]
            original_props = first_item.properties
            first_item.properties = ["nav", "scripted"]
            print(f"  - Manifest Item '{first_item.id}' 속성 변경: {original_props} -> {first_item.properties}")


            # === 3. 새로운 요소 추가 ===
            print("\n[3] 새로운 요소 추가...")
            
            # --- 메타데이터 추가 ---
            new_creator = pkg.metadata.add_creator("Amahara", role="aut", file_as="Amahara")
            print(f"  - Creator 추가: '{new_creator.content}' (ID: {new_creator.id})")
            
            # _add_dc_element를 직접 사용하여 subject 추가
            # Subject 클래스는 Package.Metadata.Subject로 접근 가능
            new_subject_obj = pkg.metadata._add_dc_element("subject", pkg.metadata.Subject, "Fantasy")
            print(f"  - Subject 추가: '{new_subject_obj.content}'")

            # _add_dc_element를 직접 사용하여 date 추가 (opf:event 속성 포함)
            new_date_obj = pkg.metadata._add_dc_element("date", pkg.metadata.Date, "2024-01-01T00:00:00Z", event="modification")
            new_date_obj.set_attr("event", "modification", OPF_NS_URI) # opf:event 속성 설정
            print(f"  - 수정 날짜 Date 추가")

            # --- Meta 태그 추가 (ET.SubElement 직접 사용) ---
            meta_tag = pkg.metadata._get_qname("meta", OPF_NS_URI)
            
            meta_el1 = ET.SubElement(pkg.metadata.element, meta_tag, name="custom-meta", content="some-value")
            meta_obj1 = pkg.metadata.Meta(meta_el1, pkg.nsmap)
            pkg.metadata.metas.append(meta_obj1)
            print(f"  - Meta 추가 (name/content): '{meta_obj1.name}' = '{meta_obj1.content}'")

            meta_el2 = ET.SubElement(pkg.metadata.element, meta_tag)
            meta_obj2 = pkg.metadata.Meta(meta_el2, pkg.nsmap)
            meta_obj2.meta_property = "dcterms:modified"
            meta_obj2.content = "2024-05-21T12:00:00Z"
            pkg.metadata.metas.append(meta_obj2)
            print(f"  - Meta 추가 (property/content): '{meta_obj2.meta_property}' = '{meta_obj2.content}'")
            
            meta_el3 = ET.SubElement(pkg.metadata.element, meta_tag, scheme="marc:relators")
            meta_obj3 = pkg.metadata.Meta(meta_el3, pkg.nsmap)
            meta_obj3.refines = f"#{main_creator.id}"
            meta_obj3.meta_property = "role"
            meta_obj3.content = "author" # text content
            pkg.metadata.metas.append(meta_obj3)
            print(f"  - Meta 추가 (refines): #{main_creator.id}의 role을 정제")


            # --- Manifest 및 Spine 아이템 추가 ---
            new_item_page = pkg.manifest.add_item("Text/p-001.xhtml", "application/xhtml+xml")
            print(f"  - Manifest Item 추가: ID='{new_item_page.id}', Href='{new_item_page.href}'")
            
            new_item_cover = pkg.manifest.add_item("Images/cover.jpg", "image/jpeg", item_id="cover-image", properties=["cover-image"])
            print(f"  - Manifest Cover Item 추가: ID='{new_item_cover.id}', Href='{new_item_cover.href}'")

            new_itemref = pkg.spine.add_itemref(new_item_page.id, linear=True)
            new_itemref.properties = ["page-spread-left"]
            print(f"  - Spine ItemRef 추가: IDRef='{new_itemref.idref}', Properties: {new_itemref.properties}")
            
            # TOC 아이템을 새로운 커버 이미지로 변경
            if pkg.spine.toc:
                 print(f"  - Spine TOC 변경 전: {pkg.spine.toc}")
                 pkg.spine.toc = new_item_cover.id
                 print(f"  - Spine TOC 변경 후: {pkg.spine.toc}")

            # === 4. 결과 출력 및 파일 저장 ===
            print("\n[4] 결과 출력 및 파일 저장...")
            modified_xml_string = pkg.to_string()
            print("\n--- 수정된 XML (문자열 출력) ---")
            print(modified_xml_string)

            pkg.write_to_file(output_filepath)
            print(f"\n--- '{output_filepath}' 파일로 저장 완료 ---")


            # === 5. 저장된 파일 재검증 ===
            print(f"\n[5] 저장된 파일 '{output_filepath}' 재검증...")
            reloaded_pkg = Package.from_file(output_filepath)
            
            assert len(reloaded_pkg.metadata.creators) == 2, "Creator 수가 2가 아님"
            assert "Amahara" in [c.content for c in reloaded_pkg.metadata.creators], "새로운 creator가 없음"
            assert reloaded_pkg.direction == "rtl", "Package dir 속성이 없음"
            assert len(reloaded_pkg.manifest.items) == len(pkg.manifest.items), "Manifest 아이템 수가 일치하지 않음"
            assert reloaded_pkg.spine.itemrefs[-1].idref == new_item_page.id, "마지막 spine itemref가 일치하지 않음"
            assert len(reloaded_pkg.metadata.metas) == len(pkg.metadata.metas), "Meta 태그 수가 일치하지 않음"
            
            print("  - 재검증 성공! 추가/수정된 내용이 올바르게 저장되었습니다.")
            

        except FileNotFoundError:
            print(f"오류: 입력 파일 '{input_filepath}'을 찾을 수 없습니다.")
        except Exception as e:
            import traceback
            print(f"테스트 중 예기치 않은 오류 발생: {e}")
            traceback.print_exc()

    # --- 테스트 실행 ---
    # 원본 파일 경로와 출력 파일 경로를 지정합니다.
    # 제공해주신 opf 파일 이름이 content.opf 라고 가정합니다.
    # 실제 파일 이름으로 변경해주세요.
    input_file = "content.opf" 
    output_file = "modified_content.opf"
    comprehensive_test_no_helpers(input_file, output_file)