# HomePass EC2 배포 가이드

## 목차
1. [EC2 초기 설정](#1-ec2-초기-설정)
2. [필수 소프트웨어 설치](#2-필수-소프트웨어-설치)
3. [Nginx 설정](#3-nginx-설정)
4. [Systemd 서비스 설정](#4-systemd-서비스-설정)
5. [GitHub Actions Secrets 설정](#5-github-actions-secrets-설정)
6. [환경 변수 설정](#6-환경-변수-설정)
7. [첫 배포](#7-첫-배포)
8. [문제 해결](#8-문제-해결)

---

## 1. EC2 초기 설정

### EC2 인스턴스 접속
```bash
chmod 400 inha-capstone-10.pem
ssh -i inha-capstone-10.pem ec2-user@ec2-44-246-219-48.us-west-2.compute.amazonaws.com
```

### 시스템 업데이트
```bash
sudo yum update -y
```

---

## 2. 필수 소프트웨어 설치

### Node.js 설치 (Frontend용)
```bash
# Node.js 20.x LTS 설치
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs

# 설치 확인
node --version
npm --version
```

### Python 3.11 설치 (Backend & Scraper용)
```bash
# Amazon Linux 2023은 기본적으로 Python 3.9가 설치되어 있습니다
# Python 3.11 설치
sudo yum install -y python3.11 python3.11-pip

# Python 버전 확인
python3.11 --version

# pip 업그레이드
python3.11 -m pip install --upgrade pip
```

### Git 설치
```bash
sudo yum install -y git
```

### Nginx 설치
```bash
sudo yum install -y nginx

# Nginx 시작 및 부팅 시 자동 시작 설정
sudo systemctl start nginx
sudo systemctl enable nginx

# 설치 확인
sudo systemctl status nginx
```

---

## 3. Nginx 설정

### Nginx 설정 파일 복사
```bash
# 홈 디렉토리에 배포 폴더 생성
mkdir -p ~/homepass

# 이 저장소의 deployment/nginx/homepass.conf 파일을 복사
sudo cp ~/homepass/deployment/nginx/homepass.conf /etc/nginx/conf.d/homepass.conf

# 또는 직접 생성:
sudo nano /etc/nginx/conf.d/homepass.conf
```

아래 내용을 붙여넣기:
```nginx
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name _;

    # Frontend - Next.js
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API - FastAPI
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend docs
    location /docs {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Nginx 설정 테스트 및 재시작
```bash
# 설정 파일 문법 검사
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx

# 상태 확인
sudo systemctl status nginx
```

---

## 4. Systemd 서비스 설정

### 서비스 파일 복사
```bash
# Systemd 서비스 파일들을 시스템 디렉토리로 복사
sudo cp ~/homepass/deployment/systemd/homepass-backend.service /etc/systemd/system/
sudo cp ~/homepass/deployment/systemd/homepass-frontend.service /etc/systemd/system/
sudo cp ~/homepass/deployment/systemd/homepass-scraper.service /etc/systemd/system/

# Systemd 데몬 리로드
sudo systemctl daemon-reload
```

### 서비스 활성화
```bash
# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable homepass-backend
sudo systemctl enable homepass-frontend
# scraper는 필요시에만 활성화
# sudo systemctl enable homepass-scraper
```

---

## 5. GitHub Actions Secrets 설정

GitHub 저장소의 Settings > Secrets and variables > Actions로 이동하여 다음 secrets를 추가하세요:

### 필수 Secrets

1. **EC2_SSH_PRIVATE_KEY**
   ```bash
   # 로컬에서 PEM 파일 내용을 복사
   cat inha-capstone-10.pem
   ```
   복사한 내용을 그대로 붙여넣기 (-----BEGIN RSA PRIVATE KEY----- 부터 -----END RSA PRIVATE KEY----- 까지)

2. **EC2_HOST**
   ```
   ec2-44-246-219-48.us-west-2.compute.amazonaws.com
   ```

3. **EC2_USER**
   ```
   ec2-user
   ```

### 추가 Secrets (환경 변수)

애플리케이션에 필요한 환경 변수들을 Secrets로 추가하세요:

- `DATABASE_URL` - 데이터베이스 연결 URL
- `JWT_SECRET` - JWT 시크릿 키
- `AWS_ACCESS_KEY_ID` - AWS 액세스 키 (S3 사용 시)
- `AWS_SECRET_ACCESS_KEY` - AWS 시크릿 키 (S3 사용 시)
- 기타 필요한 환경 변수들

---

## 6. 환경 변수 설정

### Backend 환경 변수 (.env)
```bash
# EC2에서 backend .env 파일 생성
nano ~/homepass/homepass-backend/.env
```

내용 예시:
```env
# Database
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/homepass

# JWT
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://your-domain.com"]

# AWS (if using S3)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2
```

### Frontend 환경 변수 (.env.local)
```bash
# EC2에서 frontend .env.local 파일 생성
nano ~/homepass/homepass-front/.env.local
```

내용 예시:
```env
NEXT_PUBLIC_API_URL=http://ec2-44-246-219-48.us-west-2.compute.amazonaws.com/api
```

### Scraper 환경 변수 (.env)
```bash
# EC2에서 scraper .env 파일 생성
nano ~/homepass/homepass-scraper/.env
```

내용 예시:
```env
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=homepass

# AWS S3 (if using)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET=your-bucket-name
```

---

## 7. 첫 배포

### 수동 배포 (첫 번째 배포)

```bash
# 1. 저장소 클론
cd ~
git clone https://github.com/your-username/your-repo.git homepass
cd homepass

# 2. Frontend 설정
cd homepass-front
npm install
npm run build
cd ..

# 3. Backend 설정
cd homepass-backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 4. Scraper 설정
cd homepass-scraper
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 5. 서비스 시작
sudo systemctl start homepass-backend
sudo systemctl start homepass-frontend

# 6. 서비스 상태 확인
sudo systemctl status homepass-backend
sudo systemctl status homepass-frontend
```

### GitHub로 자동 배포 설정

1. **로컬에서 Git 저장소 초기화**
   ```bash
   # 로컬 컴퓨터에서
   cd /Users/mindong-il/pass
   git init
   git add .
   git commit -m "Initial commit: Setup deployment workflow"

   # GitHub에서 새 저장소 생성 후
   git remote add origin https://github.com/your-username/homepass.git
   git branch -M main
   git push -u origin main
   ```

2. **이후 배포는 자동으로 진행됩니다**
   ```bash
   # 코드 변경 후
   git add .
   git commit -m "Update: ..."
   git push

   # GitHub Actions가 자동으로 빌드 및 배포를 진행합니다
   ```

---

## 8. 문제 해결

### 서비스 로그 확인
```bash
# Backend 로그
sudo journalctl -u homepass-backend -f

# Frontend 로그
sudo journalctl -u homepass-frontend -f

# Nginx 로그
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### 서비스 재시작
```bash
sudo systemctl restart homepass-backend
sudo systemctl restart homepass-frontend
sudo systemctl restart nginx
```

### 포트 확인
```bash
# 서비스가 포트를 리스닝하는지 확인
sudo netstat -tlnp | grep 8000  # Backend
sudo netstat -tlnp | grep 3000  # Frontend
sudo netstat -tlnp | grep 80    # Nginx
```

### 방화벽 설정 (AWS Security Group)
EC2 인스턴스의 Security Group에서 다음 포트를 허용해야 합니다:
- **Inbound Rules:**
  - HTTP (80) - 0.0.0.0/0
  - HTTPS (443) - 0.0.0.0/0 (SSL 사용 시)
  - SSH (22) - Your IP only

### MySQL 데이터베이스 설치 (필요한 경우)
```bash
# MySQL 설치
sudo yum install -y mariadb105-server

# MySQL 시작
sudo systemctl start mariadb
sudo systemctl enable mariadb

# MySQL 보안 설정
sudo mysql_secure_installation

# 데이터베이스 생성
sudo mysql -u root -p
```

MySQL에서:
```sql
CREATE DATABASE homepass CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'homepass_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON homepass.* TO 'homepass_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 유용한 명령어

```bash
# 모든 서비스 상태 확인
sudo systemctl status homepass-backend homepass-frontend nginx

# 모든 서비스 재시작
sudo systemctl restart homepass-backend homepass-frontend nginx

# 디스크 사용량 확인
df -h

# 메모리 사용량 확인
free -h

# 실행 중인 프로세스 확인
ps aux | grep -E 'node|python|nginx'
```

---

## 다음 단계

1. ✅ SSL/TLS 인증서 설정 (Let's Encrypt)
2. ✅ 도메인 연결
3. ✅ 로그 로테이션 설정
4. ✅ 백업 전략 수립
5. ✅ 모니터링 설정 (CloudWatch, etc.)

---

## 지원

문제가 발생하면 다음을 확인하세요:
- GitHub Actions 워크플로우 로그
- EC2 인스턴스 로그 (`journalctl`)
- Nginx 에러 로그
- 애플리케이션 로그
