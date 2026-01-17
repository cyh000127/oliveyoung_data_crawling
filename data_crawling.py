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
    
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    image_dir = "oliveyoung_full_images"
    os.makedirs(image_dir, exist_ok=True)

    # 카테고리 태그
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
        # {
            # "mid_name": "바디케어",
            # "subs": [
                # {"name": "바디워시/로션", "id": "1000001000700110006"},
                # {"name": "데오/바디미스트", "id": "1000001000700110007"},
                # {"name": "남성청결제", "id": "1000001000700110010"}
            # ]
        # },
        {
            "mid_name": "헤어케어",
            "subs": [
                {"name": "스프레이/왁스/젤", "id": "1000001000700090013"},
                {"name": "오일/토닉/컬크림", "id": "1000001000700090014"},
                # {"name": "헤어기기", "id": "1000001000700090015"},
                {"name": "염색/다운펌", "id": "1000001000700090012"},
                # {"name": "샴푸/린스", "id": "1000001000700090011"}
            ]
        }
    ]

    all_data = []

    try:
        driver.get("https://www.oliveyoung.co.kr")
        input("클라우드플레어 인증을 완료한 후 엔터를 누르세요...")
        
        global_cnt = 0  # 전체 번호 카운터

        for mid in category_map:
            print(f"\n[중분류] {mid['mid_name']} 작업 시작")
            
            for sub in mid['subs']:
                sub_url = f"https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo={sub['id']}"
                print(f"  > [소분류 접속] {sub['name']}")
                
                # 리스트 페이지로 이동
                driver.get(sub_url)
                time.sleep(3) 

                # 현재 페이지가 리스트 페이지가 맞는지 검증
                if "getGoodsDetail" in driver.current_url:
                    print("  ! 경고: 리스트 페이지가 아닌 상세 페이지에 머물고 있습니다. 재접속 시도...")
                    driver.get(sub_url)
                    time.sleep(3)

                # 상품 링크 수집
                try:                 
                    # 리스트 페이지에만 있는 특정 요소가 나타날 때까지 대기 (클라우드 플레어 대기)
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.prd_info")))
                    except Exception:
                        print(f"  > [오류] 상품 리스트(div.prd_info)를 찾을 수 없습니다.")
                        if driver.find_elements(By.CSS_SELECTOR, "ul.cate_prd_list"):
                             print("  > [정보] ul.cate_prd_list는 존재합니다. 선택자를 조정해야 할 수도 있습니다.")
                        raise

                    items = driver.find_elements(By.CSS_SELECTOR, "div.prd_info a.prd_thumb")
                    # print(f"발견된 상품 수: {len(items)}")
                    
                    links = [item.get_attribute("href") for item in items[:target_per_sub]]
                    # print(f"수집 대상 링크 수: {len(links)}")

                    # 만약 수집된 링크가 없다면 다음 카테고리로 이동
                    if not links:
                        print("  > 수집할 상품이 없습니다.")
                        continue
                        
                except Exception as e:
                    print(f"  > 리스트 페이지 로드/파싱 실패: {e}")
                    continue

                # 개별 상세 페이지 루프 시작
                for url in links:
                    # 이미 상세 페이지 주소인지 확인하고 이동
                    if url == driver.current_url:
                        pass
                    else:
                        driver.get(url)
                        time.sleep(2)
                    
                    try:
                        # print(f" 상세 페이지 진입 성공. 데이터 추출 시도...")
                        
                        # 번호 증가
                        global_cnt += 1

                        # 상품명 대기
                        try:
                            wait_short = WebDriverWait(driver, 5)
                            # 부분 일치로 처리
                            raw_name_elem = wait_short.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='GoodsDetailInfo_title']")))
                            product_name = re.sub(r'\[.*?\]', '', raw_name_elem.text).strip()
                            safe_product_name = re.sub(r'[\/:*?"<>|]', '', product_name) # 파일명용
                        except Exception as e:
                            print(f"    [오류] 상품명(GoodsDetailInfo_title)을 찾을 수 없음: {e}")
                            
                            try:
                                error_time = int(time.time())
                                src_filename = f"debug_source_{error_time}.html"
                                shot_filename = f"debug_shot_{error_time}.png"
                                with open(src_filename, "w", encoding="utf-8") as f:
                                    f.write(driver.page_source)
                                driver.save_screenshot(shot_filename)
                            except: pass
                            continue

                        # 브랜드
                        try:
                            # 부분 일치로 검색
                            brand_elem = driver.find_element(By.CSS_SELECTOR, "[class*='TopUtils_btn-brand']")
                            brand = brand_elem.text
                        except:
                            brand = "브랜드 정보 없음"
                        
                        goods_no = url.split("goodsNo=")[1].split("&")[0]

                        # Swiper 이미지 수집
                        img_filenames = []
                        headers = {"User-Agent": driver.execute_script("return navigator.userAgent;")}
                        
                        try:
                            # 마지막 슬라이드로 이동 (prev 버튼 클릭)
                            prev_btn = driver.find_element(By.CSS_SELECTOR, ".swiper-button-prev")
                            driver.execute_script("arguments[0].click();", prev_btn)
                            time.sleep(0.5)
                        except:
                            # 버튼이 없거나 클릭 실패 시 그냥 현재 이미지 저장
                            pass

                        # 현재 활성화된 슬라이드 이미지 저장
                        try:
                            # {index}_{제품명}.jpg 형식
                            filename = f"{global_cnt}_{safe_product_name}.jpg"
                            img_path = os.path.join(image_dir, filename)
                            
                            img_elem = wait_short.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".swiper-slide-active img")))
                            img_src = img_elem.get_attribute("src")
                            
                            # 이미지 저장
                            try:
                                response = requests.get(img_src, headers=headers, timeout=5)
                                if response.status_code == 200:
                                    with open(img_path, 'wb') as f:
                                        f.write(response.content)
                                    img_filenames.append(filename)
                                    print(f"    [성공] #{global_cnt} 이미지 저장: {filename}")
                            except Exception as img_e:
                                print(f"    [오류] 이미지 다운로드 실패: {img_e}")

                        except Exception as e:
                            print(f"    [오류] 이미지 요소 찾기 실패: {e}")

                        #  상품정보 제공고시 추출
                        try:
                            # '상품정보 제공고시' 찾기
                            accordions = driver.find_elements(By.CSS_SELECTOR, "button[class*='Accordion_accordion-btn']")
                            
                            target_btn = None
                            for btn in accordions:
                                if "상품정보 제공고시" in btn.text:
                                    target_btn = btn
                                    break
                            
                            if target_btn:
                                driver.execute_script("arguments[0].click();", target_btn)
                                time.sleep(1.0) # 펼쳐지는 시간 대기
                            else:
                                print("    [정보] '상품정보 제공고시' 버튼을 찾지 못했습니다.")

                        except Exception as e:
                            print(f"    [오류] 아코디언 버튼 클릭 실패: {e}")

                        # 테이블 데이터 추출 함수
                        def get_table_data(title):
                            try:
                                text = driver.find_element(By.XPATH, f"//th[contains(text(), '{title}')]/following-sibling::td").text
                                return text
                            except: return "정보 없음"

                        # 데이터 정제 (■, [내용] 제거)
                        volume = get_table_data("내용물의 용량").replace("■", "").strip()
                        raw_ingredients = get_table_data("화장품법에 따라 기재해야 하는 모든 성분").replace("■", "")
                        ingredients = re.sub(r'\[.*?\]', '', raw_ingredients).strip()

                        # 가격 정보 추출
                        try:
                            # 부분 일치로 검색
                            price_elem = driver.find_element(By.CSS_SELECTOR, "[class*='GoodsDetailInfo_price']")
                            price_text = price_elem.text
                            if "원" in price_text:
                                price = price_text.split("원")[0] + "원"
                            else:
                                price = price_text
                        except:
                            price = "가격 정보 없음"

                        all_data.append({
                            "No": global_cnt,
                            "대분류": "맨즈케어",
                            "중분류": mid['mid_name'],
                            "소분류": sub['name'],
                            "브랜드": brand,
                            "상품명": product_name,
                            "용량/중량": volume,
                            "주요사양": get_table_data("제품 주요 사양").replace("■", "").strip(),
                            "전성분": ingredients,
                            "가격": price,
                            "이미지목록": ", ".join(img_filenames),
                            "URL": url
                        })

                        print(f"    [완료] #{global_cnt} {product_name}")

                    except Exception as e:
                        print(f"    [오류] 상세 페이지 처리 중 실패: {e}")
                        continue


        if all_data:
            df = pd.DataFrame(all_data)
            df.to_excel("올리브영_맨즈케어_전체데이터.xlsx", index=False)
            print(f"\n작업 완료! {len(all_data)}개의 데이터가 저장")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_oliveyoung_full_active_crawler(target_per_sub=15) # sub 개수 X 12(소분류 개수)의 결과가 나옴