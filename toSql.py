import pandas as pd

# 1. 설정 및 도메인 상수
FILE_PATH = 'updated_oliveyoung_data_02.xlsx'
OUTPUT_FILE = 'insert_data_safe.sql'
# 요청하신 R2 공개 URL (마지막에 /가 포함되어 있으므로 경로 결합 시 주의)
R2_PUBLIC_URL = "https://pub-e67da594a346412f91ba6f351d463038.r2.dev/product/"

# 2. 데이터 로드
try:
    df = pd.read_excel(FILE_PATH)
except FileNotFoundError:
    print(f"오류: {FILE_PATH} 파일을 찾을 수 없습니다.")
    exit()

# SQL 특수문자(작은따옴표) 처리 함수
def escape_sql(text):
    if pd.isna(text):
        return ""
    return str(text).replace("'", "''")

# 이미지 URL 처리 함수
def transform_image_url(url):
    if pd.isna(url) or url == "":
        return ""
    
    # URL에서 파일명만 추출 (경로가 포함되어 들어올 경우 대비)
    file_name = str(url).split('/')[-1]
    
    # R2 공개 주소와 파일명 결합
    return f"{R2_PUBLIC_URL}{file_name}"

# 3. 브랜드 INSERT 문 생성
unique_brands = df['brand_id'].unique()
brand_sql = "INSERT IGNORE INTO `brands` (`name`) VALUES \n"
brand_sql += ",\n".join([f"('{escape_sql(name)}')" for name in unique_brands]) + ";"

# 4. 상품 데이터 행 생성
all_rows = []
for _, row in df.iterrows():
    # 이미지 URL 변환 적용
    final_image_url = transform_image_url(row['image_url'])
    
    # JSON 및 텍스트 데이터 클리닝
    skin_types = row['skin_types'] if pd.notna(row['skin_types']) else "[]"
    conditions = row['related_conditions'] if pd.notna(row['related_conditions']) else "[]"
    benefits = row['benefits'] if pd.notna(row['benefits']) else "[]"
    
    # SQL 행 생성
    query_row = f"""
SELECT (SELECT `brand_id` FROM `brands` WHERE `name` = '{escape_sql(row['brand_id'])}' LIMIT 1), 
'{escape_sql(row['name'])}', {row['price']}, {row['default_usage_days']}, '{row['oliveyoung_goods_no']}', 
'{escape_sql(row['category_medium'])}', '{escape_sql(row['category_small'])}', '{escape_sql(row['volume'])}', 
'{escape_sql(row['description'])[:1000]}', '{escape_sql(final_image_url)}', '{escape_sql(row['product_url'])}', 
'{escape_sql(row['ingredients'])}', '{skin_types}', '{conditions}', '{benefits}'"""
    all_rows.append(query_row.strip())

# 5. 파일 저장
batch_size = 20
product_header = "INSERT INTO `products` (`brand_id`, `name`, `price`, `default_usage_days`, `oliveyoung_goods_no`, `category_medium`, `category_small`, `volume`, `description`, `image_url`, `product_url`, `ingredients`, `skin_types`, `related_conditions`, `benefits`)\n"

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("START TRANSACTION;\n\n")
    f.write(brand_sql + "\n\n")
    
    for i in range(0, len(all_rows), batch_size):
        batch = all_rows[i:i+batch_size]
        f.write(product_header)
        f.write("\nUNION ALL\n".join(batch))
        f.write(";\n\n")
    
    f.write("COMMIT;")

print(f"총 {len(df)}개의 데이터를 처리하여 '{OUTPUT_FILE}'로 저장했습니다.")
print(f"이미지 도메인 적용 완료: {R2_PUBLIC_URL}")