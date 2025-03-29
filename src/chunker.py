import copy
from bs4 import BeautifulSoup, NavigableString, Tag


class HtmlChunker:
    """
    A class to chunk HTML content while preserving its structure.
    
    Each chunk's HTML string representation will not exceed the specified max_chars.
    """

    def __init__(self, max_chars=3000):
        """
        Initializes the HtmlChunker with a maximum character limit per chunk.
        
        :param max_chars: Maximum number of characters allowed in each chunk.
        """
        self.max_chars = max_chars

    def _create_empty_div(self):
        """
        Creates and returns an empty <div> tag using BeautifulSoup.
        
        :return: A new BeautifulSoup <div> tag.
        """
        return BeautifulSoup("<div></div>", "html.parser").div

    def _finalize_current_chunk(self, current_chunk, chunks):
        """
        Appends a copy of the current_chunk to chunks (if it has content)
        and then clears the current_chunk.
        
        :param current_chunk: The current BeautifulSoup element accumulating content.
        :param chunks: The list of chunks to append to.
        """
        if current_chunk.contents:
            chunks.append(copy.copy(current_chunk))
            current_chunk.clear()

    def _chunk_text(self, text):
        """
        Splits a long text into multiple <div> chunks each containing up to max_chars characters.
        
        :param text: The text to be split.
        :return: A list of <div> tags containing parts of the text.
        """
        chunks = []
        for i in range(0, len(text), self.max_chars):
            new_div = self._create_empty_div()
            new_div.append(text[i:i + self.max_chars])
            chunks.append(new_div)
        return chunks

    def _chunk_tag(self, tag):
        """
        Splits a Tag's children into multiple Tag chunks, ensuring that each chunk's string
        representation does not exceed max_chars.
        
        :param tag: The BeautifulSoup Tag to be chunked.
        :return: A list of chunked Tags.
        """
        chunks = []
        new_tag = tag.__copy__()
        new_tag.clear()
        for child in list(tag.contents):
            child_str = str(child)
            if len(str(new_tag)) + len(child_str) > self.max_chars:
                if new_tag.contents:
                    chunks.append(new_tag)
                    new_tag = tag.__copy__()
                    new_tag.clear()
            new_tag.append(child)
        if new_tag.contents:
            chunks.append(new_tag)
        return chunks

    def _process_large_element(self, element, chunks):
        """
        Processes an element whose string length exceeds max_chars.
        If the element is a NavigableString or Tag, it is split appropriately;
        otherwise, it is added as-is.
        
        :param element: The element to be processed.
        :param chunks: The list of chunks to append to.
        """
        element_str = str(element)
        if len(element_str) <= self.max_chars:
            new_chunk = self._create_empty_div()
            new_chunk.append(element)
            chunks.append(new_chunk)
        else:
            if isinstance(element, NavigableString):
                chunks.extend(self._chunk_text(str(element)))
            elif isinstance(element, Tag):
                chunks.extend(self._chunk_tag(element))
            else:
                chunks.append(element)

    def chunk_body_preserving_structure(self, body):
        """
        Splits the given BeautifulSoup body into chunks without breaking HTML structure.
        Each chunk's string representation will not exceed max_chars.
        
        :param body: The BeautifulSoup object representing the HTML body.
        :return: A list of BeautifulSoup objects (chunks).
        """
        chunks = []
        current_chunk = self._create_empty_div()
        for element in list(body.contents):
            element_str = str(element)
            # Check if adding the element exceeds the max character limit
            if len(str(current_chunk)) + len(element_str) > self.max_chars:
                self._finalize_current_chunk(current_chunk, chunks)
                if len(element_str) > self.max_chars:
                    self._process_large_element(element, chunks)
                else:
                    current_chunk.append(element)
            else:
                current_chunk.append(element)
        if current_chunk.contents:
            chunks.append(copy.copy(current_chunk))
        return chunks
