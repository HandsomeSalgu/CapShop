# AWS 배포 가이드

이 문서는 CapShop 프로젝트를 AWS에 배포하는 절차를 설명합니다.

## 🏗️ 아키텍처 구성

```
┌─────────────────────────────────────────────────────────┐
│ Internet                                                │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────┴──────────┐
          │                      │
    ┌─────▼──────┐      ┌──────▼──────┐
    │  CloudFront│      │ ALB/NLB     │
    │  (S3)      │      │ (EC2)       │
    └─────┬──────┘      └──────┬──────┘
          │                      │
          │              ┌───────┴──────────┐
          │              │                  │
    ┌─────▼──────┐  ┌────▼─────┐  ┌──────▼──┐
    │  S3 Bucket │  │ Backend  │  │ AI      │
    │  (Static)  │  │ (Spring) │  │ Server  │
    └────────────┘  │          │  │ (Fast   │
                    │          │  │  API)   │
                    └────┬─────┘  └──────┬──┘
                         │               │
                    ┌────▼───────────────▼───┐
                    │    Docker Compose      │
                    │ MySQL │ Redis │ (AWS  │
                    │ EC2 내부 또는 RDS/    │
                    │ ElastiCache)           │
                    └────────────────────────┘
```

## 📋 사전 준비 (로컬)

### 1. AWS 계정 및 CLI 설정
```bash
# AWS CLI 설치
# https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

aws configure
# Access Key ID: (YOUR_ACCESS_KEY)
# Secret Access Key: (YOUR_SECRET_KEY)
# Default region: us-east-1
# Default output format: json
```

### 2. GitHub Secrets 설정

다음 Secrets을 GitHub 리포지토리 Settings > Secrets and variables에 추가하세요:

```env
# AWS 자격증명
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key

# Frontend (S3 + CloudFront)
AWS_S3_BUCKET_NAME=capshop-frontend-bucket
AWS_CLOUDFRONT_DISTRIBUTION_ID=E123ABC456DEF

# Frontend 빌드
VITE_BACKEND_BASE_URL=https://api.capshop.com

# Backend 환경변수 (멀티라인 - 쌍따옴표 제거 후 복사)
BACKEND_ENV_FILE=GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
... (ai-server/.env.example 참고)

# AI Server 환경변수
AI_SERVER_ENV_FILE=AI_DETECTION_PROVIDER=gemini
GEMINI_API_KEY=...
... (ai-server/.env.example 참고)

# EC2 배포
EC2_HOST=ec2-user@your-ec2-public-ip.compute.amazonaws.com
EC2_USER=ec2-user
EC2_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

---

## 🚀 AWS 리소스 생성 (콘솔 또는 CLI)

### 1. S3 버킷 (Frontend 정적 파일)

**AWS Management Console:**
1. S3 > Create bucket
2. Bucket name: `capshop-frontend-bucket`
3. Region: `us-east-1`
4. Block Public Access: 체크 해제 (CloudFront가 접근하도록)
5. Create

**또는 CLI:**
```bash
aws s3api create-bucket \
  --bucket capshop-frontend-bucket \
  --region us-east-1
```

**버킷 정책 (CloudFront 접근 허용):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity/XXXXX"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::capshop-frontend-bucket/*"
    }
  ]
}
```

### 2. CloudFront 배포 (CDN)

**AWS Management Console:**
1. CloudFront > Create distribution
2. Origin > S3 bucket: `capshop-frontend-bucket`
3. Origin access identity: Create new
4. Viewer protocol policy: Redirect HTTP to HTTPS
5. Allowed HTTP methods: GET, HEAD, OPTIONS
6. Cache policy: Managed-CachingOptimized
7. Create

**배포 완료 후:**
- Distribution ID 복사 (예: `E123ABC456DEF`)
- Domain name 복사 (예: `d123abc.cloudfront.net`)

### 3. EC2 인스턴스 (Backend + AI Server)

**AWS Management Console:**
1. EC2 > Instances > Launch instances
2. AMI: Ubuntu 22.04 LTS (또는 최신)
3. Instance type: `t3.medium` 이상 (4GB RAM 권장)
4. Key pair: 새로 생성 (예: `capshop-key.pem`) → 다운로드
5. Network settings:
   - Allow SSH from: `0.0.0.0/0` (또는 자신의 IP)
   - Allow HTTP/HTTPS: 체크
6. Storage: 20GB 이상
7. Launch

**인스턴스 설정:**
```bash
# EC2 접속
ssh -i capshop-key.pem ec2-user@<EC2-PUBLIC-IP>

# Docker 설치
sudo apt update
sudo apt install docker.io docker-compose-plugin -y
sudo usermod -aG docker $USER
newgrp docker

# 프로젝트 클론
cd ~
git clone https://github.com/your-repo/capshop.git
cd capshop

# 시작 스크립트 생성 (자동 재시작)
sudo systemctl enable docker
```

### 4. (선택) RDS MySQL + ElastiCache Redis

**RDS MySQL:**
- Engine: MySQL 8.0
- Instance class: `db.t3.micro` 이상
- Storage: 20GB
- Security group: EC2에서 접근 가능 (포트 3306)

**ElastiCache Redis:**
- Engine: Redis 7
- Node type: `cache.t3.micro`
- Security group: EC2에서 접근 가능 (포트 6379)

---

## 🔧 로컬 환경변수 설정

### backend/.env (로컬 테스트 시)
```bash
cp backend/.env.example backend/.env
# 편집: GOOGLE_CLIENT_ID, KAKAO_CLIENT_ID, NAVER_*, JWT_SECRET 등 입력
```

### ai-server/.env (로컬 테스트 시)
```bash
cp ai-server/.env.example ai-server/.env
# 편집: AI_DETECTION_PROVIDER=gemini, GEMINI_API_KEY 등 입력
```

### 로컬 docker-compose 테스트
```bash
# 로컬: 기존 docker-compose.yml 사용
docker-compose up -d

# AWS 용도 확인 (테스트 후)
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📤 배포 실행

### GitHub Actions 자동 배포

1. **로컬에서 main 브랜치로 푸시**
```bash
git push origin main
```

2. **GitHub Actions 자동 실행**
   - `.github/workflows/deploy-aws.yml` 워크플로우 실행
   - Phase 1: Frontend 빌드 → S3 업로드 → CloudFront 무효화
   - Phase 2: EC2에 SSH 연결 → git pull → docker-compose up

3. **배포 상태 확인**
   - GitHub > Actions 탭에서 실시간 로그 확인

### 수동 배포 (긴급 상황)

**Frontend 수동 배포:**
```bash
cd frontend/web
npm install
npm run build
aws s3 sync dist s3://capshop-frontend-bucket --delete
aws cloudfront create-invalidation --distribution-id E123ABC456DEF --paths "/*"
```

**Backend 수동 배포:**
```bash
ssh -i capshop-key.pem ec2-user@<EC2-IP>
cd ~/capshop
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

---

## ✅ 배포 후 확인

### Frontend
```bash
# CloudFront URL에 접속
https://d123abc.cloudfront.net

# S3 객체 확인
aws s3 ls s3://capshop-frontend-bucket
```

### Backend API
```bash
# EC2 API 엔드포인트 확인
curl http://<EC2-PUBLIC-IP>:8080/api/health
curl https://<ALB-DNS>/api/health  # ALB 사용 시

# 로그 확인
ssh -i capshop-key.pem ec2-user@<EC2-IP>
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 데이터베이스 연결
```bash
# EC2 MySQL 접속
mysql -h <EC2-IP> -u root -p syncshopper

# 또는 RDS MySQL
mysql -h <RDS-ENDPOINT> -u admin -p syncshopper
```

---

## 🛡️ 보안 체크리스트

- [ ] **JWT_SECRET** 강력한 랜덤 문자열로 설정 (최소 32자)
- [ ] **OAuth2 redirect URI** 실제 CloudFront/ALB 주소로 설정
- [ ] **CORS_ALLOWED_ORIGINS** CloudFront 도메인만 허용
- [ ] **EC2 보안그룹**: SSH는 제한된 IP, HTTP/HTTPS는 개방
- [ ] **S3 버킷 정책**: CloudFront Origin Access Identity만 허용
- [ ] **RDS/ElastiCache**: EC2 보안그룹에서만 접근 가능
- [ ] **SSL/TLS 인증서**: ACM에서 자동 관리 (CloudFront/ALB)
- [ ] **환경변수**: GitHub Secrets 암호화 저장

---

## 🐛 트러블슈팅

### CloudFront가 403 Forbidden 반환
```bash
# S3 버킷 정책 확인
aws s3api get-bucket-policy --bucket capshop-frontend-bucket

# Origin Access Identity 확인
aws cloudfront list-cloud-front-origins-by-distribution-id --id E123ABC456DEF
```

### EC2 Docker Compose 실행 실패
```bash
# EC2에 접속해서 로그 확인
docker-compose -f docker-compose.prod.yml logs
docker-compose ps

# MySQL 연결 확인
docker-compose exec mysql mysql -u root -ppassword -e "SHOW DATABASES;"
```

### CORS 에러
```
Access-Control-Allow-Origin 헤더 확인
→ backend/.env의 CORS_ALLOWED_ORIGINS이 CloudFront 도메인을 포함하는지 확인
```

### OAuth2 Redirect 실패
```
→ Google/Kakao OAuth 콘솔에서 redirect URI 확인
→ backend/.env의 OAUTH2_*_REDIRECT_URI가 정확한지 확인
```

---

## 💡 비용 절감 팁

- **S3**: 요청당 과금 → CloudFront 캐시 설정으로 S3 요청 최소화
- **EC2**: t3.medium 스팟 인스턴스 사용 (70% 할인)
- **Data Transfer**: CloudFront는 us-east-1과의 데이터 전송이 무료
- **RDS**: 개발 환경에서 EC2 내부 MySQL로 시작, 필요시 마이그레이션

---

## 📚 참고 문서

- [AWS CloudFront 배포 가이드](https://docs.aws.amazon.com/cloudfront/latest/developerguide/GettingStarted.html)
- [AWS S3 정적 웹사이트 호스팅](https://docs.aws.amazon.com/s3/latest/userguide/WebsiteHosting.html)
- [AWS EC2 사용자 가이드](https://docs.aws.amazon.com/ec2/index.html)
- [GitHub Actions AWS 배포](https://docs.github.com/en/actions/deployment/deploying-to-your-cloud-provider/deploying-to-amazon-elastic-container-service)

---

**마지막 수정**: 2026-08-13
