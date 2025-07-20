# 위 코드를 opf_parser.py로 저장했다고 가정
from utils.epubkit.refactored.opf_parser import Package

def test_package(filepath: str):
    print(f"\n--- Testing file: {filepath} ---")
    try:
        pkg = Package.from_file(filepath)
        
        # 정보 읽기
        print(f"Version: {pkg.version}")
        title = pkg.metadata.titles[0]
        print(f"Title: {title.content}")
        
        # 정보 수정
        title.content += " (수정됨)"
        
        # 새 요소 추가
        pkg.metadata.add_creator("새로운 기여자", role="edt")
        new_item = pkg.manifest.add_item("c1.xhtml", "application/xhtml+xml")
        pkg.spine.add_itemref(new_item.id)
        
        # 결과 출력 (원본 네임스페이스 스타일이 유지되는지 확인)
        print("\n--- Modified XML Output ---")
        print(pkg.to_string())

    except (FileNotFoundError, ValueError, ET.ParseError) as e:
        print(f"An error occurred: {e}")

# 테스트 실행 (파일을 생성한 후 실행해야 함)
test_package("default_ns.opf")
#test_package("prefixed_ns.opf")