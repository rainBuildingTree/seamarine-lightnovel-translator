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
CASE_SENSITIVE_ATTRS = {
    # SVG 요소 관련 속성
    "viewbox": "viewBox",
    "preserveaspectratio": "preserveAspectRatio",
    "gradienttransform": "gradientTransform",
    "gradientunits": "gradientUnits",
    "patterntransform": "patternTransform",
    "markerstart": "markerStart",
    "markermid": "markerMid",
    "markerend": "markerEnd",
    "clippathunits": "clipPathUnits",
    "refx": "refX",
    "refy": "refY",
    "spreadmethod": "spreadMethod",
    "textlength": "textLength",
    "lengthadjust": "lengthAdjust",
    
    # SVG 애니메이션 관련 속성
    "calcmode": "calcMode",
    "keytimes": "keyTimes",
    "keysplines": "keySplines",
    "repeatcount": "repeatCount",
    "repeatdur": "repeatDur",
    "attributename": "attributeName",
    
    # MathML 관련 속성 (사용되는 경우)
    "definitionurl": "definitionURL",
    
    # EPUB/OPF 메타데이터나 EPUB 전용 네임스페이스 속성
    # (EPUB 3에서는 epub:type 등은 일반적으로 소문자지만, 혹시 몰라 추가)
    "epub:type": "epub:type",
    "unique-identifier": "unique-identifier",
}
def restore_case_sensitive_attribs(html_content):
    for lower_attr, correct_attr in CASE_SENSITIVE_ATTRS.items():
        # 정규식으로 소문자 형태의 속성명을 찾아 올바른 케이스로 변경
        pattern = re.compile(fr'(?P<before><\w+[^>]*\s){lower_attr}(?P<after>\s*=)', re.IGNORECASE)
        html_content = pattern.sub(lambda m: m.group("before") + correct_attr + m.group("after"), html_content)
    return html_content

def revert_foreign_paragraphs(original_html, translated_html):
    """
    최종 번역 결과(HTML)에서 각 <p> 태그를 검사하여,
    만약 해당 문단 내에 일본어, 키릴, 태국, 아랍, 히브리, 데바나가리, 그리스 등의 문자가 포함되어 있으면
    원문 HTML의 대응 <p> 태그 내용으로 대체하고,
    최종적으로 불필요한 <html>나 <body> 태그 없이 순수한 HTML fragment를 반환합니다.
    """
    pattern = re.compile(
        r'[\u3040-\u30FF\u31F0-\u31FF\u4E00-\u9FFF]|'  # 일본어/한자
        r'[\u0400-\u04FF\u0500-\u052F]|'                # 키릴 문자
        r'[\u0E00-\u0E7F]|'                            # 태국 문자
        r'[\u0600-\u06FF\u0750-\u077F]|'                # 아랍 문자
        r'[\u0590-\u05FF]|'                            # 히브리 문자
        r'[\u0900-\u097F]|'                            # 데바나가리 문자
        r'[\u0370-\u03FF]'                             # 그리스 문자
    )

    # "html.parser"를 사용하여 fragment로 파싱합니다.
    original_soup = BeautifulSoup(original_html, "html.parser")
    translated_soup = BeautifulSoup(translated_html, "html.parser")

    original_container = original_soup.body if original_soup.body is not None else original_soup
    translated_container = translated_soup.body if translated_soup.body is not None else translated_soup

    original_paragraphs = original_container.find_all('p')
    translated_paragraphs = translated_container.find_all('p')

    if len(translated_paragraphs) != len(original_paragraphs):
        logger.warning("원문과 번역문 간 <p> 태그 개수가 일치하지 않습니다. 문단 복원을 건너뜁니다.")
        return translated_container.decode_contents()

    for idx, trans_p in enumerate(translated_paragraphs):
        if pattern.search(trans_p.get_text()):
            trans_p.replace_with(copy.deepcopy(original_paragraphs[idx]))

    result_html = translated_container.decode_contents()

    # 후처리: case-sensitive 속성 복원을 진행합니다.
    result_html = restore_case_sensitive_attribs(result_html)

    return result_html

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
    HTML에서 <p> 및 <h1>~<h6> 태그 안의 텍스트에만 detect_repeats() 적용
    BeautifulSoup 없이 처리하여 원본 태그 구조 보존
    """
    def process_tag(match):
        tag = match.group(1)
        attrs = match.group(2) or ""  # None일 경우 빈 문자열 사용
        inner = match.group(3)
        processed_inner = detect_repeats(inner, min_repeat=min_repeat)
        return f"<{tag}{attrs}>{processed_inner}</{tag}>"

    # <p> 및 <h1>~<h6> 태그만 처리
    pattern = re.compile(r'<(p|h[1-6])(\s[^>]*)?>(.*?)</\1>', re.DOTALL)
    return pattern.sub(process_tag, html)


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
def translate_text_simple(text, language):
    prompt = (
        "당신은 라이트노벨 전문 번역가입니다.\n\n"

        "📝 번역 지침:\n"
        "- **이미 한국어로 번역된 문장은 수정하지 마십시오.**\n"
        "- **한국어가 아닌 텍스트만 자연스럽고 문학적인 한국어로 번역하십시오.**\n"
        "- **출력에는 오직 한국어만 포함되어야 하며, 외국어는 절대 포함하지 마십시오.**\n"
        "- **외국어 원문을 병기하거나 '(원문)→(번역문)'와 같은 형식으로 절대 표시하지 마십시오.**\n"
        "- 설명, 주석, 마크다운 등의 출력은 절대 하지 마십시오.\n"
        "- 'CONTENTS'는 '목차'로 번역하십시오."

        "다음 글을 검토하여 외국어만 한국어로 번역하십시오. 이미 번역된 한국어는 변경하지 마십시오:\n\n" + text
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=llm_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                max_output_tokens=8192 if max_chunk_size < 8192 else max_chunk_size,
            ),
            )
            output = response.text.strip()
            output = clean_gemini_response(output)
            output = restore_repeat_tags_translated(output)

            logger.info(
                f"Translation result:\n"
                f"--- Input HTML ---\n{text}\n"
                f"--- Output HTML ---\n{output}"
            )

            if not output:
                raise ValueError("Empty or non-HTML response from Gemini for translation.")
            time.sleep(llm_delay)
            return output
        except Exception as e:
            logger.error(f"translate_text_simple - Error on attempt {attempt}: {e}")
            if "429" in str(e) or "Resource exhausted" in str(e):
                attempt -= 1
                delay = parse_retry_delay_from_error(e)
                logger.info(f"429 error detected in translate_text_simple, retrying after {delay} seconds.")
                time.sleep(delay)
            else:
                time.sleep(5 * attempt)
    logger.error("translate_text_simple - Final failure after MAX_RETRIES attempts.")
    raise Exception("Translation failed in translate_text_simple.")

def remove_russian_from_text(text):
    prompt = (
        '당신은 문장에 섞여있는 러시아어 단어를 한국어로 번역해서 적는 번역가입니다.'
        '문장속에 있는 다른 요소는 절대 바꾸지 말고, 러시아어로 적혀있는 단어만 한국어로 바꿔 문장을 완성 하십시오.'
        '다음 문장의 러시아어 단어를 바꿔 완성된 한국어 문장으로 작성하십시오, 번역된 문장만 출력하십시오.\n\n' + text
    )
    try:
        response = client.models.generate_content(
            model=llm_model,
            contents=prompt,    
            config=types.GenerateContentConfig(
            max_output_tokens=8192 if max_chunk_size < 8192 else max_chunk_size,
            top_k=40,
            top_p=0.85,
            temperature=1.8,
            )
        )
        return response.text.strip()
    except Exception as e:
        return text

def translate_chunk_for_enhance(html_fragment, language):
    set_language(language)
    processed_html = detect_repeats(html_fragment)
    prompt = (
        '당신은 라이트노벨 전문 번역가입니다. 아래에 주어진 텍스트는 한국어 초벌 번역본입니다. 하지만 일부 외국어가 그대로 남아 있거나, 번역이 어색한 부분이 있습니다.'
        '📝 번역 지침:'
        '- 모든 문장을 자연스럽고 문학적인 한국어로 다시 다듬어 주십시오.'
        '- 고유명사(인명, 지명, 작품명 등)는 원어 발음을 기준으로 음역해 주십시오.'
        '- 원문의 의미나 논리를 임의로 해석하거나 창작하지 마십시오.'
        "- 출력에는 오직 한국어만 포함되어야 하며, 어떠한 외국어 단어나 문장도 포함되면 안 됩니다."
        "- 「 」, 『 』 문장부호는 원문 그대로 유지하고, 닫히지 않았더라도 임의로 닫지 마십시오."
        "- 원문 병기, 주석, 설명 등은 절대로 출력하지 마십시오.\n\n"
        "📌 다음 문장을 철저히 지침에 따라 자연스럽고 문학적으로 다시 번역해 주십시오 번역된 문장만 출력하시오:\n\n"+ processed_html
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=llm_model,
                contents=prompt,    
                config=types.GenerateContentConfig(
                max_output_tokens=8192 if max_chunk_size < 8192 else max_chunk_size,
                top_k=40,
                top_p=0.85,
                temperature=1.8,
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
            if len(output) > 3 * len(processed_html):
                raise ValueError("Repetition detected")
            cyrill_chars = re.findall(r'[\u0400-\u04FF\u0500-\u052F]', output)
            if len(cyrill_chars) > 0:
                output = remove_russian_from_text(output)
            
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
    Gemini API를 사용하여 일본어를 한국어로 번역합니다.
    번역에 실패할 경우 예외를 발생시킵니다.
    """
    set_language(language)
    preprocessed_html = wrap_repeats_in_paragraphs_and_headers(html_fragment)
    prompt = (
        "**중요:** 반드시 **순수하게 번역된 HTML만** 반환하십시오. 설명, 주석, 코드 블록 등 부가 내용은 포함하지 마십시오.\n\n"
        f"당신은 {language} 라이트노벨 전문 번역가이며, {language}에서 한국어로 번역합니다. 번역은 정확하고 자연스러우며 감정 표현이 풍부해야 하고, 출간에 적합해야 합니다.\n\n"
        "🎯 번역 지침:\n"
        "- 원문의 어조, 문학적 뉘앙스, 대화체 스타일 유지\n"
        "- 몰입감 있고 자연스러운 한국어 표현 사용\n\n"
        "- 비일상적인 한자어는 문맥에 맞는 현대 한국어 표현으로 의역\n"
        "- 이미 번역된 고유명사는 그대로 사용\n"
        "- 思わず는 무심코로 번역하십시오"
        "⚠️ HTML 및 형식 관련:\n"
        "- HTML 태그 및 구조(`&lt;p&gt;`, `&lt;img&gt;`, `&lt;repeat&gt;`, `class` 등)는 변경, 제거, 재배열하지 않음\n"
        "- 파일 경로, 이미지 alt 텍스트, href, 클래스 이름, 메타데이터 등 보이지 않는 정보는 번역하지 않음\n"
        f"- 최종 결과에 {language} 문자가 남으면 안 됨\n"
        "- 번역할 외국어 텍스트가 없으면 원문 HTML 그대로 반환\n\n"
        + custom_prompt +
        "\n이제 다음 HTML을 검토하여 번역하세요:\n\n" + preprocessed_html
    )

    response = client.models.generate_content(
        model=llm_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            top_p=0.8,
            temperature=1.8,
            max_output_tokens=8192 if max_chunk_size < 8192 else max_chunk_size,
        ),
    )
    # response.text가 None인 경우를 확인하고 로깅
    if response.text is None:
        logger.error(
            f"[CH{chapter_index}][CHUNK{chunk_index}] API 응답 텍스트가 None입니다. "
            f"전체 응답 객체: {response}"
        )
        raise ValueError("API response text is None, triggering retry.") # 재시도를 유발하기 위해 예외 발생
    output = response.text.strip() 
    output = clean_gemini_response(output)
    output = restore_repeat_tags_translated(output)

    logger.info(
        f"[CH{chapter_index}][CHUNK{chunk_index}] 번역 결과:\n"
        f"--- 원문 HTML ---\n{html_fragment}\n"
        f"--- 전처리 HTML ---\n{preprocessed_html}\n"
        f"--- 번역 결과 HTML ---\n{output}"
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
        error_message = f"chapter {chapter_index}, chunk {chunk_index}에 대해 Gemini로부터 빈번역 또는 HTML 형식이 아님."
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
        "- 보이는 텍스트가 없으면 빈 텍스트('')를 반환하십시오."

        "오직 번역된 한국어 텍스트만 출력하십시오."
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=llm_model,
                contents=[
                    prompt,
                    PIL.Image.open(io.BytesIO(img_bytes))
                ],
                config=types.GenerateContentConfig(
                top_k= 40,
                top_p= 0.85,
                temperature= 0.8,
                max_output_tokens=8192 if max_chunk_size < 8192 else max_chunk_size,
                frequency_penalty=0.5,
                ),
            )
            if response.text:
                output_text = response.text.strip()
            elif response.text == "''" or response.text == None:
                output_text = ""
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
    HTML 청크를 비동기적으로 번역하면서 재시도 로직을 포함합니다.
    마지막 최종 결과에 대해서만 각 <p> 태그 내 외국/일본어 문자가 발견되면 원문으로 복원합니다.
    """
    final_result = None
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
                # 번역 결과에서 HTML 태그 제외 보이는 텍스트 추출
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
                            f"번역 결과에 {count}개의 일본어(또는 외국) 문자가 포함되어 attempt {attempt}에서 재시도를 유발합니다."
                        )
                    else:
                        logger.warning(
                            f"[{chapter_index}-{chunk_index}] 최종 시도 결과에 {count}개의 일본어/외국 문자 포함. 해당 결과 사용."
                        )
                final_result = result
                break  # 성공적으로 결과를 받아왔으므로 루프 종료
            except Exception as e:
                logger.error(f"[{chapter_index}-{chunk_index}] attempt {attempt} 에서 에러 발생: {e}")
                if "429" in str(e) or "Resource exhausted" in str(e):
                    # 429 에러인 경우 재시도 전 딜레이
                    attempt -= 1
                    delay = parse_retry_delay_from_error(e)
                    logger.info(f"[{chapter_index}-{chunk_index}] 429 에러 감지, {delay}초 후 재시도.")
                    await asyncio.sleep(delay)
                else:
                    await asyncio.sleep(5 * attempt)
            finally:
                await asyncio.sleep(llm_delay)
    
    if final_result is None:
        logger.error(f"[{chapter_index}-{chunk_index}] 최대 재시도({MAX_RETRIES}회) 후 최종 실패. 원문 청크 반환.")
        final_result = html_fragment
    
    # 성공/실패 관계없이 최종 결과에 대해 각 <p> 태그를 검사하여
    # 외국/일본어 문자가 있으면 원문으로 복원합니다.
    final_result = revert_foreign_paragraphs(html_fragment, final_result)
    return final_result

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
