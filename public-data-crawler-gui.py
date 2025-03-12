import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import webbrowser

class PublicDataCrawler:
    def __init__(self, root):
        self.root = root
        self.root.title("공공데이터포털 데이터 목록 크롤러")
        self.root.geometry("620x600")
        self.root.resizable(True, True)
        
        self.driver = None
        self.crawling_in_progress = False
        self.stop_crawling = False
        self.result_data = [] 
        
        # 스타일 설정
        style = ttk.Style()
        style.configure('TButton', font=('맑은 고딕', 10))
        style.configure('TLabel', font=('맑은 고딕', 10))
        style.configure('Header.TLabel', font=('맑은 고딕', 12, 'bold'))
        
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 프레임 생성
        self.create_input_frame(main_frame)
        
        # 버튼 프레임
        self.create_control_frame(main_frame)
        
        # 로그와 결과 프레임
        bottom_frame = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.create_log_frame(bottom_frame)
        self.create_result_frame(bottom_frame)
        
        # 초기 상태 설정
        self.update_ui_state()
        
    def create_input_frame(self, parent):
        input_frame = ttk.LabelFrame(parent, text="입력 정보", padding=10)
        input_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # 입력 그리드
        input_grid = ttk.Frame(input_frame)
        input_grid.pack(fill=tk.X, expand=True)
        
        # 기관명 입력
        ttk.Label(input_grid, text="기관명 :").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.org_name_var = tk.StringVar()
        self.org_name_entry = tk.Entry(input_grid, textvariable=self.org_name_var, width=20, font=('맑은 고딕', 10))
        self.org_name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 기관코드 입력
        ttk.Label(input_grid, text="기관코드 :").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        self.org_code_var = tk.StringVar()
        self.org_code_entry = tk.Entry(input_grid, textvariable=self.org_code_var, width=20, font=('맑은 고딕', 10))
        self.org_code_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 찾아보기 버튼 추가
        code_lookup_btn = ttk.Button(input_grid, text="찾아보기", command=self.open_code_lookup)
        code_lookup_btn.grid(row=0, column=4, padx=5, pady=5, ipadx=5)
        
        # 저장 경로 선택
        ttk.Label(input_grid, text="저장 경로 :").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.save_path_var = tk.StringVar(value=os.path.join(os.getcwd(), "data"))
        save_path_entry = tk.Entry(input_grid, textvariable=self.save_path_var, width=40, font=('맑은 고딕', 10))
        save_path_entry.grid(row=1, column=1, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=3)
        
        # 수정하기 버튼
        browse_btn = ttk.Button(input_grid, text="수정하기", command=self.browse_save_path)
        browse_btn.grid(row=1, column=4, padx=5, pady=5, ipadx=5, sticky=tk.E)
        
        input_grid.columnconfigure(1, weight=1)
        input_grid.columnconfigure(2, weight=1)
    
    # 찾아보기 웹사이트 열기 함수 추가
    def open_code_lookup(self):
        webbrowser.open("https://www.code.go.kr/index.do")
        
    def create_control_frame(self, parent):
        control_frame = ttk.Frame(parent, padding=(0, 5))
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 상태 표시
        self.status_var = tk.StringVar(value="준비")
        self.status_label = tk.Label(control_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 버튼들 - 다운로드 버튼 제거
        self.stop_btn = ttk.Button(control_frame, text="크롤링 중지", command=self.stop_crawling_process)
        self.stop_btn.pack(side=tk.RIGHT, padx=5, ipadx=5)
        
        self.start_btn = ttk.Button(control_frame, text="크롤링 시작", command=self.start_crawling)
        self.start_btn.pack(side=tk.RIGHT, padx=5, ipadx=5)
        
    def create_log_frame(self, parent):
        log_frame = ttk.LabelFrame(parent, text="실행 로그", padding=5)
        parent.add(log_frame, weight=1)
        
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_columnconfigure(1, weight=0)
        
        # 로그 텍스트
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10)
        self.log_text.grid(row=0, column=0, sticky='nsew')
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.log_text.config(yscrollcommand=scrollbar.set)
        self.log_text.config(state=tk.DISABLED)
        
    def create_result_frame(self, parent):
        result_frame = ttk.LabelFrame(parent, text="크롤링 결과", padding=5)
        parent.add(result_frame, weight=2)
        
        # 결과 트리뷰
        columns = ("데이터명", "데이터설명", "제공기관", "목록타입")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=6)
        
        # 각 컬럼 설정
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=80)
        
        self.result_tree.column("데이터명", width=150)
        self.result_tree.column("데이터설명", width=200)
        
        # 스크롤바 설정
        y_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(xscrollcommand=x_scrollbar.set)
        
        # 배치
        self.result_tree.grid(row=0, column=0, sticky='nsew')
        y_scrollbar.grid(row=0, column=1, sticky='ns')
        x_scrollbar.grid(row=1, column=0, sticky='ew')
        
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
    def browse_save_path(self):
        folder_path = filedialog.askdirectory(title="저장 경로 선택")
        if folder_path:
            self.save_path_var.set(folder_path)
            
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
        
    def update_ui_state(self):
        if self.crawling_in_progress:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.org_name_entry.config(state=tk.DISABLED)
            self.org_code_entry.config(state=tk.DISABLED)
            self.status_label.config(fg="green")
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.org_name_entry.config(state=tk.NORMAL)
            self.org_code_entry.config(state=tk.NORMAL)
            self.status_label.config(fg="black")
            
    def start_crawling(self):
        org_name = self.org_name_var.get().strip()
        org_code = self.org_code_var.get().strip()
        
        if not org_name or not org_code:
            messagebox.showwarning("입력 오류", "기관명과 기관코드를 모두 입력해주세요.")
            return
            
        # 크롤링 시작
        self.crawling_in_progress = True
        self.stop_crawling = False
        self.update_ui_state()
        self.status_var.set("크롤링 중...")
        self.status_label.config(fg="green")
        
        # 결과 트리뷰 초기화
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # 로그 초기화
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 결과 데이터 초기화
        self.result_data = []
        
        # 크롤링 실행
        threading.Thread(target=self.crawling_process, args=(org_name, org_code), daemon=True).start()
            
    def stop_crawling_process(self):
        if self.crawling_in_progress:
            self.stop_crawling = True
            self.log("크롤링 중지 요청됨... 종료 중...")

            # 웹드라이버 즉시 종료
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except Exception as e:
                    self.log(f"드라이버 종료 중 오류: {e}")

            # UI 상태 업데이트 및 강제 중단
            self.crawling_in_progress = False
            self.status_var.set("준비")
            self.status_label.config(fg="black")
            self.update_ui_state()
            
            return
                
    def crawling_process(self, org_name, org_code):
        try:
            self.log(f"'{org_name}' (코드: {org_code}) 크롤링 시작")
            
            # 저장 경로 확인
            save_path = self.save_path_var.get()
            if not os.path.exists(save_path):
                os.makedirs(save_path)
                self.log(f"저장 경로 생성: {save_path}")
            
            # 웹 드라이버 설정
            self.log("웹 드라이버 초기화 중...")
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # 대상 웹 페이지로 이동
            self.log("공공데이터포털 페이지로 이동 중...")
            self.driver.get('https://www.data.go.kr/tcs/dss/selectDataSetList.do')
            
            if self.stop_crawling:
                self.log("크롤링 중지 요청 감지, 작업을 종료합니다.")
                self.finish_crawling()
                return
            
            # '제공기관별 검색' 버튼 클릭
            self.click_org_search_button()

            # 기관명 입력
            self.log(f"기관명 '{org_name}' 입력 중...")
            try:
                org_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'orgNm'))
                )
                org_input.clear()
                org_input.send_keys(org_name)
                time.sleep(0.5)
            except Exception as e:
                self.log(f"기관명 입력 실패: {e}")
                self.finish_crawling()
                return
            
            if self.stop_crawling:
                self.log("크롤링 중지 요청 감지, 작업을 종료합니다.")
                self.finish_crawling()
                return
            
            # 검색 버튼 클릭
            try:
                search_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@onclick='orgPopObj.fn_search()']"))
                )
                self.driver.execute_script("arguments[0].click();", search_btn)
            except Exception as e:
                self.log(f"검색 버튼 클릭 실패: {e}")
                self.finish_crawling()
                return

            # 검색 결과 로딩 대기
            time.sleep(2)
            
            if self.stop_crawling:
                self.log("크롤링 중지 요청 감지, 작업을 종료합니다.")
                self.finish_crawling()
                return
            
            # 기관코드 기반 앵커 클릭
            anchor_id = f"{org_code}_anchor"
            self.log(f"기관코드 '{org_code}' 선택 중...")
            try:
                anchor = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, anchor_id))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", anchor)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", anchor)
            except Exception as e:
                self.log(f"기관코드 '{org_code}' 앵커 클릭 실패: {e}")
                self.finish_crawling()
                return
            
            # 각 기관 검색 후 대기
            time.sleep(2)
            
            if self.stop_crawling:
                self.log("크롤링 중지 요청 감지, 작업을 종료합니다.")
                self.finish_crawling()
                return
            
            # 파일데이터 크롤링
            self.log("파일데이터 크롤링 중...")
            try:
                file_data_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.dtype-tab[data-type='FILE']"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", file_data_tab)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", file_data_tab)
                file_data = self.scrape_file_data(org_name)
                self.log(f"파일데이터 {len(file_data)}개 수집 완료")
            except Exception as e:
                self.log(f"파일데이터 크롤링 실패: {e}")
                file_data = []
                
            if self.stop_crawling:
                self.log("크롤링 중지 요청 감지, 작업을 종료합니다.")
                self.finish_crawling()
                return
            
            # 오픈API 크롤링
            self.log("오픈API 크롤링 중...")
            try:
                api_data_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.dtype-tab[data-type='API']"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", api_data_tab)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", api_data_tab)
                api_data = self.scrape_api_data(org_name)
                self.log(f"오픈API {len(api_data)}개 수집 완료")
            except Exception as e:
                self.log(f"오픈API 크롤링 실패: {e}")
                api_data = []
            
            if self.stop_crawling:
                self.log("크롤링 중지 요청 감지, 작업을 종료합니다.")
                self.finish_crawling()
                return
            
            # 데이터 병합
            self.result_data = file_data + api_data
            
            # 결과 표시
            self.display_results()
            
            # 크롤링 완료 후 자동 저장
            if self.result_data and not self.stop_crawling:
                self.log(f"크롤링 완료: 총 {len(self.result_data)}개 데이터 수집")
                save_path = self.save_path_var.get()
                
                # 저장 경로가 존재하는지 확인
                if not os.path.exists(save_path):
                    try:
                        os.makedirs(save_path)
                        self.log(f"저장 경로 생성: {save_path}")
                    except Exception as e:
                        self.log(f"저장 경로 생성 실패: {e}")
                        messagebox.showerror("오류", f"저장 경로를 생성할 수 없습니다: {e}")
                        return
                
                # 파일 이름 생성
                file_name = f"공공데이터목록_{org_name}.csv"
                file_path = os.path.join(save_path, file_name)
                
                try:
                    self.save_to_csv(file_path)
                    self.log(f"데이터 자동 저장 완료: {file_path}")
                    messagebox.showinfo("성공", f"데이터가 성공적으로 저장되었습니다.")
                except Exception as e:
                    self.log(f"데이터 저장 실패: {e}")
                    messagebox.showerror("오류", f"데이터 저장 중 오류가 발생했습니다.\n{e}")
            
        except Exception as e:
            self.log(f"크롤링 중 오류 발생: {e}")
        finally:
            self.finish_crawling()
            
    def click_org_search_button(self):
        try:
            org_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'orgBtn'))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", org_btn)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", org_btn)
            time.sleep(1)
        except Exception as e:
            self.log(f"제공기관별 검색 버튼 클릭 실패: {e}")
            raise
    
    def scrape_file_data(self, org_name):
        data_list = []
        page = 1
        
        while not self.stop_crawling:
            # 페이지 로드 대기
            time.sleep(2)
            
            # 데이터 수집
            result_lists = self.driver.find_elements(By.CSS_SELECTOR, ".result-list")
            
            if not result_lists:
                self.log(f"파일데이터에서 데이터를 찾을 수 없습니다.")
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
                next_page = self.driver.find_element(
                    By.XPATH, f"//a[@onclick='updatePage({page + 1}); return false;']"
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", next_page)
                page += 1
            except Exception:
                break
        
        return data_list
    
    def scrape_api_data(self, org_name):
        data_list = []
        page = 1
        
        while not self.stop_crawling:
            # 페이지 로드 대기
            time.sleep(2)
            
            # 데이터 수집
            result_lists = self.driver.find_elements(By.CSS_SELECTOR, ".result-list")
            
            if not result_lists:
                self.log(f"오픈API에서 데이터를 찾을 수 없습니다.")
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
                next_page_button = self.driver.find_element(
                    By.XPATH, f"//a[@onclick='eventFnObj.fn_pageClick({page + 1}); return false;']"
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", next_page_button)
                time.sleep(2)
                page += 1
            except Exception:
                break
        
        return data_list
    
    def display_results(self):
        # 기존 데이터 제거
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 새 데이터 추가
        for row in self.result_data:
            self.result_tree.insert("", tk.END, values=(
                row["데이터명"], 
                row["데이터설명"], 
                row["제공기관"], 
                row["목록타입"]
            ))
    
    def save_to_csv(self, file_path):
        # CSV 파일로 저장
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ["데이터명", "데이터설명", "제공기관", "목록타입"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in self.result_data:
                writer.writerow(row)
    
    def finish_crawling(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            
        self.crawling_in_progress = False
        self.status_var.set("준비")
        self.status_label.config(fg="black")
        self.update_ui_state()
        
    def on_closing(self):
        if self.driver:
            self.driver.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PublicDataCrawler(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
