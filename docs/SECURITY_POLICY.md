# 🔐 보안 정책 (Security Policy)

CapShop 프로젝트의 보안 관리 규칙과 모범 사례를 정의합니다.

---

## 1️⃣ 환경변수 관리

### ✅ 필수 사항

#### **Local 개발 환경**
```bash
# 1. .env 파일은 절대 Git에 커밋하지 않기
.env
.env.local
.env.*.local
# → .gitignore에 이미 등록됨

# 2. .env.example만 Git에 유지 (팀원 온보딩용)
.env.example  # ✅ Git에 커밋

# 3. 로컬 개발 시작
cp backend/.env.example backend/.env
# → 실제 키값 입력
```

#### **CI/CD 배포**
```bash
# GitHub Actions Secrets에만 저장
GitHub Repository Settings > Secrets and variables > Actions

# 배포 후 .env 파일 자동 삭제
# → deploy.yml & deploy-aws.yml에서 처리
```

#### **운영(Production) 환경**
```bash
# Option 1: AWS Secrets Manager (권장)
# → Spring Boot: @ConfigurationProperties + AWS SDK
# → FastAPI: boto3로 읽음

# Option 2: EC2 Parameter Store
# → AWS Systems Manager Parameter Store
# → EC2 IAM Role로 권한 제어

# Option 3: .env 파일 (불가피한 경우만)
# → 파일 권한: chmod 600 .env
# → 파일 소유: root 또는 애플리케이션 유저만 읽기 가능
```

---

## 2️⃣ 민감 정보 분류

### 🔴 **절대 평문으로 저장하면 안 되는 것**

| 항목 | 현재 상태 | 수정 후 |
|------|---------|--------|
| **JWT_SECRET** | ✅ 환경변수 | ✅ AWS Secrets Manager |
| **OAuth2 Keys** | ✅ 환경변수 | ✅ AWS Secrets Manager |
| **DB 비밀번호** | ✅ 환경변수 | ✅ AWS Secrets Manager |
| **Gmail/API 키** | ✅ 환경변수 | ✅ AWS Secrets Manager |
| **Gemini/Google API** | ✅ 환경변수 | ✅ AWS Secrets Manager |

### 🟡 **환경변수로도 괜찮은 것**

| 항목 | 관리 방식 |
|------|---------|
| **DB 호스트명** | 환경변수 (평문 OK) |
| **Redis 호스트명** | 환경변수 (평문 OK) |
| **API 엔드포인트 URL** | 환경변수 (평문 OK) |
| **포트 번호** | 환경변수 (평문 OK) |
| **로그 레벨** | 환경변수 (평문 OK) |

---

## 3️⃣ GitHub Secrets 설정 규칙

### 명명 규칙
```bash
# 서비스별 구분
BACKEND_*      # Backend 관련
AI_SERVER_*    # AI 서버 관련
AWS_*          # AWS 자격증명
DATABASE_*     # DB 설정
```

### Secret 목록 (필수)

```env
# ========== AWS Credentials ==========
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY

# ========== Backend Environment ==========
BACKEND_ENV_FILE      # 전체 backend/.env 파일 내용

# ========== AI Server Environment ==========
AI_SERVER_ENV_FILE    # 전체 ai-server/.env 파일 내용

# ========== Frontend Environment ==========
FRONTEND_ENV_FILE     # 전체 frontend/.env 파일 내용

# ========== EC2 Deployment ==========
EC2_HOST              # ec2-user@XX.XX.XX.XX
EC2_USER              # ec2-user
EC2_SSH_KEY           # -----BEGIN OPENSSH PRIVATE KEY-----...

# ========== AWS Resources ==========
AWS_S3_BUCKET_NAME
AWS_CLOUDFRONT_DISTRIBUTION_ID
```

### ⚠️ Secrets 안전 사용

```bash
# ❌ 절대 하지 말 것
- Secrets를 로그에 출력
- Secrets를 버전 관리에 커밋
- Secrets를 Slack/이메일로 공유
- 공개 리포지토리에 Secrets 저장

# ✅ 항상 할 것
- Secrets를 환경변수로만 주입
- CI/CD 배포 후 .env 파일 삭제
- 정기적으로 (분기별) Secrets 로테이션
- 퇴사자 Secrets 삭제
```

---

## 4️⃣ 하드코딩 방지 규칙

### ❌ 절대 하드코딩하면 안 되는 것

```java
// ❌ 나쁜 예
private static final String JWT_SECRET = "my-secret-key";
String db_password = "password123";
String api_key = "sk-abc123";

// ✅ 좋은 예
@Value("${app.jwt.secret}")
private String jwtSecret;

@Value("${DB_PASSWORD}")
private String dbPassword;

@Value("${GEMINI_API_KEY}")
private String apiKey;
```

### ✅ 체크리스트

- [ ] 로컬 IP 주소가 코드에 박혀 있는가?
- [ ] API 키가 상수(const/final)로 정의되어 있는가?
- [ ] 비밀번호가 기본값으로 설정되어 있는가?
- [ ] URL/도메인이 여러 환경에서 다른가?

---

## 5️⃣ Git 커밋 전 확인 사항

```bash
# 커밋 전 필수 체크
git diff HEAD  # 변경사항 검토

# 민감 정보 검사
grep -r "password\s*=" backend/
grep -r "api.key\|API_KEY" .
grep -r "secret\|SECRET" backend/
grep -r "70\.12\.60\.52" .      # 하드코딩 IP
grep -r "\.env" . | grep -v example  # .env 파일이 있는가?

# 안전한 커밋
git add .
git commit -m "feat: 기능명"
git push
```

---

## 6️⃣ 배포 환경별 권장 사항

### Local 개발
```bash
# ✅ 안전한 방식
MYSQL_ROOT_PASSWORD=local_dev_password_only
GEMINI_API_KEY=test-key-for-local-only
JWT_SECRET=dev-secret-12345

# ⚠️ 운영 환경 키 절대 사용 금지
```

### Staging (테스트)
```bash
# ✅ 권장
AWS_REGION=us-east-1
ENVIRONMENT=staging
USE_MOCK_AI=false

# GitHub Secrets 사용
BACKEND_ENV_FILE=staging-specific-vars
```

### Production (운영)
```bash
# ✅ 필수
AWS Secrets Manager 사용
AWS IAM Role로 권한 제어
CloudWatch Logs 활성화
MFA 활성화

# ❌ 절대 금지
평문 .env 파일 사용
공개 리포지토리에 Secrets 저장
개발자 로컬 키 사용
```

---

## 7️⃣ 보안 모니터링

### GitHub 설정

```bash
# Repository Settings > Security
✅ Dependabot alerts 활성화
✅ Secret scanning 활성화
✅ Require status checks to pass before merging
```

### AWS 설정

```bash
# CloudTrail: API 접근 로그
# CloudWatch: 애플리케이션 로그
# GuardDuty: 이상 탐지
# VPC Flow Logs: 네트워크 모니터링
```

---

## 8️⃣ 보안 인시던트 대응

### 🚨 만약 API 키가 Git에 커밋되었다면?

```bash
# 1. GitHub History에서 제거 (BFG Repo-Cleaner 사용)
git clone --mirror https://github.com/yourrepo/capshop.git
bfg --delete-files FILENAME repo.git
cd repo.git && git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --mirror

# 2. 즉시 키 로테이션
# → Google Cloud Console: 기존 키 삭제, 새 키 생성
# → Kakao/Naver: 키 재발급
# → GitHub Secrets 업데이트

# 3. 커밋 히스토리 정리
git rebase -i HEAD~N  # 문제 커밋까지 선택
# → git push --force-with-lease (신중히!)
```

### 🔑 만약 AWS 자격증명이 노출되었다면?

```bash
# 1. 즉시 액세스 키 비활성화
# → AWS Management Console > IAM > Access keys

# 2. CloudTrail에서 악의적 활동 확인
# → AWS CloudTrail > Event history

# 3. 모든 인스턴스 감사
# → EC2 인스턴스가 비정상 작동하는가?
# → RDS 데이터 무단 접근 여부 확인

# 4. 새 액세스 키 생성
# → GitHub Secrets 업데이트
```

---

## 9️⃣ 정기 보안 검토

### 분기별 (3개월마다)

- [ ] GitHub Secrets 목록 검토
- [ ] 불필요한 Secrets 삭제
- [ ] API 키/비밀번호 로테이션
- [ ] 퇴사자 권한 제거 확인

### 연간 (12개월마다)

- [ ] 보안 취약점 스캔 (npm audit, pip audit 등)
- [ ] OWASP Top 10 체크리스트 검토
- [ ] 의존성 업데이트
- [ ] 보안 교육

---

## 🔗 참고 문서

- [GitHub: Managing secrets for your repositories](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [AWS: Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [12-Factor App: Store config in environment](https://12factor.net/config)

---

**마지막 수정**: 2026-08-13  
**담당**: 보안팀 (또는 DevOps 팀)
