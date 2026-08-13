# AWS 마이그레이션 템플릿 및 가이드

## 개요

이 디렉토리는 CapShop 프로젝트를 Docker Compose 로컬 환경에서 **AWS 클라우드로 마이그레이션**하기 위한 모든 필요한 파일과 가이드를 포함합니다.

## 파일 구조

```
aws-migration-templates/
├── README.md                    # 이 파일
├── MIGRATION-CHECKLIST.md       # 단계별 마이그레이션 체크리스트
├── .env.backend.example         # Backend 환경변수 템플릿
├── .env.ai-server.example       # AI Server 환경변수 템플릿
├── .env.frontend.example        # Frontend 환경변수 템플릿
├── docker-compose.prod.yml      # AWS 프로덕션용 docker-compose
├── application.yml.patch        # application.yml 수정 가이드
├── ec2-user-data.sh             # EC2 부팅 스크립트
└── deploy-aws.yml               # GitHub Actions 배포 워크플로우
```

## 사용 순서

### 1단계: 마이그레이션 계획 수립

1. 상위 디렉토리에서 **AWS 마이그레이션 가이드** HTML 문서 읽기
2. 필수/선택사항 구분 후 로드맵 작성
3. **MIGRATION-CHECKLIST.md** 프린트 또는 PDF로 저장

### 2단계: 애플리케이션 설정 변경

1. **application.yml.patch** 참조하여 `backend/src/main/resources/application.yml` 수정
   - 하드코딩된 IP(70.12.60.52) 제거
   - 환경변수로 OAuth Redirect URI 변경

2. 환경변수 파일 작성
   - `.env.backend.example` → `backend/.env` (템플릿 사용)
   - `.env.ai-server.example` → `ai-server/.env` (템플릿 사용)
   - `.env.frontend.example` → `frontend/web/.env.production` (템플릿 사용)

3. **docker-compose.prod.yml** 검토 및 프로젝트 루트에 복사

### 3단계: AWS 인프라 구성

1. AWS 콘솔에서 다음을 생성:
   - EC2 인스턴스 (t3.small 이상)
   - S3 버킷 (정적 웹 호스팅 활성화)
   - CloudFront 배포 (Origin = S3)
   - Route53 설정 (선택)
   - RDS MySQL (선택)
   - ElastiCache Redis (선택)

2. **ec2-user-data.sh** 참고하여 EC2 초기화
   - 스크립트를 EC2 "사용자 데이터"에 복사 붙여넣기
   - 또는 EC2 접속 후 수동 실행

### 4단계: CI/CD 설정

1. GitHub 저장소에서:
   - Settings → Secrets and variables → Actions
   - 다음 Secrets 추가:
     - `BACKEND_ENV_FILE`: backend/.env 전체 내용
     - `AI_SERVER_ENV_FILE`: ai-server/.env 전체 내용
     - `FRONTEND_ENV_FILE`: frontend/web/.env.production 전체 내용
     - `AWS_ACCESS_KEY_ID`: AWS 액세스 키
     - `AWS_SECRET_ACCESS_KEY`: AWS 시크릿 키
     - `S3_BUCKET_NAME`: S3 버킷 이름
     - `CLOUDFRONT_DISTRIBUTION_ID`: CloudFront 배포 ID
     - `EC2_HOST`: EC2 Elastic IP 또는 도메인
     - `EC2_USERNAME`: ec2-user (또는 ubuntu)
     - `EC2_SSH_KEY`: EC2 프라이빗 키 (PEM 파일 내용)

2. **.github/workflows** 디렉토리에 **deploy-aws.yml** 복사
   - 기존 deploy.yml 대체 또는 이름 변경

### 5단계: 테스트 및 배포

1. GitHub에 코드 푸시
   - GitHub Actions이 자동으로 배포 시작

2. 또는 수동 배포:
   ```bash
   # EC2 접속
   ssh -i your-key.pem ec2-user@your-ec2-ip
   
   # 프로젝트 업데이트
   cd /home/ec2-user/CapShop
   git pull origin main
   
   # 환경변수 배포 (GitHub Secrets에서 복사)
   cat > backend/.env << 'EOF'
   <paste content from BACKEND_ENV_FILE secret>
   EOF
   chmod 600 backend/.env
   
   cat > ai-server/.env << 'EOF'
   <paste content from AI_SERVER_ENV_FILE secret>
   EOF
   chmod 600 ai-server/.env
   
   # 배포
   docker compose -f docker-compose.prod.yml up -d --build
   ```

3. QA
   - 프론트엔드: `https://your-domain.com`
   - OAuth 로그인 테스트
   - 상품 검색, 이미지 분석 테스트

4. DNS 전환 (Route53)
   - 도메인을 새 CloudFront/EC2로 지정

---

## 주요 환경변수 설정

### Backend (.env 또는 docker compose -e)

```bash
SPRING_PROFILES_ACTIVE=prod
OAUTH2_GOOGLE_REDIRECT_URI=https://your-domain.com/login/oauth2/code/google
OAUTH2_KAKAO_REDIRECT_URI=https://your-domain.com/login/oauth2/code/kakao
OAUTH2_REDIRECT_URI=https://your-domain.com/oauth/callback
OAUTH2_SIGNUP_REDIRECT_URI=https://your-domain.com/signup

# RDS 사용 시
DB_URL=jdbc:mysql://your-rds-endpoint:3306/syncshopper?serverTimezone=Asia/Seoul
DB_USERNAME=admin
DB_PASSWORD=your-strong-password
```

### AI Server

```bash
AI_DETECTION_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CSE_API_KEY=your-google-cse-key
GOOGLE_CSE_CX=your-cse-cx

DB_HOST=mysql (또는 RDS 엔드포인트)
BACKEND_BASE_URL=http://backend:8080
```

### Frontend

```bash
VITE_API_BASE_URL=https://api.your-domain.com
VITE_AI_BASE_URL=https://api.your-domain.com/ai
```

---

## 선택사항별 가이드

### RDS로 MySQL 마이그레이션

1. AWS RDS에서 MySQL 인스턴스 생성
2. 로컬에서 백업:
   ```bash
   mysqldump -u root -p syncshopper > backup.sql
   ```
3. RDS로 복원:
   ```bash
   mysql -h your-rds-endpoint.rds.amazonaws.com -u admin -p syncshopper < backup.sql
   ```
4. Backend `DB_URL` 환경변수 변경 (application-prod.yml이 이미 대응)

### ElastiCache로 Redis 마이그레이션

1. AWS ElastiCache에서 Redis 클러스터 생성
2. Backend 환경변수 변경:
   ```bash
   SPRING_DATA_REDIS_HOST=your-elasticache-endpoint
   ```

### ECS로 마이그레이션 (고급)

1. ECR 리포지토리 생성
2. Docker 이미지 ECR에 푸시
3. ECS Task Definition 작성
4. ECS Service 생성
5. ALB 설정

---

## 문제 해결

### OAuth 로그인 실패

**원인**: Redirect URI가 외부 서비스 콘솔에 등록되지 않음

**해결**:
1. Google Cloud Console / Kakao Developers 콘솔 확인
2. 새 도메인의 Redirect URI 추가
   - `https://your-domain.com/login/oauth2/code/google`
   - `https://your-domain.com/login/oauth2/code/kakao`

### 프론트엔드 404 오류

**원인**: CloudFront 에러 페이지 설정 미흡

**해결**:
1. CloudFront 배포 → Error Pages
2. 404 오류 → Custom error page: `/index.html` (선택사항)
3. 응답 코드: 200으로 설정

### RDS 연결 실패

**원인**: 보안그룹 설정

**해결**:
1. RDS 보안그룹에 EC2 인스턴스의 보안그룹 추가 (Inbound 3306)
2. RDS 엔드포인트, 사용자명, 비밀번호 확인

### Docker 컨테이너 실행 실패

**디버깅**:
```bash
# 로그 확인
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs ai-server

# 환경변수 확인
docker compose -f docker-compose.prod.yml config

# 컨테이너 상태 확인
docker compose -f docker-compose.prod.yml ps
```

---

## 보안 체크리스트

- [ ] EC2 .env 파일 권한: `chmod 600 .env`
- [ ] GitHub Secrets에 민감한 정보 저장 (절대 리포지토리에 커밋 금지)
- [ ] AWS IAM 사용자에 최소 권한만 부여 (S3, CloudFront, EC2 배포)
- [ ] RDS 비밀번호 강력한 값으로 설정
- [ ] EC2 보안그룹에 필요한 포트만 개방
- [ ] SSH 키(PEM 파일)는 별도로 안전하게 보관

---

## 비용 추정 (월간, AWS 무료 티어 제외)

| 리소스 | 예상 비용 |
|--------|---------|
| EC2 t3.small (732시간) | $10-15 |
| S3 스토리지 + CloudFront | $5-10 |
| RDS db.t3.micro (다중 AZ) | $40-50 |
| ElastiCache cache.t3.micro | $20-30 |
| NAT Gateway (선택) | $32 |
| **합계** | **$100-200 (기본)** |

프로덕션 환경의 경우 인스턴스 크기, 트래픽, 백업에 따라 비용이 증가할 수 있습니다.

---

## 추가 리소스

- [AWS Migration Accelerator Program](https://aws.amazon.com/migration/)
- [Docker Compose Best Practices](https://docs.docker.com/compose/production/)
- [AWS Architecture Center](https://aws.amazon.com/architecture/)

---

## 문의 및 피드백

이 가이드에 대해 질문이 있거나 개선사항이 있으면 이슈를 생성해주세요.

마이그레이션 완료 후 이 디렉토리는 이력 관리 목적으로 보관할 수 있습니다.
