# AWS 배포 체크리스트

## ✅ 로컬 준비 단계

### 1️⃣ 환경변수 준비

- [ ] `backend/.env` 작성
  ```bash
  cp backend/.env.example backend/.env
  # 다음 항목 입력:
  # - GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET (Google Cloud Console)
  # - KAKAO_CLIENT_ID, KAKAO_CLIENT_SECRET (Kakao Developers)
  # - NAVER_CLIENT_ID, NAVER_CLIENT_SECRET (Naver Developers)
  # - SPRING_MAIL_USERNAME, SPRING_MAIL_PASSWORD (Gmail with app password)
  # - JWT_SECRET (강력한 32자+ 랜덤 문자열)
  # - CORS_ALLOWED_ORIGINS (AWS 배포 후 설정, 현재는 기본값 유지)
  ```

- [ ] `ai-server/.env` 작성
  ```bash
  cp ai-server/.env.example ai-server/.env
  # 다음 항목 입력:
  # - AI_DETECTION_PROVIDER=gemini
  # - GEMINI_API_KEY (Google AI Studio에서 생성)
  # - GOOGLE_CSE_API_KEY, GOOGLE_CSE_CX (이전에 만든 값)
  # - DB_USER, DB_PASSWORD (로컬: root/potato)
  ```

- [ ] `frontend/web/.env.production` 생성 (이미 생성함)
  ```env
  VITE_BACKEND_BASE_URL=https://api.capshop.com
  ```

### 2️⃣ 로컬 테스트

- [ ] 로컬 docker-compose 실행
  ```bash
  docker-compose up -d
  docker-compose ps  # 모든 컨테이너 실행 중 확인
  ```

- [ ] API 헬스체크
  ```bash
  curl http://localhost:8080/api/health
  curl http://localhost:8000/docs  # FastAPI Swagger
  ```

- [ ] Frontend 로컬 실행 테스트
  ```bash
  cd frontend/web
  npm install
  npm run dev  # http://localhost:5173
  ```

---

## 🌍 AWS 리소스 생성 단계

### 3️⃣ S3 버킷 생성

- [ ] S3 버킷 생성: `capshop-frontend-bucket`
- [ ] 버킷 정책 설정 (CloudFront Origin Access Identity 허용)
- [ ] 버킷 버전 관리 활성화 (선택사항)
- [ ] S3 자동 백업 설정 (선택사항)

**AWS CLI로 생성:**
```bash
aws s3api create-bucket \
  --bucket capshop-frontend-bucket \
  --region us-east-1
```

### 4️⃣ CloudFront 배포 생성

- [ ] CloudFront Distribution 생성
  - Origin: S3 버킷 `capshop-frontend-bucket`
  - Viewer protocol: Redirect HTTP to HTTPS
  - Cache behaviors: Managed-CachingOptimized
  
- [ ] CloudFront Distribution ID 복사
  ```bash
  AWS_CLOUDFRONT_DISTRIBUTION_ID=E123ABC456DEF
  ```

- [ ] CloudFront Domain Name 확인
  ```bash
  https://d123abc.cloudfront.net
  ```

### 5️⃣ EC2 인스턴스 생성

- [ ] EC2 인스턴스 시작
  - AMI: Ubuntu 22.04 LTS 또는 Amazon Linux 2
  - Instance Type: `t3.medium` (또는 t3.large)
  - Storage: 20GB 이상
  - Security Group: SSH(22), HTTP(80), HTTPS(443) 개방

- [ ] EC2 키페어 생성 및 다운로드
  ```bash
  chmod 600 capshop-key.pem
  ```

- [ ] EC2 퍼블릭 IP 확인
  ```bash
  EC2_HOST=ec2-user@XX.XX.XX.XX
  ```

- [ ] EC2에 Docker 설치 (자동화 스크립트 준비)
  ```bash
  ssh -i capshop-key.pem ec2-user@<IP>
  sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
  sudo usermod -aG docker $USER
  newgrp docker
  ```

- [ ] 프로젝트 클론
  ```bash
  cd ~ && git clone https://github.com/yourrepo/capshop.git
  ```

### 6️⃣ (선택) RDS MySQL / ElastiCache 생성

**EC2 내부 MySQL/Redis 사용 시**: 스킵

**AWS 관리 서비스 사용 시**:
- [ ] RDS MySQL 인스턴스 생성 (또는 Aurora)
- [ ] ElastiCache Redis 클러스터 생성
- [ ] Security Groups 설정 (EC2에서 접근 가능)
- [ ] RDS 엔드포인트 확인: `capshop-db.xxxxx.us-east-1.rds.amazonaws.com`
- [ ] docker-compose.prod.yml에서 호스트명 수정

---

## 🔐 GitHub Secrets 설정

### 7️⃣ GitHub Repository Secrets 추가

**Settings > Secrets and variables > Actions**

```env
# AWS 자격증명
AWS_ACCESS_KEY_ID=AKIA.....
AWS_SECRET_ACCESS_KEY=....

# Frontend (S3 + CloudFront)
AWS_S3_BUCKET_NAME=capshop-frontend-bucket
AWS_CLOUDFRONT_DISTRIBUTION_ID=E123ABC456DEF
VITE_BACKEND_BASE_URL=https://api.capshop.com

# Backend .env 파일 (전체 내용)
BACKEND_ENV_FILE=GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
KAKAO_CLIENT_ID=...
KAKAO_CLIENT_SECRET=...
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
SPRING_MAIL_USERNAME=...
SPRING_MAIL_PASSWORD=...
JWT_SECRET=...
CORS_ALLOWED_ORIGINS=https://d123abc.cloudfront.net
OAUTH2_REDIRECT_URI=https://d123abc.cloudfront.net/oauth/callback
OAUTH2_SIGNUP_REDIRECT_URI=https://d123abc.cloudfront.net/signup
OAUTH2_GOOGLE_REDIRECT_URI=https://api.capshop.com/login/oauth2/code/google
OAUTH2_KAKAO_REDIRECT_URI=https://api.capshop.com/login/oauth2/code/kakao

# AI Server .env 파일 (전체 내용)
AI_SERVER_ENV_FILE=AI_DETECTION_PROVIDER=gemini
GEMINI_API_KEY=...
GOOGLE_CSE_API_KEY=...
GOOGLE_CSE_CX=...
DB_USER=root
DB_PASSWORD=potato
DB_NAME=syncshopper
BACKEND_BASE_URL=http://backend:8080

# EC2 SSH 접속
EC2_HOST=ec2-user@XX.XX.XX.XX
EC2_USER=ec2-user
EC2_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

---

## 🚀 배포 실행

### 8️⃣ 자동 배포 (GitHub Actions)

- [ ] 로컬에서 main 브랜치로 커밋 및 푸시
  ```bash
  git add .
  git commit -m "chore: AWS 배포 설정 추가"
  git push origin main
  ```

- [ ] GitHub Actions 워크플로우 자동 실행 확인
  - **Actions** 탭 → `AWS Deployment Pipeline` 선택
  - Phase 1: Frontend (S3 업로드 + CloudFront 무효화) 확인
  - Phase 2: Backend (EC2 SSH 배포) 확인

- [ ] 배포 로그 확인
  ```
  ✅ Deploy to S3 성공
  ✅ Invalidate CloudFront Cache 성공
  ✅ Deploy to EC2 성공
  ```

### 9️⃣ 배포 후 검증

#### Frontend
```bash
# CloudFront에 접속
https://d123abc.cloudfront.net

# 개발자 도구(F12)에서 Network 탭 확인
# Response Header에 CloudFront 헤더 표시 확인: X-Cache: Hit from cloudfront
```

#### Backend API
```bash
# EC2 헬스체크
curl http://<EC2-IP>:8080/api/health

# 또는 로드 밸런서 사용 시
curl http://<ALB-DNS>/api/health

# API 문서 확인
http://<EC2-IP>:8080/swagger-ui.html
```

#### AI Server
```bash
# AI Server 상태
curl http://<EC2-IP>:8000/docs

# EC2에 SSH 접속해서 로그 확인
docker-compose -f docker-compose.prod.yml logs -f ai-server
```

#### 데이터베이스
```bash
# EC2 내부 MySQL 접속
mysql -h <EC2-IP> -u root -p -e "SELECT VERSION();"

# 또는 RDS
mysql -h <RDS-ENDPOINT> -u admin -p -e "SELECT VERSION();"
```

---

## 🔧 배포 후 설정

### 🔟 도메인 연결 (Route 53)

- [ ] Route 53 Hosted Zone 생성
- [ ] A 레코드 추가: `capshop.com` → CloudFront Domain
- [ ] CNAME 레코드 추가: `api.capshop.com` → EC2/ALB DNS
- [ ] DNS 전파 확인 (1-48시간 소요)

### 1️⃣1️⃣ SSL/TLS 인증서 (ACM)

- [ ] AWS Certificate Manager에서 인증서 요청
  - Domain: `capshop.com`, `*.capshop.com`
  - DNS 검증 또는 이메일 검증
- [ ] CloudFront에 인증서 연결
- [ ] ALB/NLB에 인증서 연결 (HTTPS 리스너)

### 1️⃣2️⃣ 모니터링 및 로깅

- [ ] CloudWatch 로그 그룹 생성
- [ ] CloudFront 로깅 활성화 (S3)
- [ ] EC2 CloudWatch 에이전트 설치
- [ ] 알람 설정 (CPU > 80%, 메모리 부족 등)

---

## ❌ 트러블슈팅

### 배포 실패 시

1. **GitHub Actions 로그 확인**
   - Actions 탭에서 해당 실행 선택
   - Phase별 에러 메시지 확인

2. **Frontend 배포 실패**
   ```bash
   # S3 버킷 정책 확인
   aws s3api get-bucket-policy --bucket capshop-frontend-bucket
   
   # CloudFront Origin Access Identity 확인
   aws cloudfront list-distributions
   ```

3. **Backend 배포 실패**
   ```bash
   # EC2 접속
   ssh -i capshop-key.pem ec2-user@<IP>
   
   # Docker 상태 확인
   docker-compose -f docker-compose.prod.yml ps
   docker-compose -f docker-compose.prod.yml logs backend
   ```

4. **CORS 에러**
   - backend/.env의 `CORS_ALLOWED_ORIGINS` 확인
   - CloudFront 도메인이 정확히 포함되어 있는지 확인

5. **OAuth2 실패**
   - Google/Kakao Developer Console에서 redirect URI 확인
   - backend/.env의 `OAUTH2_*_REDIRECT_URI` 확인

---

## 💰 비용 예상 (월단위)

| 서비스 | 예상 비용 | 비고 |
|--------|---------|------|
| S3 | $1-5 | 저장소 + 요청 |
| CloudFront | $0.085/GB | 데이터 전송 |
| EC2 (t3.medium) | $30-50 | 온디맨드 또는 스팟 |
| RDS (미사용) | $0 | EC2 내부 MySQL |
| ElastiCache (미사용) | $0 | EC2 내부 Redis |
| **합계** | **$31-55** | 저트래픽 기준 |

---

## 📝 최종 확인

배포 완료 후:

- [ ] Frontend: https://d123abc.cloudfront.net 접속 가능
- [ ] Backend: https://api.capshop.com/api/health 200 OK
- [ ] OAuth2: Google/Kakao 로그인 정상 작동
- [ ] Database: 데이터 정상 저장/조회
- [ ] Monitoring: CloudWatch 대시보드 설정 완료
- [ ] Backup: RDS/EC2 자동 백업 설정 완료

---

**마지막 업데이트**: 2026-08-13
