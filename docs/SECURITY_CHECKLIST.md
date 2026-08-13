# 🔐 보안 체크리스트 (Security Checklist)

배포 전 **반드시** 확인해야 할 보안 항목들입니다.

---

## ✅ 코드 레벨 (Code Level)

### Application Configuration
- [ ] **application.yml**: 하드코딩된 IP 없음?
  ```bash
  grep -r "70\.12\.60\.52" backend/
  # 결과가 없어야 함 ✅
  ```

- [ ] **OAuth2 Redirect URI**: 모두 환경변수?
  ```yaml
  # ✅ 올바른 형식
  redirect-uri: ${OAUTH2_GOOGLE_REDIRECT_URI}
  
  # ❌ 잘못된 형식
  redirect-uri: ${OAUTH2_GOOGLE_REDIRECT_URI:http://localhost:8080/...}
  ```

- [ ] **JWT_SECRET**: 기본값이 강한 문자열?
  ```yaml
  secret: ${JWT_SECRET}  # 기본값 없음! (필수)
  ```

- [ ] **Database Password**: 하드코딩 없음?
  ```yaml
  # ❌ 절대 하지 말 것
  password: potato
  
  # ✅ 올바른 형식
  password: ${DB_PASSWORD:potato}
  ```

---

## ✅ 파일 레벨 (File Level)

### .env 파일 관리
- [ ] **.gitignore에 .env 등록?**
  ```bash
  cat .gitignore | grep ".env"
  # 결과: .env, .env.*, !.env.example
  ```

- [ ] **.env 파일이 Git에 커밋되지 않았나?**
  ```bash
  git log --full-history --all -- backend/.env
  # 결과가 없어야 함 ✅
  git log --full-history --all -- ai-server/.env
  git log --full-history --all -- frontend/web/.env
  ```

- [ ] **.env.example이 Git에 포함되었나?**
  ```bash
  git ls-files | grep ".env.example"
  # 결과: backend/.env.example, ai-server/.env.example 등
  ```

- [ ] **로컬 .env 파일 권한?** (선택)
  ```bash
  chmod 600 backend/.env
  chmod 600 ai-server/.env
  chmod 600 frontend/web/.env
  ```

### 소스 코드
- [ ] **API 키가 소스에 박혀있나?**
  ```bash
  grep -r "sk-" backend/ frontend/ ai-server/
  grep -r "AKIA" backend/ frontend/ ai-server/
  grep -r "AIzaSy" backend/ frontend/ ai-server/
  # 모두 결과 없어야 함
  ```

- [ ] **비밀번호가 하드코딩되어있나?**
  ```bash
  grep -rE "password|passwd|pwd|secret" backend/ | grep -v ".gradle\|.class\|.jar"
  # 주석이나 환경변수 참조만 있어야 함
  ```

---

## ✅ 배포 레벨 (Deployment Level)

### GitHub Actions
- [ ] **Secrets은 모두 등록되었나?**
  ```bash
  GitHub Settings > Secrets and variables > Actions
  
  필수:
  ☑️ BACKEND_ENV_FILE
  ☑️ AI_SERVER_ENV_FILE
  ☑️ FRONTEND_ENV_FILE
  ☑️ AWS_ACCESS_KEY_ID
  ☑️ AWS_SECRET_ACCESS_KEY
  ☑️ EC2_HOST
  ☑️ EC2_USER
  ☑️ EC2_SSH_KEY
  ```

- [ ] **Workflow에서 .env 파일 삭제?**
  ```yaml
  # deploy.yml & deploy-aws.yml 확인
  - name: Cleanup .env files for security
    run: rm -f backend/.env ai-server/.env frontend/web/.env
  ```

- [ ] **로그에 Secrets 노출 여부?**
  ```bash
  GitHub Actions 로그 검사
  "echo ${{ secrets.xxx }}" 같은 코드 없음? ✅
  ```

### Docker Compose
- [ ] **DB 비밀번호가 환경변수?**
  ```yaml
  # ✅ 올바름
  - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
  
  # ❌ 절대 금지
  - MYSQL_ROOT_PASSWORD=potato
  ```

- [ ] **env_file이 .env 참조?**
  ```yaml
  backend:
    env_file:
      - ./backend/.env  # ✅
  ```

---

## ✅ 로컬 개발 환경 (Local Development)

### 환경 설정
- [ ] **backend/.env 생성됨?**
  ```bash
  ls -la backend/.env
  # 파일 존재 + 크기 > 0
  ```

- [ ] **ai-server/.env 생성됨?**
  ```bash
  ls -la ai-server/.env
  # 파일 존재 + 크기 > 0
  cat ai-server/.env | grep "DB_NAME=syncshopper"
  # 오타 확인 (syncshoppe X, syncshopper O)
  ```

- [ ] **필수 값들이 모두 채워졌나?**
  ```bash
  # backend/.env
  grep -E "^OAUTH2_|^GOOGLE_|^KAKAO_|^JWT_" backend/.env | wc -l
  # 결과: 10개 이상
  
  # ai-server/.env
  grep -E "^GEMINI_API_KEY|^GOOGLE_CSE|^DB_" ai-server/.env | wc -l
  # 결과: 4개 이상
  ```

### 로컬 테스트
- [ ] **docker-compose 실행 성공?**
  ```bash
  docker-compose up -d
  docker-compose ps
  # 모든 컨테이너 Up 상태
  ```

- [ ] **API 헬스체크**
  ```bash
  curl http://localhost:8080/api/health
  # 200 OK
  
  curl http://localhost:8000/docs
  # FastAPI Swagger 접근 가능
  ```

- [ ] **DB 연결 확인**
  ```bash
  docker-compose exec mysql mysql -u root -ppassword -e "SHOW DATABASES;"
  # syncshopper DB 확인
  ```

---

## ✅ AWS 배포 환경 (AWS Deployment)

### 환경변수 설정
- [ ] **OAUTH2 Redirect URI가 도메인에 맞게 설정?**
  ```env
  # AWS 배포 후
  OAUTH2_REDIRECT_URI=https://capshop.com/oauth/callback
  OAUTH2_GOOGLE_REDIRECT_URI=https://api.capshop.com/login/oauth2/code/google
  OAUTH2_KAKAO_REDIRECT_URI=https://api.capshop.com/login/oauth2/code/kakao
  ```

- [ ] **CORS_ALLOWED_ORIGINS이 CloudFront 도메인?**
  ```env
  CORS_ALLOWED_ORIGINS=https://d123abc.cloudfront.net
  ```

- [ ] **JWT_SECRET이 운영용 강력한 값?**
  ```bash
  # 32자 이상 + 대소문자 + 숫자 + 특수문자
  echo -n "your-secret" | wc -c
  # 결과: 32 이상
  ```

### Google/Kakao OAuth 설정
- [ ] **Google Cloud Console에서 Redirect URI 등록?**
  ```
  Credentials > OAuth 2.0 Client IDs
  Authorized redirect URIs:
  ✅ https://api.capshop.com/login/oauth2/code/google
  ```

- [ ] **Kakao Developers에서 Redirect URI 등록?**
  ```
  My Application > 앱 설정 > 일반
  Redirect URI:
  ✅ https://api.capshop.com/login/oauth2/code/kakao
  ```

### AWS 리소스
- [ ] **EC2 보안그룹 설정?**
  ```
  Inbound Rules:
  ✅ SSH (22): 제한된 IP만
  ✅ HTTP (80): 0.0.0.0/0
  ✅ HTTPS (443): 0.0.0.0/0
  
  ❌ DB 포트(3306): 외부 노출 금지
  ❌ Redis 포트(6379): 외부 노출 금지
  ```

- [ ] **S3 버킷 정책 설정?**
  ```
  CloudFront Origin Access Identity만 허용
  Public access: Block all ✅
  ```

- [ ] **CloudFront HTTPS 활성화?**
  ```
  Viewer protocol policy: Redirect HTTP to HTTPS ✅
  ```

---

## 🚨 배포 전 최종 확인

| 항목 | 체크 | 상태 |
|------|------|------|
| 하드코딩된 IP | grep "70\.12\.60\.52" | ✅ 없음 |
| 평문 API 키 | grep -r "sk-\|AKIA\|AIzaSy" | ✅ 없음 |
| .env Git 커밋 | git log -- .env | ✅ 없음 |
| 환경변수 필수값 | backend/.env | ✅ 완성 |
| OAuth URI 설정 | Google/Kakao 콘솔 | ✅ 등록 |
| JWT Secret | 32자+ | ✅ 강함 |
| Docker compose | docker-compose ps | ✅ 실행 중 |
| API Health | curl /api/health | ✅ 200 OK |

---

## 🔄 정기 점검 (Regular Audit)

### 매월 (Monthly)
- [ ] GitHub Secrets 목록 검토
- [ ] Docker 이미지 취약점 스캔 (`trivy`)
- [ ] 로그에서 에러/경고 검토

### 분기별 (Quarterly)
- [ ] npm/pip 의존성 업데이트 + 취약점 검사
- [ ] AWS IAM 권한 검토
- [ ] 불필요한 Secrets 삭제

### 연간 (Yearly)
- [ ] OWASP Top 10 체크
- [ ] 보안 코드 리뷰
- [ ] 침투 테스트 (Penetration Test)

---

## 📋 보안 인시던트 발생 시

### 1️⃣ API 키가 Git에 노출됨
```bash
# 즉시 조치
1. GitHub에서 커밋 히스토리 삭제 (BFG Repo-Cleaner)
2. 해당 서비스(Google, Kakao, Naver)에서 키 로테이션
3. GitHub Secrets 업데이트
4. 배포 재실행
```

### 2️⃣ AWS 자격증명 노출됨
```bash
# 즉시 조치
1. AWS IAM: Access Key 비활성화
2. CloudTrail에서 의심 활동 확인
3. EC2 인스턴스 보안 검사
4. 새 Access Key 생성
5. GitHub Secrets 업데이트
```

### 3️⃣ OAuth Redirect URI 오류
```bash
# 로그인 실패 증상
Google/Kakao Developers 콘솔에서 URI 확인
→ backend/.env의 OAUTH2_*_REDIRECT_URI 수정
→ 배포 재실행
```

---

**마지막 확인**: 2026-08-13  
**담당자**: 보안팀 / DevOps 팀
