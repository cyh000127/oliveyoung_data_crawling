import os
import time
import requests
import re
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_oliveyoung_full_active_crawler(target_per_sub=15):
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    
    # 크롬 버전 문제 발생 시 아래 주석을 해제하고 본인의 크롬 버전 앞자리를 입력하세요.
    driver = uc.Chrome(options=options, version_main=144)
    # driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    image_dir = "oliveyoung_full_images"
    os.makedirs(image_dir, exist_ok=True)

    category_map = [
        {
            "mid_name": "스킨케어",
            "subs": [
                {"name": "올인원", "id": "1000001000700070006"},
                {"name": "스킨/로션/세럼", "id": "1000001000700070013"},
                {"name": "클렌징/선크림/팩", "id": "1000001000700070014"},
                {"name": "스킨케어 세트", "id": "1000001000700070012"}
            ]
        },
        {
            "mid_name": "메이크업",
            "subs": [
                {"name": "톤 로션/BB", "id": "1000001000700080015"},
                {"name": "쿠션/파운데이션", "id": "1000001000700080011"},
                {"name": "쉐딩/파우더/기름종이", "id": "1000001000700080012"},
                {"name": "컬러립밤/보습립밤", "id": "1000001000700080013"},
                {"name": "아이브로우", "id": "1000001000700080014"}
            ]
        },
        {
            "mid_name": "헤어케어",
            "subs": [
                {"name": "스프레이/왁스/젤", "id": "1000001000700090013"},
                {"name": "오일/토닉/컬크림", "id": "1000001000700090014"},
                {"name": "염색/다운펌", "id": "1000001000700090012"}
            ]
        }
    ]

    all_data = []

    try:
        driver.get("https://www.oliveyoung.co.kr")
        input("클라우드플레어 인증을 완료한 후 엔터를 누르세요...")
        
        global_cnt = 0 

        for mid in category_map:
            print(f"\n[중분류] {mid['mid_name']} 시작")
            
            for sub in mid['subs']:
                sub_url = f"https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo={sub['id']}"
                print(f"  > [소분류] {sub['name']}")
                
                driver.get(sub_url)
                time.sleep(3)

                try:                 
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.prd_info")))
                    items = driver.find_elements(By.CSS_SELECTOR, "div.prd_info a.prd_thumb")
                    links = [item.get_attribute("href") for item in items[:target_per_sub]]

                    if not links:
                        continue
                        
                except Exception as e:
                    print(f"  > 리스트 로드 실패: {e}")
                    continue

                for url in links:
                    driver.get(url)
                    time.sleep(2)
                    
                    try:
                        global_cnt += 1
                        wait_short = WebDriverWait(driver, 5)

                        # 1. 상품명 (name)
                        raw_name_elem = wait_short.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='GoodsDetailInfo_title']")))
                        product_name = re.sub(r'\[.*?\]', '', raw_name_elem.text).strip()
                        safe_product_name = re.sub(r'[\/:*?"<>|]', '', product_name)

                        # 2. 브랜드
                        try:
                            brand_name = driver.find_element(By.CSS_SELECTOR, "[class*='TopUtils_btn-brand']").text
                        except:
                            brand_name = "미분류"

                        # 3. 올리브영 상품 번호 추출
                        match = re.search(r'goodsNo=([^&]+)', url)
                        goods_no = match.group(1) if match else "N/A"

                        # 4. [수정됨] 가격 (price) - 이미지 속성 기반 추출
                        try:
                            # data-qa-name 속성을 사용하여 정확히 할인된 판매가 요소만 타겟팅
                            price_elem = driver.find_element(By.CSS_SELECTOR, "span[data-qa-name='text-product-discount-price']")
                            # 숫자 외의 문자(콤마, 원 등) 제거 후 정수 변환
                            price_val = int(re.sub(r'[^0-9]', '', price_elem.text))
                        except:
                            price_val = 0

                        # 5. 이미지 수집 (토글 및 스와이퍼 로직 유지)
                        img_filenames = []
                        headers = {"User-Agent": driver.execute_script("return navigator.userAgent;")}
                        
                        try:
                            prev_btn = driver.find_element(By.CSS_SELECTOR, ".swiper-button-prev")
                            driver.execute_script("arguments[0].click();", prev_btn)
                            time.sleep(0.5)
                        except:
                            pass

                        try:
                            filename = f"{global_cnt}_{safe_product_name}.jpg"
                            img_path = os.path.join(image_dir, filename)
                            
                            img_elem = wait_short.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".swiper-slide-active img")))
                            img_src = img_elem.get_attribute("src")
                            
                            response = requests.get(img_src, headers=headers, timeout=5)
                            if response.status_code == 200:
                                with open(img_path, 'wb') as f:
                                    f.write(response.content)
                                img_filenames.append(filename)
                        except Exception as e:
                            print(f"    [이미지오류] #{global_cnt}: {e}")

                        # 6. 상세 정보 (아코디언 클릭)
                        try:
                            accordions = driver.find_elements(By.CSS_SELECTOR, "button[class*='Accordion_accordion-btn']")
                            for btn in accordions:
                                if "상품정보 제공고시" in btn.text:
                                    driver.execute_script("arguments[0].click();", btn)
                                    time.sleep(0.8)
                                    break
                        except:
                            pass

                        def get_table_data(title):
                            try:
                                return driver.find_element(By.XPATH, f"//th[contains(text(), '{title}')]/following-sibling::td").text.replace("■", "").strip()
                            except: return ""

                        volume = get_table_data("내용물의 용량")
                        description = get_table_data("제품 주요 사양")
                        raw_ing = get_table_data("화장품법에 따라 기재해야 하는 모든 성분")
                        ingredients = re.sub(r'\[.*?\]', '', raw_ing).strip()

                        all_data.append({
                            "brand_id": brand_name,
                            "name": product_name,
                            "price": price_val,
                            "default_usage_days": 90,
                            "oliveyoung_goods_no": goods_no,
                            "category_medium": mid['mid_name'],
                            "category_small": sub['name'],
                            "volume": volume,
                            "description": description[:1000],
                            "image_url": ", ".join(img_filenames) if img_filenames else "N/A",
                            "product_url": f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={goods_no}",
                            "ingredients": ingredients
                        })

                        print(f"    [성공] #{global_cnt} {product_name} | 가격: {price_val}원")

                    except Exception as e:
                        print(f"    [오류] 상세 페이지 처리 실패: {e}")
                        continue

        if all_data:
            df = pd.DataFrame(all_data)
            with open("올리브영_수집데이터.md", "w", encoding="utf-8") as f:
                f.write(df.to_markdown(index=False))
            print(f"\n작업 완료! {len(all_data)}개 데이터 저장됨")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_oliveyoung_full_active_crawler(target_per_sub=15)