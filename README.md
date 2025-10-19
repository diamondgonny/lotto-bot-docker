# LottoBot

[비공식 동행복권 API(dhapi)](https://github.com/roeniss/dhlottery-api)를 활용한 로또 당첨 자동 확인 및 자동 구매 프로그램입니다. Discord를 통한 알림 기능을 지원합니다.

![lotto-bot-discord](https://github.com/user-attachments/assets/4ac7a958-51c8-4d58-9cfc-e5cb6ba56323)

## 📚 목차
- [Docker를 사용한 설치 (권장)](#docker를-사용한-설치-권장)
- [일반 설치 (호스트 환경)](#일반-설치-호스트-환경)
- [사용 방법](#사용-방법)
- [주의사항](#주의사항)

---

## Docker를 사용한 설치 (권장)

Docker를 사용하면 환경 설정이 간편하고 관리가 용이합니다.

### 사전 준비
- Docker 및 Docker Compose 설치
- 동행복권 홈페이지 회원가입

### 1. 저장소 복사
```shell
git clone https://github.com/diamondgonny/lotto-bot.git
cd lotto-bot
```

### 2. 설정 파일 생성
```shell
# 시크릿 디렉토리 생성
mkdir -p ~/.secrets/lottobot

# 템플릿 복사
cp .secrets-template/credentials.template ~/.secrets/lottobot/credentials
cp .secrets-template/.env.template ~/.secrets/lottobot/.env

# 설정 파일 편집
nano ~/.secrets/lottobot/credentials
nano ~/.secrets/lottobot/.env
```

**~/.secrets/lottobot/credentials:**
```toml
[default]
username = "your_dhlottery_id"
password = "your_dhlottery_password"
```

**~/.secrets/lottobot/.env:**
```env
discord_webhook_url="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
```

### 3. 로그 디렉토리 생성
```shell
mkdir -p ~/docker/logs/lottobot
mkdir -p ~/docker/volumes/lottobot
```

### 4. Docker 실행
```shell
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker logs -f lottobot
```

### 5. 모니터링
```shell
# 로또 로그 확인
tail -f ~/docker/logs/lottobot/lotto_log_*.txt

# 에러 로그 확인
cat ~/docker/logs/lottobot/lotto_error.log

# 컨테이너 상태 확인
docker ps | grep lottobot
```

**자세한 Docker 사용법은 [docker/README.md](docker/README.md)를 참조하세요.**

---

## 일반 설치 (호스트 환경)

### 0. 사전 준비
- 필수 요구사항 : Python 3.7 이상
- 지원 운영체제 : macOS, Linux
- 동행복권 홈페이지에서 회원가입을 먼저 진행하셔야 합니다.

### 1. 저장소 복사
```shell
git clone https://github.com/diamondgonny/lotto-bot.git
cd lotto-bot
```

### 2. 파이썬 가상환경 설정 (선택사항)
```shell
python -m venv venv
source venv/bin/activate
```

### 3. 필요한 패키지 설치
```shell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 환경 설정
#### 4.1 동행복권 ID/PW 사용자 인증 설정
`~/.dhapi/credentials` 파일 생성:
```toml
[default]
username = "your_username"
password = "your_password"
```

#### 4.2 Discord 웹훅 설정 (선택사항)
프로젝트 폴더에 `.env` 파일 생성:
```env
discord_webhook_url="https://discord.com/api/webhooks/your_webhook_url"
```
Discord 알림봇을 사용하려면, 먼저 Discord에서 알림받을 서버와 채널을 정하고서 웹훅을 얻어와야 합니다. [(참고)](https://discordbot.tistory.com/35)

#### 4.3 Discord 알림봇 및 가상환경 사용 여부 설정
lotto.py 상단에서 설정을 변경할 수 있습니다:
```python
DISCORD_BOT = True   # Discord 알림봇 사용 여부
USE_VENV = True      # 가상환경 사용 여부 (Docker 사용 시: False)
VENV = "venv"        # 가상환경 폴더명
```

---

## 사용 방법

### 기본 실행
```shell
python lotto.py
```

### 자동 실행 설정

#### Docker 사용 시
Docker 환경에서는 cron이 컨테이너 내부에서 자동으로 실행됩니다.
- **기본 스케줄**: 매주 일요일 오전 9시 20분 (KST)
- **변경 방법**: `crontab` 파일 수정 후 `docker-compose up -d --build`

#### 호스트 환경 사용 시
`crontab -e` 명령어로 실행 스케줄을 추가하세요. (예시: 매주 일요일 오전 9시에 실행, 가상환경 사용)
```shell
0 9 * * SUN cd {YOUR_PROJECT_PATH}/lotto-bot/ && {YOUR_PROJECT_PATH}/lotto-bot/venv/bin/python {YOUR_PROJECT_PATH}/lotto-bot/lotto.py
```

### log 파일 구조
프로그램을 처음 실행할 때 log 폴더와 파일이 자동으로 만들어집니다.
- `log/lotto_error.log`: 에러 로그
- `log/lotto_log_[회차번호].txt`: 구매 및 당첨 내역


## 주의사항

### 1. 프로그램 사용 관련
1. Discord 알림을 사용하지 않을 경우 `DISCORD_BOT = False`로 설정하세요.
2. 가상환경을 사용하지 않을 경우 `USE_VENV = False`로 설정하세요. (Docker 사용 시 자동 설정됨)
3. 프로그램 첫 실행 시 안내:
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
1. dhapi의 신뢰성이 걱정되시는 경우:
    - [비공식 동행복권 API(dhapi)](https://github.com/roeniss/dhlottery-api)에서 코드를 검토하실 수 있습니다.
2. 사용자 인증 정보의 보안이 우려되시는 경우:
    - 개인 PC에서만 프로그램을 사용하고 ~/.dhapi/credentials 파일을 안전하게 관리하여 사용자 인증 정보가 노출되지 않도록 주의하시기 바랍니다.
    - 동행복권 비밀번호를 다른 서비스와 다르게 설정하시기를 권장합니다.
