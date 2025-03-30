from bs4 import BeautifulSoup

def combine_dual_language(original_html, translated_html):
    """
    원본 HTML의 기본 구조(헤드 등)는 그대로 두고, body 내의 <p> 태그만
    원문과 번역문을 결합하여 dual language로 처리합니다.
    
    만약 body 태그나 <p> 태그가 제대로 매칭되지 않으면 fallback으로 
    번역본 전체를 별도의 컨테이너로 추가합니다.
    """
    soup_original = BeautifulSoup(original_html, 'html.parser')
    soup_translated = BeautifulSoup(translated_html, 'html.parser')
    
    # body 태그 가져오기
    original_body = soup_original.body
    translated_body = soup_translated.body
    
    if original_body is None or translated_body is None:
        # body 태그가 없으면 fallback: 전체 번역본을 반환
        return translated_html
    
    original_p_tags = original_body.find_all('p')
    translated_p_tags = translated_body.find_all('p')
    
    # <p> 태그가 하나도 없거나 개수가 다르면 fallback 처리
    if not original_p_tags or not translated_p_tags or len(original_p_tags) != len(translated_p_tags):
        # 원본 body 맨 아래에 번역본 전체를 별도 컨테이너로 추가
        #container = soup_original.new_tag("div", **{"class": "translated-content"})
        # 번역본 전체의 body 내용을 컨테이너에 복사
        #for element in translated_body.contents:
        #    container.append(element)
        #original_body.append(container)
        #return str(soup_original)
        return str(soup_translated)
    # <p> 태그가 있는 경우, 각 <p> 태그를 dual language로 변경
    for orig_tag, trans_tag in zip(original_p_tags, translated_p_tags):
        # 새 <p> 태그 생성, 원본 태그의 속성 그대로 복사
        new_tag = soup_original.new_tag("p")
        new_tag.attrs = orig_tag.attrs.copy()
        # 원본 내용 추가 (내부 HTML 유지)
        new_tag.append(BeautifulSoup(orig_tag.decode_contents(), "html.parser"))
        # 구분자 추가 (예: <br>)
        new_tag.append(soup_original.new_tag("br"))
        # 번역 내용 추가 (내부 HTML 유지)
        new_tag.append(BeautifulSoup(trans_tag.decode_contents(), "html.parser"))
        # 원본 <p> 태그를 새 태그로 교체
        orig_tag.replace_with(new_tag)
    
    return str(soup_original)
