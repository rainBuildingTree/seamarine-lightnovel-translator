import asyncio
from concurrent.futures import ThreadPoolExecutor
from ebooklib import epub
from ebooklib.epub import EpubHtml
from bs4 import BeautifulSoup, NavigableString, Tag
from google import genai
from tqdm import tqdm
import time
import copy
import re
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import uuid

# === 기본 설정 및 동기 함수들 ===

# 초기 클라이언트는 빈 API 키로 생성 (번역 시작 시 재설정)
MAX_CHUNK_CHARS = 2000
global_model_name = 'gemini-2.0-flash'

def chunk_body_preserving_structure(body, max_chars=MAX_CHUNK_CHARS):
    chunks = []
    current_chunk = BeautifulSoup("<div></div>", "html.parser").div
    for element in list(body.contents):
        element_str = str(element)
        if len(str(current_chunk)) + len(element_str) > max_chars:
            if current_chunk.contents:
                chunks.append(copy.copy(current_chunk))
                current_chunk.clear()
            if len(element_str) > max_chars:
                if isinstance(element, NavigableString):
                    text = str(element)
                    for i in range(0, len(text), max_chars):
                        new_tag = BeautifulSoup("<div></div>", "html.parser").div
                        new_tag.append(text[i:i+max_chars])
                        chunks.append(new_tag)
                elif isinstance(element, Tag):
                    temp_tag = element.__copy__()
                    temp_tag.clear()
                    for child in list(element.contents):
                        child_str = str(child)
                        if len(str(temp_tag)) + len(child_str) > max_chars:
                            if temp_tag.contents:
                                chunks.append(temp_tag)
                                temp_tag = element.__copy__()
                                temp_tag.clear()
                        temp_tag.append(child)
                    if temp_tag.contents:
                        chunks.append(temp_tag)
                else:
                    chunks.append(element)
            else:
                current_chunk.append(element)
        else:
            current_chunk.append(element)
    if current_chunk.contents:
        chunks.append(copy.copy(current_chunk))
    return chunks

def clean_gemini_response(response_text: str) -> str:
    text = response_text.strip()
    if text.startswith("```html"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text

def translate_chunk_with_html(html_fragment, chapter_index, chunk_index):
    prompt = '''
**Important:** Do NOT include any comments or explanations in your output. Only return the translated result.

You are a professional Japanese-to-Korean translator who specializes in translating Japanese light novels with accuracy, fluency, and emotional nuance.
Translate the following HTML content from Japanese into natural Korean, suitable for publication in an officially localized light novel. Maintain the tone, dialogue, and literary nuance. Use fluent and immersive Korean that feels professionally written.
You're translating Japanese light novels. Follow these strict guidelines:

⚠️ Strict Instructions:
- Only translate visible Japanese text.
- NEVER remove or modify any HTML tags, structure, or attributes (like <p>, <img>, class names, etc.)
- Do NOT translate file paths, image `alt`, `href`, class names, or non-visible metadata.
- NEVER include Japanese characters in your respond
- If there is no Japanese text, return the input HTML unchanged.
- ❗ Only respond with raw HTML.
- Do NOT include explanations, comments, markdown code blocks, or any extra content.

Now translate:

### html
''' + html_fragment
    try:
        response = client.models.generate_content(
            model=global_model_name,
            contents=prompt
        )
        output = response.text.strip()
        output = clean_gemini_response(output)
        if not output or "<" not in output:
            raise ValueError("Empty or non-HTML response from Gemini")
        return output
    except Exception as e:
        print("Gemini error Retrying(1):", e)
        time.sleep(5.0)
        try:
            response = client.models.generate_content(
                model=global_model_name,
                contents=prompt
            )
            output = response.text.strip()
            output = clean_gemini_response(output)
            if not output or "<" not in output:
                raise ValueError("Empty or non-HTML response from Gemini")
            return output
        except Exception as e:
            print("Gemini error Retrying(2):", e)
            time.sleep(15.0)
            try:
                response = client.models.generate_content(
                    model=global_model_name,
                    contents=prompt
                )
                output = response.text.strip()
                output = clean_gemini_response(output)
                if not output or "<" not in output:
                    raise ValueError("Empty or non-HTML response from Gemini")
                return output
            except Exception as e:
                print("Gemini error Retrying:", e)
                return html_fragment

# === 비동기 처리 관련 함수들 ===

MAX_RETRIES = 3

async def async_translate_chunk(html_fragment, chapter_index, chunk_index, semaphore, executor):
    for attempt in range(1, MAX_RETRIES + 1):
        async with semaphore:
            try:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    executor, 
                    translate_chunk_with_html, 
                    html_fragment, 
                    chapter_index, 
                    chunk_index
                )
                return result
            except Exception as e:
                print(f"[{chapter_index}-{chunk_index}] 에러 발생 (시도 {attempt}): {e}")
                await asyncio.sleep(5 * attempt)
    print(f"[{chapter_index}-{chunk_index}] 최종 실패. 원본 반환.")
    return html_fragment

async def translate_chapter_async(html, chapter_index, executor, semaphore):
    soup = BeautifulSoup(html, 'html.parser')
    head = soup.head
    body = soup.body if soup.body else soup
    chunks = chunk_body_preserving_structure(body)
    tasks = []
    for chunk_index, chunk in enumerate(chunks):
        html_fragment = str(chunk)
        tasks.append(async_translate_chunk(html_fragment, chapter_index, chunk_index, semaphore, executor))
    translated_chunks = await asyncio.gather(*tasks)
    new_soup = BeautifulSoup("", "html.parser")
    html_tag = new_soup.new_tag("html")
    new_soup.append(html_tag)
    if head:
        html_tag.append(copy.copy(head))
    new_body = new_soup.new_tag("body")
    for translated_chunk in translated_chunks:
        chunk_soup = BeautifulSoup(translated_chunk, "html.parser")
        for content in list(chunk_soup.contents):
            new_body.append(content)
    html_tag.append(new_body)
    return str(new_soup)

async def translate_epub_async(input_path, output_path, max_concurrent_requests):
    book = epub.read_epub(input_path)
    translated_book = epub.EpubBook()

    item_map = {}
    for item in book.get_items():
        new_item = epub.EpubItem(
            uid=item.get_id(),
            file_name=item.file_name,
            media_type=item.media_type,
            content=item.content
        )
        item_map[item.get_id()] = new_item
        translated_book.add_item(new_item)

    translated_book.set_identifier(f'{uuid.uuid4()}')    

    # 책 제목 번역
    metadata_title = book.get_metadata('DC', 'title')
    if metadata_title:
        original_title = metadata_title[0][0]
        def translate_text(text, chapter_index=0, chunk_index=0):
            html_fragment = f"<div>{text}</div>"
            translated_html = translate_chunk_with_html(html_fragment, chapter_index, chunk_index)
            soup = BeautifulSoup(translated_html, "html.parser")
            return soup.get_text()
        translated_title = translate_text(original_title, chapter_index=0, chunk_index=0)
        #book.set_title(translated_title)
        translated_book.set_title(translated_title)

    translated_book.set_language('ko')

    cover = book.get_item_with_id('cover')
    if cover:
        translated_book.set_cover(cover.file_name, cover.content)

    creators = book.get_metadata('DC', 'creator')
    for creator in creators:
        translated_book.add_author(creator[0])

    translated_book.add_metadata('DC', 'contributor', 'SeaMarine')

    # TOC 번역
    def translate_toc_entry(entry, chapter_index=0, chunk_index=0):
        if isinstance(entry, epub.Link):
            entry.title = translate_text(entry.title, chapter_index, chunk_index)
            return entry
        elif isinstance(entry, tuple) and len(entry) == 2:
            link, subitems = entry
            link.title = translate_text(link.title, chapter_index, chunk_index)
            new_subitems = [translate_toc_entry(sub, chapter_index, chunk_index) for sub in subitems]
            return (link, new_subitems)
        else:
            return entry
        
    translated_book.toc = book.toc
    translated_book.spine = book.spine

    epub.write_epub(output_path, translated_book)
    translated_book = epub.read_epub(output_path)
    translated_book.toc = [translate_toc_entry(entry, chapter_index=0, chunk_index=0) for entry in translated_book.toc]
    
    chapter_items = [item for item in translated_book.get_items() if isinstance(item, EpubHtml)]

    semaphore = asyncio.Semaphore(max_concurrent_requests)
    executor = ThreadPoolExecutor(max_concurrent_requests)
    
    tasks = []
    for idx, item in enumerate(chapter_items):
        html = item.get_content().decode('utf-8')
        tasks.append(translate_chapter_async(html, idx + 1, executor, semaphore))
    
    translated_results = await asyncio.gather(*tasks)
    for item, translated_html in zip(chapter_items, translated_results):
        item.set_content(translated_html.encode('utf-8'))
    
    epub.write_epub(output_path, translated_book)
    return output_path

# === GUI 구현 (tkinter) ===

class TranslatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sea Marine EPUB Translator")
        self.geometry("600x550")
        
        self.input_path = None
        self.output_path = None
        
        # API 키 입력
        self.api_key_label = tk.Label(self, text="API Key:")
        self.api_key_label.pack(pady=5)
        self.api_key_entry = tk.Entry(self, width=50, show="*")
        self.api_key_entry.pack(pady=5)
        
        # 최대 동시 요청 수 설정 (1~100)
        self.concurrent_label = tk.Label(self, text="Max Concurrent Requests (1-10):")
        self.concurrent_label.pack(pady=5)
        self.concurrent_spinbox = tk.Spinbox(self, from_=1, to=20, width=5)
        self.concurrent_spinbox.delete(0, tk.END)
        self.concurrent_spinbox.insert(0, "1")
        self.concurrent_spinbox.pack(pady=5)
        
        # EPUB 파일 선택 버튼
        self.select_button = tk.Button(self, text="Select Epub File", command=self.select_file)
        self.select_button.pack(pady=10)
        
        self.file_label = tk.Label(self, text="Selected File: None")
        self.file_label.pack()
        
        # 번역 시작 버튼
        self.translate_button = tk.Button(self, text="Start Translation", command=self.start_translation, state=tk.DISABLED)
        self.translate_button.pack(pady=10)
        
        # 진행 상황 표시용 텍스트 박스
        self.log_text = tk.Text(self, height=10)
        self.log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 진행바
        self.progress = ttk.Progressbar(self, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill=tk.X, padx=10, pady=5)
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("EPUB Files", "*.epub"), ("All Files", "*.*")]
        )
        if file_path:
            self.input_path = file_path
            self.file_label.config(text=f"Selected File: {os.path.basename(file_path)}")
            self.translate_button.config(state=tk.NORMAL)
    
    def start_translation(self):
        if not self.input_path:
            messagebox.showwarning("WARNING", "Please select an EPUB file first!")
            return
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showwarning("WARNING", "Please enter your API key!")
            return
        # 동시 요청 수를 Spinbox에서 읽음 (문자열을 정수로 변환)
        try:
            max_concurrent = int(self.concurrent_spinbox.get())
            if max_concurrent < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("FBI WARNING", "Why on earth are you putting a strange value in the number of concurrent requests?")
            return
        
        # output 파일 경로 생성
        dir_name = os.path.dirname(self.input_path)
        base_name = os.path.splitext(os.path.basename(self.input_path))[0]
        self.output_path = os.path.join(dir_name, base_name + "_translated.epub")
        
        self.translate_button.config(state=tk.DISABLED)
        self.select_button.config(state=tk.DISABLED)
        self.log_text.insert(tk.END, "Starting translation...\n")
        self.progress.start(10)
        
        # 백그라운드 스레드에서 번역 실행 (GUI 멈춤 방지)
        threading.Thread(target=self.run_translation, args=(max_concurrent,), daemon=True).start()
    
    def run_translation(self, max_concurrent):
        try:
            # 입력된 API 키로 전역 클라이언트 재설정
            api_key = self.api_key_entry.get().strip()
            global client
            client = genai.Client(api_key=api_key)
            
            asyncio.run(translate_epub_async(self.input_path, self.output_path, max_concurrent))
            self.log_text.insert(tk.END, f"Translation completed! File: {self.output_path}\n")
        except Exception as e:
            self.log_text.insert(tk.END, f"An error occurred during translation: {e}\nActually I also don't know why Good Luck")
        finally:
            self.progress.stop()
            self.translate_button.config(state=tk.NORMAL)
            self.select_button.config(state=tk.NORMAL)

if __name__ == '__main__':
    app = TranslatorGUI()
    app.mainloop()
