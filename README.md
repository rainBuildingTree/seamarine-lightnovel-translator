# 📘 SeaMarine Light Novel Translator

일본어 라이트노벨 `.epub` 파일을 클릭 몇 번으로 자연스럽게 **한국어로 번역**해주는 도구입니다.  
Google Gemini API를 사용하여 빠르고 정확한 번역을 제공합니다.

---

## ✅ 기능 요약

- 일본어 `.epub` 파일 → 한국어 번역본 `.epub` 자동 생성
- Google Gemini 2.0 Flash API 사용
- GUI 기반으로 초보자도 쉽게 사용 가능
- HTML 구조 보존, 이미지/링크 손상 없음

---
## Zip파일 다운로드
[https://github.com/rainBuildingTree/seamarine-lightnovel-translator/releases/tag/epub%EB%B2%88%EC%97%AD%EA%B8%B0](https://github.com/rainBuildingTree/seamarine-lightnovel-translator/releases/tag/1.1.0%EC%97%85%EB%8D%B0%EC%9D%B4%ED%8A%B8)

## 🧰 준비물

| 준비물                      | 설명                                                                 |
|----------------------------|----------------------------------------------------------------------|
| `SeaMarine_LightNovel_Translator.zip` | 프로그램이 담긴 압축 파일 (실행 파일 + 라이브러리 포함)                 |
| Google Gemini API 키       | 번역을 위해 반드시 필요합니다. [API 키 발급 바로가기](https://makersuite.google.com/app/apikey) |
| 번역하고 싶은 `.epub` 파일 | 일본어로 된 라이트노벨 `.epub` 파일 (루비 문자 제거 필수? 사실 제거 안하고 테스트 안해봄)                                 |

---

## 📦 압축 해제 & 실행 안내 (중요!)

> ⚠️ 반드시 `.zip` 압축을 푼 후, 폴더 안의 `SeaMarine_LightNovel_Translator.exe` 파일을 실행해야 합니다!

1. `SeaMarine_LightNovel_Translator.zip` 압축을 풉니다.  
2. 생성된 폴더 안에 있는 `SeaMarine_LightNovel_Translator.exe` 를 실행합니다.  
3. `.exe` 파일만 따로 빼서 실행하면 오류가 발생합니다!

---

## 🚀 사용 방법 (QuickStart)

### 1. 프로그램 실행

- `SeaMarine_LightNovel_Translator.exe` 를 더블 클릭하여 실행합니다.

### 2. API Key 입력

- Google Gemini에서 발급받은 **API 키**를 입력칸에 붙여넣습니다.
- [👉 API 키 발급 가이드](https://makersuite.google.com/app/apikey)
### 3. 번역기 설정하기
#### 3.1. Gemini 모델 설정
1.5프로, 2.0플래시, 2.5프로 중 선택 (2.0 추천, 성능은 2.5가 가장 좋지만 사용 제한이 빡세서 한권도 못할 가능성 높음)

#### 3.2. 청크 사이즈 선택하기
청크 사이즈는 프로그램이 Gemini에게 번역요청을 보낼 때 한번에 최대 몇자의 글을 보낼지 결정하는 설정 값입니다.
클 수록 한번에 큰 맥락에서 번역 가능하고, 2.5프로의 경우 요청수를 줄일 수 있다는 장점이 있지만,
한번에 글을 많이 보낼 수록 내용을 까먹을 위험성이 올라갑니다.
최근 발표자료를 보면 제미니는 2000토큰 (한국어/일본어 기준 약 2500-3500자 사이) 이후부터 내용을 100% 기억하지는 못하는 것으로 확인됐습니다.
커스텀 프롬프트나 프로그램 내부적으로 들어가는 약 200토큰의 프롬프트도 Gemini가 기억하는 내용에 포함되니 이 점 고려해주세요.

#### 3.3. 커스텀 프롬프트!
이제 Gemini에게 번역 요청을 보낼 때 사용할 유저 커스텀 프롬프트를 적을 수 있습니다 야호!

#### 3.4 동시 요청 수 설정 (Concurrent)
- 기본값은 `1`로, 이 경우에도 작동 합니다. 
- 빠른 번역을 원할 경우 `10` 혹은 그 이상 으로 올릴 수 있지만 (구글 제미니 유료계정 기준 50까지도 가능했음)
- 동시 요청수가 너무 커지면 구글 서버에서 Limit을 걸 수 있습니다.

#### 3.5 현재 설정 저장
이제 열심히 api키, 커스텀 프롬프트, 다른 설정등을 프로그램을 킬때마다 적을 필요 없어졌습니다.
(모든 저장요소는 유저의 로컬 컴퓨터, 폴더안의 _internal폴더의 settings.json에 저장됩니다.)

### 4. EPUB 파일 선택

- `Select EPUB File` 버튼을 눌러 번역할 `.epub` 파일을 선택하세요.

### 5. 번역 시작

- `Start Translation` 버튼을 클릭하면 번역이 시작됩니다.
- 아래 로그창에서 실시간 진행 상황을 확인할 수 있습니다.

### 6. 번역 결과 확인

- 번역이 끝나면 원본과 같은 폴더에  
  ✅ `원본파일명_translated.epub`  
  형식으로 번역본이 생성됩니다.

---

## ❓ 자주 묻는 질문

### Q. 번역이 너무 느려요!

- 인터넷 속도와 API 응답에 따라 느릴 수 있습니다.
- `Max Concurrent Requests` 값을 높이면 빨라지지만 요금이 올라갈 수 있습니다.


### Q. 번역 결과가 자연스럽지 않아요.

- 일부 일본어 표현이나 고유명사는 후처리가 필요할 수 있습니다.

---

