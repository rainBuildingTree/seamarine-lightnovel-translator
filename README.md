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
[https://github.com/rainBuildingTree/seamarine-lightnovel-translator/releases/tag/epub%EB%B2%88%EC%97%AD%EA%B8%B0](https://github.com/rainBuildingTree/seamarine-lightnovel-translator/releases/tag/101hotfix)

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

### 3. EPUB 파일 선택

- `Select EPUB File` 버튼을 눌러 번역할 `.epub` 파일을 선택하세요.

### 4. 동시 요청 수 설정 (Concurrent)

- 기본값은 `1`로, 이 경우에도 작동 합니다. 
- 빠른 번역을 원할 경우 `10` 혹은 그 이상 으로 올릴 수 있지만, **요금이 나올 수 있습니다.**
- 동시 요청수가 너무 커지면 구글 서버에서 Limit을 걸 수 있습니다.

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
- `Max Concurrent Requests`은 


### Q. 번역 결과가 자연스럽지 않아요.

- 일부 일본어 표현이나 고유명사는 후처리가 필요할 수 있습니다.

---

