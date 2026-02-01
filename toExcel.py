import pandas as pd
import re

def convert_md_to_excel(input_file, output_file):
    try:
        # 1. 파일 읽기
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 2. Markdown 표 파싱 (구분선(|:---|) 제외)
        table_data = []
        for line in lines:
            line = line.strip()
            if line.startswith('|') and not re.match(r'^\|[:\-\s|]+$', line):
                # 양 끝의 | 제거 후 분리
                row = [cell.strip() for cell in line.strip('|').split('|')]
                table_data.append(row)

        if not table_data:
            print("데이터를 찾을 수 없습니다.")
            return

        # 3. 데이터프레임 생성 (첫 줄은 헤더)
        df = pd.DataFrame(table_data[1:], columns=table_data[0])

        # 4. 숫자 데이터 변환 (가격 등)
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['default_usage_days'] = pd.to_numeric(df['default_usage_days'], errors='coerce')

        # 5. 엑셀 저장
        df.to_excel(output_file, index=False)
        print(f"변환 성공! 파일 저장 완료: {output_file}")

    except Exception as e:
        print(f"에러 발생: {e}")

# 실행
convert_md_to_excel('올리브영_수집데이터.md', '올리브영_데이터_결과.xlsx')