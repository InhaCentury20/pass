# 빠른 시작 가이드

## 당신이 해야 할 작업들

### 1. GitHub 저장소 생성 및 코드 푸시

```bash
# 로컬에서 (현재 디렉토리에서)
git init
git add .
git commit -m "Initial commit: Setup deployment"

# GitHub에서 새 저장소 생성 후
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### 2. GitHub Actions Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

필수 Secrets:
- **EC2_SSH_PRIVATE_KEY**: `inha-capstone-10.pem` 파일 전체 내용
- **EC2_HOST**: `ec2-35-82-41-239.us-west-2.compute.amazonaws.com`
- **EC2_USER**: `ec2-user`

### 3. EC2 서버에서 초기 설정

```bash
# 1. EC2 접속
ssh -i inha-capstone-10.pem ec2-user@ec2-35-82-41-239.us-west-2.compute.amazonaws.com

# 2. 시스템 업데이트
sudo yum update -y

# 3. Node.js 설치
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs

# 4. Python 3.11 설치
sudo yum install -y python3.11 python3.11-pip

# 5. Git 설치
sudo yum install -y git

# 6. Nginx 설치
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# 7. MySQL 설치 (필요한 경우)
sudo yum install -y mariadb105-server
sudo systemctl start mariadb
sudo systemctl enable mariadb
sudo mysql_secure_installation
```

### 4. 프로젝트 클론 및 설정

```bash
# 홈 디렉토리로 이동
cd ~

# 저장소 클론
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git homepass
cd homepass

# Frontend 빌드
cd homepass-front
npm install
npm run build
cd ..

# Backend 가상환경 설정
cd homepass-backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Scraper 가상환경 설정
cd homepass-scraper
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..
```

### 5. 환경 변수 설정

```bash
# Backend .env
nano ~/homepass/homepass-backend/.env
```
내용:
```env
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/homepass
JWT_SECRET=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]
```

```bash
# Frontend .env.local
nano ~/homepass/homepass-front/.env.local
```
내용:
```env
NEXT_PUBLIC_API_URL=http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com/api
```

```bash
# Scraper .env
nano ~/homepass/homepass-scraper/.env
```
내용:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=homepass
```

### 6. Systemd 서비스 설정

```bash
# 서비스 파일 복사
sudo cp ~/homepass/deployment/systemd/homepass-backend.service /etc/systemd/system/
sudo cp ~/homepass/deployment/systemd/homepass-frontend.service /etc/systemd/system/
sudo cp ~/homepass/deployment/systemd/homepass-scraper.service /etc/systemd/system/

# Systemd 리로드
sudo systemctl daemon-reload

# 서비스 활성화 및 시작
sudo systemctl enable homepass-backend
sudo systemctl enable homepass-frontend
sudo systemctl start homepass-backend
sudo systemctl start homepass-frontend

# 상태 확인
sudo systemctl status homepass-backend
sudo systemctl status homepass-frontend
```

### 7. Nginx 설정

```bash
# Nginx 설정 파일 복사
sudo cp ~/homepass/deployment/nginx/homepass.conf /etc/nginx/conf.d/homepass.conf

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 8. AWS Security Group 설정

EC2 인스턴스의 Security Group에서 Inbound Rules 추가:
- HTTP (80): 0.0.0.0/0
- HTTPS (443): 0.0.0.0/0
- SSH (22): Your IP

### 9. 데이터베이스 설정 (MySQL 사용 시)

```bash
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

### 10. 브라우저에서 확인

- Frontend: http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com/
- Backend API Docs: http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com/docs

---

## 이후 배포

코드 변경 후:
```bash
git add .
git commit -m "Update: ..."
git push
```

GitHub Actions가 자동으로 빌드, 테스트 및 배포를 진행합니다!

---

## 문제 해결

### 서비스 로그 확인
```bash
sudo journalctl -u homepass-backend -f
sudo journalctl -u homepass-frontend -f
```

### 서비스 재시작
```bash
sudo systemctl restart homepass-backend
sudo systemctl restart homepass-frontend
sudo systemctl restart nginx
```

### 포트 확인
```bash
sudo netstat -tlnp | grep -E '3000|8000|80'
```

---

## 주의사항

1. `.env` 파일들은 **절대 Git에 커밋하지 마세요**
2. PEM 키는 안전하게 보관하세요
3. 데이터베이스 비밀번호는 강력하게 설정하세요
4. 정기적으로 백업을 수행하세요

---

더 자세한 내용은 `DEPLOYMENT_GUIDE.md`를 참조하세요.
