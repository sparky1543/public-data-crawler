# 라이브러리
import time
import pandas as pd
import os
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import re
import html

# 기관코드 파일 불러오기
df = pd.read_csv('./data/기관코드.csv')

# 최대 재시도 횟수 설정
MAX_RETRIES = 3

# 안전하게 요소 클릭하는 함수
def click_element_safely(driver, element, retries=MAX_RETRIES):
    if element is None:
        return False
    
    for attempt in range(retries):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", element)
            time.sleep(1)
            return True
        except Exception as e:
            if attempt < retries - 1:
                print(f"요소 클릭 실패, 재시도 중... ({attempt+1}/{retries})")
                time.sleep(1)
            else:
                print(f"요소 클릭 최종 실패: {e}")
                return False

# 페이지 상태 확인 함수
def is_page_loaded(driver, wait_time=10):
    try:
        return WebDriverWait(driver, wait_time).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except TimeoutException:
        return False

# 안전하게 뒤로 가기 함수
def safe_back(driver, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            driver.back()
            time.sleep(2)
            if is_page_loaded(driver):
                return True
        except Exception as e:
            if attempt < retries - 1:
                print(f"뒤로 가기 실패, 재시도 중... ({attempt+1}/{retries})")
                time.sleep(1)
            else:
                print(f"뒤로 가기 최종 실패: {e}")
                return False
    return False

# 웹페이지 새로고침 함수
def refresh_page(driver, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            driver.refresh()
            time.sleep(2)
            if is_page_loaded(driver):
                return True
        except Exception as e:
            if attempt < retries - 1:
                print(f"페이지 새로고침 실패, 재시도 중... ({attempt+1}/{retries})")
                time.sleep(1)
            else:
                print(f"페이지 새로고침 최종 실패: {e}")
                return False
    return False

# '제공기관별 검색' 버튼 클릭 함수
def click_org_search_button(driver, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            # '.no-data' 요소 찾기를 제거하고 직접 요소 찾기로 변경
            org_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, 'orgBtn'))
            )
            
            if org_btn and click_element_safely(driver, org_btn):
                return True
            else:
                raise Exception("버튼 찾기 또는 클릭 실패")
        except Exception as e:
            if attempt < retries - 1:
                print(f"제공기관별 검색 버튼 클릭 실패, 재시도 중... ({attempt+1}/{retries})")
                refresh_page(driver)
                time.sleep(1)
            else:
                print(f"제공기관별 검색 버튼 클릭 최종 실패: {e}")
                return False
    return False

# 상세 페이지에서 설명 가져오기 함수
def get_detail_description(driver, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            # 상세 설명 찾기
            description_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.cont"))
            )
            
            if description_element:
                # 방법 1: innerHTML 가져오기
                description_html = description_element.get_attribute('innerHTML')
                
                # <br> 태그를 줄바꿈으로 변환 (이 작업을 먼저 해야 <br>이 줄바꿈으로 올바르게 변환됨)
                description_text = description_html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
                
                # 모든 HTML 태그 제거 (정규식 사용)
                description_text = re.sub(r'<[^>]*>', '', description_text)
                
                # HTML 엔티티 디코딩 (예: &amp; -> &)
                description_text = html.unescape(description_text)
                
                # 여러 줄바꿈 정리 및 앞뒤 공백 제거
                description_text = re.sub(r'\n\s*\n', '\n\n', description_text)
                description_text = description_text.strip()
                
                return description_text
            else:
                raise Exception("상세 설명 요소를 찾을 수 없음")
                
        except Exception as e:
            if attempt < retries - 1:
                print(f"상세 설명 가져오기 실패, 재시도 중... ({attempt+1}/{retries})")
                time.sleep(1)
            else:
                print(f"상세 설명 가져오기 최종 실패: {e}")
                return "상세 설명 가져오기 실패"
    
    return "상세 설명 가져오기 실패"

# 현재 데이터 타입에 따라 다음 페이지 버튼 찾기 함수
def find_next_page_button(driver, page, data_type):
    try:
        if data_type == "FILE":
            return WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, 
                f"//a[@onclick='updatePage({page + 1}); return false;']"))
            )
        else:  # API
            return WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, 
                f"//a[@onclick='eventFnObj.fn_pageClick({page + 1}); return false;']"))
            )
    except (TimeoutException, NoSuchElementException):
        # 다음 페이지 없으면 조용히 None 반환
        return None

# 파일 데이터 수집 함수
def scrape_file_data(driver, org_name):
    data_list = []
    page = 1

    while True:
        # 페이지 로드 대기
        time.sleep(2)
        
        if not is_page_loaded(driver):
            print(f"페이지 {page}가 제대로 로드되지 않았습니다. 새로고침 시도...")
            if not refresh_page(driver):
                break
        
        # 데이터 수집
        try:
            result_lists = driver.find_elements(By.CSS_SELECTOR, ".result-list")
        except Exception as e:
            print(f"결과 목록 요소 찾기 실패: {e}")
            result_lists = []

        if not result_lists:
            print(f"페이지 {page}에서 result-list 데이터 없음.")
            break

        for result_list in result_lists:
            try:
                items = result_list.find_elements(By.CSS_SELECTOR, "ul > li")
            except Exception as e:
                print(f"항목 목록 찾기 실패: {e}")
                continue

            for item in items:
                try:
                    data_name_element = item.find_element(By.CSS_SELECTOR, ".title")
                    data_name = data_name_element.text.strip()
                    
                    # 데이터명 클릭하여 상세 페이지로 이동
                    if click_element_safely(driver, data_name_element):
                        # 상세 페이지 로드 대기
                        time.sleep(2)
                        
                        # 상세 설명 가져오기
                        data_desc = get_detail_description(driver)
                        
                        # 뒤로 가기
                        if not safe_back(driver):
                            print("뒤로 가기 실패, 메인 페이지로 다시 이동 시도...")
                            driver.get('https://www.data.go.kr/tcs/dss/selectDataSetList.do')
                            time.sleep(2)
                            return pd.DataFrame(data_list)
                        
                        # 페이지 로드 대기
                        time.sleep(2)
                    else:
                        data_desc = "상세 페이지 접근 실패"
                    
                except Exception as e:
                    print(f"데이터 항목 처리 중 오류: {e}")
                    data_name = "데이터명 없음"
                    data_desc = "데이터설명 없음"
                    # 오류 발생 시 뒤로 가기 시도
                    safe_back(driver)

                data_list.append({
                    "데이터명": data_name,
                    "데이터설명": data_desc,
                    "제공기관": org_name,
                    "목록타입": "파일데이터"
                })

        # 진행 상황 저장
        temp_df = pd.DataFrame(data_list)
        temp_df.to_excel(f'./data/temp_{org_name}_파일데이터_{page}.xlsx', index=False)
                
        # 다음 페이지로 이동
        next_page = find_next_page_button(driver, page, "FILE")
        if next_page and click_element_safely(driver, next_page):
            page += 1
            time.sleep(2)
        else:
            print(f"다음 페이지({page+1})로 이동할 수 없습니다.")
            break

    # 데이터프레임 반환
    return pd.DataFrame(data_list)

# 오픈API 데이터 수집 함수
def scrape_api_data(driver, org_name):
    data_list = []
    page = 1

    while True:
        # 페이지 로드 대기
        time.sleep(2)
        
        if not is_page_loaded(driver):
            print(f"페이지 {page}가 제대로 로드되지 않았습니다. 새로고침 시도...")
            if not refresh_page(driver):
                break
        
        # 데이터 수집
        try:
            result_lists = driver.find_elements(By.CSS_SELECTOR, ".result-list")
        except Exception as e:
            print(f"결과 목록 요소 찾기 실패: {e}")
            result_lists = []

        if not result_lists:
            print(f"페이지 {page}에서 result-list 데이터 없음.")
            break

        for result_list in result_lists:
            try:
                items = result_list.find_elements(By.CSS_SELECTOR, "ul > li")
            except Exception as e:
                print(f"항목 목록 찾기 실패: {e}")
                continue

            for item in items:
                try:
                    data_name_element = item.find_element(By.CSS_SELECTOR, ".title")
                    data_name = data_name_element.text.strip()
                    
                    # 데이터명 클릭하여 상세 페이지로 이동
                    if click_element_safely(driver, data_name_element):
                        # 상세 페이지 로드 대기
                        time.sleep(2)
                        
                        # 상세 설명 가져오기
                        data_desc = get_detail_description(driver)
                        
                        # 뒤로 가기
                        if not safe_back(driver):
                            print("뒤로 가기 실패, 메인 페이지로 다시 이동 시도...")
                            driver.get('https://www.data.go.kr/tcs/dss/selectDataSetList.do')
                            time.sleep(2)
                            return pd.DataFrame(data_list)
                        
                        # 페이지 로드 대기
                        time.sleep(2)
                    else:
                        data_desc = "상세 페이지 접근 실패"
                    
                except Exception as e:
                    print(f"데이터 항목 처리 중 오류: {e}")
                    data_name = "데이터명 없음"
                    data_desc = "데이터설명 없음"
                    # 오류 발생 시 뒤로 가기 시도
                    safe_back(driver)

                data_list.append({
                    "데이터명": data_name,
                    "데이터설명": data_desc,
                    "제공기관": org_name,
                    "목록타입": "오픈API"
                })
        
        # 진행 상황 저장
        temp_df = pd.DataFrame(data_list)
        temp_df.to_excel(f'./data/temp_{org_name}_오픈API_{page}.xlsx', index=False)
        
        # 다음 페이지로 이동
        next_page = find_next_page_button(driver, page, "API")
        if next_page and click_element_safely(driver, next_page):
            page += 1
            time.sleep(2)
        else:
            print(f"다음 페이지({page+1})로 이동할 수 없습니다.")
            break

    # 데이터프레임 반환
    return pd.DataFrame(data_list)

# 메인 검색 함수
def search_org_data(driver, org_name, org_code):
    # '제공기관별 검색' 버튼 클릭
    if not click_org_search_button(driver):
        print("초기 화면으로 돌아갑니다.")
        driver.get('https://www.data.go.kr/tcs/dss/selectDataSetList.do')
        time.sleep(2)
        return pd.DataFrame(), pd.DataFrame()

    # 기관명 입력
    try:
        org_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, 'orgNm'))
        )
        org_input.clear()
        org_input.send_keys(org_name)
        time.sleep(0.5)
    except Exception as e:
        print(f"기관명 입력 필드를 찾을 수 없습니다: {e}")
        return pd.DataFrame(), pd.DataFrame()

    # 검색 버튼 클릭
    try:
        search_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@onclick='orgPopObj.fn_search()']"))
        )
        if not click_element_safely(driver, search_btn):
            print("검색 버튼 클릭 실패")
            return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        print(f"검색 버튼을 찾을 수 없습니다: {e}")
        return pd.DataFrame(), pd.DataFrame()

    # 검색 결과 로딩 대기
    time.sleep(2)

    # 기관코드 기반 앵커 클릭
    anchor_id = f"{org_code}_anchor"
    try:
        anchor = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, anchor_id))
        )
        if not click_element_safely(driver, anchor):
            print(f"기관코드 '{org_code}' 앵커 클릭 실패")
            return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        print(f"기관코드 '{org_code}' 앵커를 찾을 수 없습니다: {e}")
        return pd.DataFrame(), pd.DataFrame()

    # 각 기관 검색 후 2초 대기
    time.sleep(2)

    # 파일데이터 목록 클릭
    try:
        file_data_tab = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.dtype-tab[data-type='FILE']"))
        )
        if not click_element_safely(driver, file_data_tab):
            print("파일데이터 탭 클릭 실패")
            return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        print(f"파일데이터 탭을 찾을 수 없습니다: {e}")
        return pd.DataFrame(), pd.DataFrame()
    
    # 파일데이터 크롤링 실행
    file_df = scrape_file_data(driver, org_name)
    
    # 오픈API 목록 클릭
    try:
        api_data_tab = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.dtype-tab[data-type='API']"))
        )
        if not click_element_safely(driver, api_data_tab):
            print("오픈API 탭 클릭 실패")
            return file_df, pd.DataFrame()
    except Exception as e:
        print(f"오픈API 탭을 찾을 수 없습니다: {e}")
        return file_df, pd.DataFrame()
    
    # 오픈API 크롤링 실행
    api_df = scrape_api_data(driver, org_name)
    
    return file_df, api_df

# 데이터 디렉토리 확인 및 생성
if not os.path.exists('./data'):
    os.makedirs('./data')

# 웹 드라이버 설정
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
# 안정성을 위한 추가 옵션
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 중간 저장 및 오류 기록을 위한 설정
log_file = open('./data/scraping_log.txt', 'a', encoding='utf-8')

try:
    driver = webdriver.Chrome(service=service, options=options)
    
    # 처리 결과 저장용 리스트
    processed_orgs = []
    
    # 대상 웹 페이지로 이동
    driver.get('https://www.data.go.kr/tcs/dss/selectDataSetList.do')
    time.sleep(3)
    
    # 이미 처리된 기관 목록 확인 (중간에 중단된 경우 재개를 위함)
    processed_file = './data/processed_orgs.txt'
    if os.path.exists(processed_file):
        with open(processed_file, 'r', encoding='utf-8') as f:
            processed_orgs = [line.strip() for line in f.readlines()]
    
    # 검색 및 클릭 로직
    for index, row in df.iterrows():
        org_name = row['공공기관명']
        org_code = str(row['기관코드'])
        
        # 이미 처리된 기관이면 건너뛰기
        if org_name in processed_orgs:
            print(f"\n[{index+1}/{len(df)}] '{org_name}'은(는) 이미 처리되었습니다. 건너뜁니다.")
            continue
        
        print(f"\n[{index+1}/{len(df)}] '{org_name}' 검색 중...")
        log_file.write(f"\n[{index+1}/{len(df)}] '{org_name}' 검색 시작 - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        try:
            # 메인 검색 함수 호출
            file_df, api_df = search_org_data(driver, org_name, org_code)
            
            # 데이터가 있는 경우만 처리
            if not file_df.empty or not api_df.empty:
                # 데이터 병합
                total_df = pd.concat([file_df, api_df], ignore_index=True)
                total_df.reset_index(drop=True, inplace=True)
                
                # 결과 저장
                output_file = f'./data/{org_name}_공공데이터목록.xlsx'
                total_df.to_excel(output_file, index=False)
                print(f"'{org_name}' 데이터 저장 완료: {output_file}")
                
                # 처리된 기관 목록에 추가
                processed_orgs.append(org_name)
                with open(processed_file, 'a', encoding='utf-8') as f:
                    f.write(f"{org_name}\n")
            else:
                print(f"'{org_name}'의 데이터가 없습니다.")
                
            # 홈페이지로 돌아가기
            driver.get('https://www.data.go.kr/tcs/dss/selectDataSetList.do')
            time.sleep(3)
        
        except Exception as e:
            error_msg = f"'{org_name}' 처리 중 오류 발생: {e}\n{traceback.format_exc()}"
            print(error_msg)
            log_file.write(error_msg + "\n")
            
            # 오류 발생 시 홈페이지로 돌아가서 계속 진행
            try:
                driver.get('https://www.data.go.kr/tcs/dss/selectDataSetList.do')
                time.sleep(3)
            except:
                # 드라이버 재시작 시도
                try:
                    driver.quit()
                    time.sleep(2)
                    driver = webdriver.Chrome(service=service, options=options)
                    driver.get('https://www.data.go.kr/tcs/dss/selectDataSetList.do')
                    time.sleep(3)
                except Exception as restart_error:
                    print(f"드라이버 재시작 실패: {restart_error}")
                    break

except Exception as e:
    error_msg = f"전체 실행 중 오류 발생: {e}\n{traceback.format_exc()}"
    print(error_msg)
    log_file.write(error_msg + "\n")

finally:
    # 모든 작업 완료 후 브라우저 종료
    try:
        driver.quit()
    except:
        pass
    
    log_file.write("\n크롤링 작업 완료 및 브라우저 종료 - " + time.strftime('%Y-%m-%d %H:%M:%S') + "\n")
    log_file.close()
    
    print("\n크롤링 작업 완료 및 브라우저 종료")
