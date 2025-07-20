"""
This module provides a representation of the EPUB `mimetype` file.

The `mimetype` file is a required component of an EPUB archive. It must be
the first file in the ZIP container, stored without compression, and must
contain the exact ASCII string "application/epub+zip".

This module offers a simple class to represent this content and a utility
function to verify it.
"""

from __future__ import annotations

class Mimetype:
    """
    Represents the content of the EPUB `mimetype` file.

    This class encapsulates the required, fixed content of the `mimetype` file,
    which is always "application/epub+zip". It provides convenient methods
    for accessing this content as bytes or a string.

    An instance of this class doesn't hold any unique state; it's a simple
    utility wrapper around a constant value.
    """
    def __init__(self):
        """
        Initializes a Mimetype instance.

        The `data` attribute is hard-coded to the required mimetype content.
        """
        self.data = b"application/epub+zip"

    def __bytes__(self) -> bytes:
        """
        Returns the mimetype content as a raw bytes object.

        This is the format required for writing to the `mimetype` file.

        Returns:
            bytes: The content `b"application/epub+zip"`.
        """
        return self.data

    def __str__(self) -> str:
        """
        Returns the mimetype content as a string.

        The content is decoded using 'ascii', as specified by the EPUB standard.

        Returns:
            str: The content `"application/epub+zip"`.
        """
        return self.data.decode("ascii")

    @staticmethod
    def verify(data: bytes) -> bool:
        """
        Verifies if the given bytes represent a valid EPUB mimetype.

        This static method checks if the input data, after stripping any
        leading or trailing whitespace, matches the required string
        `b"application/epub+zip"`. This is useful for validating an
        existing `mimetype` file from an EPUB archive.

        Args:
            data (bytes): The byte content read from a potential mimetype file.

        Returns:
            bool: True if the data is a valid EPUB mimetype, False otherwise.
            
        Example:
            >>> valid_data = b"  application/epub+zip  \\n"
            >>> Mimetype.verify(valid_data)
            True
            >>> invalid_data = b"application/zip"
            >>> Mimetype.verify(invalid_data)
            False
        """
        return data.strip() == b"application/epub+zip"