#!/bin/bash

# ===== EC2 부팅 스크립트 (User Data) =====
# EC2 인스턴스 생성 시 "고급 세부 정보" → "사용자 데이터"에 이 스크립트를 입력합니다.
# 이 스크립트는 인스턴스 부팅 시 한 번만 자동 실행됩니다.

set -e

echo "================================"
echo "EC2 초기화 시작"
echo "================================"

# 시간대 설정 (서울)
timedatectl set-timezone Asia/Seoul
echo "시간대 설정 완료: Asia/Seoul"

# ===== 패키지 업데이트 =====
yum update -y

# ===== Docker 설치 =====
echo "Docker 설치 중..."
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user
echo "Docker 설치 완료"

# ===== Docker Compose 설치 =====
echo "Docker Compose 설치 중..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
/usr/local/bin/docker-compose --version
echo "Docker Compose 설치 완료"

# ===== Git 설치 (이미 기본 포함되지만 명시적으로) =====
echo "Git 버전 확인..."
git --version

# ===== 프로젝트 디렉토리 생성 및 리포지토리 클론 =====
echo "프로젝트 디렉토리 생성 중..."
mkdir -p /home/ec2-user/CapShop
cd /home/ec2-user/CapShop

# GitHub 저장소에서 클론
# (SSH 키 또는 HTTPS 토큰 필요. 여기서는 HTTPS 사용)
echo "GitHub 저장소 클론 중..."
git clone https://github.com/YOUR_USERNAME/CapShop.git . || git pull origin main

# ===== AWS Secrets Manager에서 환경변수 다운로드 (선택사항) =====
# EC2 IAM Role이 Secrets Manager 접근 권한을 가지고 있어야 합니다.

# echo "AWS Secrets Manager에서 환경변수 다운로드 중..."
# aws secretsmanager get-secret-value --secret-id capshop/backend/env \
#   --query SecretString --output text > backend/.env
# aws secretsmanager get-secret-value --secret-id capshop/ai-server/env \
#   --query SecretString --output text > ai-server/.env
# chmod 600 backend/.env ai-server/.env

# ===== 수동 배포 준비 (권장) =====
# GitHub Actions에서 SSH를 통해 .env 파일을 배포할 때까지 기다립니다.
echo "수동 배포를 기다리는 중..."
echo "GitHub Actions 또는 수동으로 .env 파일을 EC2에 배포해야 합니다."
echo "배포 후: docker compose -f docker-compose.prod.yml up -d --build"

# ===== CloudWatch Agent 설치 (선택사항) =====
# echo "CloudWatch Agent 설치 중..."
# wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
# rpm -U ./amazon-cloudwatch-agent.rpm
# echo "CloudWatch Agent 설치 완료"

# ===== 로그 기록 =====
echo "EC2 초기화 완료: $(date)" > /var/log/capshop-init.log

echo "================================"
echo "EC2 초기화 완료"
echo "================================"
echo "다음 단계:"
echo "1. backend/.env, ai-server/.env 파일 배포"
echo "2. docker compose -f docker-compose.prod.yml up -d --build"
echo "3. EC2 보안그룹에서 80/443 포트 개방 (ALB 사용 시 8080/8000은 내부만)"

# ===== GitHub Actions에서 자동 배포하는 방식 =====
# 이 스크립트 실행 후, GitHub Actions이 SSH로 다음을 자동 실행:
# 1. git pull origin main
# 2. .env 파일 배포 (GitHub Secrets에서)
# 3. docker compose up -d --build
