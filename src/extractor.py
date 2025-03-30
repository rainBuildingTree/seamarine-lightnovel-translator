import json
import csv
from ebooklib import epub
from bs4 import BeautifulSoup

class ProperNounExtractor:
    def __init__(self, epub_path: str, client, llm_model: str):
        self.epub_path = epub_path
        self.client = client
        self.llm_model = llm_model
        self.prompt = '''You are given a Japanese novel text. Extract all the proper nouns found in the text and translate each of them into Korean. Return the result strictly as a JSON object with Japanese names as keys and their Korean translations as values. Do not include any other commentary or explanation.

Example format:
{
  "田中": "다나카",
  "東京": "도쿄"
}

Here is the text:
'''
        self.proper_nouns = {}

    def extract_text(self) -> str:
        book = epub.read_epub(self.epub_path)
        full_text = ""
        for item in book.get_items():
            if isinstance(item, epub.EpubHtml):
                try:
                    content = item.get_content().decode('utf-8')
                    soup = BeautifulSoup(content, 'html.parser')
                    full_text += soup.get_text() + '\n'
                except Exception as e:
                    print(f"[ERROR] Content decode failed: {e}")
        return full_text

    def split_text(self, text: str, max_length: int = 2000) -> list[str]:
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]

    def clean_response(self, response_text: str) -> str:
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:].strip()
        elif text.startswith("```"):
            text = text[3:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        return text

    def run_extraction(self, progress_callback=None):
        full_text = self.extract_text()
        chunks = self.split_text(full_text)
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            try:
                response = self.client.models.generate_content(
                    model=self.llm_model,
                    contents=self.prompt + chunk
                )
                cleaned = self.clean_response(response.text.strip())
                new_dict = json.loads(cleaned)
                self.proper_nouns.update(new_dict)
            except Exception as e:
                print(f"[ERROR] Failed to parse chunk: {e}")
            if progress_callback:
                progress_callback(int((i + 1) / total_chunks * 100))

    def save_to_csv(self, filename="proper_nouns.csv"):
        with open(filename, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Japanese", "Korean", "Use?(y/n)"])
            for jp, kr in self.proper_nouns.items():
                writer.writerow([jp, kr, 'y'])
