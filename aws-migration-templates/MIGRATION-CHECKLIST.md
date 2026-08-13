# AWS 마이그레이션 체크리스트

## Phase 0: 준비 (마이그레이션 전)

### AWS 계정 설정
- [ ] AWS 계정 생성 및 IAM 사용자 설정
- [ ] AWS CLI 설정 및 자격증명 확인
- [ ] 결제 알림 설정
- [ ] CloudTrail 활성화 (선택사항)

### 로컬 환경 준비
- [ ] 현재 로컬 환경에서 `docker compose up` 실행 확인
- [ ] 전체 기능 QA 완료 (회원가입, 로그인, 상품 검색 등)
- [ ] 현재 MySQL 데이터 백업: `mysqldump -u root -p syncshopper > backup.sql`

---

## Phase 1: AWS 인프라 구성 (2-3시간)

### VPC 및 네트워킹
- [ ] VPC 생성 또는 기존 VPC 확인
- [ ] 퍼블릭 서브넷 1개 생성 (또는 확인)
- [ ] Internet Gateway 생성 및 연결
- [ ] Route Table 설정 (0.0.0.0/0 → IGW)

### EC2 인스턴스
- [ ] EC2 인스턴스 생성 (t3.small 이상)
  - [ ] OS: Amazon Linux 2 또는 Ubuntu 22.04 LTS
  - [ ] 네트워크: VPC, 퍼블릭 서브넷
  - [ ] 보안그룹: 22(SSH), 80/443(HTTP/HTTPS), 8080/8000(선택) 포트 열기
  - [ ] Key Pair 생성 및 다운로드 (`.pem` 파일 안전하게 보관)
- [ ] Elastic IP 할당 (선택사항이나 권장)
- [ ] EC2 Tag 설정: Name=CapShop-Backend 등

### S3 및 CloudFront
- [ ] S3 버킷 생성 (이름: `capshop-frontend-{account-id}`)
  - [ ] 정적 웹 사이트 호스팅 활성화
  - [ ] 인덱스 문서: `index.html`
  - [ ] 에러 문서: `index.html` (Vue Router history 모드)
  - [ ] 블록 퍼블릭 액세스 설정 활성화 (OAC 사용)
- [ ] CloudFront 배포 생성
  - [ ] Origin: S3 (OAC 사용)
  - [ ] Viewer protocol policy: Redirect HTTP to HTTPS
  - [ ] Cache policy: CachingOptimized 또는 CachingDisabled (개발 중)
  - [ ] Origin access control (OAC) 생성 및 적용
  - [ ] 버킷 정책 자동 업데이트 확인

### 도메인 및 HTTPS
- [ ] Route53 호스팅 영역 생성 또는 기존 도메인 연결
  - [ ] A 레코드: your-domain.com → CloudFront (임시, 나중에 변경)
- [ ] ACM 인증서 생성 (us-east-1 리전 for CloudFront)
  - [ ] your-domain.com
  - [ ] *.your-domain.com (와일드카드)
  - [ ] DNS 검증
- [ ] ACM 인증서 생성 (ap-northeast-2 리전 for ALB/EC2)
  - [ ] api.your-domain.com
  - [ ] DNS 검증

### RDS (선택사항)
- [ ] RDS 서브넷 그룹 생성 (필수)
- [ ] RDS 인스턴스 생성 (mysql:8.0, db.t3.micro)
  - [ ] VPC: 기존 VPC 선택
  - [ ] 보안그룹: EC2만 3306 접근 허용
  - [ ] Multi-AZ: 프로덕션이면 Yes (비용 추가)
  - [ ] 자동 백업: 7일 이상
- [ ] RDS 엔드포인트 확인 및 메모

### ElastiCache (선택사항)
- [ ] ElastiCache 서브넷 그룹 생성
- [ ] Redis 클러스터 생성 (cache.t3.micro)
  - [ ] VPC: 기존 VPC
  - [ ] 보안그룹: EC2만 6379 접근
  - [ ] 엔드포인트 확인 및 메모

---

## Phase 2: 애플리케이션 설정 변경 (1-2시간)

### 환경변수 파일 준비
- [ ] `backend/.env` 작성 (aws-migration-templates/.env.backend.example 참조)
  - [ ] SPRING_PROFILES_ACTIVE=prod
  - [ ] OAUTH2_GOOGLE_REDIRECT_URI=https://your-domain.com/...
  - [ ] OAUTH2_KAKAO_REDIRECT_URI=https://your-domain.com/...
  - [ ] OAUTH2_REDIRECT_URI=https://your-domain.com/...
  - [ ] OAUTH2_SIGNUP_REDIRECT_URI=https://your-domain.com/...
  - [ ] DB_URL (RDS 사용 시 RDS 엔드포인트)
  - [ ] JWT_SECRET (강력한 값으로 변경)

- [ ] `ai-server/.env` 작성 (aws-migration-templates/.env.ai-server.example 참조)
  - [ ] DB_HOST (RDS 사용 시 RDS 엔드포인트)
  - [ ] BACKEND_BASE_URL=http://backend:8080

- [ ] `frontend/web/.env.production` 작성 (aws-migration-templates/.env.frontend.example 참조)
  - [ ] VITE_API_BASE_URL=https://api.your-domain.com
  - [ ] VITE_AI_BASE_URL=https://api.your-domain.com/ai

### 소스 코드 수정
- [ ] `backend/src/main/resources/application.yml` 수정
  - [ ] spring.profiles.active: ${SPRING_PROFILES_ACTIVE:local}
  - [ ] 하드코딩된 IP(70.12.60.52) 모두 제거
  - [ ] OAUTH2_GOOGLE_REDIRECT_URI: ${OAUTH2_GOOGLE_REDIRECT_URI} (기본값 없음)
  - [ ] OAUTH2_KAKAO_REDIRECT_URI: ${OAUTH2_KAKAO_REDIRECT_URI} (기본값 없음)
  - [ ] OAUTH2_REDIRECT_URI: ${OAUTH2_REDIRECT_URI} (기본값 없음)
  - [ ] OAUTH2_SIGNUP_REDIRECT_URI: ${OAUTH2_SIGNUP_REDIRECT_URI} (기본값 없음)

- [ ] `docker-compose.prod.yml` 생성 (aws-migration-templates/docker-compose.prod.yml 참조)
  - [ ] frontend 서비스 제거
  - [ ] mysql/redis 엔드포인트 환경변수로 변경 가능하게 설정

- [ ] 로컬 `docker-compose.yml` 유지 (개발용)

### GitHub Actions CI/CD 설정
- [ ] `BACKEND_ENV_FILE` Secret 추가
- [ ] `AI_SERVER_ENV_FILE` Secret 추가
- [ ] `FRONTEND_ENV_FILE` Secret 추가
- [ ] `AWS_ACCESS_KEY_ID` Secret 추가 (또는 OIDC 설정)
- [ ] `AWS_SECRET_ACCESS_KEY` Secret 추가 (또는 OIDC 설정)
- [ ] `S3_BUCKET_NAME` Secret 추가
- [ ] `CLOUDFRONT_DISTRIBUTION_ID` Secret 추가
- [ ] `EC2_HOST` Secret 추가 (EC2 Elastic IP 또는 도메인)
- [ ] `EC2_USERNAME` Secret 추가 (보통 ec2-user)
- [ ] `EC2_SSH_KEY` Secret 추가 (PEM 파일 전체 내용)

- [ ] `.github/workflows/deploy-aws.yml` 생성 (aws-migration-templates/deploy-aws.yml 참조)
  - [ ] 백엔드 Maven 빌드 스텝
  - [ ] 프론트엔드 npm 빌드 스텝
  - [ ] S3 배포 스텝
  - [ ] CloudFront 캐시 무효화 스텝
  - [ ] EC2 SSH 배포 스텝

---

## Phase 3: EC2 배포 (1시간)

### EC2 초기화
- [ ] EC2 인스턴스 접속 확인
  ```bash
  ssh -i your-key.pem ec2-user@your-ec2-public-ip
  ```

- [ ] 초기 설정 스크립트 실행 (aws-migration-templates/ec2-user-data.sh)
  - [ ] Docker 설치 확인: `docker --version`
  - [ ] Docker Compose 설치 확인: `docker-compose --version`
  - [ ] 시간대 확인: `date`

- [ ] 프로젝트 클론
  ```bash
  cd /home/ec2-user
  git clone https://github.com/YOUR_USERNAME/CapShop.git
  cd CapShop
  ```

- [ ] 환경변수 파일 배포
  - [ ] `backend/.env` 파일 생성 (권한 600)
  - [ ] `ai-server/.env` 파일 생성 (권한 600)
  - [ ] `docker-compose.prod.yml` 확인

### 데이터베이스 마이그레이션 (RDS 선택 시)
- [ ] 로컬에서 백업 다운로드: `mysqldump -u root -p syncshopper > backup.sql`
- [ ] EC2로 백업 파일 전송: `scp -i key.pem backup.sql ec2-user@ec2-ip:~`
- [ ] EC2에서 RDS로 복원:
  ```bash
  mysql -h your-rds-endpoint.rds.amazonaws.com -u admin -p syncshopper < backup.sql
  ```
- [ ] 테이블 확인:
  ```bash
  mysql -h your-rds-endpoint.rds.amazonaws.com -u admin -p -e "USE syncshopper; SHOW TABLES;"
  ```

### 컨테이너 실행
- [ ] docker-compose 실행:
  ```bash
  docker compose -f docker-compose.prod.yml up -d --build
  ```

- [ ] 컨테이너 상태 확인:
  ```bash
  docker compose -f docker-compose.prod.yml ps
  ```

- [ ] 로그 확인:
  ```bash
  docker compose -f docker-compose.prod.yml logs -f backend
  docker compose -f docker-compose.prod.yml logs -f ai-server
  ```

---

## Phase 4: 외부 서비스 설정 (1시간)

### Google OAuth
- [ ] Google Cloud Console 접속
- [ ] 프로젝트 선택 (또는 신규 생성)
- [ ] "APIs & Services" → "Credentials"
- [ ] OAuth 2.0 클라이언트 ID 선택
- [ ] Authorized redirect URIs에 새 도메인 추가:
  - [ ] `https://your-domain.com/login/oauth2/code/google`
  - [ ] (테스트 완료 후 기존 IP는 제거)
- [ ] 저장

### Kakao Developers
- [ ] Kakao Developers 콘솔 접속
- [ ] 애플리케이션 선택
- [ ] "카카오 로그인" 선택
- [ ] Redirect URI 수정:
  - [ ] `https://your-domain.com/login/oauth2/code/kakao`
  - [ ] (테스트 완료 후 기존 IP는 제거)
- [ ] 저장

### Naver Developers
- [ ] Naver Developers 콘솔 접속
- [ ] 애플리케이션 선택
- [ ] API 설정 → 서비스 URL 수정 (있다면)
  - [ ] `https://your-domain.com`
- [ ] 저장

---

## Phase 5: QA 및 검증 (1시간)

### 백엔드 기본 동작
- [ ] EC2에서 포트 열려 있는지 확인:
  ```bash
  curl http://localhost:8080/health (또는 Swagger 엔드포인트)
  ```

- [ ] AI 서버 동작 확인:
  ```bash
  curl http://localhost:8000/docs
  ```

### 프론트엔드
- [ ] S3 + CloudFront에서 프론트엔드 로드
  ```
  https://your-domain.com
  ```
- [ ] 홈페이지 로드 확인
- [ ] 콘솔 에러 없는지 확인 (F12)

### 기본 기능 테스트
- [ ] 회원가입
  - [ ] Google OAuth 로그인
  - [ ] Kakao OAuth 로그인
  - [ ] Naver OAuth 로그인 (있다면)
- [ ] 상품 검색
- [ ] 이미지 업로드
- [ ] AI 이미지 분석 요청
- [ ] 캐시 동작 (반복 요청 빠른 응답)

### 성능 및 보안
- [ ] HTTPS 인증서 유효성 확인
- [ ] 보안그룹 설정 재확인 (필요 없는 포트는 닫기)
- [ ] .env 파일 권한 확인: `ls -la backend/.env` (600이어야 함)
- [ ] 로그에 민감한 정보 노출 없는지 확인

---

## Phase 6: DNS 컷오버 (1시간)

### Route53 설정
- [ ] Route53에서 기존 DNS 레코드 백업
- [ ] A 레코드 수정
  - [ ] `your-domain.com` → CloudFront 배포 (ALIAS)
  - [ ] `api.your-domain.com` → EC2 또는 ALB (A record)
- [ ] TTL 설정: 300초 (빠른 전환을 위해 낮춤)

### DNS 전환
- [ ] 새 설정이 반영될 때까지 기다리기 (보통 5-30분)
- [ ] DNS 확인:
  ```bash
  nslookup your-domain.com
  dig your-domain.com
  ```

### 모니터링
- [ ] 실시간 모니터링 (24시간):
  - [ ] 에러 로그 확인
  - [ ] 트래픽 정상 여부
  - [ ] 외부 서비스(OAuth, Naver API) 동작 확인
- [ ] CloudWatch Logs 모니터링
- [ ] EC2 CPU/메모리 사용률 확인

---

## Phase 7: 정리 및 최적화

### 이전 인프라 정리
- [ ] 구 self-hosted runner 환경 백업 (1주일 유지)
- [ ] 테스트 완료 후 구 인프라 폐기
  - [ ] 로컬 MySQL 데이터 백업 (최종)
  - [ ] 로컬 docker-compose 중지

### 비용 최적화
- [ ] CloudFront 캐싱 정책 조정
- [ ] EC2 인스턴스 크기 재검토 (트래픽 패턴 확인 후)
- [ ] RDS 백업 보존 기간 조정
- [ ] 비용 알림 설정

### 운영 개선
- [ ] CloudWatch Alarms 설정
  - [ ] EC2 CPU > 80%
  - [ ] 에러 로그 기준
  - [ ] RDS CPU > 75%
- [ ] SNS 알림 구성 (이메일, Slack 등)
- [ ] 정기 백업 스케줄 확인
- [ ] 재해 복구 계획 수립

---

## 문제 해결 (Troubleshooting)

### OAuth 로그인 실패
- [ ] OAuth Redirect URI가 정확한지 확인
- [ ] 외부 서비스 콘솔에서 URL 등록 여부 확인
- [ ] 브라우저 개발자 도구에서 리다이렉트 URL 확인

### 데이터베이스 연결 실패
- [ ] RDS 보안그룹에서 EC2가 3306 포트 접근 가능한지 확인
- [ ] RDS 엔드포인트가 정확한지 확인
- [ ] DB 사용자명/비밀번호 정확성 확인

### S3/CloudFront 프론트엔드 로드 실패
- [ ] S3 버킷 정책이 OAC를 허용하는지 확인
- [ ] CloudFront Origin path 설정 확인
- [ ] 404 → index.html 라우팅 설정 확인

### 컨테이너 시작 실패
- [ ] 로그 확인: `docker compose logs`
- [ ] 환경변수가 .env에 올바르게 설정되었는지 확인
- [ ] 포트 충돌 확인: `netstat -an | grep LISTEN`

---

## 최종 확인

- [ ] 모든 단계 완료
- [ ] 팀원들에게 새 URL 공유
- [ ] 문서 업데이트 (README, 배포 가이드 등)
- [ ] 마이그레이션 완료 보고
