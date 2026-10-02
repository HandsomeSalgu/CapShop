# CapShop AWS 배포 핸드오프

최초 작성: 2026-10-01 (Claude Code 세션 1)
최종 갱신: 2026-10-02 (Codex — Secrets 14개 저장 확인, Step G 사람의 명시적 확인 대기)
대상: 이 저장소에서 배포 작업을 이어받는 사람 또는 에이전트 (**Codex 앱에서 실행 예정**)

이 문서가 `docs/AWS_DEPLOYMENT.md`, `docs/DEPLOYMENT_CHECKLIST.md`보다 우선한다. 그 두 문서는 초기 설계 단계에 쓴 것이라 리전(us-east-1), EC2에서 git clone 하는 방식, `MYSQL_ROOT_PASSWORD` 등 **지금 설계와 다른 내용**이 들어 있다. 충돌하면 이 문서를 따른다.

---

## 0. 이 문서를 받은 에이전트(Codex)에게 — 먼저 읽을 것

### 0-1. 지금 상태 한 줄 요약

Step A는 `97b9b32`로 커밋되었고 PR #1이 main에 merge되었다(`9218239`). 로컬 main 동기화와 작업 브랜치 삭제도 완료했다. 인계 직후 첫 할 일은 Step B였고, **현재 Step B~F 각 항목의 완료 확인을 모두 받았고, 다음은 Step G의 명시적 완료·push 확인**이다(사람이 지정한 B→C→D→F→E 순서). B~F 완료 확인 전 push 금지. main 배포의 실제 제공 실패 로그는 `Setup SSH` exit code 1이었고, Secrets 부재로 단정하지 않는다. SSH 단일 IP 제한에 대응한 워크플로 수정은 로컬 커밋 `c08ac83`에만 있다. 사람이 Actions용 IAM 추가 정책 저장, EC2 역할 부착, SSH(내 IP) 및 8080 인바운드 설정, Docker·Compose·STS 필수 검증 3개 통과를 확인했다. CloudFront의 EC2 원본, 네 경로, 403/404 오류 페이지 설정도 완료를 확인했다. OAuth 운영 URI 및 Secrets 14개 저장 확인도 받았다. 아직 push하지 않았고, 실제 재배포·API·DB·브라우저 로그인 결과는 미검증이다.

### 0-2. 에이전트가 직접 해도 되는 일

- 승인된 코드·문서 수정을 **로컬 커밋** (`git commit`까지만; Step A는 완료)
- 파이프라인(`deploy-aws.yml`), compose(`docker-compose.prod.yml`) 파일 읽기·리뷰·버그 수정
- 이 문서(`HANDOFF.md`) 갱신 — 작업 진행 시 섹션 11 "세션 이력"에 한 줄씩 추가할 것
- 로컬 `.env` 파일을 **읽어서** Secrets 값 템플릿을 사람에게 보여주는 것 (5장)

### 0-3. 반드시 사람에게 확인받고 할 일

- **`git push origin main` 또는 Actions 재실행** — Step G에서만, 사람이 **"B~F 전부 끝났다"**고 명시적으로 확인한 뒤 실행한다. 이번 로컬 수정은 push해야 반영되므로 이전 실패 run을 재실행하는 것만으로 SSH 수정이 적용되지는 않는다.
- AWS 콘솔 / GitHub Secrets / Google·Kakao 콘솔 작업(Step B~F)은 에이전트가 할 수 없다. 이 문서의 해당 절을 사람에게 **그대로 안내**하고, 끝났다는 답을 받은 뒤 다음 단계로 넘어간다.
- EC2에 ssh 접속해서 명령 실행 (Step C) — 키 파일 `C:\develop\project\key\capshop-key.pem`이 로컬에 있으므로 기술적으로는 가능하지만, 사람이 명시적으로 시킬 때만.

### 0-4. 절대 하지 말 것

- `backend/.env`, `ai-server/.env`, `frontend/web/.env.production`을 **커밋하거나 문서에 값 그대로 적지 말 것** (실제 API 키·OAuth 시크릿이 들어 있음, gitignore 대상)
- `docs/AWS_DEPLOYMENT.md`, `docs/DEPLOYMENT_CHECKLIST.md`를 "정답"으로 보고 코드를 되돌리지 말 것 (outdated)
- `docker-compose.prod.yml`의 `127.0.0.1` 포트 바인딩(mysql/redis/ai-server)을 `0.0.0.0`으로 풀지 말 것
- `.github/workflows/deploy.yml`의 트리거를 다시 `push`로 되돌리지 말 것 (self-hosted 러너는 폐기됨)

### 0-5. 자주 쓰는 확인 명령

```bash
git status --short                 # 로컬 수정 확인; 로컬 커밋 후에는 깨끗해야 함
git log --oneline -5
git diff .github/workflows/deploy-aws.yml docker-compose.prod.yml
```

> Windows에서 `git diff`/`git add` 할 때 `LF will be replaced by CRLF` 경고가 뜨는데 **무시해도 된다.** 저장소에는 LF로 저장되고 Linux 러너는 LF를 읽는다.

---

## 1. 프로젝트 구조

```
CapShop/
├── Dockerfile                 # backend 이미지 (eclipse-temurin:23-jdk, backend/target/*-SNAPSHOT.jar 복사)
├── docker-compose.yml         # 로컬 개발용 (frontend/backend/ai/mysql/redis 전부 빌드)
├── docker-compose.prod.yml    # EC2용 (backend/ai는 ECR 이미지 pull, mysql/redis는 공식 이미지)
├── .github/workflows/
│   ├── deploy-aws.yml         # ★ 메인 배포 파이프라인 (main push 시 실행)
│   └── deploy.yml             # 구 self-hosted 러너용 — workflow_dispatch(수동)로 전환됨
├── backend/                   # Spring Boot 3, Java 23, Maven, MyBatis, MySQL, Redis
│   ├── mvnw                   # Maven wrapper (git index에 100755 실행권한 기록됨)
│   ├── src/main/java/com/syncshopper/controller/HealthController.java  # GET /api/health, /api/health/db
│   ├── src/main/resources/application.yml       # 공통 설정 (환경변수 참조)
│   ├── src/main/resources/application-local.yml # 로컬 프로필
│   ├── src/main/resources/application-prod.yml  # 운영 프로필 (DB_URL/DB_USERNAME/DB_PASSWORD 필수, 기본값 없음)
│   └── .env.example
├── ai-server/                 # FastAPI, Python 3.11-slim, Gemini + Google CSE
│   ├── Dockerfile
│   ├── app/core/config.py     # 환경변수 → Settings
│   └── .env.example
├── frontend/web/              # Vue 3 + Vite
│   ├── nginx.conf             # (구) 로컬 docker용 리버스프록시 — CloudFront behavior 설계의 참고 자료
│   └── .env.production        # 로컬에만 존재 (gitignore). CI는 Secrets의 VITE_BACKEND_BASE_URL 사용
├── database/schema.sql        # MySQL 초기화 스크립트 (syncshopper DB)
├── docs/                      # 초기 설계 문서들 (일부 내용 outdated — 상단 참고)
└── HANDOFF.md                 # 이 문서
```

로컬 `.env` 파일들(`backend/.env`, `ai-server/.env`, `frontend/web/.env.production`)은 gitignore 대상이며 **이 머신에 실제 키 값이 들어 있다** (2026-10-01 세션 2에서 존재 확인). 운영용 값은 여기서 복사해 GitHub Secrets에 넣는다 (5장 참고).

---

## 2. 목표 아키텍처

```
git push (main)
 ├─ [job: deploy-frontend]  npm ci → vite build → S3 sync → CloudFront invalidation
 ├─ [job: build-and-push]   Maven(jar) → docker build ×2 → ECR push (capshop-backend, capshop-ai-server)
 └─ [job: deploy-to-ec2]    (needs: build-and-push) compose + .env 번들을 tar|ssh 로 EC2에 복사
                            → ECR login(IAM Role) → docker compose pull → up -d
                            (EC2는 빌드하지 않음. git도 필요 없음.)

브라우저 ─HTTPS─▶ CloudFront (d141l5y1f86nit.cloudfront.net)
                  ├─ /*                                  → S3 (정적 Vue)
                  └─ /api/* /oauth2/* /login/* /uploads/* → EC2:8080 (HTTP origin)   ← 설정 완료 확인, 실제 배포 검증 전
EC2 (docker compose, 프로젝트명 capshop-prod)
  backend:8080 (외부 공개) ─ ai-server:8000 (127.0.0.1만) ─ mysql:3306 (127.0.0.1만) ─ redis:6379 (127.0.0.1만)
```

---

## 3. 완료된 것

### 3-1. 코드 — 커밋 완료 (`3c8348b aws ec2 배포 환경으로 변경` 및 이후 커밋, origin/main 과 동기화됨)

- `application.yml`: 하드코딩 IP(`70.12.60.52`) 전부 제거. OAuth redirect URI 4개와 JWT secret은 환경변수 **필수**(기본값 없음). `app.cors.allowed-origins` 추가.
- `SecurityConfig.java`: CORS를 `allowedOriginPatterns("*")` → `CORS_ALLOWED_ORIGINS` 환경변수(쉼표 구분) 기반으로 변경. `/api/health`, `/api/health/db`는 permitAll.
- `application-local.yml`, `docker-compose.yml`: DB 비밀번호 환경변수화 (기본값은 로컬용 `potato` 유지).
- `backend/.env.example`, `ai-server/.env.example` 작성.
- `docs/` 하위 4개 문서 (상단 주의사항 참고).
- 원격 main 기준 최근 커밋: `9218239 Merge pull request #1` (Step A 커밋 `97b9b32` 포함)

### 3-2. 코드 — Step A 완료, PR #1 merge됨

> 아래 변경은 `97b9b32`로 커밋되어 PR #1을 통해 main에 반영되었다(`9218239`). 표는 당시 변경 기록이다. 이후 Codex의 SSH 접속 수정은 로컬 커밋으로 준비하며, B~F 완료 확인 전 push하지 않는다.

| 파일 | 내용 |
|---|---|
| `.github/workflows/deploy-aws.yml` | 3-job 파이프라인 전면 재작성. 리전 `ap-northeast-2`. 이전 버전의 치명적 버그 수정: Maven `working-directory` 누락, SSH heredoc `'EOF'` 때문에 `$BACKEND_ENV`가 치환 안 되던 문제(→ 번들 파일로 복사하는 방식으로 변경), EC2 git clone 의존 제거. `chmod +x ./mvnw` 추가. `deploy-to-ec2`는 `needs: build-and-push`. |
| `docker-compose.prod.yml` | backend/ai 이미지를 `${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/capshop-{backend,ai-server}:latest` 로 변경. `MYSQL_USER=capshop` 추가, root/앱 비밀번호 모두 `${MYSQL_PASSWORD}`. mysql/redis/ai 포트를 `127.0.0.1` 바인딩. backend/ai가 mysql/redis healthcheck 통과 후 뜨도록 `depends_on.condition: service_healthy`. `schema.sql`을 `/docker-entrypoint-initdb.d/01-schema.sql`로 마운트. |
| `.github/workflows/deploy.yml` | 트리거를 `workflow_dispatch`(수동)로 변경, Docker 단계 주석 처리. AWS 파이프라인과 충돌 방지. |
| `frontend/web/package-lock.json` | `npm install` 부산물. 그대로 커밋해도 됨. |
| `backend/mvnw` (index mode) | `git update-index --chmod=+x` 로 실행권한 기록됨 (`git ls-files -s` → `100755`). Linux 러너에서 `Permission denied` 방지. |
| `HANDOFF.md` | 이 문서도 Step A 커밋에 포함됨. |

### 3-3. AWS 인프라 (리전: ap-northeast-2 서울)

| 리소스 | 상태 | 값 |
|---|---|---|
| IAM 사용자 (GitHub Actions용) | ✅ | `capshop-github-actions` — S3/CloudFront/ECR 권한 부여됨. 액세스 키 발급됨 |
| S3 버킷 | ✅ | `capshop-frontend` — 수동 업로드로 Vue 앱 뜨는 것 확인함 |
| CloudFront | ✅ Step D 설정 완료 확인 | `d141l5y1f86nit.cloudfront.net` — 프론트 기본 동작은 S3, `/api/*`, `/oauth2/*`, `/login/*`, `/uploads/*`는 `capshop-ec2`. 403/404→`/index.html`, 응답 200 저장을 사람이 확인. 실제 통신·SPA 새로고침은 배포 후 검증 |
| ECR 저장소 | ✅ | `capshop-backend`, `capshop-ai-server` (서울 리전 확인됨) |
| EC2 인스턴스 | ✅ 초기 설정·검증 완료 | `15.164.50.114`, `ec2-15-164-50-114.ap-northeast-2.compute.amazonaws.com`, Amazon Linux 2023 / `ec2-user`. 키페어: `C:\develop\project\key\capshop-key.pem`. 실제 IAM 역할 `CapShopEC2Role` 부착. Docker·Compose·STS 필수 검증 3개 통과. 컨테이너는 아직 없음 |
| AWS 계정 ID | — | `256600409763` |

---

## 4. 남은 작업 (이 순서대로)

### Step A. 변경 보존 — 완료

`97b9b32`로 커밋 후 PR #1 merge(`9218239`) 완료. Codex가 `git checkout main`, `git pull origin main`, `git branch -d feat/aws-ecr-deploy`를 실행했고 정리 직후 작업 트리가 깨끗함을 확인했다. main 배포는 1회 실패했다. 실제 제공 로그는 SSH 준비 단계 실패이며 Secrets 부재 여부는 확정되지 않았다. 코드 수정 필요 여부는 실패 원인을 확인해 판단한다.

### Step B. EC2에 IAM Role 부착 (ECR pull 권한) — 사람이 AWS 콘솔에서

1. IAM → Roles → Create role → Trusted entity: **AWS service / EC2**
2. 정책: `AmazonEC2ContainerRegistryReadOnly`
3. 이름 `capshop-ec2-role` → 생성
4. EC2 → 인스턴스 선택 → Actions → Security → **Modify IAM role** → 부착

✅ 사람의 완료 확인을 받았다. 이후 STS 출력으로 확인한 실제 역할명은 `CapShopEC2Role`이다(권장 이름과 달라도 같은 권한이면 사용 가능).

이걸 해야 EC2에 액세스 키를 두지 않고 `aws ecr get-login-password`가 동작한다. (파이프라인 `deploy-to-ec2` job이 이 명령을 쓴다.)

### Step C. EC2 초기 설치 (최초 1회) — 사람이 ssh로 (또는 명시적 지시 시 에이전트)

보안그룹 인바운드: **22 (내 IP), 8080 (0.0.0.0/0)** 만. 3306/6379/8000은 열지 않는다 (compose가 127.0.0.1로 묶어둠).

**GitHub Actions SSH 접근 추가 설정 (Codex 수정분 push 전에 필요)**

- 사람이 확인한 보안 그룹: `sg-0d5d069bfcaac365f` (`launch-wizard-2`). 인계 당시 스크린샷은 22(단일 IP)와 80만 있었으나, 사람이 **8080 허용 및 SSH 22(내 IP) 규칙 저장**을 완료했다.
- 기본 SSH 규칙은 내 IP로 유지한다. 워크플로는 배포 러너의 IPv4 하나(`/32`)에 TCP 22를 임시 허용하고, 마지막 `always()` 단계에서 자신이 만든 규칙 ID만 제거한다. 배포 job은 동시에 실행되지 않도록 직렬화한다.
- IAM → Users → `capshop-github-actions` → Permissions → Add permissions → Create inline policy → JSON에 아래 정책을 추가한다. 기존 S3/CloudFront/ECR 권한은 유지한다. 정책 이름 예: `CapShopDeployTemporarySSH`.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress"
      ],
      "Resource": "arn:aws:ec2:ap-northeast-2:256600409763:security-group/sg-0d5d069bfcaac365f"
    }
  ]
}
```

- 정리 단계 실패나 러너 강제 종료로 임시 규칙이 남으면, 인바운드 규칙에서 `CapShop-Actions-<run id>-<attempt>` 설명의 규칙만 사람이 제거한다. 내 IP 규칙은 제거하지 않는다. 실제 AWS에서의 생성·제거 동작은 첫 배포 때 확인한다.

```bash
ssh -i C:\develop\project\key\capshop-key.pem <USER>@<EC2_PUBLIC_IP>     # Amazon Linux: ec2-user / Ubuntu: ubuntu
```

Amazon Linux 2023 (aws CLI 기본 설치돼 있음):
```bash
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
exit   # 그룹 반영 위해 재접속
```

Ubuntu 22.04:
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 unzip
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip && unzip awscliv2.zip && sudo ./aws/install
exit
```

재접속 후 검증 (3개 모두 통과해야 함):
```bash
docker ps                      # 권한 에러 없이 빈 목록
docker compose version
aws sts get-caller-identity    # IAM Role 덕분에 키 설정 없이 계정 정보(256600409763)가 나와야 함
```

✅ 사람이 전달한 실제 결과: `docker ps` 권한 오류 없이 빈 목록, `Docker Compose version v5.5.1`, STS 계정 `256600409763` 및 `assumed-role/CapShopEC2Role/i-03078ba13191a7b1a`. 초기 설치·필수 검증 완료. ECR pull 및 실제 배포는 아직 미검증.

### Step D. CloudFront 설정 추가 (★ 빼먹으면 프론트가 API를 못 부른다) — 사람이 AWS 콘솔에서

CloudFront는 HTTPS인데 `http://<EC2-IP>:8080`을 브라우저에서 직접 부르면 **mixed content로 차단**된다. 구 `frontend/web/nginx.conf`가 하던 프록시 역할을 CloudFront가 대신해야 한다.

**D-1. Origin 추가**
- Origin domain: EC2 퍼블릭 DNS (예: `ec2-xx-xx-xx-xx.ap-northeast-2.compute.amazonaws.com`)
- Protocol: **HTTP only**, HTTP port **8080**
- Custom header 추가: `X-Forwarded-Proto` = `https` (Spring의 `forward-headers-strategy: native`가 이 헤더로 https 여부를 판단. CloudFront는 기본적으로 `X-Forwarded-Proto`를 안 보냄)

**D-2. Behavior 4개 추가** (path pattern → EC2 origin)
- `/api/*`, `/oauth2/*`, `/login/*`, `/uploads/*`
- Viewer protocol: Redirect HTTP to HTTPS
- Allowed methods: **GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE**
- Cache policy: **CachingDisabled**
- Origin request policy: **AllViewer** (헤더·쿠키·쿼리스트링 전부 전달 — OAuth 세션 쿠키 때문에 필수)

**D-3. SPA 라우팅용 Error pages** (Vue history 모드 — `/oauth/callback`, `/signup` 같은 딥링크가 S3에서 403 나는 것 방지)
- 403 → `/index.html`, response code 200
- 404 → `/index.html`, response code 200

✅ Step D 완료 확인: 사람이 EC2 원본 생성(HTTP only / 8080 / `X-Forwarded-Proto=https`)을 완료했다고 답했다. `/api/*`가 S3 원본 `capshop-backend`를 가리키던 상태를 발견해 `capshop-ec2`와 `AllViewer`로 수정했다. 이후 동작 목록 스크린샷으로 네 경로가 모두 `capshop-ec2`에 연결되고 기본 동작은 프론트 S3인 것을 확인했다. 나머지 동작도 안내된 정책으로 저장했다고 답했으며, 403/404 오류 페이지 두 개 저장을 확인받았다. 실시간 전파 상태와 실제 통신·로그인·새로고침은 배포 후 검증한다.

### Step E. GitHub Secrets 등록 — 사람이 GitHub에서

**Google 운영 값 결정 완료:** 사람이 현재 계정의 기존 `CapShop` OAuth 클라이언트를 운영용으로 사용하도록 지시했다. 해당 클라이언트의 운영 Redirect URI 등록을 확인했고, 사람이 전체 클라이언트 ID와 새로 추가한 시크릿을 제공했다. 운영 템플릿의 Google ID·Secret 두 값만 해당 쌍으로 교체하고 로컬 환경 파일은 유지한다. 실제 값은 문서나 파일에 저장하지 않는다.

Repository → Settings → Secrets and variables → Actions. 전체 목록은 5장. 값은 로컬 `backend/.env`, `ai-server/.env`에서 가져오되 **운영용으로 바뀌는 항목**이 있다 (5장 표의 비고). 에이전트는 로컬 `.env`를 읽어 5장 템플릿의 `<...>` 자리를 채운 완성본을 **채팅으로만** 보여줄 수 있다 (파일/문서에 쓰지 말 것).

✅ 2026-10-02 사람이 Secrets 14개 저장을 하나씩 확인했다. 실제 값은 이 문서에 기록하지 않는다.

- [x] BACKEND_ENV_FILE
- [x] AI_SERVER_ENV_FILE
- [x] AWS_ACCESS_KEY_ID
- [x] AWS_SECRET_ACCESS_KEY
- [x] AWS_ACCOUNT_ID
- [x] AWS_ECR_BACKEND_REPO
- [x] AWS_ECR_AI_REPO
- [x] AWS_S3_BUCKET_NAME
- [x] AWS_CLOUDFRONT_DISTRIBUTION_ID
- [x] VITE_BACKEND_BASE_URL
- [x] EC2_HOST
- [x] EC2_USER
- [x] EC2_SSH_KEY
- [x] MYSQL_PASSWORD

AWS 키는 로컬 CLI의 동일한 키 ID와 비밀키 존재를 확인하고, 읽기 전용 STS 호출로 계정과 `capshop-github-actions` 사용자 인증 성공을 확인했다. 비밀키와 SSH 키는 사람이 로컬 PowerShell에서 클립보드로 복사해 GitHub에 저장했고 채팅에 표시하지 않았다. 기존 `MYSQL_ROOT_PASSWORD` Secret은 이번 워크플로에서 사용하지 않으며, 필수 이름 `MYSQL_PASSWORD`를 별도로 추가했다.

### Step F. OAuth 제공자 콘솔에 Redirect URI 등록 — 사람이

- Google Cloud Console → Credentials → OAuth 2.0 Client → Authorized redirect URIs에 추가:
  `https://d141l5y1f86nit.cloudfront.net/login/oauth2/code/google`
- Kakao Developers → 앱 → Redirect URI에 추가:
  `https://d141l5y1f86nit.cloudfront.net/login/oauth2/code/kakao`
- 기존 로컬용 URI(`http://localhost:8080/...`)는 지우지 말고 **추가**만 한다.

### Step G. 재배포 → 검증 (B~F 완료를 사람에게 확인받은 뒤)

원래 권장 트리거는 Actions에서 실패한 run의 **Re-run all jobs**다. 단, 이번 문서·SSH 수정은 로컬 커밋에 있으므로 **수정 적용에는 사람 확인 후 아래 push가 필요하다.** 이 push가 재배포 트리거를 겸하므로 빈 커밋은 불필요하다. B~F와 Actions용 IAM 추가 권한 설정이 완료되었다는 확인 전에는 push하거나 재실행하지 않는다.

```bash
git push origin main
```
Actions 탭에서 `AWS Deployment Pipeline`의 3개 job(`deploy-frontend`, `build-and-push`, `deploy-to-ec2`)이 모두 성공하는지 사람에게 확인받는다. 임시 SSH 규칙 제거 단계 성공도 확인한다. 검증은 8장. 실패 시 7장 "알려진 함정" 12개부터 대조.

---

## 5. GitHub Secrets 전체 목록

`AWS_REGION`은 워크플로 `env`에 `ap-northeast-2`로 박혀 있어 Secret이 아니다.

| Secret 이름 | 값 | 비고 |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | IAM 사용자 `capshop-github-actions`의 키 | 로컬 `aws configure`에 쓴 것과 동일 |
| `AWS_SECRET_ACCESS_KEY` | 〃 | |
| `AWS_ACCOUNT_ID` | `256600409763` | |
| `AWS_ECR_BACKEND_REPO` | `capshop-backend` | ⚠️ `docker-compose.prod.yml`에 이 이름이 **하드코딩**돼 있다. 바꾸려면 compose도 같이 수정 |
| `AWS_ECR_AI_REPO` | `capshop-ai-server` | ⚠️ 위와 동일 |
| `AWS_S3_BUCKET_NAME` | `capshop-frontend` | |
| `AWS_CLOUDFRONT_DISTRIBUTION_ID` | CloudFront 콘솔의 Distribution ID (`E`로 시작) | |
| `VITE_BACKEND_BASE_URL` | `https://d141l5y1f86nit.cloudfront.net` | API가 CloudFront 경유이므로 프론트 도메인과 동일 |
| `EC2_HOST` | EC2 퍼블릭 IP **만** (예: `3.35.12.34`) | ⚠️ `ec2-user@` 붙이지 말 것. 워크플로가 `$EC2_USER@$EC2_HOST`로 조합함 |
| `EC2_USER` | `ec2-user` (Amazon Linux) 또는 `ubuntu` | |
| `EC2_SSH_KEY` | `C:\develop\project\key\capshop-key.pem` 파일 **전체 내용** | `-----BEGIN ... -----END` 포함 |
| `MYSQL_PASSWORD` | `capshop` | root와 앱 계정(`capshop`) 비밀번호 양쪽에 쓰임. `MYSQL_ROOT_PASSWORD`는 **필요 없음** |
| `BACKEND_ENV_FILE` | 아래 템플릿 | 기존에 등록된 로컬용 값을 **운영용으로 교체** |
| `AI_SERVER_ENV_FILE` | 아래 템플릿 | 〃 |

기존 Secret 중 `FRONTEND_ENV_FILE`은 새 파이프라인에서 사용하지 않는다 (지워도 됨).

### `BACKEND_ENV_FILE` 템플릿

`<...>` 부분은 로컬 `backend/.env`에서 복사. 나머지는 아래 값 그대로.

```env
GOOGLE_CLIENT_ID=<로컬 backend/.env 값>
GOOGLE_CLIENT_SECRET=<로컬 값>
KAKAO_CLIENT_ID=<로컬 값>
KAKAO_CLIENT_SECRET=<로컬 값>
NAVER_CLIENT_ID=<로컬 값>
NAVER_CLIENT_SECRET=<로컬 값>
SPRING_MAIL_USERNAME=<로컬 값>
SPRING_MAIL_PASSWORD=<로컬 값>

SPRING_PROFILES_ACTIVE=prod

OAUTH2_REDIRECT_URI=https://d141l5y1f86nit.cloudfront.net/oauth/callback
OAUTH2_SIGNUP_REDIRECT_URI=https://d141l5y1f86nit.cloudfront.net/signup
OAUTH2_GOOGLE_REDIRECT_URI=https://d141l5y1f86nit.cloudfront.net/login/oauth2/code/google
OAUTH2_KAKAO_REDIRECT_URI=https://d141l5y1f86nit.cloudfront.net/login/oauth2/code/kakao
CORS_ALLOWED_ORIGINS=https://d141l5y1f86nit.cloudfront.net

JWT_SECRET=<새로 생성: openssl rand -base64 48 | tr -d '\n=+/'>

DB_URL=jdbc:mysql://mysql:3306/syncshopper?serverTimezone=Asia/Seoul&characterEncoding=UTF-8
DB_USERNAME=capshop
DB_PASSWORD=capshop

AI_FASTAPI_TIMEOUT_MS=180000
```

`SPRING_PROFILES_ACTIVE=prod`와 `DB_URL`은 **없으면 부팅 실패**한다. `application.yml`의 기본 프로필이 `local`이고, `application-prod.yml`은 `${DB_URL}`에 기본값이 없다. (compose가 `SPRING_DATASOURCE_URL`도 같은 값으로 넣어주지만, `DB_URL`이 비어 있으면 placeholder 해석 단계에서 먼저 터진다. 둘 다 둔다.)

### `AI_SERVER_ENV_FILE` 템플릿

```env
AI_DETECTION_PROVIDER=gemini
GEMINI_API_KEY=<로컬 ai-server/.env 값>
GOOGLE_CSE_API_KEY=<로컬 값>
GOOGLE_CSE_CX=<로컬 값>

DB_USER=capshop
DB_PASSWORD=capshop
DB_NAME=syncshopper
```

`DB_HOST`, `DB_PORT`, `BACKEND_BASE_URL`은 compose가 주입하므로 넣지 않는다.

---

## 6. 확정된 설정값 요약

| 항목 | 값 |
|---|---|
| 리전 | `ap-northeast-2` |
| CloudFront 도메인 | `d141l5y1f86nit.cloudfront.net` |
| 프론트 API base URL | CloudFront 도메인과 동일 (behavior로 프록시) |
| DB 계정 | `capshop` / `capshop` (MySQL root 비밀번호도 동일). EC2 밖에서는 접근 불가하므로 단순 값 허용 |
| DB 이름 | `syncshopper` (schema.sql이 생성) |
| 이미지 태그 | `latest` 고정 |
| EC2 배포 디렉터리 | `~/capshop/` (파이프라인이 자동 생성) |
| compose 프로젝트명 | `capshop-prod` |

---

## 7. 알려진 함정 / 주의사항

1. **로컬 `.env`와 GitHub Secret 값은 달라야 한다.** 로컬은 `root/potato` + localhost URL, 운영은 `capshop/capshop` + CloudFront URL. 로컬 파일을 그대로 Secret에 복사하면 운영이 깨진다.
2. **MySQL 계정 생성은 볼륨이 비어 있는 첫 실행에만** 일어난다. 나중에 비밀번호를 바꾸려면 EC2에서 `docker compose -f docker-compose.prod.yml down -v` (데이터 삭제됨) 후 재배포.
3. **`.env` 파일은 EC2에 남는다** (`~/capshop/.env`, `~/capshop/backend/.env`, `~/capshop/ai-server/.env`, chmod 600). compose가 매번 읽어야 하므로 삭제하지 않는다. EC2 셸 접근 = 시크릿 접근이므로 기본 22번 포트는 내 IP로 제한한다. CI는 러너 IP 하나만 임시 허용하며 배포 후 그 규칙을 제거한다(Step C 추가 설정).
4. **Secrets의 멀티라인 값**(`BACKEND_ENV_FILE` 등)은 GitHub Secret 입력창에 그대로 여러 줄 붙여넣으면 된다. 워크플로가 `printf '%s\n'`으로 파일에 쓴다.
5. **mixed content**: Step D를 안 하면 CloudFront(https) 페이지에서 EC2(http) 호출이 브라우저에서 차단된다. 콘솔 F12 → Network에 `blocked:mixed-content`가 보이면 이 문제.
6. **OAuth `redirect_uri_mismatch`**: Step F 누락이거나, Secret의 `OAUTH2_*_REDIRECT_URI`와 콘솔 등록값이 글자 하나라도 다를 때.
7. **Spring이 http로 인식**: D-1의 `X-Forwarded-Proto: https` 커스텀 헤더를 안 넣으면 일부 리다이렉트가 `http://`로 생성될 수 있다.
8. `docs/AWS_DEPLOYMENT.md`, `docs/DEPLOYMENT_CHECKLIST.md`는 outdated. 이 문서와 다르면 이 문서가 맞다.
9. `frontend/web/Dockerfile.prod`는 현재 파이프라인에서 쓰지 않는다 (CI가 node로 직접 빌드). 삭제해도 무방.
10. 기존 `deploy.yml`(self-hosted 러너)은 `workflow_dispatch`로 바꿔뒀다. 노트북 러너가 꺼져 있어도 main push가 대기 상태로 걸리지 않는다.
11. `docker-compose.prod.yml` 주석에 RDS 예시로 `us-east-1`이 적혀 있는데 **주석일 뿐**이다. 실제 리전은 `${AWS_REGION}`(= `ap-northeast-2`)으로 들어간다. 헷갈리면 주석만 고쳐도 된다.
12. `deploy-to-ec2` job은 EC2에 `aws` CLI와 `docker compose`(v2 플러그인)가 있어야 돈다. Step C 검증 3개가 통과하지 않았으면 push하지 말 것.

---

## 8. 배포 후 검증

```bash
# 1) API 헬스체크 (CloudFront 경유 — Step D 검증까지 됨)
curl -i https://d141l5y1f86nit.cloudfront.net/api/health
curl -i https://d141l5y1f86nit.cloudfront.net/api/health/db     # DB 연결까지 확인

# 2) EC2 직접 (CloudFront 문제와 백엔드 문제 분리용)
curl -i http://<EC2_PUBLIC_IP>:8080/api/health

# 3) EC2 컨테이너 상태
ssh -i capshop-key.pem <USER>@<EC2_IP>
cd ~/capshop
docker compose -f docker-compose.prod.yml ps        # 4개 모두 Up (mysql/redis는 healthy)
docker compose -f docker-compose.prod.yml logs backend --tail 50
docker compose -f docker-compose.prod.yml logs ai-server --tail 50

# 4) DB 접속 (EC2 내부에서만 가능)
docker compose -f docker-compose.prod.yml exec mysql mysql -ucapshop -pcapshop syncshopper -e "SHOW TABLES;"

# 5) 브라우저
#    https://d141l5y1f86nit.cloudfront.net 접속 → Google/Kakao 로그인 → /oauth/callback 으로 돌아와야 함
#    새로고침해도 403 안 나야 함 (Step D-3)
```

---

## 9. 왜 이렇게 설계했는지 (의사결정 기록)

- **EC2에서 빌드하지 않고 ECR pull만**: t3.medium에서 Maven + Docker 빌드는 느리고 메모리를 많이 먹는다. CI 러너에서 빌드하면 EC2는 작아도 되고 롤백도 이미지 태그만 바꾸면 된다.
- **EC2에 git 없음**: 파이프라인이 필요한 파일(compose, .env, schema.sql)만 `tar | ssh`로 복사. EC2에 소스가 없으니 노출 면적이 줄고 "EC2는 실행만"이라는 원칙이 지켜진다.
- **MySQL/Redis를 EC2 컨테이너로**: RDS/ElastiCache는 비용과 설정 부담이 커서 1차 배포에서는 제외. compose에서 호스트명만 바꾸면 나중에 전환 가능 (`SPRING_DATASOURCE_URL`, `SPRING_DATA_REDIS_HOST`).
- **CloudFront가 API 프록시**: 도메인·ACM 인증서·ALB 없이도 HTTPS로 API를 제공할 수 있는 가장 싼 방법. 구 nginx.conf의 경로 4개를 behavior로 그대로 옮긴 것.
- **self-hosted 러너 포기**: 처음엔 노트북 러너로 테스트했는데 PowerShell 실행 정책, Docker Desktop 부재 등으로 계속 막혔다. 이 과정의 커밋이 8/13의 "오류 수정" 연속 커밋들이다.

---

## 10. 로컬 개발 (참고)

```bash
docker compose up -d           # docker-compose.yml — root/potato, localhost
cd frontend/web && npm run dev # http://localhost:5173
```
로컬 `backend/.env`는 `OAUTH2_*_REDIRECT_URI`가 localhost 기준, `CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000`. Docker Desktop이 없는 머신에서는 Maven 빌드까지만 가능.

---

## 11. 세션 이력 (이어받는 에이전트는 여기에 한 줄씩 추가할 것)

| 날짜 | 도구 | 한 일 | 결과 |
|---|---|---|---|
| ~2026-08-13 | 사람 + 노트북 self-hosted 러너 | `deploy.yml`로 로컬 러너 배포 시도 | PowerShell 정책·Docker Desktop 부재로 실패 → 포기 (커밋 `c49e096`~`c2a0d22`) |
| 2026-10-01 | Claude Code 세션 1 | 코드 환경변수화, `deploy-aws.yml` 재작성, `docker-compose.prod.yml` ECR화, AWS 리소스 생성(IAM/S3/CloudFront/ECR/EC2), `HANDOFF.md` 초안 작성 | 코드는 미커밋 상태로 남김 |
| 2026-10-01 | Claude Code 세션 2 | 미커밋 파일 5개를 열어 문서 3-2절과 대조 검증, `/api/health` 엔드포인트 실존 확인, `mvnw` 100755 확인, 로컬 `.env` 3개 존재 확인. 이 문서에 0장(에이전트 규칙)·11장(세션 이력) 추가 및 세부 보강 | **코드·인프라 변경 없음.** 커밋도 하지 않음 → Step A부터 시작하면 됨 |
| 2026-10-01 | 사람 (Claude Code 이후) | Step A를 `97b9b32`로 커밋, PR #1을 main에 merge(`9218239`), 첫 main 배포 실행 | 실패 run 1회 존재. 당초 Secrets 부재로 예상했으나 실제 제공 로그는 `Setup SSH` exit code 1이므로 원인을 재확인함 |
| 2026-10-01 | Codex | HANDOFF 전체 읽기, 로컬 main 동기화 및 병합된 작업 브랜치 삭제. 사람이 EC2_HOST 갱신을 확인했고 SSH 단일 IP 제한 및 보안 그룹 ID를 제공함. 러너 IP `/32` 임시 허용·규칙 ID로 정리·SSH 재시도 추가, 문서 최신화 | YAML·IAM JSON 파싱, 전체 13개 Bash 구문 검사, mock으로 `/32` 생성·잘못된 IP 거절·AWS 실패 시 출력 없음·해당 규칙 ID만 제거 확인. AWS 호출 없이 로컬 검증함. 로컬 커밋까지만 진행, push 없음. Actions용 IAM 권한 추가 및 B~F/배포/헬스체크/OAuth 검증 완료 확인은 아직 없음 |
| 2026-10-01 | Codex + 사람 | SSH 수정·문서 로컬 커밋 `c08ac83`. 사람이 Actions용 IAM 추가 정책 저장, Step B 역할 부착, Step C SSH/8080 규칙과 Windows 키 ACL 수정, EC2 초기 설정을 수행 | 사람이 보낸 출력으로 Docker 권한·Compose v5.5.1·STS 계정 `256600409763` 및 `CapShopEC2Role` 확인. Step B~C 완료, 다음 Step D. push·재실행 없음, 최종 검증 미완료 |
| 2026-10-01 | Codex + 사람 | Step D EC2 원본 추가, `/api/*`의 S3 원본 연결을 EC2로 수정, 4개 동작과 SPA 오류 페이지 설정 안내 | 네 경로의 `capshop-ec2` 연결을 스크린샷으로 확인, 403/404→`/index.html`, 응답 200 저장 확인을 받음. 다음 Step F→E. push·재실행 없음, 최종 검증 미완료 |

| 2026-10-01 | Codex + 사람 | Google 콘솔에 운영 Redirect URI가 이미 있음을 확인해 중복 항목 제거 후 저장, Kakao 운영 URI도 기존 등록 확인. Step E용 로컬 환경 파일과 운영 설정 검토 | Google 콘솔에서 선택한 클라이언트와 로컬 환경 파일의 클라이언트 ID 불일치 발견. 동일 클라이언트의 Redirect URI 확인 전 Google 설정을 완료로 간주하지 않음. Secrets 완성본은 아직 제공하지 않았으며 비밀값을 파일에 저장하지 않음. push 없음 |

| 2026-10-02 | Codex + 사람 | 현재 계정에서 로컬 Google 클라이언트를 찾지 못해, 사람 지시에 따라 기존 CapShop OAuth 클라이언트를 운영용으로 선택. 사람이 새 시크릿을 추가하고 ID·Secret을 제공. 로컬 환경 파일을 읽어 운영 템플릿 검토 | Step F 운영 URI 확인 완료. Google 값 교체, 새 JWT 생성, 운영 프로필·CloudFront URL·DB 계정 검토를 마치고 BACKEND_ENV_FILE을 채팅으로만 제공하는 단계. Secrets 저장 완료는 아직 확인 전. 비밀값 파일 저장·로컬 환경 파일 수정·push 없음 |

| 2026-10-02 | Codex + 사람 | 운영용 BACKEND_ENV_FILE·AI_SERVER_ENV_FILE을 채팅으로만 준비하고 사람이 저장. 나머지 12개 Secret도 순서대로 저장 확인. 로컬 AWS 키 ID 일치 확인과 STS 인증 검증 | Secrets 총 14개 저장 확인 완료. B~F 개별 항목 확인 완료, 사람이 전체 완료 및 push를 명시적으로 확인하기를 기다림. SSH 수정 및 문서 변경은 로컬 커밋에만 있음. 비밀값 파일 저장·로컬 환경 파일 수정·push 없음, 배포 및 최종 검증 미완료 |
