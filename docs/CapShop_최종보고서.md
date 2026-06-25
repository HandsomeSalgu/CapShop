# CapShop 최종보고서

| 구분 | 내용 |
|---|---|
| 프로젝트명 | CapShop |
| Repository | SyncShopper/syncshopper |
| 프로젝트 기간 | 2026.06.01 ~ 2026.06.26 |
| 서비스 유형 | YouTube Frame Capture 기반 AI Commerce Recommendation 서비스 |
| 작성일 | 2026.06.26 |
| 문서 버전 | v1.0 |

---

## 1. 프로젝트 개요

### 1.1 프로젝트 한 줄 소개

**CapShop**은 사용자가 YouTube 영상 시청 중 발견한 상품을 직접 검색하지 않아도, 영상 속 상품 영역을 캡처하면 AI가 이미지를 분석하고 유사 쇼핑 상품을 추천해주는 서비스이다.

### 1.2 프로젝트 배경

최근 사용자는 YouTube, Shorts, 릴스 등 영상 콘텐츠를 통해 다양한 상품을 접한다.  
그러나 영상 속 상품은 상품명, 브랜드명, 모델명, 정확한 키워드를 알기 어려운 경우가 많다.

기존 방식에서는 사용자가 영상을 멈춘 뒤 다음과 같은 과정을 직접 수행해야 했다.

- 상품의 색상, 형태, 로고, 브랜드를 눈으로 확인
- 추측한 키워드로 검색
- 여러 쇼핑몰 결과를 비교
- 실제 영상 속 상품과 유사한지 직접 판단

이 과정은 번거롭고 정확도가 낮으며, 영상 시청 흐름을 방해한다.  
CapShop은 이러한 문제를 해결하기 위해 **영상 프레임 캡처 + AI 이미지 분석 + 쇼핑 검색 추천**을 하나의 흐름으로 연결하였다.

### 1.3 프로젝트 목표

| 목표 | 설명 |
|---|---|
| 상품 검색 진입 장벽 감소 | 사용자가 상품명을 몰라도 이미지 캡처만으로 상품을 찾을 수 있도록 한다. |
| 영상 시청 경험 유지 | 영상 시청 중 별도 검색 과정을 최소화한다. |
| AI 기반 상품 특징 추출 | 이미지, OCR, 시각 특징을 분석하여 검색어를 생성한다. |
| 유사 상품 추천 | 네이버 쇼핑 검색 결과와 AI 판단을 활용하여 유사 상품을 추천한다. |
| 사용자 행동 데이터 축적 | 조회, 클릭, 위시리스트, 구매 링크 클릭 데이터를 저장하여 개인화 추천 확장 기반을 마련한다. |

---

## 2. 팀 구성 및 역할

| 역할 | 담당자 | 담당 영역 |
|---|---|---|
| 팀장 | 박화랑 | 백엔드, Chrome Extension, AI 기반 검색 연동, 전체 기능 통합 |
| 팀원 | 권태혁 | Frontend Web, 추천 시스템, 관리자 화면 |

---

## 3. 개발 범위

### 3.1 사용자 기능

- 회원가입
- 일반 로그인
- Google OAuth 로그인
- Kakao OAuth 로그인
- 이메일 중복 확인
- 이메일 인증
- 이메일 찾기
- 비밀번호 찾기
- 상품 목록 조회
- 상품 상세 조회
- 베스트 상품 조회
- 카테고리별 상품 조회
- AI 추천 상품 조회
- 위시리스트
- 최근 조회 내역
- 마이페이지 프로필 관리

### 3.2 Chrome Extension 기능

- YouTube 영상 페이지 감지
- CapShop 캡처 버튼 표시
- 영상 일시정지 후 상품 영역 선택
- 현재 탭 이미지 캡처
- 선택 영역 Crop
- 캡처 이미지 미리보기
- 빠른 검색 / 정밀 검색 선택
- 검색 힌트 입력
- AI 분석 요청
- 분석 진행 상태 표시
- 추천 상품 결과 패널 표시
- 상품 클릭 로그 저장
- 구매 링크 클릭 로그 저장
- 햄스터 마스코트 상태 애니메이션

### 3.3 AI 기능

- 캡처 이미지 분석
- OCR 기반 텍스트 추출
- 상품명, 브랜드, 색상, 형태, 로고, 특징 추출
- 검색어 생성
- 네이버 쇼핑 검색 결과 수집
- Gemini 기반 검색 보조
- 텍스트 기반 후보 필터링
- 이미지 유사도 기반 리랭킹
- 후보 상품 적합도 판단
- 최종 추천 결과 반환

### 3.4 관리자 기능

- 관리자 대시보드
- 사용자 관리
- 게시글 관리
- 공지사항 관리
- FAQ 관리
- 이벤트 관리

---

## 4. 시스템 아키텍처

### 4.1 전체 구조

```text
┌─────────────────────┐
│   Chrome Extension  │
│  - YouTube 감지      │
│  - 영역 캡처         │
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
│ Google / Kakao OAuth │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      Database       │
│ MySQL / Redis        │
└─────────────────────┘
```

### 4.2 기술 스택

#### Frontend Web

| 기술 | 사용 목적 |
|---|---|
| Vue 3 | 사용자 화면 및 관리자 화면 구현 |
| Vite | 프론트엔드 개발 서버 및 빌드 |
| Vue Router | 페이지 라우팅 |
| Pinia | 전역 상태 관리 |
| Axios | API 통신 |
| Chart.js | 차트 시각화 |
| Vue Advanced Cropper | 이미지 Crop 관련 기능 확장 |

#### Backend

| 기술 | 사용 목적 |
|---|---|
| Java 25 | 백엔드 개발 언어 |
| Spring Boot | 백엔드 애플리케이션 프레임워크 |
| Spring Security | 인증 및 인가 |
| OAuth2 Client | Google / Kakao 소셜 로그인 |
| JWT | 토큰 기반 인증 |
| MyBatis | SQL Mapper 기반 데이터 접근 |
| Redis | 토큰 블랙리스트 및 캐시 |
| Springdoc OpenAPI | Swagger API 문서화 |
| MySQL | 서비스 데이터 저장 |
| Lombok | 반복 코드 감소 |

#### AI Server

| 기술 | 사용 목적 |
|---|---|
| Python | AI 서버 개발 언어 |
| FastAPI | AI 분석 API 서버 |
| LangGraph | AI 분석 파이프라인 구성 |
| Gemini API | 이미지 분석 및 검색 보조 |
| Naver Search API | 쇼핑 상품 검색 |
| Pandas | 데이터 처리 |
| Scikit-learn | 유사도 계산 및 후보 필터링 |
| SQLAlchemy / PyMySQL | 사용자 행동 데이터 기반 추천 처리 |

#### Chrome Extension

| 기술 | 사용 목적 |
|---|---|
| Manifest V3 | Chrome Extension 구성 |
| Content Script | YouTube 페이지 내 UI 삽입 |
| Background Script | 탭 캡처 및 API 요청 중계 |
| chrome.storage.local | 토큰, 설정, 패널 위치 저장 |
| Canvas API | 선택 영역 이미지 Crop |

---

## 5. 주요 기능 구현 결과

### 5.1 회원가입 및 로그인

#### 구현 내용

- 일반 회원가입
- 이메일 중복 확인
- 이메일 인증번호 발송 및 검증
- 일반 로그인
- JWT Access Token 발급
- Google OAuth 로그인
- Kakao OAuth 로그인
- 현재 로그인 사용자 조회
- 로그아웃 처리
- 이메일 찾기
- 임시 비밀번호 발급

#### 구현 결과

사용자는 일반 이메일 계정 또는 소셜 계정을 통해 서비스에 로그인할 수 있다.  
로그인 성공 시 JWT 토큰을 발급받고, 인증이 필요한 API 요청에 사용한다.  
Chrome Extension에서도 동일한 인증 정보를 활용하여 AI 분석 요청을 수행한다.

---

### 5.2 상품 조회 기능

#### 구현 내용

- 상품 목록 조회
- 상품 상세 조회
- 베스트 상품 조회
- 카테고리별 상품 조회
- 상품 이미지, 가격, 브랜드, 쇼핑몰 정보 표시
- 상품 상세 조회 시 사용자 행동 로그 저장

#### 구현 결과

사용자는 웹 화면에서 일반 쇼핑몰처럼 상품을 탐색할 수 있다.  
상품 상세 화면에서는 상품 이미지, 가격, 설명, 외부 판매 링크 등을 확인할 수 있다.  
상품 조회 기록은 향후 개인화 추천을 위한 데이터로 활용 가능하다.

---

### 5.3 YouTube 상품 캡처 Extension

#### 구현 내용

- YouTube watch / shorts 페이지 감지
- CapShop 캡처 런처 표시
- 로그인 여부 확인
- 로그인하지 않은 경우 Extension 내부 로그인 패널 표시
- 캡처 버튼 클릭 시 영상 일시정지
- 사용자가 상품 영역을 드래그하여 선택
- 선택 영역 최소 크기 검증
- 현재 탭 캡처
- 선택 영역 Crop
- 캡처 이미지 미리보기
- 빠른 검색 / 정밀 검색 선택
- 검색 힌트 입력
- 분석 요청 전송
- 결과 패널 표시
- 상품 클릭 및 구매 링크 클릭 로그 저장

#### 구현 결과

사용자는 YouTube 영상을 시청하다가 관심 있는 상품을 발견하면 Extension에서 바로 상품 영역을 캡처할 수 있다.  
캡처된 이미지는 Backend를 통해 AI Server로 전달되며, 분석 결과와 추천 상품은 YouTube 화면 위의 결과 패널에 표시된다.

---

### 5.4 AI 이미지 분석

#### 구현 내용

- 캡처 이미지 기반 상품 분석
- OCR 기반 텍스트 후보 추출
- 시각 특징 분석
- 상품 유형, 색상, 스타일, 형태, 로고 텍스트 추출
- 검색 가능한 상품명 또는 검색 힌트 생성
- 사용자 입력 힌트 반영
- 분석 결과 품질 정보 반환
- 검색어 후보 생성

#### 구현 결과

AI Server는 사용자가 캡처한 이미지를 분석하여 상품 검색에 필요한 정보를 추출한다.  
상품명을 정확히 알 수 없는 경우에도 색상, 형태, 카테고리, 로고 텍스트 등을 조합하여 검색 가능한 키워드를 생성한다.

---

### 5.5 유사 상품 검색 및 추천

#### 구현 내용

- 네이버 쇼핑 검색 API 연동
- Gemini 기반 검색 보조
- 검색 후보 다각화
- 검색 결과 통합
- 텍스트 기반 후보 필터링
- 이미지 유사도 기반 리랭킹
- 최종 후보 판단
- Top3 상품 제공
- 추천 상품 카드 표시

#### 구현 결과

AI 분석 결과를 기반으로 네이버 쇼핑 검색을 수행하고, 검색 결과 중 유사도가 높은 상품을 사용자에게 추천한다.  
사용자는 추천 상품 카드에서 상품 이미지, 상품명, 쇼핑몰명, 브랜드, 가격을 확인하고 외부 판매 페이지로 이동할 수 있다.

---

### 5.6 빠른 검색 / 정밀 검색

#### 구현 내용

| 검색 방식 | 설명 |
|---|---|
| 빠른 검색 | 이미지 리랭킹과 후보 판단 일부를 생략하고 빠르게 검색 결과를 제공 |
| 정밀 검색 | 이미지 유사도 리랭킹과 후보 판단을 포함하여 더 신중하게 추천 |

#### 구현 결과

사용자는 상황에 따라 빠른 결과가 필요하면 빠른 검색을 선택하고, 더 정확한 추천이 필요하면 정밀 검색을 선택할 수 있다.  
검색 방식 선택은 Extension 결과 패널에서 제공된다.

---

### 5.7 사용자 행동 로그

#### 구현 내용

- 상품 상세 조회 로그
- 추천 상품 클릭 로그
- 외부 판매 페이지 이동 로그
- Extension 결과 패널 출처 저장
- YouTube videoId 저장
- 상품 순위, 검색어, detectionId, confidence, mallName, source, externalProductId 등 메타데이터 저장
- 구매 링크 클릭 로그 별도 저장

#### 구현 결과

사용자의 행동 데이터를 축적하여 향후 개인화 추천과 서비스 품질 개선에 활용할 수 있는 기반을 마련하였다.

---

### 5.8 위시리스트 및 최근 조회 내역

#### 구현 내용

- 위시리스트 추가
- 위시리스트 삭제
- 사용자별 위시리스트 조회
- 동일 상품 중복 추가 방지
- 최근 조회 내역 확인

#### 구현 결과

사용자는 관심 상품을 위시리스트에 저장하고, 최근 본 상품을 다시 확인할 수 있다.  
이 기능은 사용자 편의성과 재방문 가능성을 높이는 역할을 한다.

---

### 5.9 관리자 기능

#### 구현 내용

- 관리자 대시보드
- 사용자 목록 조회
- 사용자 관리
- 게시글 목록 조회
- 게시글 등록
- 게시글 수정
- 게시글 삭제 또는 숨김
- 공지사항 / FAQ / 이벤트 관리

#### 구현 결과

관리자는 서비스 운영에 필요한 사용자 및 게시글 관리 기능을 사용할 수 있다.  
게시글은 사용자 화면의 공지사항, FAQ, 이벤트 영역과 연결된다.

---

### 5.10 마스코트 기반 UX

#### 구현 내용

Chrome Extension에 햄스터 마스코트를 적용하여 서비스 상태를 시각적으로 표현하였다.

| 상태 | 마스코트 동작 |
|---|---|
| 대기 | 해바라기씨 먹기 |
| 캡처 | 카메라 들고 촬영 |
| 분석 중 | 탐정처럼 단서 찾기 |
| 검색 중 | 박스 뒤적이기 |
| 리랭킹 중 | 카드 정리하기 |
| 성공 | 만세 |
| 실패 | 울기 |
| Hover | 말풍선 표시 |
| Dragging | 뛰어가기 |

#### 구현 결과

단순한 로딩 화면 대신 마스코트를 활용하여 사용자가 현재 분석 상태를 직관적으로 이해할 수 있게 하였다.  
프로젝트의 브랜드 이미지와 사용자 경험을 강화하는 요소로 활용되었다.

---

## 6. 데이터베이스 설계

### 6.1 주요 테이블

| 테이블 | 설명 |
|---|---|
| users | 사용자 및 관리자 계정 |
| user_preferences | 사용자 관심 카테고리, 브랜드 |
| products | 상품 정보 |
| posts | 공지사항, FAQ, 이벤트 게시글 |
| detections | YouTube 캡처 기반 AI 탐지 결과 |
| search_queries | AI 분석 결과 기반 검색어 |
| search_results | 외부 검색 API 결과 |
| product_candidates | 추천 후보 상품 |
| recommendations | 사용자에게 추천된 상품 기록 |
| wishlists | 사용자 위시리스트 |
| user_events | 사용자 행동 로그 |
| ai_analysis_logs | AI 서버 요청 및 응답 로그 |
| affiliate_clicks | 구매 링크 클릭 로그 |

### 6.2 데이터 설계 특징

- 사용자와 상품을 중심으로 추천, 위시리스트, 행동 로그를 연결하였다.
- Detection 단위로 AI 분석 결과, 검색어, 검색 결과, 후보 상품을 추적할 수 있도록 구성하였다.
- 사용자 행동 로그는 product_id, recommendation_id, event_type, source_page, video_id, metadata_json을 포함하여 확장성 있게 설계하였다.
- AI 분석 로그는 request_payload, response_payload, success_yn, error_message, latency_ms를 저장하여 장애 분석과 품질 개선에 활용할 수 있도록 하였다.
- 외부 상품 데이터는 source와 external_product_id를 통해 출처를 식별할 수 있도록 하였다.

---

## 7. 주요 API

### 7.1 Backend API

| Method | URL | 설명 |
|---|---|---|
| POST | `/api/auth/signup` | 회원가입 |
| POST | `/api/auth/login` | 로그인 |
| GET | `/api/auth/me` | 현재 로그인 사용자 조회 |
| POST | `/api/auth/logout` | 로그아웃 |
| GET | `/api/auth/check-email` | 이메일 중복 확인 |
| POST | `/api/auth/email/send-code` | 이메일 인증번호 발송 |
| POST | `/api/auth/email/verify-code` | 이메일 인증번호 검증 |
| POST | `/api/auth/find-email` | 이메일 찾기 |
| POST | `/api/auth/find-password` | 임시 비밀번호 발급 |
| GET | `/api/products` | 상품 목록 조회 |
| GET | `/api/products/{id}` | 상품 상세 조회 |
| GET | `/api/products/best` | 베스트 상품 조회 |
| GET | `/api/products/category` | 카테고리별 상품 조회 |
| POST | `/api/detections/analyze` | 캡처 이미지 기반 상품 분석 요청 |
| GET | `/api/commerce/search` | 외부 쇼핑 검색 |
| GET | `/api/commerce/top3` | 검색 결과 Top3 조회 |
| POST | `/api/user-events` | 사용자 행동 로그 저장 |

### 7.2 AI Server API

| Method | URL | 설명 |
|---|---|---|
| GET | `/health` | AI Server 상태 확인 |
| POST | `/api/ai/analyze-frame` | 캡처 이미지 기반 상품 분석 |
| POST | `/api/ai/generate-commerce-query` | 상품 검색어 생성 |
| GET | `/api/ai/recommendations/{user_id}` | 사용자 행동 기반 추천 키워드 조회 |

---

## 8. AI 분석 파이프라인

### 8.1 처리 흐름

```text
Frame Analyzer
  ↓
OCR Analysis
  ↓
Visual Analysis
  ↓
Search Identification
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

### 8.2 단계별 설명

| 단계 | 설명 |
|---|---|
| Frame Analyzer | 캡처 이미지를 분석하여 기본 상품 후보 정보를 추출 |
| OCR Analysis | 이미지에 포함된 텍스트를 인식 |
| Visual Analysis | 색상, 형태, 스타일, 상품 종류 등 시각 특징 분석 |
| Search Identification | OCR과 이미지 특징을 조합하여 검색 대상 식별 |
| Query Generator | 네이버 쇼핑 검색에 사용할 primary/fallback query 생성 |
| Search Branch | 네이버 쇼핑 검색과 Gemini 검색 보조를 통해 후보 수집 |
| Merge Search Results | 여러 검색 결과를 하나의 후보 목록으로 통합 |
| Text Filter | 상품명, 브랜드, 카테고리 기반으로 후보 필터링 |
| Visual Reranker | 이미지 유사도 기준으로 후보 상품 재정렬 |
| Candidate Judge | 최종 후보 상품의 적합도 판단 |
| Final Formatter | Frontend/Extension에서 사용 가능한 응답 형태로 변환 |

---

## 9. 프로젝트 일정

### 9.1 전체 기간

- 시작일: 2026.06.01
- 종료일: 2026.06.26

### 9.2 주요 일정

| 기간 | 작업 |
|---|---|
| 06.01 ~ 06.03 | 프로젝트 기획, 요구사항 정의 |
| 06.03 ~ 06.06 | DB 설계, API 구조 설계 |
| 06.05 ~ 06.12 | 인증, 사용자, 상품 조회 Backend 구현 |
| 06.08 ~ 06.15 | Frontend Web 화면 구현 |
| 06.10 ~ 06.18 | Chrome Extension 캡처 기능 구현 |
| 06.13 ~ 06.21 | AI Server 분석 파이프라인 구현 |
| 06.17 ~ 06.23 | 네이버 쇼핑 검색, Gemini 연동, 추천 결과 처리 |
| 06.21 ~ 06.24 | 관리자 기능 및 사용자 행동 로그 구현 |
| 06.24 ~ 06.26 | 통합 테스트, 문서화, 발표 준비 |

---

## 10. 테스트 결과

### 10.1 기능 테스트

| 테스트 항목 | 결과 | 비고 |
|---|---|---|
| 회원가입 | 완료 | 이메일 중복 확인 및 인증 흐름 포함 |
| 일반 로그인 | 완료 | JWT 발급 확인 |
| Google OAuth 로그인 | 완료 | OAuth Callback 처리 확인 |
| Kakao OAuth 로그인 | 완료 | OAuth Callback 처리 확인 |
| 상품 목록 조회 | 완료 | 목록 화면 표시 확인 |
| 상품 상세 조회 | 완료 | 상세 정보 표시 확인 |
| 베스트 상품 조회 | 완료 | 베스트 상품 영역 표시 |
| 카테고리 상품 조회 | 완료 | 카테고리 기준 필터링 |
| YouTube 페이지 감지 | 완료 | watch/shorts URL 기준 감지 |
| 상품 영역 캡처 | 완료 | 드래그 선택 및 Crop 확인 |
| 캡처 이미지 미리보기 | 완료 | 결과 패널 표시 |
| 빠른 검색 | 완료 | 빠른 검색 요청값 확인 |
| 정밀 검색 | 완료 | 정밀 검색 요청값 확인 |
| AI 분석 요청 | 완료 | Backend → AI Server 연동 확인 |
| 네이버 쇼핑 검색 | 완료 | 검색 결과 수집 확인 |
| 추천 상품 표시 | 완료 | 상품 카드 표시 확인 |
| 상품 클릭 로그 | 완료 | user_events 저장 확인 |
| 구매 링크 클릭 로그 | 완료 | affiliate_clicks 저장 확인 |
| 관리자 게시글 관리 | 완료 | 등록/수정/조회 흐름 확인 |

### 10.2 예외 테스트

| 예외 상황 | 처리 결과 |
|---|---|
| 로그인하지 않고 분석 요청 | 로그인 패널 표시 |
| Access Token 만료 | 토큰 제거 후 재로그인 요구 |
| YouTube videoId 없음 | 오류 메시지 표시 |
| 영상 timestamp 없음 | 오류 메시지 표시 |
| 캡처 영역이 너무 작음 | 경고 메시지 표시 후 분석 중단 |
| Backend 연결 실패 | 서버 연결 오류 메시지 표시 |
| AI 분석 실패 | 분석 실패 메시지 및 재시도 안내 |
| 검색 결과 없음 | 표시할 상품 없음 메시지 표시 |
| 외부 상품 링크 없음 | 링크 비활성화 처리 |

---

## 11. 프로젝트 성과

### 11.1 기능적 성과

- YouTube 영상 기반 상품 캡처 기능 구현
- AI 이미지 분석과 OCR을 활용한 상품 특징 추출 구현
- 네이버 쇼핑 검색 API 기반 상품 후보 수집 구현
- 빠른 검색과 정밀 검색 모드 구현
- Chrome Extension 결과 패널에서 추천 상품 표시 구현
- 일반 로그인 및 Google/Kakao 소셜 로그인 구현
- 사용자 행동 로그 기반 추천 확장 구조 구현
- 관리자 사용자/게시글 관리 기능 구현

### 11.2 기술적 성과

- Frontend, Backend, AI Server, Extension을 분리한 구조로 구현하였다.
- Spring Boot와 FastAPI를 연동하여 AI 분석 요청 흐름을 구성하였다.
- LangGraph 기반 AI 분석 파이프라인을 적용하였다.
- OCR, 이미지 분석, 검색어 생성, 검색 결과 필터링, 리랭킹을 하나의 흐름으로 연결하였다.
- 사용자 행동 로그와 AI 분석 로그를 저장하여 추후 품질 개선이 가능하도록 설계하였다.
- Chrome Extension에서 Canvas API를 활용해 사용자가 선택한 영역만 이미지로 추출하였다.

### 11.3 사용자 경험 성과

- 사용자는 상품명을 몰라도 캡처만으로 유사 상품을 찾을 수 있다.
- YouTube 화면을 벗어나지 않고 추천 상품을 확인할 수 있다.
- 검색 힌트 입력을 통해 사용자가 AI 분석 방향을 보조할 수 있다.
- 마스코트 애니메이션을 통해 분석 진행 상태를 직관적으로 확인할 수 있다.

---

## 12. 문제점 및 해결 과정

### 12.1 외부 검색 API 이슈

#### 문제

Google Custom Search JSON API 사용을 검토했으나, 신규 프로젝트에서 API 접근 제한 및 403 오류가 발생할 수 있었다.

#### 해결

프로젝트에서는 네이버 쇼핑 검색 API를 중심으로 상품 검색을 수행하고, Gemini 기반 검색 보조를 함께 활용하는 방향으로 전환하였다.

---

### 12.2 이미지 URL 오류 이슈

#### 문제

외부 검색 결과의 이미지 URL 중 일부가 AI Provider에서 다운로드되지 않아 400 오류가 발생하는 문제가 있었다.

#### 해결

이미지 URL 검증 실패 시 전체 분석을 중단하지 않고, 문제가 되는 후보 이미지를 제외하거나 재시도하는 방식으로 안정성을 높였다.

---

### 12.3 상품명 불확실성 문제

#### 문제

영상 속 상품은 정확한 모델명이나 브랜드명을 알 수 없는 경우가 많았다.

#### 해결

OCR, 색상, 형태, 로고, 카테고리, 사용자 힌트를 조합하여 검색어 후보를 여러 방향으로 생성하도록 설계하였다.

---

### 12.4 Extension 인증 흐름 문제

#### 문제

Chrome Extension에서 사용자가 로그인하지 않은 상태로 분석 요청을 시도할 수 있었다.

#### 해결

분석 요청 전 chrome.storage.local에 저장된 Access Token을 확인하고, 토큰이 없으면 Extension 내부 로그인 패널을 표시하도록 구현하였다.

---

## 13. 한계점

| 한계 | 설명 |
|---|---|
| 동일 상품 보장 어려움 | 이미지 기반 검색 특성상 정확한 동일 상품보다는 유사 상품 추천에 가깝다. |
| 영상 품질 의존성 | 캡처 이미지가 흐리거나 상품이 작게 보이면 분석 정확도가 낮아질 수 있다. |
| OCR 한계 | 로고나 텍스트가 작거나 왜곡된 경우 OCR 인식률이 낮을 수 있다. |
| 외부 API 의존성 | 네이버 검색 API, Gemini API의 응답 품질과 가용성에 영향을 받는다. |
| 개인화 추천 초기 한계 | 사용자 행동 데이터가 부족한 초기에는 추천 품질이 제한적이다. |
| 운영 환경 분리 필요 | 현재 개발 환경 중심 설정을 운영 환경에 맞게 분리할 필요가 있다. |

---

## 14. 향후 개선 방향

### 14.1 추천 정확도 개선

- 이미지 유사도 모델 고도화
- 카테고리별 검색어 생성 전략 분리
- 상품명, 브랜드, 로고 인식 정확도 개선
- 검색 결과 품질 평가 지표 도입
- 정답/오답 피드백 기반 추천 개선

### 14.2 개인화 추천 강화

- 사용자 클릭 로그 기반 관심 카테고리 추론
- 위시리스트 기반 추천
- 최근 조회 상품 기반 추천
- 사용자별 선호 브랜드 반영
- 행동 로그 기반 협업 필터링 또는 콘텐츠 기반 추천 적용

### 14.3 서비스 안정성 개선

- Docker Compose 기반 통합 실행 환경 구성
- GitHub Actions 기반 CI/CD 구축
- 운영 환경용 Secret 분리
- API 모니터링 및 에러 알림 추가
- AI 분석 실패율, 평균 응답 시간 대시보드 구성

### 14.4 UX 개선

- Extension 결과 패널 디자인 개선
- 추천 상품 비교 기능 추가
- 캡처 영역 자동 추천 기능 추가
- 마스코트 애니메이션 품질 개선
- 모바일 또는 다른 영상 플랫폼 확장 검토

---

## 15. 기대 효과

### 15.1 사용자 측면

- 상품명을 몰라도 영상 속 상품을 쉽게 찾을 수 있다.
- 별도의 검색 과정 없이 영상 시청 중 바로 상품 탐색이 가능하다.
- 유사 상품을 빠르게 비교할 수 있다.
- 관심 상품을 위시리스트와 최근 조회 내역으로 관리할 수 있다.

### 15.2 서비스 측면

- 영상 콘텐츠와 쇼핑 경험을 자연스럽게 연결할 수 있다.
- 사용자 행동 로그를 기반으로 개인화 추천 서비스로 확장할 수 있다.
- 외부 쇼핑 검색 API와 AI 분석을 결합한 커머스 추천 플랫폼으로 발전할 수 있다.

### 15.3 기술 측면

- Chrome Extension, Spring Boot, FastAPI, AI API, 외부 쇼핑 API를 통합한 실전형 서비스 구조를 구현하였다.
- 이미지 분석, OCR, 검색어 생성, 검색 결과 필터링, 리랭킹 흐름을 경험하였다.
- 사용자 행동 로그 기반 추천 시스템으로 확장 가능한 데이터 구조를 설계하였다.

---

## 16. 최종 결론

CapShop은 영상 속 상품을 발견한 순간부터 상품 추천까지 이어지는 과정을 간편하게 만드는 것을 목표로 한 서비스이다.  
기존에는 사용자가 직접 상품의 특징을 추측하고 검색해야 했지만, CapShop은 Chrome Extension을 통해 영상 속 상품 영역을 캡처하고 AI가 이를 분석하여 유사 상품을 추천한다.

본 프로젝트를 통해 다음과 같은 결과를 달성하였다.

- YouTube 영상 기반 상품 캡처 기능 구현
- AI 이미지 분석 및 OCR 기반 상품 특징 추출
- 네이버 쇼핑 검색 API 기반 상품 추천
- 빠른 검색 / 정밀 검색 기능 제공
- 사용자 인증 및 소셜 로그인 구현
- 상품 조회, 위시리스트, 최근 조회 내역 구현
- 사용자 행동 로그 및 AI 분석 로그 저장 구조 구현
- 관리자 기능 구현
- 향후 개인화 추천으로 확장 가능한 구조 마련

결과적으로 CapShop은 영상 콘텐츠와 쇼핑 경험을 연결하는 새로운 탐색 방식을 제안하며, 향후 추천 정확도와 개인화 기능을 고도화하면 실사용 가능한 AI Commerce 서비스로 발전할 수 있다.

---

## 17. 부록

### 17.1 실행 환경

| 구분 | 내용 |
|---|---|
| Backend | Java 25, Spring Boot, MySQL, Redis |
| Frontend | Node.js 20 이상, Vue 3, Vite |
| AI Server | Python 3.11 이상, FastAPI |
| Database | MySQL 8.x |
| Extension | Chrome Manifest V3 |

### 17.2 주요 환경 변수

#### Backend

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

#### AI Server

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

### 17.3 참고 문서

- 요구사항정의서
- WBS 및 간트차트
- README.md
- database/schema.sql
- frontend/web router
- frontend/extension manifest 및 content script
- backend application.yml
- ai-server FastAPI router
