## 기관별 공공데이터 목록 크롤러
공공데이터포털에서 기관별 데이터 목록을 자동으로 추출하는 크롤러입니다.  
기관명과 기관코드 정보를 포함한 CSV 파일을 입력으로 받아 각 기관의 공공데이터 목록을 수집하고 저장합니다.

### 프로젝트 구조

```
📁 public-data-crawler
│── 📂 data
│   ├── 기관코드.csv    # 입력 파일
│── 📜 public-data-crawler.py  # 크롤러 실행 파일
│── 📜 README.md        # 프로젝트 설명 파일
```

### 설치 및 실행 방법

#### 1️⃣ 필수 라이브러리 설치
```
pip install selenium pandas webdriver-manager
```

#### 2️⃣ 입력 파일 준비
```data/기관코드.csv``` 파일을 준비합니다.
- 기관 코드는 [행정표준코드관리시스템](https://www.code.go.kr/index.do)에서 확인할 수 있습니다.
- CSV 파일은 '공공기관명'과 '기관코드' 두 개의 열(Column)로 구성됩니다.


#### 3️⃣ 크롤러 실행
```public-data-crawler.py``` 파일을 실행하면 ```data``` 폴더에 기관별 공공데이터목록 파일이 저장됩니다.

