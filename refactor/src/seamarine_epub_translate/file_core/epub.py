import os
import posixpath
import re
import zipfile

from lxml import etree as ET

from .errors import *
from .base import FileCore


class EpubFileCore(FileCore):
    def __init__(self, path: str):
        self._validate_epub_path(path)
        self._initialize_state(path)
        self._load_archive_contents()
        self._parse_container_and_opf()
        toc_id, spine, manifest = self._extract_spine_and_manifest()
        self._populate_toc_and_chapters(toc_id, spine, manifest)
        self._backup_originals()
        self._normalize_chapters()

    def _validate_epub_path(self, path: str) -> None:
        if path is None or not os.path.exists(path):
            raise FileNotFoundError(f"No epub found at {path}")
        _, ext = os.path.splitext(os.path.basename(path))
        if ext.lower() != ".epub":
            raise ValueError(f"Only .epub Files Are Supported (Got: {ext})")

    def _initialize_state(self, path: str) -> None:
        self.path: str = path
        self.contents: dict[str, bytes] = {}
        self.chapters: list[str] = []
        self.toc: str = ""
        self.originals_of: dict[str, str] = {}
        self.text_dict: dict[str, str] = {}

    def _load_archive_contents(self) -> None:
        with zipfile.ZipFile(self.path, "r") as archive:
            self.contents = {name: archive.read(name) for name in archive.namelist()}

    def _parse_container_and_opf(self) -> None:
        container_path = "META-INF/container.xml"
        if container_path not in self.contents:
            raise BrokenEpubError("META-INF/container.xml not found")
        container_tree: ET._Element = ET.fromstring(self.contents[container_path])
        rootfile = container_tree.find(
            "container:rootfile",
            {"container": "urn:oasis:names:tc:opendocument:xmlns:container"},
        )
        if rootfile is None:
            raise BrokenEpubError(".//container:rootfile Not Found")
        self.opf_path = rootfile.attrib.get("full-path")
        if not self.opf_path or self.opf_path not in self.contents:
            raise BrokenEpubError(f"{self.opf_path} Not Found")
        self.opf_dir = posixpath.dirname(self.opf_path)
        self.opf_tree: ET._Element = ET.fromstring(self.contents[self.opf_path])
        self._opf_ns = {
            "container": "urn:oasis:names:tc:opendocument:xmlns:container",
            "opf": "http://www.idpf.org/2007/opf",
            "dc": "http://purl.org/dc/elements/1.1/",
        }

    def _extract_spine_and_manifest(self) -> tuple[str | None, list[ET._Element], dict[str, str]]:
        spine_elem = self.opf_tree.find("opf:spine", self._opf_ns)
        toc_id = spine_elem.attrib.get("toc", None)
        spine = spine_elem.findall("opf:itemref", self._opf_ns)
        manifest = {
            item.attrib.get("id"): item.attrib.get("href")
            for item in self.opf_tree.find("opf:manifest", self._opf_ns).findall("opf:item", self._opf_ns)
        }
        return toc_id, spine, manifest

    def _populate_toc_and_chapters(self, toc_id: str | None, spine: list[ET._Element], manifest: dict[str, str]) -> None:
        self.toc = manifest[toc_id]
        for itemref in spine:
            href = manifest[itemref.attrib.get("idref")]
            self.chapters.append(posixpath.join(self.opf_dir, href))

    def _backup_originals(self) -> None:
        for chapter in self.chapters:
            chapter_name, extension = posixpath.splitext(posixpath.basename(chapter))
            backup_chapter = posixpath.join("seamarine_bkup", f"{chapter_name}_bkup{extension}")
            if backup_chapter not in self.contents:
                self.contents[backup_chapter] = self.contents[chapter]
            self.originals_of[chapter] = backup_chapter

    def _normalize_chapters(self) -> None:
        self.contents = {
            chapter: self._flatten_paragraphs(self.contents[chapter].decode())
            for chapter in self.chapters
        }

    def _flatten_paragraphs(self, xml_text: str) -> bytes:
        parser = ET.XMLParser(ns_clean=True, recover=True)
        root = ET.fromstring(xml_text, parser)

        for ruby in root.findall("//*[local-name() = 'ruby']"):
            rts = ruby.findall(".//*[local-name() = 'rt']")
            rbs = ruby.findall(".//*[local-name() = 'rb']")
            if rts:
                text = "".join((rt.text or "") for rt in rts)
            elif rbs:
                text = "".join((rb.text or "") for rb in rbs)
            else:
                text = "".join((ruby.itertext() or ""))
            parent = ruby.getparent()
            idx = parent.index(ruby)
            parent.remove(ruby)
            if idx == 0:
                parent.text = (parent.text or "") + text
            else:
                parent[idx - 1].tail = (parent[idx - 1].tail or "") + text

        for p in root.findall("//*[local-name() = 'p']"):
            for span in p.findall(".//*[local-name() = 'span']"):
                if "tcy" in span.get("class", "") or "line-break" in span.get("class", ""):
                    text = "".join(span.itertext() or "")
                    parent = span.getparent()
                    idx = parent.index(span)
                    parent.remove(span)
                    if idx == 0:
                        parent.text = (parent.text or "") + text
                    else:
                        parent[idx - 1].tail = (parent[idx - 1].tail or "") + text

        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    def get_dict_to_translate(self) -> dict[str, str]:
        """
        Extract text nodes from all chapter XHTML files, replace each text node
        in-place with a placeholder token of the form [[[id]]], and return a
        dictionary mapping the string id to the original text node content.

        The id starts from '0' and increments across nodes.
        If this function has already been executed once (i.e., self.text_dict
        is non-empty), it performs no work and returns the existing
        self.text_dict.
        """
        if self.text_dict:
            return self.text_dict
            
        next_id = self._compute_next_id()
        collected: dict[str, str] = {}

        parser = ET.XMLParser(ns_clean=True, recover=True)
        for chapter in self.chapters:
            xml_bytes = self.contents[chapter]
            root = ET.fromstring(xml_bytes, parser)

            next_id, additions = self._replace_texts_with_placeholders(root, next_id)
            collected.update(additions)

            # Persist modified chapter back into memory
            self.contents[chapter] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        # Keep a global record for later reference
        self.text_dict.update(collected)
        return collected

    def _compute_next_id(self) -> int:
        """Compute the next numeric id based on existing keys in self.text_dict."""
        if not self.text_dict:
            return 0
        try:
            return max(int(k) for k in self.text_dict.keys()) + 1
        except ValueError:
            return 0

    def _replace_texts_with_placeholders(
        self, root: ET._Element, next_id: int
    ) -> tuple[int, dict[str, str]]:
        """
        Walk the XML tree and, for each text node (element.text and child.tail),
        create exactly ONE placeholder [[[id]]] per text node.
        - No sentence splitting. One text_value = one replacement.
        - Whitespace-only nodes are preserved and not replaced.
        - Already placeholderized nodes are skipped.
        Returns the updated next_id and the additions mapping.
        """
        additions: dict[str, str] = {}

        def process_text_node(text_value: str) -> str:
            nonlocal next_id, additions
            if text_value is None or text_value == "":
                return text_value
            # Skip nodes that appear already processed
            if "[[[" in text_value and "]]]" in text_value:
                return text_value

            # Preserve whitespace-only nodes to keep layout intact
            if text_value.strip() == "":
                return text_value

            id_str = str(next_id)
            next_id += 1
            additions[id_str] = text_value
            return f"[[[{id_str}]]]"

        # Iterative DFS to avoid recursion depth issues while preserving order:
        # process element.text, then each child's subtree, then that child's tail.
        stack: list[tuple[ET._Element, str]] = [(root, "enter")]
        while stack:
            node, state = stack.pop()
            if state == "enter":
                if node.text:
                    node.text = process_text_node(node.text)
                children = list(node)
                # Push in reverse order so the first child is processed first
                for child in reversed(children):
                    stack.append((child, "tail"))
                    stack.append((child, "enter"))
            elif state == "tail":
                if node.tail:
                    node.tail = process_text_node(node.tail)

        return next_id, additions

    