# 라이브러리
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 기관코드 파일 불러오기
df = pd.read_csv('./data/기관코드.csv')

# '제공기관별 검색' 버튼 클릭 함수
def click_org_search_button():
    try:
        org_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, 'orgBtn'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", org_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", org_btn)
        time.sleep(1)
    except Exception as e:
        print(f"제공기관별 검색 버튼 클릭 실패: {e}")
        driver.quit()
        exit()
        
# 파일 데이터 수집 함수
def scrape_file_data(org_name):
    data_list = []
    page = 1

    while True:
        # 페이지 로드 대기
        time.sleep(2)

        # 데이터 수집
        result_lists = driver.find_elements(By.CSS_SELECTOR, ".result-list")

        if not result_lists:
            print(f"페이지 {page}에서 result-list 데이터 없음.")
            break

        for result_list in result_lists:
            items = result_list.find_elements(By.CSS_SELECTOR, "ul > li")
            for item in items:
                try:
                    data_name = item.find_element(By.CSS_SELECTOR, ".title").text.strip()
                except Exception:
                    data_name = "데이터명 없음"
                try:
                    data_desc = item.find_element(By.CSS_SELECTOR, ".ellipsis.publicDataDesc").text.strip()
                except Exception:
                    data_desc = "데이터설명 없음"

                data_list.append({
                    "데이터명": data_name,
                    "데이터설명": data_desc,
                    "제공기관": org_name,
                    "목록타입": "파일데이터"
                })

        # 다음 페이지로 이동
        try:
            next_page = driver.find_element(
                By.XPATH, f"//a[@onclick='updatePage({page + 1}); return false;']"
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", next_page)
            page += 1
        except Exception:
            break

    # 데이터프레임 반환
    return pd.DataFrame(data_list)

# 오픈API 데이터 수집 함수
def scrape_api_data(org_name):
    data_list = []
    page = 1

    while True:
        # 페이지 로드 대기
        time.sleep(2)

        # 데이터 수집
        result_lists = driver.find_elements(By.CSS_SELECTOR, ".result-list")

        if not result_lists:
            print(f"페이지 {page}에서 result-list 데이터 없음.")
            break

        for result_list in result_lists:
            items = result_list.find_elements(By.CSS_SELECTOR, "ul > li")
            for item in items:
                try:
                    data_name = item.find_element(By.CSS_SELECTOR, ".title").text.strip()
                except Exception:
                    data_name = "데이터명 없음"
                try:
                    data_desc = item.find_element(By.CSS_SELECTOR, ".ellipsis.publicDataDesc").text.strip()
                except Exception:
                    data_desc = "데이터설명 없음"

                data_list.append({
                    "데이터명": data_name,
                    "데이터설명": data_desc,
                    "제공기관": org_name,
                    "목록타입": "오픈API"
                })

        # 다음 페이지로 이동
        try:
            next_page_button = driver.find_element(
                By.XPATH, f"//a[@onclick='eventFnObj.fn_pageClick({page + 1}); return false;']"
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", next_page_button)
            time.sleep(2)
            page += 1
        except Exception:
            break

    # 데이터프레임 반환
    return pd.DataFrame(data_list)

# ------------------------------------------------------------------------------------------------------------------------

# 웹 드라이버 설정
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=service, options=options)

# 대상 웹 페이지로 이동
driver.get('https://www.data.go.kr/tcs/dss/selectDataSetList.do')

# 검색 및 클릭 로직
for index, row in df.iterrows():
    org_name = row['공공기관명']
    org_code = str(row['기관코드'])
    print(f"\n[{index+1}/{len(df)}] '{org_name}' 검색 중...")

    # '제공기관별 검색' 버튼 클릭
    click_org_search_button()

    # 기관명 입력
    try:
        org_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, 'orgNm'))
        )
        org_input.clear()
        org_input.send_keys(org_name)
        time.sleep(0.5)
    except Exception as e:
        print(f"기관명 입력 실패: {e}")
        continue

    # 검색 버튼 클릭
    try:
        search_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@onclick='orgPopObj.fn_search()']"))
        )
        driver.execute_script("arguments[0].click();", search_btn)
    except Exception as e:
        print(f"검색 버튼 클릭 실패: {e}")
        continue

    # 검색 결과 로딩 대기
    time.sleep(2)

    # 기관코드 기반 앵커 클릭
    anchor_id = f"{org_code}_anchor"
    try:
        anchor = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, anchor_id))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", anchor)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", anchor)
    except Exception as e:
        print(f"기관코드 '{org_code}' 앵커 클릭 실패: {e}")
        continue

    # 각 기관 검색 후 2초 대기
    time.sleep(2)

    # 파일데이터 목록 클릭
    try:
        file_data_tab = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.dtype-tab[data-type='FILE']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", file_data_tab)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", file_data_tab)
    except Exception as e:
        print(f"파일데이터 탭 클릭 실패: {e}")
        driver.quit()
        exit()
       
    # 파일데이터 크롤링 실행
    file_df = scrape_file_data(org_name)
    
    # 오픈API 목록 클릭
    try:
        api_data_tab = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.dtype-tab[data-type='API']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", api_data_tab)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", api_data_tab)
    except Exception as e:
        print(f"오픈API 탭 클릭 실패: {e}")
        driver.quit()
        exit()

    # 오픈API 크롤링 실행
    api_df = scrape_api_data(org_name)

    # 데이터 병합
    total_df = pd.concat([file_df, api_df], ignore_index=True)
    total_df.reset_index(drop=True, inplace=True)

    total_df.to_excel(f'./data/{org_name}_공공데이터목록.xlsx', index=False)

# 모든 작업 완료 후 브라우저 종료
driver.quit()
print("\n크롤링 작업 완료 및 브라우저 종료")
