import pandas as pd
import google.generativeai as genai
import time
import os

# GENI_API_KEY = "여기에_발급받은_API_키를_넣으세요"
GENI_API_KEY = ""
INPUT_FILE = "올리브영_맨즈케어_전체데이터.xlsx"
OUTPUT_FILE = "올리브영_맨즈케어_분석데이터.xlsx"

genai.configure(api_key=GENI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

import json

def get_analysis_batch(items):
    """AI에게 성분 분석 요청 (배치 처리)"""
    
    prompt = f"""
    너는 화장품 성분 분석 전문가야. 아래 제공된 화장품들의 전성분을 분석해서 정보를 제공해줘.
    결과는 반드시 **JSON 배열** 형식을 지켜야 해.
    
    [입력 데이터]
    {json.dumps(items, ensure_ascii=False, indent=2)}

    [필수 출력 형식]
    [
      {{
        "id": 입력된_id,
        "피부타입": "건성, 지성, 민감성 중 1개",
        "관련질환": "여드름, 아토피, 건선, 지루성피부염 중 해당되는 것 (없으면 '일반')",
        "주요효능": "보습, 진정, 미백, 탄력 중 핵심 2가지"
      }},
      ...
    ]
    
    다른 말은 일절 하지 말고 오직 JSON 데이터만 출력해.
    """
    try:
        response = model.generate_content(prompt)

        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"      [오류] API 호출/파싱 실패: {e}")
        return None

def run_automation():
    if not os.path.exists(INPUT_FILE):
        print(f"파일이 없습니다: {INPUT_FILE}")
        return

    # 데이터 로드
    df = pd.read_excel(INPUT_FILE)
    print(f"총 {len(df)}건의 데이터 분석을 시작합니다. (배치 크기: 10)")
    results_map = {i: {"피부타입": "분석실패", "관련질환": "분석실패", "주요효능": "분석실패"} for i in range(len(df))}

    BATCH_SIZE = 5
    
    # 배치 단위로 처리
    for i in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[i : i + BATCH_SIZE]
        batch_items = []
        
        print(f"[{i+1}~{min(i+BATCH_SIZE, len(df))}/{len(df)}] 배치 분석 중...")

        for idx, row in batch.iterrows():
            batch_items.append({
                "id": idx,
                "name": row['상품명'],
                "ingredients": str(row['전성분'])[:500] 
            })
        
        ai_results = None
        max_retries = 3
        
        for attempt in range(max_retries):
            ai_results = get_analysis_batch(batch_items)
            
            if ai_results is not None:
                break
            else:
                if attempt < max_retries - 1:
                    wait_time = 65 
                    print(f"      [대기] 사용량 제한 도달. {wait_time}초 대기 후 재시도... ({attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print("      [실패] 재시도 횟수 초과. 다음 배치로 넘어갑니다.")

        if ai_results:
            for item in ai_results:
                original_idx = item.get("id")
                if original_idx in results_map:
                    results_map[original_idx] = {
                        "피부타입": item.get("피부타입", "정보없음"),
                        "관련질환": item.get("관련질환", "정보없음"),
                        "주요효능": item.get("주요효능", "정보없음")
                    }
        else:
            print("      -> 배치 분석 실패 (데이터 없음)")

        time.sleep(15)

    # 결과 매핑
    skin_types = [results_map[i]["피부타입"] for i in range(len(df))]
    diseases = [results_map[i]["관련질환"] for i in range(len(df))]
    effects = [results_map[i]["주요효능"] for i in range(len(df))]

    if '가격' in df.columns:
        price_idx = df.columns.get_loc('가격') + 1
        df.insert(price_idx, '피부타입', skin_types)
        df.insert(price_idx + 1, '관련질환', diseases)
        df.insert(price_idx + 2, '주요효능', effects)
    else:
        df['피부타입'] = skin_types
        df['관련질환'] = diseases
        df['주요효능'] = effects

    # 최종 저장
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\n작업 완료! 파일이 저장되었습니다: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_automation()