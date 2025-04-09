import json
import csv
import time
from ebooklib import epub
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import ast

# 추가: 최대 재시도 횟수
MAX_RETRIES = 3

# 추가: 에러 메시지에서 "retry after X" 형태로 시간(초)을 파싱하기 위한 함수
def parse_retry_delay_from_error(error) -> int:
    """
    주어진 에러 메시지에서 재시도 지연시간(초)을 추출합니다.
    에러 메시지에 "retry after <숫자>" 형태가 있다면 해당 숫자를 반환하고,
    그렇지 않으면 기본값 10초를 반환합니다.
    """
    try:
        match = re.search(r"retry after (\d+)", str(error), re.IGNORECASE)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return 10
'''
def get_retry_delay_from_exception(e: Exception, extra_seconds: int = 2) -> int:
    """
    429 RESOURCE_EXHAUSTED 에러 메시지(429 QuotaExceeded)에서 retryDelay(예: "50s")를 추출해
    초 단위 int로 반환합니다. 만약 해당 정보가 없으면 0을 반환합니다.
    
    :param e: 예외 객체
    :param extra_seconds: retryDelay에 추가로 더 기다리고 싶은 초 (기본값 1초)
    :return: 대기해야 할 총 초 (retryDelay + extra_seconds). 해당 정보가 없으면 0.
    """
    error_str = str(e)
    start_idx = error_str.find('{')
    retry_seconds = 0

    # JSON 문자열 부분 추출
    if start_idx != -1:
        json_str = error_str[start_idx:]

        try:
            err_data = json.loads(json_str)
            # details 찾아서 type.googleapis.com/google.rpc.RetryInfo 부분 확인
            details = err_data["error"].get("details", [])
            for detail in details:
                if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                    retry_str = detail.get("retryDelay", "")  # 예: "50s"
                    match = re.match(r"(\d+)s", retry_str)
                    if match:
                        retry_seconds = int(match.group(1))
                        break
        except json.JSONDecodeError:
            print(f"[ERROR] JSON decode error: {error_str}")
            return 10

    return retry_seconds + extra_seconds if retry_seconds > 0 else 0
'''
def get_retry_delay_from_exception(error_str: str, extra_seconds: int = 2) -> int:
    """
    error_str 안에 포함된 Python-style dict 문자열에서 'retryDelay' 값을 추출해 초(int)로 반환합니다.
    :param error_str: 에러 문자열
    :param extra_seconds: 추가 대기 시간 (기본값 1초)
    :return: retryDelay + extra_seconds (없으면 0)
    """
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


class ProperNounExtractor:
    def __init__(self, epub_path: str, client, llm_model: str, language: str = 'Japanese'):
        self.epub_path = epub_path
        self.client = client
        self.llm_model = llm_model
        self.language = language
        self.prompt = f'''You are a text processor that extracts and translates proper nouns from a {self.language} light novel text into Korean.

🎯 Task:
- Identify all proper nouns in the input text.
- Translate each proper noun into Korean.
- Return the result strictly as a JSON object.
- Use the original {self.language} proper noun as the key, and the Korean translation as the value.

⚠️ Output Requirements:
- Respond **only** with the JSON object.
- Do **not** include any commentary, explanation, or formatting outside the JSON.
- Follow this format exactly:

{{
  "田中": "다나카",
  "東京": "도쿄"
}}

📄 The input text is below:
'''
        self.proper_nouns = {}

    def extract_text(self) -> str:
        book = epub.read_epub(self.epub_path)
        full_text = ""
        for item in book.get_items():
            if isinstance(item, epub.EpubHtml):
                try:
                    content = item.get_content().decode('utf-8')
                    soup = BeautifulSoup(content, 'lxml-xml')
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

    def process_chunk(self, chunk, delay):
        """
        chunk 문자열을 Gemini API에 보내 proper noun을 추출하고
        429 (Resource exhausted) 에러 발생 시 동적으로 재시도 지연시간을 적용하여
        최대 MAX_RETRIES만큼 재시도하는 로직을 포함합니다.
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.llm_model,
                    contents=self.prompt + chunk
                )
                cleaned = self.clean_response(response.text.strip())
                new_dict = json.loads(cleaned)

                # 정상 응답을 받은 경우, 요청 후 지연 (기존 delay) 적용
                time.sleep(delay)
                return new_dict

            except Exception as e:
                print(f"[ERROR] Attempt {attempt} - Failed to parse chunk: {e}")

                # 429 혹은 Resource exhausted 에러라면 parse_retry_delay_from_error 사용
                if "429" in str(e) or "Resource exhausted" in str(e):
                    attempt -= 1
                    dynamic_delay = get_retry_delay_from_exception(str(e))
                    print(f"  => 429/Resource exhausted 에러 감지. {dynamic_delay}초 후 재시도합니다.")
                    time.sleep(dynamic_delay)
                else:
                    # 그 외 에러는 기본적으로 점진적 증가
                    time.sleep(5 * attempt)

        print("[ERROR] Final failure after MAX_RETRIES attempts. Returning empty dict.")
        return {}

    def run_extraction(self, delay, max_concurrent_requests=1, progress_callback=None):
        full_text = self.extract_text()
        chunks = self.split_text(full_text)
        total_chunks = len(chunks)
        completed = 0

        with ThreadPoolExecutor(max_workers=max_concurrent_requests) as executor:
            # 각 청크에 대해 process_chunk 함수를 실행하도록 작업 제출
            futures = {
                executor.submit(self.process_chunk, chunk, delay): chunk
                for chunk in chunks
            }
            for future in as_completed(futures):
                result = future.result()
                # 결과를 self.proper_nouns에 업데이트
                self.proper_nouns.update(result)
                completed += 1
                if progress_callback:
                    progress_callback(int(completed / total_chunks * 100))

    def save_to_csv(self, filename="proper_nouns.csv"):
        with open(filename, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["원어", "한국어"])
            for origin, kr in self.proper_nouns.items():
                writer.writerow([origin, kr])
