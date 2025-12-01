# 당신이 해야 할 작업 체크리스트

## ✅ 완료된 작업 (자동으로 생성됨)

- [x] GitHub Actions 워크플로우 생성
- [x] Systemd 서비스 파일 생성
- [x] Nginx 설정 파일 생성
- [x] 배포 가이드 문서 작성
- [x] 환경 변수 템플릿 파일 생성
- [x] EC2 초기 설정 스크립트 생성

---

## 📋 당신이 해야 할 작업

### 1️⃣ GitHub 저장소 설정 (로컬 컴퓨터에서)

```bash
# 현재 디렉토리에서 실행
cd /Users/mindong-il/pass

# Git 초기화
git init

# 모든 파일 추가
git add .

# 첫 커밋
git commit -m "Initial commit: Setup HomePass deployment"

# GitHub에서 새 저장소를 생성한 후 (예: homepass)
# 원격 저장소 연결 (YOUR_USERNAME을 본인 계정으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/homepass.git

# 메인 브랜치로 변경
git branch -M main

# 푸시
git push -u origin main
```

### 2️⃣ GitHub Actions Secrets 설정

1. GitHub 저장소로 이동
2. Settings → Secrets and variables → Actions 클릭
3. "New repository secret" 버튼 클릭
4. 다음 3개의 Secrets 추가:

#### EC2_SSH_PRIVATE_KEY
```bash
# 로컬 터미널에서 PEM 파일 내용 복사
cat /Users/mindong-il/pass/inha-capstone-10.pem
```
- Name: `EC2_SSH_PRIVATE_KEY`
- Secret: 위 명령어로 출력된 전체 내용 붙여넣기 (-----BEGIN부터 -----END까지)

#### EC2_HOST
- Name: `EC2_HOST`
- Secret: `ec2-35-82-41-239.us-west-2.compute.amazonaws.com`

#### EC2_USER
- Name: `EC2_USER`
- Secret: `ec2-user`

### 3️⃣ AWS Security Group 설정

1. AWS EC2 Console로 이동
2. 인스턴스 선택 → Security → Security groups 클릭
3. Inbound rules → Edit inbound rules
4. 다음 규칙 추가:

| Type  | Protocol | Port Range | Source    | Description        |
|-------|----------|------------|-----------|--------------------|
| HTTP  | TCP      | 80         | 0.0.0.0/0 | Web traffic        |
| HTTPS | TCP      | 443        | 0.0.0.0/0 | Secure web traffic |
| SSH   | TCP      | 22         | My IP     | SSH access         |

### 4️⃣ EC2 서버 초기 설정

```bash
# EC2 서버 접속
ssh -i inha-capstone-10.pem ec2-user@ec2-35-82-41-239.us-west-2.compute.amazonaws.com

# 초기 설정 스크립트 다운로드 및 실행
# (GitHub에 푸시한 후)
cd ~
git clone https://github.com/YOUR_USERNAME/homepass.git
cd homepass
chmod +x deployment/setup-ec2.sh
./deployment/setup-ec2.sh

# 또는 수동으로 설치 (아래 명령어들 실행)
```

#### 수동 설치 명령어:
```bash
# 시스템 업데이트
sudo yum update -y

# Node.js 20 설치
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs

# Python 3.11 설치
sudo yum install -y python3.11 python3.11-pip

# Git 설치
sudo yum install -y git

# Nginx 설치
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# MariaDB 설치
sudo yum install -y mariadb105-server
sudo systemctl start mariadb
sudo systemctl enable mariadb

# MariaDB 보안 설정
sudo mysql_secure_installation
```

### 5️⃣ 데이터베이스 생성

```bash
# MySQL 접속
sudo mysql -u root -p
```

MySQL에서 실행:
```sql
CREATE DATABASE homepass CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'homepass_user'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON homepass.* TO 'homepass_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 6️⃣ 환경 변수 파일 생성 (EC2에서)

#### Backend 환경 변수
```bash
nano ~/homepass/homepass-backend/.env
```
내용 (예시 파일 참고하여 수정):
```env
DATABASE_URL=mysql+aiomysql://homepass_user:STRONG_PASSWORD_HERE@localhost:3306/homepass
JWT_SECRET=your-super-secret-jwt-key-change-this-to-random-string
JWT_ALGORITHM=HS256
CORS_ORIGINS=["http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com"]
```

#### Frontend 환경 변수
```bash
nano ~/homepass/homepass-front/.env.local
```
내용:
```env
NEXT_PUBLIC_API_URL=http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com/api
```

#### Scraper 환경 변수
```bash
nano ~/homepass/homepass-scraper/.env
```
내용:
```env
DB_HOST=localhost
DB_USER=homepass_user
DB_PASSWORD=STRONG_PASSWORD_HERE
DB_NAME=homepass
```

### 7️⃣ 프로젝트 초기 빌드 (EC2에서)

```bash
cd ~/homepass

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

### 8️⃣ Systemd 서비스 설정 (EC2에서)

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

# 서비스 상태 확인
sudo systemctl status homepass-backend
sudo systemctl status homepass-frontend
```

### 9️⃣ Nginx 설정 (EC2에서)

```bash
# Nginx 설정 파일 복사
sudo cp ~/homepass/deployment/nginx/homepass.conf /etc/nginx/conf.d/homepass.conf

# 설정 파일 문법 검사
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 🔟 테스트

브라우저에서 다음 URL 접속:
- Frontend: http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com/
- Backend API Docs: http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com/docs

---

## 🎉 완료!

이제 코드를 수정하고 GitHub에 푸시하면 자동으로 배포됩니다:

```bash
# 로컬에서
git add .
git commit -m "Update: feature description"
git push
```

GitHub Actions가 자동으로:
1. ✅ Frontend 빌드 및 린트 검사
2. ✅ Backend import 테스트
3. ✅ Scraper import 테스트
4. ✅ EC2에 배포
5. ✅ 서비스 재시작

---

## 🔧 문제 해결

### 서비스가 시작되지 않을 때
```bash
# 로그 확인
sudo journalctl -u homepass-backend -f
sudo journalctl -u homepass-frontend -f

# 서비스 재시작
sudo systemctl restart homepass-backend
sudo systemctl restart homepass-frontend
```

### Nginx 에러
```bash
# Nginx 로그 확인
sudo tail -f /var/log/nginx/error.log

# Nginx 재시작
sudo systemctl restart nginx
```

### 포트 확인
```bash
# 서비스가 포트를 리스닝하는지 확인
sudo netstat -tlnp | grep 3000  # Frontend
sudo netstat -tlnp | grep 8000  # Backend
sudo netstat -tlnp | grep 80    # Nginx
```

---

## 📚 추가 문서

- 상세 배포 가이드: `deployment/DEPLOYMENT_GUIDE.md`
- 빠른 시작 가이드: `deployment/QUICK_START.md`
- 프로젝트 README: `README.md`

---

## ⚠️ 주의사항

1. **.env 파일은 절대 Git에 커밋하지 마세요!** (.gitignore에 이미 추가됨)
2. PEM 키 파일은 안전하게 보관하세요
3. 데이터베이스 비밀번호는 강력하게 설정하세요
4. JWT_SECRET은 랜덤한 긴 문자열로 설정하세요
5. 정기적으로 시스템 백업을 수행하세요

---

**질문이나 문제가 있으면 생성된 문서들을 참고하세요!**
