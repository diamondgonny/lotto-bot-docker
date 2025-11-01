# LottoBot

[![Docker Hub](https://img.shields.io/docker/v/diamondgonny/lotto-bot?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/diamondgonny/lotto-bot)
[![Docker Image Size](https://img.shields.io/docker/image-size/diamondgonny/lotto-bot/latest)](https://hub.docker.com/r/diamondgonny/lotto-bot)
[![Docker Pulls](https://img.shields.io/docker/pulls/diamondgonny/lotto-bot)](https://hub.docker.com/r/diamondgonny/lotto-bot)

[비공식 동행복권 API(dhapi)](https://github.com/roeniss/dhlottery-api)를 활용한 로또 당첨 자동 확인 및 자동 구매 프로그램입니다. Discord를 통한 알림 기능을 지원합니다.

![lotto-bot-discord](https://github.com/user-attachments/assets/4ac7a958-51c8-4d58-9cfc-e5cb6ba56323)

> **⚠️ 중요**: 이 저장소는 **Docker 전용**으로 개편되었습니다.

## 📚 목차
- [Docker Hub에서 이미지 사용 (권장)](#docker-hub에서-이미지-사용-권장)
- [로컬에서 빌드 및 실행](#로컬에서-빌드-및-실행)
- [사용 방법](#사용-방법)
- [주의사항](#주의사항)

---

## Docker Hub에서 이미지 사용 (권장)

Docker Hub에 미리 빌드된 이미지를 사용하면 빌드 과정 없이 바로 실행할 수 있습니다.

### 사전 준비
- Docker 및 Docker Compose 설치
- 동행복권 홈페이지 회원가입

### 1. 작업 디렉토리 생성
```shell
mkdir lotto-bot && cd lotto-bot
```

### 2. 설정 파일 생성
```shell
# credentials 파일 생성
cat > credentials << 'EOF'
# DH Lottery Credentials
DHLOTTERY_USERNAME="your_dhlottery_id"
DHLOTTERY_PASSWORD="your_dhlottery_password"
EOF

# .env 파일 생성
cat > .env << 'EOF'
# Discord Webhook
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
EOF

# 파일 권한 설정 (선택사항)
chmod 600 credentials .env
```

**credentials**와 **.env** 파일을 편집하여 실제 정보를 입력하세요.

### 3. docker-compose.yml 파일 생성
```shell
cat > docker-compose.yml << 'EOF'
services:
  lotto-bot:
    image: diamondgonny/lotto-bot:latest
    container_name: lotto-bot
    restart: unless-stopped

    environment:
      - TZ=Asia/Seoul

    env_file:
      - ./.env
      - ./credentials

    volumes:
      - ./log:/app/log
EOF
```

### 4. Docker 실행
```shell
# 컨테이너 시작
docker compose up -d

# 실시간 로그 확인
docker logs -f lotto-bot
```

**자세한 사용법 및 트러블슈팅은 [OPERATION.md](OPERATION.md)를 참조하세요.**

---

## 로컬에서 빌드 및 실행

소스 코드를 수정하거나 직접 빌드하려는 경우 이 방법을 사용하세요.

### 사전 준비
- Docker 및 Docker Compose 설치
- 동행복권 홈페이지 회원가입

### 1. 저장소 복사
```shell
git clone https://github.com/diamondgonny/lotto-bot-docker.git
cd lotto-bot-docker
```

### 2. 설정 파일 생성
```shell
# 템플릿 복사
cp credentials.example credentials
cp .env.example .env

# 설정 파일 편집
vim credentials
vim .env

# 파일 권한 설정 (선택사항)
chmod 600 credentials .env
```

**credentials:**
```env
# DH Lottery Credentials
DHLOTTERY_USERNAME="your_dhlottery_id"
DHLOTTERY_PASSWORD="your_dhlottery_password"
```

**.env:**
```env
# Discord Webhook
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
```

### 3. Docker 실행
```shell
# 빌드 및 실행
docker compose up -d

# 실시간 로그
docker logs -f lotto-bot
```

**자세한 사용법 및 트러블슈팅은 [OPERATION.md](OPERATION.md)를 참조하세요.**

---

## 사용 방법

### 자동 실행 (Cron)
Docker 환경에서는 cron이 컨테이너 내부에서 자동으로 실행됩니다.
- **기본 스케줄**: 매주 일요일 오전 9시 20분 (KST)
- **변경 방법**: `crontab` 파일 수정 후 `docker compose up -d --build`

### 수동 실행 (테스트)
```shell
# 컨테이너 내부에서 직접 실행
docker exec lotto-bot /usr/local/bin/python /app/lotto.py
```

### 로그 파일 구조
로그는 프로젝트 루트의 `log/` 디렉토리에 자동으로 생성됩니다.
- `lotto_error.log`: 에러 로그
- `lotto_log_[회차번호].txt`: 구매 및 당첨 내역


## 주의사항

### 1. 프로그램 사용 관련
1. Discord 알림을 사용하지 않을 경우 `.env`에서 `DISCORD_WEBHOOK_URL` 값을 비워두거나 제거하면 됩니다.
2. 프로그램 첫 실행 시 안내:
    - 이 프로그램은 '지난 회차 당첨 확인 + 이번 회차 구매' 기능을 포함합니다.
    - 첫 구매 시에는 '로또 구매 내역(lotto_log_[회차번호].txt)을 찾을 수 없습니다.' 에러 메시지가 표시됩니다.
    - 이는 이전 회차의 구매 기록이 없어서 발생하는 부분이므로 걱정하지 않으셔도 됩니다.

### 2. 구매 및 충전 제한
1. 온라인 로또 6/45의 회차당 최대 구매 한도는 5줄(5,000원)입니다.
2. 예치금은 동행복권 사이트에서 직접 충전하셔야 합니다.
3. 출금은 본인 명의 계좌로만 가능합니다.

### 3. 보안 관련 안내
#### 위험 수준
- 구매 한도가 제한적이고 본인 명의 계좌로만 출금이 가능하므로, 혹시라도 사용자 인증 정보가 노출되었을 때에 발생할 수 있는 피해는 제한적입니다.
#### 인증 방식
- 동행복권 사이트는 JSESSIONID로 유저를 인증합니다.
- 이 프로그램이 사용하는 dhapi는 requests를 이용해 로그인한 후 발급받은 JSESSIONID를 복권 구매에 활용합니다.
#### 보안 제안사항
- dhapi의 신뢰성이 우려되시는 경우:
    - [비공식 동행복권 API(dhapi)](https://github.com/roeniss/dhlottery-api)에서 코드를 검토하실 수 있습니다.
#### 보안 기능
- 외부 접근으로부터 격리 (인바운드 포트 노출 없음)
- Docker 이미지에 인증 정보가 포함되지 않음
- 로그에 인증 정보가 노출되지 않음
