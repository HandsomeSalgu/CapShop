# 🐳 SyncShopper 인프라(도커) 설치 및 실행 가이드

이 프로젝트는 로컬 PC 환경을 오염시키지 않기 위해 데이터베이스(MySQL)와 캐시 서버(Redis)를 **Docker(도커)** 컨테이너로 띄워서 사용합니다. 
아래 가이드에 따라 도커를 설치하고 인프라를 띄워주세요.

---

## 1. Docker Desktop 설치 방법 (Windows 기준)

1. **다운로드**: [Docker Desktop 공식 홈페이지](https://www.docker.com/products/docker-desktop/)에 접속하여 **"Download for Windows"** 를 클릭합니다.
2. **설치 진행**: 
   - 다운로드받은 `Docker Desktop Installer.exe`를 실행합니다.
   - 중간에 "Use WSL 2 instead of Hyper-V" 옵션이 체크되어 있는지 확인합니다. (권장)
   - 설치가 완료되면 **컴퓨터를 재부팅(Restart)** 해야 할 수 있습니다.
3. **실행 및 로그인**: 
   - 재부팅 후 바탕화면이나 시작 메뉴에서 **Docker Desktop**을 실행합니다.
   - (선택 사항) 우측 상단에서 로그인하거나, 로그인 없이 그냥 사용(Skip)하셔도 됩니다.
   - 좌측 하단의 🐳 아이콘이 **초록색(Engine running)** 으로 바뀌면 준비 완료입니다!

---

## 2. 인프라(MySQL, Redis) 실행 방법

도커가 정상적으로 켜져 있다면, 이제 우리의 `compose.yaml` 파일을 실행하여 데이터베이스 서버들을 한 번에 띄울 차례입니다.

1. **터미널(Cmd/PowerShell) 열기**
   - 개발을 진행 중인 프로젝트 루트 폴더(`syncshopper`)로 이동합니다.

2. **인프라 폴더로 이동**
   ```bash
   cd infra
   ```

3. **도커 컨테이너 실행 (백그라운드)**
   - 아래 명령어를 입력하면 `compose.yaml` 파일에 적힌 대로 MySQL과 Redis를 다운로드하고 실행합니다.
   ```bash
   docker compose up -d
   ```
   > 💡 `-d` 옵션은 "백그라운드(Detached) 모드"를 의미합니다. 이 옵션을 켜면 터미널 창을 꺼도 서버가 백그라운드에서 계속 안전하게 돌아갑니다.

4. **실행 상태 확인**
   - 아래 명령어를 쳤을 때 `mysql_db`와 `redis_cache`가 **"Up"** 상태로 뜨면 성공입니다!
   ```bash
   docker compose ps
   ```

---

## 3. 유용한 도커 명령어 모음

- **서버 끄기**: 작업을 다 마치고 서버를 내리고 싶을 때
  ```bash
   docker compose down
  ```
- **실시간 로그 보기**: Redis나 MySQL 내부에서 에러가 나는지 확인하고 싶을 때
  ```bash
   docker compose logs -f
  ```
- **Redis 캐시 강제 초기화**: 저장된 추천 데이터(Redis)를 싹 지우고 싶을 때
  ```bash
   docker compose exec redis redis-cli flushall
  ```
