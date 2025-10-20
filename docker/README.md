# LottoBot Docker 배포 가이드

이 문서는 LottoBot을 Docker 환경에서 운영하기 위한 서버 설정 가이드입니다.

## 📋 사전 요구사항

- Docker 및 Docker Compose 설치
- DH Lottery 계정 (회원가입 필수)
- (선택) Discord Webhook URL

## 🏗️ 서버 디렉토리 구조

```
/home/ubuntu/
├── services/
│   └── lotto-bot-docker/              # Git 저장소 클론
│       ├── Dockerfile
│       ├── docker-compose.yml
│       ├── entrypoint.sh
│       ├── crontab
│       ├── lotto.py
│       └── ...
│
├── .secrets/
│   └── lottobot/
│       ├── credentials         # DH Lottery 로그인 정보
│       └── .env                # Discord webhook URL
│
└── docker/
    ├── volumes/
    │   └── lottobot/
    │       └── .dhapi/         # dhapi 설정 (자동 생성)
    │
    └── logs/
        └── lottobot/           # 로그 파일 (자동 생성)
            ├── lotto_log_XXXX.txt
            └── lotto_error.log
```

## 🚀 설치 및 배포 단계

### 1. 저장소 클론

```bash
mkdir -p ~/services
cd ~/services
git clone https://github.com/diamondgonny/lotto-bot-docker.git
cd lotto-bot-docker
```

### 2. 시크릿 디렉토리 생성 및 설정

```bash
# 시크릿 디렉토리 생성
mkdir -p ~/.secrets/lottobot

# 템플릿 복사
cp .secrets-template/credentials.template ~/.secrets/lottobot/credentials
cp .secrets-template/.env.template ~/.secrets/lottobot/.env

# 편집
vim ~/.secrets/lottobot/credentials
vim ~/.secrets/lottobot/.env
```

**credentials 파일 내용:**
```toml
[default]
username = "your_dhlottery_id"
password = "your_dhlottery_password"
```

**\.env 파일 내용:**
```env
discord_webhook_url="https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN"
```

### 3. 로그 디렉토리 생성

```bash
mkdir -p ~/docker/logs/lottobot
mkdir -p ~/docker/volumes/lottobot
```

### 4. Docker 이미지 빌드 및 실행

```bash
cd ~/services/lotto-bot-docker

# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker logs -f lottobot
```

## 📊 모니터링

### 컨테이너 상태 확인

```bash
# 컨테이너 실행 상태
docker ps | grep lottobot

# 컨테이너 로그
docker logs lottobot

# 실시간 로그
docker logs -f lottobot
```

### 로또 구매/당첨 로그 확인

```bash
# 최근 로그 확인
tail -f ~/docker/logs/lottobot/lotto_log_*.txt

# 특정 회차 로그 확인
cat ~/docker/logs/lottobot/lotto_log_1234.txt

# 에러 로그 확인
cat ~/docker/logs/lottobot/lotto_error.log
```

### 수동 실행 (테스트용)

```bash
# 컨테이너 내부에서 수동 실행
docker exec lottobot /usr/local/bin/python /app/lotto.py
```

## ⏰ Cron 스케줄

- **실행 시간**: 매주 일요일 오전 9시 20분 (KST)
- **작업 내용**:
  1. 지난 회차 당첨 결과 확인
  2. 현재 회차 로또 구매 (자동 5게임, 5,000원)

**스케줄 변경 방법:**
1. `crontab` 파일 수정
2. 이미지 재빌드: `docker-compose up -d --build`

## 💾 백업

### 로그 백업

```bash
# 로그 디렉토리 전체 백업
tar -czf lottobot-logs-$(date +%Y%m%d).tar.gz ~/docker/logs/lottobot/

# 백업 디렉토리로 이동
mkdir -p ~/docker/backups/volumes/lottobot
mv lottobot-logs-*.tar.gz ~/docker/backups/volumes/lottobot/
```

## 🔒 보안 권고사항

1. **시크릿 파일 권한 설정**:
   ```bash
   chmod 600 ~/.secrets/lottobot/credentials
   chmod 600 ~/.secrets/lottobot/.env
   ```

2. **정기적인 비밀번호 변경** (DH Lottery 계정)

## 🐛 트러블슈팅

### 문제: 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker logs lottobot

# 설정 파일 존재 확인
ls -la ~/.secrets/lottobot/

# 권한 확인
ls -la ~/.secrets/lottobot/credentials
```

### 문제: 로또 구매 실패

1. DH Lottery 계정 잔액 확인 (웹사이트에서 직접 로그인)
2. 에러 로그 확인: `cat ~/docker/logs/lottobot/lotto_error.log`
3. dhapi 인증 정보 확인: `~/.secrets/lottobot/credentials`

### 문제: Discord 알림이 오지 않음

1. `.env` 파일 확인: `cat ~/.secrets/lottobot/.env`
2. Webhook URL 유효성 확인
3. 컨테이너 재시작: `docker-compose restart`

### 문제: Cron이 실행되지 않음

```bash
# 컨테이너 내부 진입
docker exec -it lottobot bash

# Cron 상태 확인
ps aux | grep cron

# Crontab 확인
crontab -l

# Cron 로그 확인
cat /var/log/cron.log
```

## 📝 참고사항

- **구매 한도**: 회차당 5,000원 (5게임)
- **추첨 시간**: 매주 토요일 20:35 KST
- **당첨금 수령**: DH Lottery 웹사이트에서 등록된 계좌로만 출금 가능
- **첫 실행**: 첫 실행 시 `FileNotFoundError`는 정상 (이전 로그 파일 없음)
