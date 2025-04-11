import asyncio
import copy
import logging
import PIL.Image
from bs4 import BeautifulSoup
from chunker import HtmlChunker
import re 
import time
import PIL
import io
import ast
from google.genai import types
import html

# Constants
MAX_RETRIES = 3

def parse_retry_delay_from_error(error, extra_seconds=2) -> int:
    """
    주어진 에러 메시지에서 재시도 지연시간(초)을 추출합니다.
    에러 메시지에 "retry after <숫자>" 형태가 있다면 해당 숫자를 반환하고,
    그렇지 않으면 기본값 10초를 반환합니다.
    """
    error_str = str(error)
    start_idx = error_str.find('{')
    if start_idx == -1:
        return 0  # JSON 부분 없음
    
    dict_str = error_str[start_idx:]
    retry_seconds = 0

    try:
        # JSON이 아니라 Python dict처럼 생긴 문자열이므로 literal_eval 사용
        err_data = ast.literal_eval(dict_str)
        details = err_data.get("error", {}).get("details", [])
        for detail in details:
            if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                retry_str = detail.get("retryDelay", "")  # 예: "39s"
                match = re.match(r"(\d+)s", retry_str)
                if match:
                    retry_seconds = int(match.group(1))
                    break
    except Exception as e:
        print(f"[WARN] retryDelay 파싱 실패: {e}")
        return 10

    return retry_seconds + extra_seconds if retry_seconds > 0 else 0

# Setup logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler_stream = logging.StreamHandler()
    handler_file = logging.FileHandler('translator.log', encoding='utf-8')
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s:%(name)s: %(message)s')
    handler_stream.setFormatter(formatter)
    handler_file.setFormatter(formatter)
    logger.addHandler(handler_stream)
    logger.addHandler(handler_file)
    logger.setLevel(logging.INFO)

client = None
max_chunk_size = 3000
llm_model = 'gemini-2.0-flash'
custom_prompt = ''
llm_delay = 0.0
japanese_char_threshold = 15
language = 'Japanese'

def set_client(client_instance):
    """Sets the global client instance for API calls."""
    global client
    client = client_instance

def set_llm_model(name):
    global llm_model
    llm_model = name

def set_chunk_size(size):
    global max_chunk_size
    max_chunk_size = size

def set_custom_prompt(prompt):
    global custom_prompt
    if prompt:
        custom_prompt = prompt

def set_llm_delay(time):
    global llm_delay
    llm_delay = time

def set_japanese_char_threshold(threshold):
    global japanese_char_threshold
    japanese_char_threshold = threshold
    
def set_language(lang):
    global language
    language = lang

def clean_gemini_response(response_text: str) -> str:
    """
    Cleans the Gemini API response by stripping markdown formatting.
    """
    text = response_text.strip()
    if text.startswith("```html"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.startswith("### html"):
        text = text[8:].strip()
    if text.startswith("```html"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text

def detect_repeats(text: str, min_repeat: int = 4, max_unit_len: int = 10) -> str:
    """
    주어진 텍스트에서 반복되는 문자열을 <repeat time="N">...<repeat> 형태로 감싸서 반환
    """
    i = 0
    result = ""
    text_len = len(text)

    while i < text_len:
        replaced = False
        for unit_len in range(max_unit_len, 0, -1):
            unit = text[i:i + unit_len]
            if not unit or i + unit_len > text_len:
                continue

            repeat_count = 1
            while text[i + repeat_count * unit_len: i + (repeat_count + 1) * unit_len] == unit:
                repeat_count += 1

            if repeat_count >= min_repeat:
                result += f'<repeat time="{repeat_count}">{unit}</repeat>'
                i += unit_len * repeat_count
                replaced = True
                break

        if not replaced:
            result += text[i]
            i += 1

    return result

def wrap_repeats_in_paragraphs_and_headers(html: str, min_repeat: int = 4) -> str:
    """
    HTML에서 <p> 및 <h1>~<h6> 태그 안의 텍스트에만 <repeat> 태그 적용
    """
    soup = BeautifulSoup(html, "lxml-xml")
    target_tags = [f"h{i}" for i in range(1, 7)] + ["p"]

    for tag in soup.find_all(target_tags):
        for child in tag.find_all(string=True, recursive=True):
            original = str(child)
            replaced = detect_repeats(original, min_repeat=min_repeat)
            if replaced != original:
                child.replace_with(replaced)

    return str(soup)


def restore_repeat_tags_translated(html_content: str) -> str:
    """
    HTML 내 이스케이프된 <repeat time="N">...</repeat> 태그를 실제 반복 문자열로 복원
    """
    # 1. HTML 문자열 내 이스케이프된 문자(&lt;, &gt; 등)를 실제 문자로 변환
    unescaped_html = html.unescape(html_content)
    
    # 2. 정규식 패턴: <repeat time="N">...</repeat> (단순 중첩 없이 처리)
    pattern = re.compile(r'<repeat\s+time="(\d+)">(.*?)</repeat>', re.DOTALL)
    
    # 반복적으로 찾아서 교체 (태그 안에 또 repeat가 있을 경우에도 처리)
    while True:
        match = pattern.search(unescaped_html)
        if not match:
            break
        
        count = int(match.group(1))
        content = match.group(2)
        repeated_content = content * count
        
        unescaped_html = unescaped_html[:match.start()] + repeated_content + unescaped_html[match.end():]
    
    return unescaped_html

def count_closing_tags(html: str, tags: list[str]) -> dict:
    """
    HTML 문자열에서 지정된 태그들의 닫는 태그(</tag>) 개수를 반환
    """
    counts = {}
    for tag in tags:
        closing_pattern = f"</{tag}>"
        counts[tag] = html.count(closing_pattern)
    return counts

def translate_chunk_for_enhance(html_fragment, language):
    set_language(language)
    processed_html = detect_repeats(html_fragment)
    prompt = (
        "당신은 한국어 라이트노벨 전문 번역가입니다. 아래에 주어진 텍스트는 이미 한국어로 번역된 상태이지만, 일부 외국어(일본어, 영어, 키릴문자 등)가 그대로 남아 있을 수 있습니다.\n\n"

        "📝 번역 지침:\n"
        "- **이미 한국어로 번역된 문장은 수정하지 마십시오.**\n"
        "- **한국어가 아닌 텍스트만 자연스럽고 문학적인 한국어로 번역하십시오.**\n"
        "- **출력에는 오직 한국어만 포함되어야 하며, 외국어는 절대 포함하지 마십시오.**\n"
        "- **일본어/영어 원문을 병기하거나 '→'와 같은 형식으로 표시하지 마십시오.**\n"
        "- 설명, 주석, 마크다운 등의 출력은 절대 하지 마십시오.\n"
        "- 번역할 외국어가 없다면 원본 텍스트를 그대로 반환하십시오.\n\n"

        "❌ 잘못된 예시:\n"
        "田中……？ → 다나카......?\n"
        "Tanaka......?: 다나카......?\n\n"

        "✅ 올바른 예시:\n"
        "다나카......?\n\n"

        "다음 글을 검토하여 외국어만 한국어로 번역하십시오. 이미 번역된 한국어는 변경하지 마십시오:\n\n"
        + processed_html
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=llm_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                max_output_tokens=8192 if max_chunk_size < 8192 else max_chunk_size,
                frequency_penalty=0.5,
            ),
            )
            output = response.text.strip()
            output = clean_gemini_response(output)
            output = restore_repeat_tags_translated(output)
            
            logger.info(
                f"Translation result:\n"
                f"--- Input HTML ---\n{html_fragment}\n"
                f"--- Output HTML ---\n{output}"
            )

            if not output:
                raise ValueError("Empty or non-HTML response from Gemini for translation.")
            time.sleep(llm_delay)
            return output
        except Exception as e:
            logger.error(f"translate_chunk_for_enhance - Error on attempt {attempt}: {e}")
            if "429" in str(e) or "Resource exhausted" in str(e):
                attempt -= 1
                delay = parse_retry_delay_from_error(e)
                logger.info(f"429 error detected in translate_chunk_for_enhance, retrying after {delay} seconds.")
                time.sleep(delay)
            else:
                time.sleep(5 * attempt)
    logger.error("translate_chunk_for_enhance - Final failure after MAX_RETRIES attempts.")
    raise Exception("Translation failed in translate_chunk_for_enhance.")

def translate_chunk_with_html(html_fragment, chapter_index, chunk_index, language):
    """
    Translates a chunk of HTML from Japanese to Korean using the Gemini API.
    Raises an exception if the translation fails.
    """
    set_language(language)

    preprocessed_html = wrap_repeats_in_paragraphs_and_headers(html_fragment)

    prompt = (
        "**중요:** 반드시 **순수하게 번역된 HTML만** 반환하십시오. 설명, 주석, 코드 블록, 그 외 부가적인 내용은 절대 포함하지 마십시오.\n\n"

        f"당신은 {language} 라이트노벨 전문 번역가이며, {language}에서 한국어로 번역하는 일을 수행합니다. "
        "번역은 정확하고 자연스러우며 감정 표현이 풍부해야 하며, 국내 정식 출간에 적합한 수준이어야 합니다.\n\n"

        "🎯 번역 지침:\n"
        "- 원문의 어조, 문학적 뉘앙스, 대화체 스타일을 최대한 유지하십시오.\n"
        "- 몰입감 있고 자연스러운 한국어 표현을 사용하십시오.\n\n"

        "⚠️ HTML 및 형식 관련 규칙:\n"
        "- HTML 태그, 구조, 속성(`<p>`, `<img>`, `<repeat>` `class` 등)은 절대 수정, 제거, 재배열하지 마십시오.\n"
        "- 파일 경로, 이미지 alt 텍스트, href, class 이름, 메타데이터 등 **보이지 않는 정보는 번역하지 마십시오.**\n"
        f"- 최종 결과에 {language} 텍스트가 남아 있어서는 안 됩니다.\n"
        "- 번역할 외국어 텍스트가 없다면, 원본 HTML을 그대로 반환하십시오.\n\n"

        + custom_prompt +

        "\n이제 다음 HTML을 검토하여 번역을 수행하십시오:\n\n" + preprocessed_html
    )

    response = client.models.generate_content(
        model=llm_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            top_k=50,
            top_p=0.85,
            temperature=1.8,
            max_output_tokens=8192 if max_chunk_size < 8192 else max_chunk_size,
            frequency_penalty=0.5,
        ),
    )
    output = response.text.strip()
    output = clean_gemini_response(output)

    output = restore_repeat_tags_translated(output)

    logger.info(
        f"[CH{chapter_index}][CHUNK{chunk_index}] Translation result:\n"
        f"--- Input HTML ---\n{html_fragment}\n"
        f"--- Preprocessed HTML ---\n{preprocessed_html}\n"
        f"--- Output HTML ---\n{output}"
    )

    input_tag_counts = count_closing_tags(html_fragment, ["p"] + [f"h{i}" for i in range(1, 7)])
    output_tag_counts = count_closing_tags(output, ["p"] + [f"h{i}" for i in range(1, 7)])

    if input_tag_counts["p"] != output_tag_counts["p"]:
        raise ValueError(f"<p> 태그 개수 불일치: input={input_tag_counts['p']} / output={output_tag_counts['p']}")

    input_h_total = sum(input_tag_counts[f"h{i}"] for i in range(1, 7))
    output_h_total = sum(output_tag_counts[f"h{i}"] for i in range(1, 7))
    if input_h_total != output_h_total:
        raise ValueError(f"<h1>~<h6> 태그 총 개수 불일치: input={input_h_total} / output={output_h_total}")

    if not output or "<" not in output:
        error_message = f"Empty or non-HTML response from Gemini for chapter {chapter_index}, chunk {chunk_index}."
        logger.error(error_message)
        raise ValueError(error_message)

    time.sleep(llm_delay)
    return output

def annotate_image(img_bytes, language):
    set_language(language)
    prompt = (
        "당신은 이미지 속에 포함된 읽을 수 있는 텍스트를 확인하게 됩니다.\n"
        "당신의 임무는 이미지에 보이는 모든 읽을 수 있는 텍스트를 추출하여 자연스러운 한국어로 번역하는 것입니다.\n\n"

        "📝 번역 지침:\n"
        "- 이미지에 **보이는 텍스트만** 번역하십시오.\n"
        "- 한국어 원어민이 읽기에 자연스러운 표현을 사용하십시오.\n"
        "- 출력에는 **한국어만 포함**되어야 하며, 외국어는 절대 포함하지 마십시오.\n"
        "- 설명, 주석, 마크다운 등의 형식은 절대 추가하지 마십시오.\n\n"

        "오직 번역된 한국어 텍스트만 출력하십시오."
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    prompt,
                    PIL.Image.open(io.BytesIO(img_bytes))
                ],
                config=types.GenerateContentConfig(
                top_k= 50,
                top_p= 0.85,
                temperature= 0.8,
                max_output_tokens=8192 if max_chunk_size < 8192 else max_chunk_size,
                frequency_penalty=0.5,
                ),
            )
            output_text = response.text.strip()
            logger.info(f"--- Output Annotation ---\n{output_text}")
            return output_text
        except Exception as e:
            logger.error(f"annotate_image - Error on attempt {attempt}: {e}")
            if "429" in str(e) or "Resource exhausted" in str(e):
                attempt -= 1
                delay = parse_retry_delay_from_error(e)
                logger.info(f"429 error detected in annotate_image, retrying after {delay} seconds.")
                time.sleep(delay)
            else:
                time.sleep(5 * attempt)
    logger.error("annotate_image - Final failure after MAX_RETRIES attempts.")
    raise Exception("Annotate image failed.")

async def async_translate_chunk(html_fragment, chapter_index, chunk_index, semaphore, executor):
    """
    Asynchronously translates an HTML chunk with retry logic.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        async with semaphore:
            try:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    executor,
                    translate_chunk_with_html,
                    html_fragment,
                    chapter_index,
                    chunk_index,
                    language
                )
                # 번역 결과에서 HTML 태그를 제외한 보이는 텍스트 추출
                soup = BeautifulSoup(result, "lxml-xml")
                visible_text = soup.get_text()
                japanese_chars = re.findall(r'[\u3040-\u30FF\u31F0-\u31FF\u4E00-\u9FFF]', visible_text)
                cyrill_chars = re.findall(r'[\u0400-\u04FF\u0500-\u052F]', visible_text)
                thai_chars = re.findall(r'[\u0E00-\u0E7F]', visible_text)
                arabic_chars = re.findall(r'[\u0600-\u06FF\u0750-\u077F]', visible_text)
                hebrew_chars = re.findall(r'[\u0590-\u05FF]', visible_text)
                devanagari_chars = re.findall(r'[\u0900-\u097F]', visible_text)
                greek_chars = re.findall(r'[\u0370-\u03FF]', visible_text)
                
                if japanese_chars or cyrill_chars or thai_chars or arabic_chars or hebrew_chars or devanagari_chars or greek_chars:
                    foreign_chars = japanese_chars + cyrill_chars + thai_chars + arabic_chars + hebrew_chars + devanagari_chars + greek_chars
                else:
                    foreign_chars = []
                count = len(foreign_chars)
                if count >= japanese_char_threshold:
                    if attempt < MAX_RETRIES:
                        raise Exception(
                            f"Translation result contains {count} Japanese characters on attempt {attempt}, triggering a retry."
                        )
                    else:
                        logger.warning(
                            f"[{chapter_index}-{chunk_index}] Last attempt result contains {count} Japanese characters. Using it."
                        )
                return result
            except Exception as e:
                logger.error(f"[{chapter_index}-{chunk_index}] Error on attempt {attempt}: {e}")
                if "429" in str(e) or "Resource exhausted" in str(e):
                    attempt -= 1
                    delay = parse_retry_delay_from_error(e)
                    logger.info(f"[{chapter_index}-{chunk_index}] 429 error detected, retrying after {delay} seconds.")
                    await asyncio.sleep(delay)
                else:
                    await asyncio.sleep(5 * attempt)
            finally:
                await asyncio.sleep(llm_delay)
    logger.error(f"[{chapter_index}-{chunk_index}] Final failure after {MAX_RETRIES} attempts. Returning original fragment.")
    return html_fragment

async def translate_chapter_async(html, chapter_index, executor, semaphore):
    """
    Translates an entire chapter asynchronously by splitting it into chunks,
    translating each chunk concurrently, and recombining the results.
    """
    soup = BeautifulSoup(html, 'lxml-xml')
    head = soup.head
    body = soup.body if soup.body else soup

    # Use HtmlChunker to split the body into manageable chunks.
    chunker = HtmlChunker(max_chars=max_chunk_size)
    chunks = chunker.chunk_body_preserving_structure(body)

    tasks = []
    for chunk_index, chunk in enumerate(chunks):
        html_fragment = str(chunk)
        tasks.append(
            async_translate_chunk(html_fragment, chapter_index, chunk_index, semaphore, executor)
        )
    translated_chunks = await asyncio.gather(*tasks)

    new_soup = BeautifulSoup("", "lxml-xml")
    html_tag = new_soup.new_tag("html")
    new_soup.append(html_tag)
    if head:
        html_tag.append(copy.copy(head))
    new_body = new_soup.new_tag("body")
    for translated_chunk in translated_chunks:
        chunk_soup = BeautifulSoup(translated_chunk, "lxml-xml")
        for content in list(chunk_soup.contents):
            new_body.append(content)
    html_tag.append(new_body)
    return str(new_soup)
