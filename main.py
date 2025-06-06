import sys
import os

# 'src' 디렉터리를 파이썬 경로에 추가합니다.
# 이렇게 하면 'src' 디렉터리 내의 모듈을 임포트할 수 있습니다.
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

from seamarine_epub_translator import main as translator_main

if __name__ == '__main__':
    translator_main()