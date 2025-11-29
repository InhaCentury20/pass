#!/bin/bash

# HomePass EC2 초기 설정 스크립트
# 이 스크립트는 EC2 인스턴스에서 한 번만 실행하면 됩니다

set -e  # 에러 발생 시 중단

echo "=== HomePass EC2 초기 설정 시작 ==="

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 시스템 업데이트
echo -e "${GREEN}[1/8] 시스템 업데이트 중...${NC}"
sudo yum update -y

# 2. Node.js 설치
echo -e "${GREEN}[2/8] Node.js 20.x 설치 중...${NC}"
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs
echo "Node.js version: $(node --version)"
echo "NPM version: $(npm --version)"

# 3. Python 3.11 설치
echo -e "${GREEN}[3/8] Python 3.11 설치 중...${NC}"
sudo yum install -y python3.11 python3.11-pip
echo "Python version: $(python3.11 --version)"

# 4. Git 설치
echo -e "${GREEN}[4/8] Git 설치 중...${NC}"
sudo yum install -y git
echo "Git version: $(git --version)"

# 5. Nginx 설치
echo -e "${GREEN}[5/8] Nginx 설치 중...${NC}"
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
echo "Nginx 상태: $(sudo systemctl is-active nginx)"

# 6. MySQL/MariaDB 설치
echo -e "${GREEN}[6/8] MariaDB 설치 중...${NC}"
sudo yum install -y mariadb105-server
sudo systemctl start mariadb
sudo systemctl enable mariadb
echo "MariaDB 상태: $(sudo systemctl is-active mariadb)"

echo -e "${YELLOW}MariaDB 보안 설정을 진행해주세요:${NC}"
echo "sudo mysql_secure_installation"

# 7. 프로젝트 디렉토리 생성
echo -e "${GREEN}[7/8] 프로젝트 디렉토리 생성 중...${NC}"
mkdir -p ~/homepass
echo "프로젝트 디렉토리: ~/homepass"

# 8. 유용한 도구 설치
echo -e "${GREEN}[8/8] 유용한 도구 설치 중...${NC}"
sudo yum install -y htop net-tools

echo ""
echo -e "${GREEN}=== EC2 초기 설정 완료! ===${NC}"
echo ""
echo "다음 단계:"
echo "1. MariaDB 보안 설정: sudo mysql_secure_installation"
echo "2. GitHub에서 프로젝트 클론: cd ~/homepass && git clone <your-repo-url> ."
echo "3. 환경 변수 파일 생성 (.env 파일들)"
echo "4. Systemd 서비스 설정"
echo "5. Nginx 설정"
echo ""
echo "자세한 내용은 QUICK_START.md를 참조하세요."
