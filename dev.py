import pandas as pd
import os
import uuid

# --- [설정 부분] ---
excel_file = 'updated_oliveyoung_data.xlsx'
image_dir = 'oliveyoung_full_images'
target_column = 'image_url'
output_excel = 'updated_oliveyoung_data_02.xlsx'

print("🚀 작업을 시작합니다...")

# 1. 경로 및 파일 확인
if not os.path.exists(excel_file):
    print(f"❌ 에러: 엑셀 파일({excel_file})을 찾을 수 없습니다.")
    exit()

if not os.path.isdir(image_dir):
    print(f"❌ 에러: 이미지 폴더({image_dir})를 찾을 수 없습니다.")
    exit()

# 2. 데이터 불러오기
try:
    df = pd.read_excel(excel_file)
    print(f"✅ 엑셀 로드 완료: 총 {len(df)}개의 행이 있습니다.")
except Exception as e:
    print(f"❌ 엑셀 읽기 실패: {e}")
    exit()

# 3. 실제 이름 변경 작업
success_count = 0
not_found_count = 0

print("🔍 이름 변경 프로세스 가동...")

for index, row in df.iterrows():
    original_filename = str(row[target_column]).strip() # 공백 제거
    
    # 엑셀 값이 비어있는 경우 패스
    if original_filename == 'nan' or not original_filename:
        continue
        
    old_path = os.path.join(image_dir, original_filename)
    
    # 실제 폴더에 파일이 있는지 확인
    if os.path.exists(old_path):
        ext = os.path.splitext(original_filename)[1] # 확장자 추출
        new_filename = f"{uuid.uuid4()}{ext}"
        new_path = os.path.join(image_dir, new_filename)
        
        try:
            os.rename(old_path, new_path)
            df.at[index, target_column] = new_filename # 엑셀 데이터 변경
            success_count += 1
        except Exception as e:
            print(f"⚠️ {original_filename} 변경 중 오류: {e}")
    else:
        # 파일이 폴더에 없는 경우
        not_found_count += 1

# 4. 결과 저장
df.to_excel(output_excel, index=False)

print("-" * 30)
print(f"✨ 작업 완료!")
print(f"📦 성공적으로 바뀐 파일: {success_count}개")
print(f"❓ 폴더에서 못 찾은 파일: {not_found_count}개")
print(f"📝 결과 저장 파일: {output_excel}")
print("-" * 30)