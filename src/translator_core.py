import asyncio
import copy
import logging
from bs4 import BeautifulSoup
from chunker import HtmlChunker
import re 
import time

# Constants
MAX_RETRIES = 3

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
    response = client.models.generate_content(
        model=llm_model,
        contents=prompt,
    )
    output = response.text.strip()
    output = clean_gemini_response(output)

    # Log the translation result
    logger.info(
        f"Translation result:\n"
        f"--- Input HTML ---\n{html_fragment}\n"
        f"--- Output HTML ---\n{output}"
    )

    if not output:
        error_message = f"Empty or non-HTML response from Gemini for chapter, chunk."
        logger.error(error_message)
        raise ValueError(error_message)
    time.sleep(llm_delay)
    return output
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
        "- Do NOT include explanations, comments, markdown code blocks, or any extra content.\n\n",
        f"{custom_prompt}"
        "Now translate:\n\n### html\n" + html_fragment
    )
    response = client.models.generate_content(
        model=llm_model,
        contents=prompt,
    )
    output = response.text.strip()
    output = clean_gemini_response(output)

    # Log the translation result
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

def annotate_image(img_path):
    print("Annotating image")
    imgfile = client.files.upload(file=img_path)
    prompt = '''You will be shown an image containing Japanese text.
Your task is to extract all readable Japanese text from the image and translate it into Korean.
- Output only the Korean translation as a single paragraph in plain text.
- Do not include any Japanese text, explanations, or comments.
- Do not use markdown or any formatting.
- Keep the output clean, natural, and in fluent Korean.
Again: Only output the full Korean translation as one paragraph. Nothing else.'''
    output = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            imgfile,
            "\n\n",
            prompt,
        ],
    )
    return output.text.strip()



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
                soup = BeautifulSoup(result, "html.parser")
                visible_text = soup.get_text()
                japanese_chars = re.findall(r'[\u3040-\u30FF\u31F0-\u31FF\u4E00-\u9FFF]', visible_text)
                if japanese_chars is None:
                    japanese_chars = []
                count = len(japanese_chars)
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
                await asyncio.sleep(5 * attempt)
            finally:
                await asyncio.sleep(llm_delay)
    logger.error(
        f"[{chapter_index}-{chunk_index}] Final failure after {MAX_RETRIES} attempts. Returning original fragment."
    )
    return html_fragment


async def translate_chapter_async(html, chapter_index, executor, semaphore):
    """
    Translates an entire chapter asynchronously by splitting it into chunks,
    translating each chunk concurrently, and recombining the results.
    """
    soup = BeautifulSoup(html, 'html.parser')
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
