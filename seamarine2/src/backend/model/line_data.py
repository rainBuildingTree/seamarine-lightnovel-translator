import csv

class LineData:
    def __init__(self, file, original, translated):
        self.file = file
        self.original = original
        self.translated = translated

    def __repr__(self):
        return f"LineData(file='{self.file}', original='{self.original}', translated='{self.translated}')"

def save_line_data_to_csv(data_list: list[LineData], filename: str):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(['file', 'original', 'translated'])

        for item in data_list:
            writer.writerow([item.file, item.original, item.translated])
    print(f"'{filename}'에 데이터가 성공적으로 저장되었습니다.")

def load_line_data_from_csv(filename: str) -> list[LineData]:
    loaded_data = []
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)

            header = next(reader, None)
            if header is None:
                return []

            for row in reader:
                if len(row) == 3:
                    file, original, translated = row
                    loaded_data.append(LineData(file, original, translated))
    except Exception:
        return None
    return loaded_data