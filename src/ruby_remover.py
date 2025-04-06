import zipfile
import os
import shutil
from bs4 import BeautifulSoup

def remove_ruby_tags_from_html(html_content):
    soup = BeautifulSoup(html_content, "lxml-xml")
    
    for ruby in soup.find_all("ruby"):
        # <rt>와 <rp>는 통째로 제거
        for rt in ruby.find_all("rt"):
            rt.decompose()
        for rp in ruby.find_all("rp"):
            rp.decompose()
        # <rb>는 태그만 제거하고 텍스트는 남김
        for rb in ruby.find_all("rb"):
            rb.unwrap()
        # <ruby> 자체도 제거하고 내부 텍스트만 유지
        ruby.unwrap()
    
    return str(soup)

def remove_ruby_from_epub(epub_path, progress_callback = None, log_callback = None):
    # 1. 원본 백업
    base, ext = os.path.splitext(epub_path)
    backup_path = f"{base}_with_ruby{ext}"
    shutil.copy(epub_path, backup_path)
    if progress_callback:
        progress_callback(25)
    if log_callback:
        log_callback(f"루비 제거 전 EPUB이 ({backup_path})에 저장되었습니다.")

    # 2. 작업 디렉토리 설정
    temp_dir = "temp_epub"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    if progress_callback:
        progress_callback(30)
    if log_callback:
        log_callback("임시 작업용 경로 생성 완료")

    try:
        # 3. EPUB 압축 해제
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        if progress_callback:
            progress_callback(45)
        if log_callback:
            log_callback("EPUB 파일 읽기 완료")

        # 4. HTML 계열 파일 수정
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith((".html", ".xhtml", ".htm")):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    new_content = remove_ruby_tags_from_html(content)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
        if progress_callback:
            progress_callback(85)
        if log_callback:
            log_callback("EPUB내 루비문자 제거 완료")

        # 5. EPUB 다시 압축 (원래 파일에 덮어쓰기)
        with zipfile.ZipFile(epub_path, 'w') as zip_out:
            for foldername, subfolders, filenames in os.walk(temp_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    archive_name = os.path.relpath(file_path, temp_dir)
                    if archive_name == "mimetype":
                        zip_out.writestr("mimetype", open(file_path, "rb").read(), compress_type=zipfile.ZIP_STORED)
                    else:
                        zip_out.write(file_path, archive_name, compress_type=zipfile.ZIP_DEFLATED)

        if progress_callback:
            progress_callback(95)
        if log_callback:
            log_callback("루비문자 제거된 EPUB 재생성 완료")

    finally:
        # 6. 작업 디렉토리 제거 (정상/에러 상관없이)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            if progress_callback:
                progress_callback(100)
            if log_callback:
                log_callback("임시 작업공간 삭제 완료")
