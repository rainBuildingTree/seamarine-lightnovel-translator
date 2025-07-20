"""
This module provides classes for parsing, creating, and manipulating
the EPUB container.xml file as defined by the OCF specification.

The primary class is `Container`, which represents the entire
`META-INF/container.xml` file. It uses a nested class, `Container.Rootfile`,
to manage the `<rootfile>` element, which points to the main OPF package file.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET

from .namespaces import NAMESPACES
for prefix, url in NAMESPACES.items():
    ET.register_namespace(prefix, url)

class Container:
    """
    Represents an EPUB `container.xml` file.

    This class provides an interface to parse, modify, and generate
    the `container.xml` file, which is the standard entry point for an
    EPUB file. It locates the root package file (.opf) within the EPUB structure.

    Attributes:
        tree (ET.ElementTree): The underlying XML element tree.
        version (str): The 'version' attribute of the <container> element.
        rootfile (Container.Rootfile): The primary rootfile entry.
    """

    class BrokenError(Exception):
        """
        Raised when the `container.xml` file is malformed or missing
        required elements/attributes.
        """
        pass

    class Rootfile:
        """
        Represents a <rootfile> element within container.xml.

        This class encapsulates the data for a single rootfile entry,
        which points to a package document (OPF file).
        """
        def __init__(self, element: ET.Element = None):
            """
            Initializes a Rootfile instance.

            Note:
                It's generally recommended to use the classmethods `from_element`
                or `new` instead of calling this constructor directly.
            
            Args:
                full_path (str, optional): The path to the OPF file. Defaults to None.
                media_type (str, optional): The media type of the OPF file.
                                            Defaults to "application/oebps-package+xml".
                element (ET.Element, optional): The underlying XML element. Defaults to None.
            """
            self.element: ET.Element = element
            
        @classmethod
        def from_element(cls, rootfile_element: ET.Element):
            """
            Creates a Rootfile instance from an existing XML element.

            Args:
                rootfile_element (ET.Element): The <rootfile> XML element.

            Returns:
                Container.Rootfile: A new instance representing the element.
            
            Raises:
                Container.BrokenError: If 'full-path' or 'media-type' attributes are missing.
            """
            full_path = rootfile_element.attrib.get("full-path")
            media_type = rootfile_element.attrib.get("media-type")

            if not all([full_path, media_type]):
                missing = [attr for attr, val in [("full-path", full_path), ("media-type", media_type)] if not val]
                raise Container.BrokenError(f"Missing required attribute(s) in <rootfile>: {', '.join(missing)}")
            
            return cls(rootfile_element)
        
        @classmethod
        def new(cls, full_path: str, media_type: str = "application/oebps-package+xml"):
            """
            Creates a new Rootfile instance and its corresponding XML element.

            Args:
                full_path (str): The path to the OPF file (e.g., 'OEBPS/content.opf').
                media_type (str, optional): The media type of the file.
                                            Defaults to "application/oebps-package+xml".

            Returns:
                Container.Rootfile: A new instance ready to be added to a Container.

            Raises:
                ValueError: If `full_path` is not provided.
            """
            if not full_path:
                raise ValueError("full_path must be provided")
            
            element = ET.Element(
                f"{{{NAMESPACES['container']}}}rootfile",
                attrib={"full-path": full_path, "media-type": media_type}
            )
            return cls(element)
        
        @property
        def full_path(self):
            """str: The full path to the package document (e.g., 'OEBPS/content.opf')."""
            return self.element.attrib["full-path"]
        @full_path.setter
        def full_path(self, value):
            self.element.attrib["full-path"] = value

        @property
        def media_type(self):
            """str: The media type of the package document."""
            return self.element.attrib["media-type"]
        @media_type.setter
        def media_type(self, value):
            self.element.attrib["media-type"] = value

        def __str__(self) -> str:
            """Returns the XML string representation of the <rootfile> element."""
            return ET.tostring(self.element, encoding="unicode")
    

    def __init__(self, tree: ET.ElementTree, version: str, rootfile: Container.Rootfile):
        """
        Initializes the Container object.

        Note:
            It is recommended to use `Container.from_xml()` or `Container.new()`
            to create instances of this class.
        """
        self.tree = tree
        self.version = version
        self.rootfile = rootfile

    @classmethod
    def from_xml(cls, container_xml: bytes | str | ET.Element | ET.ElementTree):
        """
        Parses XML content and creates a Container instance.

        Args:
            container_xml: The source XML content. Can be raw bytes, a string,
                           an `Element`, or an `ElementTree`.

        Returns:
            Container: A new instance populated with data from the XML.

        Raises:
            Container.BrokenError: If the XML is missing the <rootfile> element.
            TypeError: If the input `container_xml` is of an unsupported type.
        
        Example:
            >>> xml_content = '''
            ... <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
            ...   <rootfiles>
            ...     <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
            ...   </rootfiles>
            ... </container>'''
            >>> container = Container.from_xml(xml_content)
            >>> print(container.rootfile.full_path)
            OEBPS/content.opf
        """
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
        
        rootfile_element = root.find(".//container:rootfile", NAMESPACES)
        if rootfile_element is None:
            raise cls.BrokenError("Missing <rootfile> element in container.xml.")
        
        rootfile = cls.Rootfile.from_element(rootfile_element)
        return cls(tree, version, rootfile)
    
    @classmethod
    def new(cls, rootfile_path: str, version: str = "1.0"):
        """
        Creates a new, standard Container instance from scratch.

        Args:
            rootfile_path (str): The path for the `full-path` attribute of the
                                 new <rootfile> element.
            version (str, optional): The container version. Defaults to "1.0".

        Returns:
            Container: A new instance representing a valid `container.xml` file.
        
        Raises:
            ValueError: If `rootfile_path` is not provided.
        
        Example:
            >>> container = Container.new(rootfile_path="EPUB/package.opf")
            >>> container.save("META-INF/container.xml")
        """
        if not rootfile_path:
            raise ValueError("rootfile_path must be provided")

        root = ET.Element(f"{{{NAMESPACES['container']}}}container", attrib={"version": version})
        rootfiles = ET.SubElement(root, f"{{{NAMESPACES['container']}}}rootfiles")
        
        rootfile = cls.Rootfile.new(full_path=rootfile_path)
        rootfiles.append(rootfile.element)
        
        tree = ET.ElementTree(root)
        return cls(tree, version, rootfile)
    
    def to_dict(self) -> dict:
        """
        Serializes the container's essential data to a dictionary.

        Returns:
            dict: A dictionary representation of the container's data.
        """
        return {
            "version": self.version,
            "rootfile": {
                "full-path": self.rootfile.full_path,
                "media-type": self.rootfile.media_type
            }
        }
        
    def __str__(self) -> str:
        """
        Returns a pretty-printed XML string representation of the container.

        Useful for debugging and human-readable output.

        Returns:
            str: A formatted XML string with indentation.
        """
        root_copy = self.tree.getroot()
        ET.indent(root_copy, space="\t")
        return ET.tostring(root_copy, encoding="unicode")
    
    def __bytes__(self) -> bytes:
        """
        Returns the raw XML content as bytes, including the XML declaration.

        This is suitable for writing directly to a file.

        Returns:
            bytes: The UTF-8 encoded XML content.
        """
        return ET.tostring(self.tree.getroot(), encoding="utf-8", xml_declaration=True)
    
    def __eq__(self, other) -> bool:
        """
        Checks for equality by comparing the content of two Container objects.

        Two containers are considered equal if their version and rootfile
        information are identical.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if the containers are semantically equal, False otherwise.
        """
        return isinstance(other, Container) and self.to_dict() == other.to_dict()
    
    def save(self, path: str, encoding: str = "utf-8", xml_declaration: bool = True):
        """
        Saves the container's XML content to a file.

        This method will create parent directories if they do not exist.

        Args:
            path (str): The full path to the destination file (e.g., 'META-INF/container.xml').
            encoding (str, optional): The file encoding. Defaults to "utf-8".
            xml_declaration (bool, optional): Whether to include the XML declaration
                                              (e.g., `<?xml ... ?>`). Defaults to True.
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.tree.write(path, encoding=encoding, xml_declaration=xml_declaration)