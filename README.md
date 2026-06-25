# CapShop

> 영상 속 상품을 캡처하면 AI가 상품을 분석하고, 유사한 쇼핑 상품을 추천해주는 서비스

<br/>

## 프로젝트 소개

**CapShop**은 유튜브 영상 시청 중 마음에 드는 상품을 발견했을 때, 사용자가 직접 상품명을 검색하지 않아도 원하는 상품을 쉽게 찾을 수 있도록 돕는 서비스입니다.

사용자는 크롬 익스텐션을 통해 영상 속 상품 영역을 캡처할 수 있습니다.
캡처된 이미지는 AI 서버에서 분석되며, OCR 정보와 시각적 특징을 바탕으로 상품 후보를 추출합니다. 이후 네이버 쇼핑 검색과 Gemini 기반 분석을 활용하여 유사 상품을 추천합니다.

본 프로젝트는 초기 기획 단계에서 **SyncShopper**라는 가제로 시작되었으며, 최종 서비스명은 **CapShop**으로 확정되었습니다.

CapShop은 영상 콘텐츠와 쇼핑 경험을 자연스럽게 연결하는 것을 목표로 합니다.

<br/>

## 팀 구성

| 역할 | 이름  | 담당                   |
| -- | --- | -------------------- |
| 팀장 | 박화랑 | 백엔드, 익스텐션, AI기반 검색 |
| 팀원 | 권태혁 | 프론트엔드, 추천시스템               |


<br/>

## 핵심 기능

### 1. 영상 속 상품 캡처

* 유튜브 영상 위에서 원하는 상품 영역 선택
* 크롬 익스텐션을 통한 간편한 캡처
* 선택 영역 기반 AI 분석 요청

### 2. AI 기반 상품 분석

* 캡처 이미지 분석
* OCR 기반 텍스트 추출
* 상품명, 브랜드, 색상, 로고, 형태 등 특징 추출
* 검색에 적합한 상품 키워드 생성

### 3. 유사 상품 검색 및 추천

* 네이버 쇼핑 검색 API 기반 상품 후보 수집
* Gemini 기반 검색 보조
* 텍스트 기반 후보 필터링
* 이미지 유사도 기반 리랭킹
* 최종 추천 상품 제공

### 4. 사용자 서비스 기능

* 회원가입 및 로그인
* Google / Kakao OAuth 로그인
* 상품 목록 조회
* 상품 상세 조회
* 베스트 상품 조회
* 카테고리별 상품 조회
* 위시리스트
* 최근 조회 내역
* AI 추천 상품 조회

### 5. 관리자 기능

* 관리자 대시보드
* 사용자 관리
* 게시글 관리
* 공지사항 / FAQ / 이벤트 관리

<br/>

## 서비스 흐름

```text
1. 사용자가 유튜브 영상을 시청한다.
2. 크롬 익스텐션으로 영상 속 상품 영역을 캡처한다.
3. 캡처 이미지가 백엔드 서버로 전달된다.
4. 백엔드는 AI 서버에 상품 분석을 요청한다.
5. AI 서버는 이미지와 OCR 정보를 분석한다.
6. 분석 결과를 바탕으로 검색어를 생성한다.
7. 네이버 쇼핑 검색과 Gemini 검색을 통해 상품 후보를 수집한다.
8. 후보 상품을 필터링하고 리랭킹한다.
9. 최종 추천 상품을 사용자에게 제공한다.
```

<br/>

## 시스템 아키텍처

```text
┌─────────────────────┐
│   Chrome Extension  │
│  - 화면 캡처         │
│  - 분석 요청         │
│  - 결과 패널 표시    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    Frontend Web     │
│  Vue 3 / Vite        │
│  Pinia / Router      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      Backend        │
│ Spring Boot          │
│ Security / OAuth2    │
│ JWT / MyBatis        │
│ Redis / Swagger      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      AI Server      │
│ FastAPI / LangGraph  │
│ OCR / Image Analysis │
│ Query Generation     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ External Services   │
│ Naver Search API     │
│ Gemini API           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      Database       │
│ MySQL / Redis        │
└─────────────────────┘
```

<br/>

## 기술 스택

### Frontend

| 기술         | 사용 목적            |
| ---------- | ---------------- |
| Vue 3      | 사용자 화면 구현        |
| Vite       | 프론트엔드 개발 서버 및 빌드 |
| Vue Router | 페이지 라우팅          |
| Pinia      | 전역 상태 관리         |
| Axios      | API 통신           |
| Chart.js   | 차트 시각화           |

<br/>

### Backend

| 기술                | 사용 목적                 |
| ----------------- | --------------------- |
| Java 25           | 백엔드 개발 언어             |
| Spring Boot       | 백엔드 애플리케이션 프레임워크      |
| Spring Security   | 인증 및 인가 처리            |
| OAuth2 Client     | Google / Kakao 소셜 로그인 |
| JWT               | 토큰 기반 인증              |
| MyBatis           | SQL Mapper 기반 데이터 접근  |
| Redis             | 토큰 블랙리스트 및 캐시 처리      |
| Springdoc OpenAPI | Swagger API 문서화       |
| MySQL             | 서비스 데이터 저장            |

<br/>

### AI Server

| 기술               | 사용 목적           |
| ---------------- | --------------- |
| Python           | AI 서버 개발 언어     |
| FastAPI          | AI 분석 API 서버    |
| LangGraph        | AI 분석 파이프라인 구성  |
| Gemini API       | 이미지 분석 및 검색 보조  |
| Naver Search API | 쇼핑 상품 검색        |
| Pandas           | 데이터 처리          |
| Scikit-learn     | 유사도 계산 및 후보 필터링 |

<br/>

## 주요 디렉토리 구조

```text
syncshopper
├── ai-server
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   ├── schemas
│   │   └── services
│   └── requirements.txt
│
├── backend
│   ├── src
│   │   ├── main
│   │   │   ├── java/com/syncshopper
│   │   │   └── resources
│   │   └── test
│   └── pom.xml
│
├── database
│   └── schema.sql
│
├── frontend
│   └── web
│       ├── src
│       │   ├── assets
│       │   ├── components
│       │   ├── router
│       │   ├── stores
│       │   └── views
│       └── package.json
│
├── docs
├── infra
└── README.md
```

<br/>

## 데이터베이스 설계

CapShop은 사용자, 상품, AI 분석 결과, 검색 결과, 추천 결과, 사용자 행동 로그를 중심으로 데이터를 관리합니다.

| 테이블                | 설명                 |
| ------------------ | ------------------ |
| users              | 사용자 및 관리자 계정       |
| user_preferences   | 사용자 관심 카테고리 및 브랜드  |
| products           | 상품 정보              |
| posts              | 공지사항, FAQ, 이벤트 게시글 |
| detections         | 유튜브 캡처 기반 AI 탐지 결과 |
| search_queries     | AI 분석 결과 기반 검색어    |
| search_results     | 외부 검색 API 결과       |
| product_candidates | 추천 후보 상품           |
| recommendations    | 사용자에게 추천된 상품 기록    |
| wishlists          | 사용자 위시리스트          |
| user_events        | 사용자 행동 로그          |
| ai_analysis_logs   | AI 서버 요청 및 응답 로그   |
| affiliate_clicks   | 구매 링크 클릭 로그        |

<br/>

## AI 분석 파이프라인

AI 서버는 FastAPI와 LangGraph를 기반으로 상품 분석 파이프라인을 구성합니다.

```text
Frame Analyzer
  ↓
Query Generator
  ↓
Naver Search / Gemini Search
  ↓
Merge Search Results
  ↓
Text Filter
  ↓
Visual Reranker
  ↓
Candidate Judge
  ↓
Final Formatter
```

### 단계별 설명

| 단계                   | 설명                             |
| -------------------- | ------------------------------ |
| Frame Analyzer       | 캡처 이미지와 OCR 정보를 분석하여 상품 특징을 추출 |
| Query Generator      | 상품 분석 결과를 바탕으로 검색어 생성          |
| Search Branch        | 네이버 쇼핑 검색과 Gemini 검색을 통해 후보 수집 |
| Merge Search Results | 여러 검색 결과를 하나의 후보 목록으로 통합       |
| Text Filter          | 상품명, 브랜드, 카테고리 기반으로 후보 필터링     |
| Visual Reranker      | 이미지 유사도를 기준으로 후보 상품 재정렬        |
| Candidate Judge      | 최종 후보 상품의 적합도 판단               |
| Final Formatter      | 프론트엔드에서 사용 가능한 응답 형태로 변환       |

<br/>

## 주요 API

### Auth API

| Method | URL                           | 설명            |
| ------ | ----------------------------- | ------------- |
| POST   | `/api/auth/signup`            | 회원가입          |
| POST   | `/api/auth/login`             | 로그인           |
| GET    | `/api/auth/me`                | 현재 로그인 사용자 조회 |
| POST   | `/api/auth/logout`            | 로그아웃          |
| GET    | `/api/auth/check-email`       | 이메일 중복 확인     |
| POST   | `/api/auth/email/send-code`   | 이메일 인증번호 발송   |
| POST   | `/api/auth/email/verify-code` | 이메일 인증번호 검증   |
| POST   | `/api/auth/find-email`        | 이메일 찾기        |
| POST   | `/api/auth/find-password`     | 임시 비밀번호 발급    |

<br/>

### Product API

| Method | URL                      | 설명          |
| ------ | ------------------------ | ----------- |
| GET    | `/api/products`          | 상품 목록 조회    |
| GET    | `/api/products/{id}`     | 상품 상세 조회    |
| GET    | `/api/products/best`     | 베스트 상품 조회   |
| GET    | `/api/products/category` | 카테고리별 상품 조회 |

<br/>

### AI API

| Method | URL                               | 설명              |
| ------ | --------------------------------- | --------------- |
| POST   | `/api/ai/analyze-frame`           | 캡처 이미지 기반 상품 분석 |
| POST   | `/api/ai/generate-commerce-query` | 상품 검색어 생성       |
| GET    | `/health`                         | AI 서버 상태 확인     |

<br/>

### Commerce API

| Method | URL                    | 설명            |
| ------ | ---------------------- | ------------- |
| GET    | `/api/commerce/search` | 외부 쇼핑 검색      |
| GET    | `/api/commerce/top3`   | 검색 결과 Top3 조회 |

<br/>

## 실행 방법

### 1. 사전 준비

다음 프로그램이 설치되어 있어야 합니다.

```text
Java 25
Node.js 20 이상
Python 3.11 이상
MySQL 8.x
Redis
```

<br/>

### 2. Database 실행

MySQL에 접속한 뒤 `database/schema.sql`을 실행합니다.

```bash
mysql -u root -p < database/schema.sql
```

<br/>

### 3. Backend 실행

```bash
cd backend
mvn spring-boot:run
```

Backend 기본 실행 주소는 다음과 같습니다.

```text
http://localhost:8080
```

Swagger 문서는 다음 주소에서 확인할 수 있습니다.

```text
http://localhost:8080/swagger-ui.html
```

<br/>

### 4. Frontend 실행

```bash
cd frontend/web
npm install
npm run dev
```

Frontend 기본 실행 주소는 다음과 같습니다.

```text
http://localhost:5173
```

<br/>

### 5. AI Server 실행

```bash
cd ai-server
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Windows PowerShell 환경에서는 다음 명령어로 가상환경을 활성화합니다.

```bash
.venv\Scripts\Activate.ps1
```

AI Server 기본 실행 주소는 다음과 같습니다.

```text
http://localhost:8000
```

Health Check는 다음 주소에서 확인할 수 있습니다.

```text
http://localhost:8000/health
```

<br/>

## 환경 변수

프로젝트 실행을 위해 다음 환경변수 설정이 필요합니다.

### Backend

```env
JWT_SECRET=your-jwt-secret

GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

KAKAO_CLIENT_ID=your-kakao-client-id
KAKAO_CLIENT_SECRET=your-kakao-client-secret

NAVER_CLIENT_ID=your-naver-client-id
NAVER_CLIENT_SECRET=your-naver-client-secret

SPRING_MAIL_USERNAME=your-email
SPRING_MAIL_PASSWORD=your-email-app-password

OAUTH2_REDIRECT_URI=http://localhost:5173/oauth/callback
OAUTH2_SIGNUP_REDIRECT_URI=http://localhost:5173/signup
OAUTH2_GOOGLE_REDIRECT_URI=http://localhost:8080/login/oauth2/code/google
OAUTH2_KAKAO_REDIRECT_URI=http://localhost:8080/login/oauth2/code/kakao
AI_FASTAPI_TIMEOUT_MS=180000
```

<br/>

### AI Server

```env
AI_DETECTION_PROVIDER=gemini
AI_COMMERCE_QUERY_PROVIDER=gemini
AI_ANALYSIS_PROVIDER=gemini
AI_VISUAL_RERANKER_PROVIDER=gemini
AI_RESULT_JUDGE_PROVIDER=gemini

GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_VISION_MODEL=gemini-2.5-flash
GEMINI_QUERY_MODEL=gemini-2.5-flash
GEMINI_SEARCH_MODEL=gemini-2.5-flash

BACKEND_BASE_URL=http://localhost:8080
VITE_BACKEND_BASE_URL=http://localhost:8080

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=syncshopper
```

<br/>

## 브랜치 전략

```text
main
 └── release
      └── develop
           └── feature/기능명
```

| 브랜치       | 설명           |
| --------- | ------------ |
| main      | 최종 배포 브랜치    |
| release   | 배포 후보 브랜치    |
| develop   | 통합 개발 브랜치    |
| feature/* | 기능 단위 개발 브랜치 |

<br/>

## 커밋 컨벤션

| 타입       | 설명                   |
| -------- | -------------------- |
| feat     | 새로운 기능 추가            |
| fix      | 버그 수정                |
| refactor | 코드 리팩토링              |
| style    | 코드 포맷팅 및 스타일 수정      |
| docs     | 문서 수정                |
| test     | 테스트 코드 추가 및 수정       |
| chore    | 설정 파일, 빌드 작업 등 기타 변경 |

예시:

```bash
feat: 상품 상세 조회 API 구현
fix: OAuth 로그인 콜백 오류 수정
docs: README 실행 방법 추가
```

<br/>

## 프로젝트 특징

### 영상 기반 쇼핑 검색

영상 속 상품을 직접 검색어로 입력하지 않아도, 사용자가 캡처한 이미지 기반으로 상품을 분석하고 검색합니다.

### AI 분석과 외부 검색 API 결합

이미지 분석, OCR, 검색어 생성, 외부 쇼핑 검색을 하나의 흐름으로 연결하여 유사 상품 추천 결과를 제공합니다.

### 빠른 검색 / 정밀 검색 지원

사용자는 상황에 따라 빠른 결과가 필요한 경우 빠른 검색을, 더 정확한 분석이 필요한 경우 정밀 검색을 선택할 수 있습니다.

### 사용자 행동 로그 기반 확장성

상품 조회, 위시리스트, 추천 상품 클릭, 구매 링크 클릭 등의 행동 데이터를 저장하여 향후 개인화 추천 기능으로 확장할 수 있습니다.

### 마스코트 기반 UX

크롬 익스텐션에 햄스터 마스코트를 적용하여 분석 중, 검색 중, 성공, 실패 등의 상태를 직관적으로 표현합니다.

<br/>

## 시연 화면

> 아래 영역에는 프로젝트 시연 이미지 또는 GIF를 추가합니다.

### 메인 화면

```text
이미지 추가 예정
```

### 유튜브 캡처 화면

```text
이미지 추가 예정
```

### AI 분석 화면

```text
이미지 추가 예정
```

### 추천 상품 결과 화면

```text
이미지 추가 예정
```

### 상품 상세 화면

```text
이미지 추가 예정
```

### 관리자 화면

```text
이미지 추가 예정
```

<br/>

## 기대 효과

CapShop은 영상 콘텐츠와 쇼핑 검색을 연결하여 사용자가 상품을 찾는 과정을 줄여줍니다.

기존에는 영상 속 상품을 찾기 위해 사용자가 직접 브랜드, 색상, 디자인, 로고 등을 추측해 검색해야 했습니다. CapShop은 캡처 이미지 기반 AI 분석을 통해 이러한 과정을 자동화하고, 관련 상품 후보를 빠르게 추천합니다.

이를 통해 사용자는 콘텐츠 시청 흐름을 유지하면서 자연스럽게 상품 탐색과 구매 연결까지 이어갈 수 있습니다.

<br/>

## 향후 개선 방향

* Docker Compose 기반 통합 실행 환경 구성
* GitHub Actions 기반 CI/CD 추가
* 백엔드 단위 테스트 및 통합 테스트 보강
* AI 서버 테스트 코드 추가
* 검색 결과 품질 평가 지표 추가
* 추천 알고리즘 고도화
* 사용자 행동 로그 기반 개인화 추천 강화
* 크롬 익스텐션 UI/UX 개선
* 운영 환경용 보안 설정 분리
* 배포 환경 구성 및 모니터링 추가

<br/>

## 프로젝트 목표

CapShop은 영상 속 상품을 발견하는 순간부터 상품 추천까지 이어지는 과정을 간편하게 만드는 것을 목표로 합니다.

사용자가 상품명을 몰라도 원하는 상품을 찾을 수 있도록 하고, 영상 콘텐츠와 쇼핑 경험을 자연스럽게 연결하는 새로운 탐색 방식을 제안합니다.
