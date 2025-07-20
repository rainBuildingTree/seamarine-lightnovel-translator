from google import genai
from google.genai import types
from logger_config import setup_logger
import logging
import os
from backend.model import AiModelConfig
import ast
import time
import re
import json

class TranslateCore:
    def __init__(self, language_from=""):
        self._logger = logging.getLogger("seamarine_translate")
        try:
            self.language_from = language_from
            self._key: str = ""
            self._client = None if self._key == "" else genai.Client()
            self._model_data: AiModelConfig
            self._logger.info(str(self) + ".__init__")
        except Exception as e:
            self._logger.error(str(self) + str(e))
        
    def register_key(self, key: str) -> bool: 
        try:
            os.environ['GOOGLE_API_KEY'] = key
            self._client = genai.Client()
            self._logger.info(str(self) + f".register_key({key})")
            return True
        except Exception as e:
            self._logger.error(str(self) + f".register_key({key})\n-> " + str(e))
            return False
        
    def update_model_data(self, data: AiModelConfig) -> bool:
        try:
            self._model_data = data
            self._logger.info(str(self) + f".update_model_data({str(data.to_dict())})")
            return True
        except Exception as e:
            self._logger.error(str(self) + f".update_model_data({str(data.to_dict())})\n-> " + str(e))
            return False

    def get_model_list(self) -> list[str]:
        try:
            raw_model_list = self._client.models.list()
            model_list = [
                (model.name).removeprefix("models/")
                for model in raw_model_list
                for action in model.supported_actions
                if action == 'generateContent'
            ]
            self._logger.info(str(self) + ".get_model_list -> " + str(model_list))
            return model_list
        except Exception as e:
            self._logger.error(str(self) + str(e))
            return []
        
    def generate_content(self, contents: str | bytes, divide_n_conquer = True, resp_in_json = False):
        try:
            gen_config = types.GenerateContentConfig(
                max_output_tokens= 65536 if '2.5' in self._model_data.name else 8192,
                system_instruction= self._model_data.system_prompt,
                temperature= self._model_data.temperature,
                top_p= self._model_data.top_p,
                frequency_penalty= self._model_data.frequency_penalty,
                safety_settings = [
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.OFF
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.OFF
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.OFF
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.OFF
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                        threshold=types.HarmBlockThreshold.OFF
                    )
                ],
            )
            if self._model_data.use_thinking_budget:
                gen_config.thinking_config = types.ThinkingConfig(thinking_budget=self._model_data.thinking_budget)
            
            resp = self._client.models.generate_content(
                model=self._model_data.name,
                contents=contents,
                config=gen_config
            )

            if resp.prompt_feedback and resp.prompt_feedback.block_reason:
                self._logger.warning(f"Response blocked with the reason {resp.prompt_feedback.block_reason}")
                if divide_n_conquer:
                    return self._divide_and_conquer_json(contents) if resp_in_json else self._divide_and_conquer(contents)
                else:
                    return ""
            return self._clean_gemini_response(resp.text)
        except Exception as e:
            self._logger.error(f"{str(self)}.generate_content -> {str(e)}")
            if "429" in str(e) or "Resource exhausted" in str(e):
                dynamic_delay = self._get_retry_delay_from_exception(str(e))
                self._logger.info(str(self) + f".process_chunk\n-> 429/Resource Exhausted Detected. Retry after {dynamic_delay} seconds")
                time.sleep(dynamic_delay)
                return self.generate_content(contents)
            else:
                return ""
        
    def count_token(self, text):
        return self._client.models.count_tokens(text)
    
    def _get_retry_delay_from_exception(self, error_str: str, extra_seconds: int = 5) -> int:
        start_idx = error_str.find('{')
        if start_idx == -1:
            return 0 
        
        dict_str = error_str[start_idx:]
        retry_seconds = 0

        try:
            err_data = ast.literal_eval(dict_str)
            details = err_data.get("error", {}).get("details", [])
            for detail in details:
                if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                    retry_str = detail.get("retryDelay", "")
                    match = re.match(r"(\d+)s", retry_str)
                    if match:
                        retry_seconds = int(match.group(1))
                        break
        except Exception as e:
            self._logger.warning(f"Failed to parse retryDelay: {e}")
            return 10

        return retry_seconds + extra_seconds if retry_seconds > 0 else 0

    def _divide_and_conquer_json(self, contents: str) -> str:
        json_dict = json.loads(contents)
        keys = list(json_dict.keys())
        mid = len(keys) // 2
        first_half = {k: json_dict[k] for k in keys[:mid]}
        second_half = {k: json_dict[k] for k in keys[mid:]}

        subcontents_1 = json.dumps(first_half)
        subcontents_2 = json.dumps(second_half)

        subdict_1 = {}
        subdict_2 = {}
        for i in range(3):
            try:
                subresp_1 = self.generate_content(subcontents_1, resp_in_json=True)
                subdict_1.update(json.loads(subresp_1))
            except Exception as e:
                self._logger.exception(f"Failed to divide and conquer in json, retry...({i})")
                continue
        for i in range(3):
            try:
                subresp_2 = self.generate_content(subcontents_2, resp_in_json=True)
                subdict_2.update(json.loads(subresp_2))
            except Exception as e:
                self._logger.exception(f"Failed to divide and conquer in json, retry...({i})")
                continue


        merged_dict = {}
        merged_dict.update(subdict_1)
        merged_dict.update(subdict_2)

        return str(merged_dict)
    
    def _divide_and_conquer(self, contents: str) -> str:
        subcontents_1 = contents[0:len(contents)//2]
        subcontents_2 = contents[len(contents)//2:len(contents)]

        


    def _clean_gemini_response(self, response_text: str) -> str:
        """
        Cleans the Gemini API response by stripping markdown formatting.
        """
        text = response_text.strip()
        if text.startswith("```html"):
            text = text[7:].strip()
        elif text.startswith("```json"):
            text = text[7:].strip()
        elif text.startswith("```"):
            text = text[3:].strip()
        if text.startswith("### html"):
            text = text[8:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        self.escape_special_chars_in_json_string_safe(text)
            
        return text
    
    def escape_special_chars_in_json_string_safe(self, s: str) -> str:
        """
        JSON과 유사한 문자열에서 큰따옴표로 묶인 값 내부의 특수문자들을
        '안전하게' 이스케이프 처리합니다. 이미 이스케이프된 문자는 건드리지 않습니다.

        :param s: JSON 형태를 띤 입력 문자열
        :return: 특수문자가 올바르게 이스케이프 처리된 문자열
        """
        
        # 이스케이프 처리가 필요한 문자와 그 결과 매핑
        # 백슬래시를 맨 앞에 두는 것이 가독성과 논리에 좋습니다.
        escape_map = {
            '\\': '\\\\',
            '"': '\\"',
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
            '\b': '\\b',
            '\f': '\\f',
        }

        def escape_match(match: re.Match) -> str:
            """re.sub에 사용될 바깥쪽 콜백 함수"""
            # "value" -> value
            content = match.group(1)

            def inner_replacer(m: re.Match) -> str:
                """문자열 내용물에 대해 실행될 안쪽 치환 함수"""
                # 그룹 1: 유효한 이스케이프 시퀀스 (예: \", \\, \n)
                if m.group(1):
                    # 이미 올바르므로 그대로 반환
                    return m.group(1)
                # 그룹 2: 이스케이프가 필요한 문자 (예: ", \, 개행문자)
                else:
                    char_to_escape = m.group(2)
                    return escape_map.get(char_to_escape, char_to_escape)

            # 안쪽 정규표현식:
            # 그룹 1: (\\.) -> 백슬래시(\)로 시작하는 모든 두 글자 문자(유효/무효 이스케이프 모두 포함)
            # 그룹 2: (["\\\n\r\t\b\f]) -> 이스케이프가 필요한 문자들의 집합
            # | (OR) 로 두 그룹을 연결하여 둘 중 하나를 찾습니다.
            # 이 패턴은 `\`가 앞에 붙은 문자를 우선적으로 그룹 1로 매치하므로,
            # `"`는 `\"`의 일부가 아닐 때만 그룹 2로 매치됩니다.
            inner_pattern = r'(\\.)|(["\\\n\r\t\b\f])'
            
            # 문자열 내용물(content)에 대해서만 추가적인 치환 작업 수행
            escaped_content = re.sub(inner_pattern, inner_replacer, content)

            # 다시 큰따옴표로 감싸서 반환
            return f'"{escaped_content}"'

        # 바깥쪽 정규표현식: 큰따옴표로 감싸인 모든 부분을 찾음
        outer_pattern = r'"((?:[^"\\]|\\.)*)"'
        
        # re.sub를 사용하여 패턴에 맞는 모든 부분을 escape_match 함수의 결과로 치환
        return re.sub(outer_pattern, escape_match, s)