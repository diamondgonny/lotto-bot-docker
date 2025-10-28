# LottoBot Docker 운영 가이드

이 문서는 LottoBot Docker 컨테이너 운영을 위한 가이드입니다.

> **기본 설치는 [메인 README](README.md)를 참조하세요.**

## 📋 목차

- [서버 디렉토리 구조 예시](#서버-디렉토리-구조-예시)
- [모니터링](#모니터링)
- [백업](#백업)
- [트러블슈팅](#트러블슈팅)

## 🏗️ 서버 디렉토리 구조 예시

```
/home/user/
├── apps/
│   └── lotto-bot-docker/       # Git 저장소 클론
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
    └── lottobot/
        └── logs/               # lotto.py가 로그 파일 생성
            ├── lotto_log_XXXX.txt
            └── lotto_error.log
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
tail -f ~/docker/lottobot/logs/lotto_log_*.txt

# 특정 회차 로그 확인
cat ~/docker/lottobot/logs/lotto_log_1234.txt

# 에러 로그 확인
cat ~/docker/lottobot/logs/lotto_error.log
```

## 💾 백업

### 로그 백업 (필요시)

```bash
# 백업 디렉토리 생성 (없을시)
mkdir -p ~/docker/lottobot/backups

# 로그 디렉토리 전체 백업
tar -czf lottobot-logs-$(date +%Y%m%d).tar.gz ~/docker/lottobot/logs/

# 백업 파일 이동
mv lottobot-logs-*.tar.gz ~/docker/lottobot/backups/
```

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
2. 에러 로그 확인: `cat ~/docker/lottobot/logs/lotto_error.log`
3. dhapi 인증 정보 확인:
   ```bash
   # 컨테이너 내부 TOML 파일 확인 (entrypoint.sh가 생성)
   docker exec lottobot cat /root/.dhapi/credentials
   # [default] 섹션에 username과 password가 올바르게 생성되었는지 확인
   ```

### 문제: Discord 알림이 오지 않음

1. `.env` 파일 확인: `cat ~/.secrets/lottobot/.env`
2. Webhook URL 유효성 확인
3. 컨테이너 재시작

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
