## 기관별 공공데이터 목록 크롤러

공공데이터포털에서 기관별 공공데이터 목록을 자동으로 수집하는 크롤러입니다.  
기관명과 기관코드를 입력하면 해당 기관의 데이터를 검색하여 저장합니다.

### 주요 기능

- 공공데이터포털에서 기관별 데이터 목록 자동 크롤링
- CSV 파일 기반 일괄 처리 (Python 스크립트 버전)
- GUI 환경에서 간편하게 실행 가능 (GUI 실행 파일 버전)
- 크롤링 진행 상황 실시간 확인
- Selenium + Chrome WebDriver 기반 자동화

### 프로젝트 구조

```
📁 public-data-crawler
│── 📂 data
│   ├── 기관코드.csv    # 기관코드 및 기관명 정보가 담긴 입력 파일
│── 📜 public-data-crawler.py  # 콘솔 실행 스크립트
│── 📜 public-data-crawler-gui.py # 화면 인터페이스 제공 스크립트
│── 📜 README.md        # 프로젝트 설명 및 사용 가이드
```

### 설치 및 실행 방법

#### Python 스크립트 버전

1. 필수 라이브러리 설치
```bash
pip install selenium pandas webdriver-manager
```

2. 입력 파일 준비
`data/기관코드.csv` 파일을 준비합니다.
    - 기관 코드는 [행정표준코드관리시스템](https://www.code.go.kr/index.do)에서 확인할 수 있습니다.
    - CSV 파일은 '공공기관명'과 '기관코드' 두 개의 열(Column)로 구성됩니다.

3. 크롤러 실행
아래 명령어를 실행하면 `data` 폴더에 기관별 공공데이터 목록이 저장됩니다.
```bash
python public-data-crawler.py
```

#### GUI 실행 파일 버전

1. 다운로드
Releases에서 `PublicDataCrawler_v1.0.0.exe` 파일을 다운로드합니다.

2. 크롤러 실행
   - `public-data-crawler.exe` 실행  
   - `기관명`과 `기관코드` 입력 후 크롤링 시작 버튼 클릭
   - 크롤링 진행 상황을 GUI에서 실시간으로 확인
   - 크롤링 완료 후 자동으로 저장 경로에 데이터 저장

### 시스템 요구 사항

- Python 3.6 이상 (스크립트 버전)
- Windows 10/11 지원 (GUI 버전)
- Chrome 브라우저 설치 필수 (자동 WebDriver 업데이트 포함)

### 변경 사항

**v1.0.0**
- GUI 환경에서 기관별 데이터 목록 수집 가능  
- 진행 상황 표시 및 에러 로그 출력 기능 추가  
- 데이터 자동 저장 기능 포함

### 문의 및 피드백

버그 제보 및 기능 개선 요청은 **Issues**에 남겨주세요.
