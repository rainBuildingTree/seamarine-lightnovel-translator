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
    handler_file = logging.FileHandler('translator.log')
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

def translate_chunk_for_enhance(html_fragment):
    prompt = (
        '''You are a professional Non Korean-to-Korean translator for light novels.
Translate the following plain text into fluent, immersive Korean suitable for official publication.
Rules:
- Only translate visible text.
- Output must be in natural Korean with accurate tone and literary nuance.
- Respond with Korean translation only — no Non-Korean, no explanations, no comments, no markdown.
If there's no Non Korean text, return the input unchanged.\n Now translate:''' + html_fragment
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=llm_model,
                contents=prompt,
            )
            output = response.text.strip()
            output = clean_gemini_response(output)

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

def translate_chunk_with_html(html_fragment, chapter_index, chunk_index):
    """
    Translates a chunk of HTML from Japanese to Korean using the Gemini API.
    Raises an exception if the translation fails.
    """
    prompt = (
        "**Important:** Do NOT include any comments or explanations in your output. Only return the translated result.\n\n"
        "You are a professional Japanese-to-Korean translator who specializes in translating Japanese light novels with accuracy, fluency, and emotional nuance.\n"
        "Translate the following HTML content from Japanese into natural Korean, suitable for publication in an officially localized light novel. "
        "Maintain the tone, dialogue, and literary nuance. Use fluent and immersive Korean that feels professionally written.\n"
        "You're translating Japanese light novels. Follow these strict guidelines:\n\n"
        "⚠️ Strict Instructions:\n"
        "- Only translate visible Japanese text.\n"
        "- NEVER remove or modify any HTML tags, structure, or attributes (like <p>, <img>, class names, etc.)\n"
        "- Do NOT translate file paths, image `alt`, `href`, class names, or non-visible metadata.\n"
        "- NEVER include Japanese characters in your respond\n"
        "- If there is no Japanese text, return the input HTML unchanged.\n"
        "- ❗ Only respond with raw HTML.\n"
        "- Do NOT include explanations, comments, markdown code blocks, or any extra content.\n\n" +
        custom_prompt +
        "Now translate:\n\n### html\n" + html_fragment
    )
    response = client.models.generate_content(
        model=llm_model,
        contents=prompt,
    )
    output = response.text.strip()
    output = clean_gemini_response(output)

    logger.info(
        f"[CH{chapter_index}][CHUNK{chunk_index}] Translation result:\n"
        f"--- Input HTML ---\n{html_fragment}\n"
        f"--- Output HTML ---\n{output}"
    )

    if not output or "<" not in output:
        error_message = f"Empty or non-HTML response from Gemini for chapter {chapter_index}, chunk {chunk_index}."
        logger.error(error_message)
        raise ValueError(error_message)
    time.sleep(llm_delay)
    return output

def annotate_image(img_bytes):
    print("Annotating image")
    prompt = '''You will be shown an image containing Japanese text.
Your task is to extract all readable Japanese text from the image and translate it into Korean.
- Do not include any Japanese text, explanations, or comments.
- Keep the output clean, natural, and in fluent Korean.'''
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    prompt,
                    PIL.Image.open(io.BytesIO(img_bytes))
                ],
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
