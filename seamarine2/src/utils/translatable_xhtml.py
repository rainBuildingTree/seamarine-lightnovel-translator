from bs4 import BeautifulSoup, NavigableString, Comment
import re

def chunk_text_dict(text_dict: dict[int, str], chunk_size: int) -> list[dict[int, str]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be bigger than 0")

    result_chunks: list[dict[int, str]] = []
    current_chunk: dict[str, str] = {}
    current_length: int = 0

    for doc_id, text in text_dict.items():
        text_len = len(text)
        if current_length + text_len > chunk_size and current_chunk:
            result_chunks.append(current_chunk)
            current_chunk = {}
            current_length = 0
        current_chunk[doc_id] = text
        current_length += text_len

    if current_chunk:
        result_chunks.append(current_chunk)

    return result_chunks

class TranslatableXHTML:
    def __init__(self, html: str, start_id: int = 0):
        self.soup: BeautifulSoup = BeautifulSoup(html, "lxml-xml")
        self.text_dict: dict[int, str] = {}
        self.stard_id = start_id
        self.end_id = start_id - 1
        self._extract_and_replace_text()

    def _is_translatable(self, element: NavigableString) -> bool:
        if not element.strip():
            return False
        if isinstance(element, Comment):
            return False
        if element.parent.name in ['script', 'style', '[document]']:
            return False
        return True
    
    def _extract_and_replace_text(self):
        for text_node in self.soup.find_all(string=True):
            if self._is_translatable(text_node):
                original_text = text_node.string.strip()
                if original_text:
                    self.end_id += 1
                    self.text_dict[f"{self.end_id}"] = original_text
                    placeholder = f"[[[{self.end_id}]]]"
                    text_node.replace_with(NavigableString(placeholder))

    def get_text_chunks(self, chunk_size: int) -> list[dict[int, str]]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be bigger than 0")

        result_chunks: list[dict[int, str]] = []
        current_chunk: dict[int, str] = {}
        current_length: int = 0

        for doc_id, text in self.text_dict.items():
            text_len = len(text)
            if current_length + text_len > chunk_size and current_chunk:
                result_chunks.append(current_chunk)
                current_chunk = {}
                current_length = 0
            current_chunk[doc_id] = text
            current_length += text_len

        if current_chunk:
            result_chunks.append(current_chunk)

        return result_chunks

    def rebase_ids(self, start_id: int) -> int:
        new_text_dict = {}
        id_map = {}
        
        sorted_old_ids = sorted(self.text_dict.keys())
        
        for i, old_id in enumerate(sorted_old_ids):
            new_id = start_id + i
            id_map[f"{old_id}"] = new_id
            new_text_dict[f"{new_id}"] = self.text_dict[f"{old_id}"]

        placeholder_regex = re.compile(r'\[\[\[(\d+)\]\]\]')
        for text_node in self.soup.find_all(string=re.compile(r'\[\[\[')):
            match = placeholder_regex.search(text_node)
            if match:
                old_id = int(match.group(1))
                if old_id in id_map:
                    new_id = id_map[old_id]
                    new_placeholder = f"[[[{new_id}]]]"
                    text_node.replace_with(NavigableString(new_placeholder))

        self.text_dict = new_text_dict
        
        self.end_id = start_id + len(self.text_dict) - 1 if self.text_dict else start_id - 1
        return self.end_id
    
    def force_horizontal_writing(self) -> object:
        """HTML 내에 head에 writing-mode 스타일을 추가."""
        head = self.soup.find("head")
        if head is None:
            head = self.soup.new_tag("head")
            if self.soup.html:
                self.soup.html.insert(0, head)
            else:
                self.soup.insert(0, head)
        style_tag = self.soup.new_tag("style")
        style_tag.string = "body { writing-mode: horizontal-tb !important; }"
        head.append(style_tag)
        return self
    
    def update_texts(self, updated_texts: dict[str, str]):
        for text_id, text in updated_texts.items():
            if text_id in self.text_dict:
                self.text_dict[text_id] = text
            else:
                pass
                #print(f"Warning: ID {text_id} is not in text_dict. Ignore.")
        return self
    
    def get_translated_html(self) -> str:
        temp_soup = BeautifulSoup(str(self.soup), 'lxml-xml')

        placeholder_regex = re.compile(r'\[\[\[(\d+)\]\]\]')
        for text_node in temp_soup.find_all(string=re.compile(r'\[\[\[')):
            match = placeholder_regex.search(text_node)
            if match:
                text_id = match.group(1)
                translated_text = self.text_dict.get(text_id)
                if translated_text is not None:
                    text_node.replace_with(NavigableString(translated_text))

        return str(temp_soup)