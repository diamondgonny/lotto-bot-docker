# LottoBot Docker 운영 가이드

이 문서는 LottoBot Docker 컨테이너 운영을 위한 가이드입니다.

> **기본 설치는 [메인 README](README.md)를 참조하세요.**

## 📋 목차

- [모니터링](#모니터링)
- [백업](#백업)
- [트러블슈팅](#트러블슈팅)

## 📊 모니터링

### 컨테이너 상태 확인

```bash
# 컨테이너 실행 상태
docker ps | grep lotto-bot

# 컨테이너 로그
docker logs lotto-bot

# 실시간 로그
docker logs -f lotto-bot
```

### 로또 구매/당첨 로그 확인

```bash
# 최근 로그 확인
tail -f log/lotto_log_*.txt

# 특정 회차 로그 확인
cat log/lotto_log_1234.txt

# 에러 로그 확인
cat log/lotto_error.log
```

## 💾 백업

### 로그 백업 (필요시)

```bash
# 백업 디렉토리 생성 (없을시)
mkdir -p backups

# 로그 디렉토리 전체 백업
tar -czf lotto-bot-logs-$(date +%Y%m%d).tar.gz log/

# 백업 파일 이동
mv lotto-bot-logs-*.tar.gz backups/
```

## 🐛 트러블슈팅

### 문제: 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker logs lotto-bot

# 설정 파일 존재 확인
ls -la .credentials .env

# 권한 확인
ls -la .credentials
```

### 문제: 로또 구매 실패

1. DH Lottery 계정 잔액 확인 (웹사이트에서 직접 로그인)
2. 에러 로그 확인: `cat log/lotto_error.log`
3. dhapi 인증 정보 확인:
   ```bash
   # 컨테이너 내부 TOML 파일 확인 (entrypoint.sh가 생성)
   docker exec lotto-bot cat /home/lottobot/.dhapi/credentials
   # [default] 섹션에 username과 password가 올바르게 생성되었는지 확인
   # .credentials 파일의 환경변수가 올바르게 로드되었는지 확인합니다.
   ```

### 문제: Discord 알림이 오지 않음

1. `.env` 파일 확인: `cat .env`
2. Webhook URL 유효성 확인
3. 설치된 crontab에 환경 변수가 포함되었는지 확인:
   ```bash
   docker exec lotto-bot crontab -l
   ```
4. 컨테이너 재시작

### 문제: Cron이 실행되지 않음

```bash
# 컨테이너 내부 진입
docker exec -it lotto-bot bash

# Cron 상태 확인
ps aux | grep cron

# Crontab 확인
crontab -l

# Cron 로그 확인
cat /var/log/cron.log
```
