import pandas as pd
import json

# 1. 데이터 로드
df = pd.read_excel('올리브영_데이터_결과.xlsx')

# SQL 특수문자(작은따옴표) 처리 함수
def escape_sql(text):
    if pd.isna(text):
        return ""
    return str(text).replace("'", "''")

# 2. 브랜드 INSERT 문 생성
unique_brands = df['brand_id'].unique()
brand_sql = "INSERT IGNORE INTO `brands` (`name`) VALUES \n"
brand_sql += ",\n".join([f"('{escape_sql(name)}')" for name in unique_brands]) + ";"

# 3. 상품 데이터 행 생성
all_rows = []
for _, row in df.iterrows():
    # JSON 및 텍스트 데이터 클리닝
    skin_types = row['skin_types'] if pd.notna(row['skin_types']) else "[]"
    conditions = row['related_conditions'] if pd.notna(row['related_conditions']) else "[]"
    benefits = row['benefits'] if pd.notna(row['benefits']) else "[]"
    
    # 각 행을 SELECT 문으로 구성
    query_row = f"""
SELECT (SELECT `brand_id` FROM `brands` WHERE `name` = '{escape_sql(row['brand_id'])}' LIMIT 1), 
'{escape_sql(row['name'])}', {row['price']}, {row['default_usage_days']}, '{row['oliveyoung_goods_no']}', 
'{escape_sql(row['category_medium'])}', '{escape_sql(row['category_small'])}', '{escape_sql(row['volume'])}', 
'{escape_sql(row['description'])[:1000]}', '{escape_sql(row['image_url'])}', '{escape_sql(row['product_url'])}', 
'{escape_sql(row['ingredients'])}', '{skin_types}', '{conditions}', '{benefits}'"""
    all_rows.append(query_row.strip())

# 4. 파일 저장 (끊어서 기록하기)
batch_size = 20  # 한 번에 넣을 데이터 개수 설정
product_header = "INSERT INTO `products` (`brand_id`, `name`, `price`, `default_usage_days`, `oliveyoung_goods_no`, `category_medium`, `category_small`, `volume`, `description`, `image_url`, `product_url`, `ingredients`, `skin_types`, `related_conditions`, `benefits`)\n"

with open('insert_data_safe.sql', 'w', encoding='utf-8') as f:
    # 안전을 위해 트랜잭션 시작
    f.write("START TRANSACTION;\n\n")
    
    # 브랜드 먼저 삽입
    f.write(brand_sql + "\n\n")
    
    # 상품 데이터를 batch_size만큼 끊어서 INSERT 문 생성
    for i in range(0, len(all_rows), batch_size):
        batch = all_rows[i:i+batch_size]
        f.write(product_header)
        f.write("\nUNION ALL\n".join(batch))
        f.write(";\n\n")
    
    # 트랜잭션 완료
    f.write("COMMIT;")

print(f"총 {len(df)}개의 데이터를 {batch_size}개씩 끊어서 'insert_data_safe.sql'로 저장했습니다.")