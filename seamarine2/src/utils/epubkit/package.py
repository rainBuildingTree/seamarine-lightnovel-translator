import os
from lxml import etree as ET
import uuid
from langcodes import Language
from enum import Enum

from .namespaces import NAMESPACES
for prefix, url in NAMESPACES.items():
    ET.register_namespace(prefix, url)

class _ElementWrapper:
    def __init__(self, element: ET._Element):
        if element is None:
            raise ValueError("Element must not be None")
        self.element: ET._Element = element

    @property
    def text(self) -> str: return self.element.text

    def get_attrib(self, name: str, namespace: str = None) -> str:
        if namespace is not None:
            return self.element.attrib[f"{{{namespace}}}{name}"]
        return self.element.attrib[name]
    
    def set_attrib(self, name: str, value: str, namespace: str = None):
        if namespace is not None:
            self.element.attrib[f"{{{namespace}}}{name}"] = value
        else:
            self.element.attrib[name] = value

class DublinCoreMeta(_ElementWrapper):
    @property
    def direction(self) -> str: return self.get_attrib("dir")
    @direction.setter
    def direction(self, value: str): self.set_attrib("dir", value)

    @property
    def id(self) -> str: return self.get_attrib("id")
    @id.setter
    def id(self, value: str): self.set_attrib("id", value)

    @property
    def language(self) -> str: return self.get_attrib("lang", NAMESPACES["xml"])
    @language.setter
    def language(self, value: str): self.set_attrib("lang", value, NAMESPACES["xml"])

class Meta(DublinCoreMeta):
    @property
    def meta_property(self) -> str: return self.get_attrib("property")
    @meta_property.setter
    def meta_property(self, value: str): self.set_attrib("property", value)

    @property
    def refines(self) -> str: return self.get_attrib("refines")
    @refines.setter
    def refines(self, value: str): self.set_attrib("refines", value)

    @property
    def scheme(self) -> str: return self.get_attrib("scheme")
    @scheme.setter
    def scheme(self, value: str): self.set_attrib("scheme", value)

    ### FOR EPUB2 COMPATIBILITY ###
    @property
    def name(self) -> str: return self.get_attrib("name")
    @name.setter
    def name(self, value: str): self.set_attrib("name", value)

    @property
    def content(self) -> str: return self.get_attrib("content")
    @content.setter
    def content(self, value: str): self.set_attrib("content")

##### Dublin Core Required Elements #####
class Identifier(DublinCoreMeta):
    def __init__(self, element: ET._Element):
        super().__init__(element)
        if element.tag != f"{{{NAMESPACES["dc"]}}}identifier":
            raise ValueError("Expected <dc:identifier> element")
    
    ### FOR EPUB2 COMPATIBILITY ###    
    @property
    def scheme(self) -> str: self.get_attrib("scheme", NAMESPACES["opf"])
    @scheme.setter
    def scheme(self, value: str): self.set_attrib("scheme", value, NAMESPACES["opf"])

        
class Title(DublinCoreMeta):
    def __init__(self, element: ET._Element):
        super().__init__(element)
        if element.tag != f"{{{NAMESPACES["dc"]}}}title":
            raise ValueError("Expected <dc:title> element")

class Language(DublinCoreMeta):
    def __init__(self, element: ET._Element):
        super().__init__(element)
        if element.tag != f"{{{NAMESPACES["dc"]}}}language":
            raise ValueError("Expected <dc:language> element")

##### Dublin Core Optional Elements #####
class Stakeholder(DublinCoreMeta):
    @property
    def role(self) -> str: return self.get_attrib("role", NAMESPACES["opf"])
    @role.setter
    def role(self, value: str): self.set_attrib("role", value, NAMESPACES["opf"])

    @property
    def file_as(self) -> str: return self.get_attrib("file-as", NAMESPACES["opf"])
    @file_as.setter
    def file_as(self, value: str): self.set_attrib("file-as", NAMESPACES["opf"])
    
class Contributor(Stakeholder):
    def __init__(self, element: ET._Element):
        super().__init__(element)
        if element.tag != f"{{{NAMESPACES['dc']}}}contributor":
            raise ValueError("Expected <dc:contributor> element")

class Creator(Stakeholder):
    def __init__(self, element: ET._Element):
        super().__init__(element)
        if element.tag != f"{{{NAMESPACES['dc']}}}creator":
            raise ValueError("Expected <dc:creator> element")

class Date(DublinCoreMeta):
    def __init__(self, element: ET._Element):
        super().__init__(element)
        if element.tag != f"{{{NAMESPACES['dc']}}}date":
            raise ValueError("Expected <dc:date> element")
        
    ### FOR EPUB2 COMPATIBILITY ###
    @property
    def event(self) -> str: return self.get_attrib("event", NAMESPACES["opf"])
    @event.setter
    def event(self, value: str): self.set_attrib("event", value, NAMESPACES["opf"])

class Subject(DublinCoreMeta):
    def __init__(self, element: ET._Element):
        super().__init__(element)
        if element.tag != f"{{{NAMESPACES['dc']}}}subject":
            raise ValueError("Expected <dc:subject> element")

class Type(DublinCoreMeta):
    def __init__(self, element: ET._Element):
        super().__init__(element)
        if element.tag != f"{{{NAMESPACES['dc']}}}type":
            raise ValueError("Expected <dc:type> element")






    



class Package:
    class Metadata:
        class Meta:
            def __init__(self, element: ET.Element):
                self.element = element
            
            @property
            def direction(self) -> str | None:
                return self.element.attrib.get("dir")
            @direction.setter
            def direction(self, value: str):
                self.element.attrib["dir"] = value

            @property
            def id(self) -> str | None:
                return self.element.attrib.get("id")
            @id.setter
            def id(self, value: str):
                self.element.attrib["id"] = value

            @property
            def meta_property(self) -> str | None:
                return self.element.attrib.get("property")
            @meta_property.setter
            def meta_property(self, value: str):
                self.element.attrib["property"] = value

            @property
            def refines(self) -> str | None:
                return self.element.attrib.get("refines")
            @refines.setter
            def refines(self, value: str):
                self.element.attrib["refines"] = value

            @property
            def scheme(self) -> str | None:
                temp = self.element.attrib.get("scheme")
                if temp is not None:
                    return temp
                return self.element.attrib.get(f"{{{NAMESPACES["opf"]}}}scheme")
            @scheme.setter
            def scheme(self, value: str):
                self.element.attrib["scheme"] = value
            
            @property
            def language(self) -> str | None:
                return self.element.attrib.get(f"{{{NAMESPACES['xml']}}}lang")
            @language.setter
            def language(self, value: str):
                self.element.attrib[f"{{{NAMESPACES['xml']}}}lang"] = value

            @property
            def name(self) -> str | None:
                return self.element.attrib.get("name")
            @name.setter
            def name(self, value: str):
                self.element.attrib["name"] = value

            @property
            def content(self) -> str | None:
                temp = self.element.attrib.get("content")
                if temp is not None:
                    return temp
                return self.element.text
            @content.setter
            def content(self, value: str):
                if self.element.attrib.get("content") is not None:
                    self.element.attrib["content"] = value
                else:
                    self.element.text = value

            def attr(self, attr_name: str, attr_namespace: str = None) -> str | None:
                if attr_namespace is not None:
                    return self.element.attrib.get(f"{{{attr_namespace}}}{attr_name}")
                return self.element.attrib.get(attr_name)
            def set_attr(self, attr_name: str, value: str, attr_namespace: str = None):
                if attr_namespace is not None:
                    self.element.attrib[f"{{{attr_namespace}}}{attr_name}"] = value
                else:
                    self.element.attrib[attr_name] = value

        class Identifier:
            def __init__(self, element: ET.Element):
                self.element: ET.Element = element
            
            @property
            def id(self) -> str | None:
                return self.element.attrib.get("id")
            @id.setter
            def id(self, value: str):
                self.element.attrib["id"] = value
            
            @property
            def content(self) -> str | None:
                return self.element.text
            @content.setter
            def content(self, value: str):
                self.element.text = value

            def attr(self, attr_name: str, attr_namespace: str = None) -> str | None:
                if attr_namespace is not None:
                    return self.element.attrib.get(f"{{{attr_namespace}}}{attr_name}")
                return self.element.attrib.get(attr_name)
            def set_attr(self, attr_name: str, value: str, attr_namespace: str = None):
                if attr_namespace is not None:
                    self.element.attrib[f"{{{attr_namespace}}}{attr_name}"] = value
                else:
                    self.element.attrib[attr_name] = value
        
        class Title:
            def __init__(self, element: ET.Element):
                self.element: ET.Element = element

            @property
            def direction(self) -> str | None:
                return self.element.attrib.get("dir")
            @direction.setter
            def direction(self, value: str):
                self.element.attrib["dir"] = value

            @property
            def id(self):
                return self.element.attrib.get("id")
            @id.setter
            def id(self, value: str):
                self.element.attrib["id"] = value

            @property
            def language(self) -> str | None:
                return self.element.attrib.get(f"{{{NAMESPACES['xml']}}}lang")
            @language.setter
            def language(self, value: str):
                self.element.attrib[f"{{{NAMESPACES['xml']}}}lang"] = value

            @property
            def content(self) -> str | None:
                return self.element.text
            @content.setter
            def content(self, value: str):
                self.element.text = value

            def attr(self, attr_name: str, attr_namespace: str = None) -> str | None:
                if attr_namespace is not None:
                    return self.element.attrib.get(f"{{{attr_namespace}}}{attr_name}")
                return self.element.attrib.get(attr_name)
            def set_attr(self, attr_name: str, value: str, attr_namespace: str = None):
                if attr_namespace is not None:
                    self.element.attrib[f"{{{attr_namespace}}}{attr_name}"] = value
                else:
                    self.element.attrib[attr_name] = value

        class Language:
            def __init__(self, element: ET.Element):
                self.element: ET.Element = element
            
            @property
            def id(self) -> str | None:
                return self.element.attrib.get("id")
            @id.setter
            def id(self, value: str):
                self.element.attrib["id"] = value

            @property
            def content(self) -> str | None:
                return self.element.text
            @content.setter
            def content(self, value: str):
                self.element.text = value

            def attr(self, attr_name: str, attr_namespace: str = None) -> str | None:
                if attr_namespace is not None:
                    return self.element.attrib.get(f"{{{attr_namespace}}}{attr_name}")
                return self.element.attrib.get(attr_name)
            def set_attr(self, attr_name: str, value: str, attr_namespace: str = None):
                if attr_namespace is not None:
                    self.element.attrib[f"{{{attr_namespace}}}{attr_name}"] = value
                else:
                    self.element.attrib[attr_name] = value

        class OptionalDublinCore:
            def __init__(self, element: ET.Element):
                self.element: ET.Element = element

            @property
            def direction(self) -> str | None:
                return self.element.attrib.get("dir")
            @direction.setter
            def direction(self, value: str):
                self.element.attrib["dir"] = value

            @property
            def id(self) -> str | None:
                return self.element.attrib.get("id")
            @id.setter
            def id(self, value: str):
                self.element.attrib["id"] = value

            @property
            def language(self) -> str | None:
                return self.element.attrib.get(f"{{{NAMESPACES['xml']}}}lang")
            @language.setter
            def language(self, value: str):
                self.element.attrib[f"{{{NAMESPACES['xml']}}}lang"] = value

            def attr(self, attr_name: str, attr_namespace: str = None) -> str | None:
                if attr_namespace is not None:
                    return self.element.attrib.get(f"{{{attr_namespace}}}{attr_name}")
                return self.element.attrib.get(attr_name)
            def set_attr(self, attr_name: str, value: str, attr_namespace: str = None):
                if attr_namespace is not None:
                    self.element.attrib[f"{{{attr_namespace}}}{attr_name}"] = value
                else:
                    self.element.attrib[attr_name] = value
        
        class Contributor(OptionalDublinCore):
            def __init__(self, element: ET.Element):
                if element.tag != f"{{{NAMESPACES['dc']}}}contributor":
                    raise ValueError(f"Expected <dc:contributor> element, got <{element.tag}>")
                super().__init__(element)

            @property
            def file_as(self) -> str | None:
                return self.attr("file-as", NAMESPACES["opf"])
            @file_as.setter
            def file_as(self, value: str):
                self.set_attr("file-as", value, NAMESPACES["opf"])

            @property
            def role(self) -> str | None:
                return self.attr("role", NAMESPACES["opf"])
            @role.setter
            def role(self, value: str):
                self.set_attr("role", value, NAMESPACES["opf"])

        class Creator(OptionalDublinCore):
            def __init__(self, element: ET.Element):
                if element.tag != f"{{{NAMESPACES['dc']}}}creator":
                    raise ValueError(f"Expected <dc:creator> element, got <{element.tag}>")
                super().__init__(element)

            @property
            def file_as(self) -> str | None:
                return self.attr("file-as", NAMESPACES["opf"])
            @file_as.setter
            def file_as(self, value: str):
                self.set_attr("file-as", value, NAMESPACES["opf"])

            @property
            def role(self) -> str | None:
                return self.attr("role", NAMESPACES["opf"])
            @role.setter
            def role(self, value: str):
                self.set_attr("role", value, NAMESPACES["opf"])

        class Date(OptionalDublinCore):
            def __init__(self, element: ET.Element):
                if element.tag != f"{{{NAMESPACES['dc']}}}date":
                    raise ValueError(f"Expected <dc:date> element, got <{element.tag}>")
                super().__init__(element)

        class Subject(OptionalDublinCore):
            def __init__(self, element: ET.Element):
                if element.tag != f"{{{NAMESPACES['dc']}}}subject":
                    raise ValueError(f"Expected <dc:subject> element, got <{element.tag}>")
                super().__init__(element)

            @property
            def authority(self) -> str | None:
                return self.attr("authority", NAMESPACES["opf"])
            @authority.setter
            def authority(self, value: str):
                self.set_attr("authority", value, NAMESPACES["opf"])

            @property
            def term(self) -> str | None:
                return self.attr("term", NAMESPACES["opf"])
            @term.setter
            def term(self, value: str):
                self.set_attr("term", value, NAMESPACES["opf"])

        class Type(OptionalDublinCore):
            def __init__(self, element: ET.Element):
                if element.tag != f"{{{NAMESPACES['dc']}}}type":
                    raise ValueError(f"Expected <dc:type> element, got <{element.tag}>")
                super().__init__(element)

        def __init__(self, element: ET.Element):
            self.element: ET.Element = element

            self.identifiers: list[Package.Metadata.Identifier] = [
                Package.Metadata.Identifier(el)
                for el in element.findall("dc:identifier", NAMESPACES)
            ]
            self.titles: list[Package.Metadata.Title] = [
                Package.Metadata.Title(el)
                for el in element.findall("dc:title", NAMESPACES)
            ]
            self.languages: list[Package.Metadata.Language] = [
                Package.Metadata.Language(el)
                for el in element.findall("dc:language", NAMESPACES)
            ]
            self.contributors: list[Package.Metadata.Contributor] = [
                Package.Metadata.Contributor(el)
                for el in element.findall("dc:contributor", NAMESPACES)
            ]
            self.creators: list[Package.Metadata.Creator] = [
                Package.Metadata.Creator(el)
                for el in element.findall("dc:creator", NAMESPACES)
            ]
            self.dates: list[Package.Metadata.Date] = [
                Package.Metadata.Date(el)
                for el in element.findall("dc:date", NAMESPACES)
            ]
            self.subjects: list[Package.Metadata.Subject] = [
                Package.Metadata.Subject(el)
                for el in element.findall("dc:subject", NAMESPACES)
            ]
            self.types: list[Package.Metadata.Type] = [
                Package.Metadata.Type(el)
                for el in element.findall("dc:type", NAMESPACES)
            ]
            handled_tags = {
                f"{{{NAMESPACES['dc']}}}{name}"
                for name in [
                    "identifier", "title", "language", "contributor",
                    "creator", "date", "subject", "type"
                ]
            }
            self.optional_dublin_cores: list[Package.Metadata.OptionalDublinCore] = [
                Package.Metadata.OptionalDublinCore(el)
                for el in element.findall("*")
                if el.tag.startswith(f"{{{NAMESPACES['dc']}}}") and el.tag not in handled_tags
            ]
            self.metas: list[Package.Metadata.Meta] = [
                Package.Metadata.Meta(el)
                for el in element.findall("meta", NAMESPACES)
            ]


    class Manifest:
        class Item:
            def __init__(self, element: ET.Element):
                self.element: ET.Element = element
            
            @property
            def fallback(self) -> str | None:
                return self.element.attrib.get("fallback")
            @fallback.setter
            def fallback(self, value: str):
                self.element.attrib["fallback"] = value
            def set_fallback(self, fallback_item):
                self.element.attrib["fallback"] = fallback_item.id
            
            @property
            def href(self) -> str | None:
                return self.element.attrib.get("href")
            @href.setter
            def href(self, value: str):
                self.element.attrib["href"] = value
            
            @property
            def id(self) -> str | None:
                return self.element.attrib.get("id")
            @id.setter
            def id(self, value: str):
                self.element.attrib["id"] = value

            @property
            def media_overlay(self) -> str | None:
                return self.element.attrib.get("media-overlay")
            @media_overlay.setter
            def media_overlay(self, value: str):
                self.element.attrib["media-overlay"] = value
            def set_media_overlay(self, media_overlay_item):
                self.element.attrib["media-overlay"] = media_overlay_item.id
            
            @property
            def media_type(self) -> str | None:
                return self.element.attrib.get("media-type")
            @media_type.setter
            def media_type(self, value: str):
                self.element.attrib["media-overlay"] = value

            @property
            def properties(self) -> str | None:
                return self.element.attrib.get("properties")
            @properties.setter
            def properties(self, value: str):
                self.element.attrib["properties"] = value

        def __init__(self, element: ET.Element):
            self.element: ET.Element = element
            self.items: list[Package.Manifest.Item] = [
                Package.Manifest.Item(el)
                for el in element.findall("item", NAMESPACES)
            ]

        @property
        def id(self) -> str | None:
            return self.element.attrib.get("id")
        @id.setter
        def id(self, value: str):
            self.element.attrib["id"] = value

    class Spine:
        class ItemRef:
            def __init__(self, element: ET.Element):
                self.element = element
        
            @property
            def id(self) -> str | None:
                return self.element.attrib.get("id")
            @id.setter
            def id(self, value: str):
                self.element.attrib["id"] = value

            @property
            def idref(self) -> str | None:
                return self.element.attrib.get("idref")
            @idref.setter
            def idref(self, value: str):
                self.element.attrib["idref"] = value
            def set_idref(self, manifest_item):
                self.element.attrib["idref"] = manifest_item.id
            
            @property
            def linear(self) -> str | None:
                return self.element.attrib.get("linear")
            @linear.setter
            def linear(self, value: str):
                self.element.attrib["linear"] = value
            
            @property
            def properties(self) -> str | None:
                return self.element.attrib.get("properties")
            @properties.setter
            def properties(self, value: str):
                self.element.attrib["properties"] = value

        def __init__(self, element: ET.Element):
            self.element = element
            self.itemrefs: list[Package.Spine.ItemRef] = [
                Package.Spine.ItemRef(el)
                for el in element.findall("itemref", NAMESPACES)
            ]
        
        @property
        def id(self) -> str | None:
            return self.element.attrib.get("id")
        @id.setter
        def id(self, value):
            self.element.attrib["id"] = value

        @property
        def page_propagation_direction(self) -> str | None:
            return self.element.attrib.get("page-propagation-direction")
        @page_propagation_direction.setter
        def page_propagation_direction(self, value: str):
            self.element.attrib["page-propagation-direction"] = value
        
        @property
        def toc(self) -> str | None:
            return self.element.attrib.get("toc")
        @toc.setter
        def toc(self, value: str):
            self.element.attrib["toc"] = value


    class Guide:
        class Reference:
            def __init__(self, element: ET.Element):
                self.element = element

            @property
            def type_attr(self) -> str | None:
                return self.element.attrib.get("type")
            @type_attr.setter
            def type_attr(self, value: str):
                self.element.attrib["type"] = value
            
            @property
            def title(self) -> str | None:
                return self.element.attrib.get("title")
            @title.setter
            def title(self, value: str):
                self.element.attrib["title"] = value
            
            @property
            def href(self) -> str | None:
                return self.element.attrib.get("href")
            @href.setter
            def href(self, value: str):
                self.element.attrib["href"] = value
            def set_href(self, manifest_item):
                self.element.attrib["href"] = manifest_item.href

        def __init__(self, element: ET.Element):
            self.element: ET.Element = element
            self.references: list[Package.Guide.Reference] = [
                Package.Guide.Reference(el)
                for el in element.findall("reference", NAMESPACES)
            ]
            
    class Collection:
        class Link:
            def __init__(self, element: ET.Element):
                self.element = element
            
            @property
            def href(self) -> str | None:
                return self.element.attrib.get("href")
            @href.setter
            def href(self, value: str):
                self.element.attrib["href"] = value
            
        def __init__(self, element: ET.Element):
            self.element = element
            self.metadata = Package.Metadata(element.find("metadata", NAMESPACES))
            self.collections: list[Package.Collection] = [
                Package.Collection(el)
                for el in element.findall("collection", NAMESPACES)
            ]
            self.links: list[Package.Collection.Link] = [
                Package.Collection.Link(el)
                for el in element.findall("link", NAMESPACES)
            ]

        @property
        def dir(self) -> str | None:
            return self.element.attrib.get("dir")
        @dir.setter
        def dir(self, value: str):
            self.element.attrib["dir"] = value
        
        @property
        def id(self) -> str | None:
            return self.element.attrib.get("id")
        @id.setter
        def id(self, value: str):
            self.element.attrib["id"] = value

        @property
        def role(self) -> str | None:
            return self.element.attrib.get("role")
        @role.setter
        def role(self, value: str):
            self.element.attrib["role"] = value

        @property
        def language(self) -> str | None:
            return self.element.attrib.get(f"{{{NAMESPACES['xml']}}}lang")
        @language.setter
        def language(self, value: str):
            self.element.attrib[f"{{{NAMESPACES['xml']}}}lang"] = value

        
    def __init__(self, tree: ET.ElementTree):
        self.tree = tree
        self.element = tree.getroot()
        self.metadata: Package.Metadata = Package.Metadata(tree.getroot().find("metadata", NAMESPACES))
        self.manifest: Package.Manifest = Package.Manifest(tree.getroot().find("manifest", NAMESPACES))
        self.spine: Package.Spine = Package.Spine(tree.getroot().find("spine", NAMESPACES))
        self.guide: Package.Guide = Package.Guide(tree.getroot().find("guide"), NAMESPACES)
        self.collections: list[Package.Collection] = [
            Package.Collection(el)
            for el in tree.getroot().findall("collection", NAMESPACES)
        ]

    @property
    def dir(self) -> str | None:
        return self.element.attrib.get("dir")
    @dir.setter
    def dir(self, value: str):
        self.element.attrib["dir"] = value

    @property
    def id(self) -> str | None:
        return self.element.attrib.get("id")
    @id.setter
    def id(self, value: str):
        self.element.attrib["id"] = value

    @property
    def prefix(self) -> str | None:
        return self.element.attrib.get("prefix")
    @prefix.setter
    def prefix(self, value: str):
        self.element.attrib["prefix"] = value

    @property
    def language(self) -> str | None:
        return self.element.attrib.get(f"{{{NAMESPACES['xml']}}}lang")
    @language.setter
    def language(self, value: str):
        self.element.attrib[f"{{{NAMESPACES['xml']}}}lang"] = value

    @property
    def unique_identifier(self) -> str | None:
        return self.element.attrib.get("unique-identifier")
    @unique_identifier.setter
    def unique_identifier(self, value: str):
        self.element.attrib["unique-identifier"] = value
    def set_unique_identifier(self, identifier_metadata):
        self.element.attrib["unique-identifier"] = identifier_metadata.id
    
    @property
    def version(self) -> str | None:
        return self.element.attrib.get("version")
    @version.setter
    def version(self, value: str):
        self.element.attrib["version"] = value

