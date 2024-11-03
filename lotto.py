import subprocess
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

DISCORD_BOT = True

if DISCORD_BOT:
    load_dotenv()

"""
1) ~/.dhapi/credentials 파일 내 동행복권 ID/PW 저장 [필수]
[default]
username = "______"
password = "______"
2) .env 파일 내 디스코드 웹훅 URL 저장 [선택: DISCORD_BOT = True로 설정]
discord_webhook_url="https://discord.com/api/webhooks/______"
"""


def send_message(msg):
    """디스코드 메세지 전송"""
    if DISCORD_BOT:
        discord_webhook_url = os.getenv('discord_webhook_url')
        message = {"content": f"{str(msg)}"}
        requests.post(discord_webhook_url, data=message)

def get_lotto_round_and_target_date(target_date):
    """주어진 날짜의 로또 회차와 추첨일 계산"""
    # 입력받은 날짜를 datetime 객체로 변환 (이미 datetime인 경우는 그대로 사용)
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y-%m-%d')
        first_round_date = datetime(2002, 12, 7)
        if target_date < first_round_date:
            return None
    # 해당 주의 토요일 찾기
    days_until_saturday = (5 - target_date.weekday()) % 7
    target_saturday = target_date + timedelta(days=days_until_saturday)
    # 1회차부터 몇 주가 지났는지 계산
    weeks_difference = (target_saturday - first_round_date).days // 7
    # 회차 계산 (1회차부터 시작하므로 +1)
    round_number = weeks_difference + 1
    # 추첨 생방송 시간을 20:35:00으로 설정
    target_saturday = target_saturday.replace(hour=20, minute=35, second=0)
    return round_number, target_saturday

def check_error_in_stderr(stderr_output: str) -> Exception:
    """표준 에러 출력을 확인하고 해당되는 예외를 발생"""
    error_types = {
        "FileNotFoundError": FileNotFoundError,
        "KeyError": KeyError,
        "RuntimeError": RuntimeError,
        "ValueError": ValueError
    }
    error_message = stderr_output.strip()
    # 예외 처리
    for error_name, error_class in error_types.items():
        if error_name in stderr_output:
            raise error_class(error_message)
    if "Error" in stderr_output or "Exception" in stderr_output:
        raise Exception(error_message)

def run_dhapi_command(cmd):
    """dhapi 명령어를 subprocess로 실행하고 결과를 반환"""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stderr:
        check_error_in_stderr(result.stderr)
    return result

def write_to_log(file_path, content, mode='a'):
    """로그 파일에 내역 저장"""
    with open(file_path, mode) as f:
        f.write(content)

def check_buy_and_report_lotto():
    """에치금 확인, 로또 구매 및 결과 기록을 수행"""
    today = datetime.now().strftime('%Y-%m-%d')
    today_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    round_number, target_saturday = get_lotto_round_and_target_date(today)
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
    os.makedirs(log_dir, exist_ok=True)
    log_filename = f'lotto_log_{round_number}.txt'
    log_path = os.path.join(log_dir, log_filename)

    try:
        result_check = run_dhapi_command(['dhapi', 'show-balance'])
        result_buy = run_dhapi_command(['dhapi', 'buy-lotto645', '-y'])
        log_content = (
            f"=== {round_number}회 ({target_saturday} 추첨)==="
            f"\n{result_check.stdout}\n{result_buy.stdout}\n"
        )
        write_to_log(log_path, log_content)
        return "로또6/45 복권을 구매하였습니다."

    except (RuntimeError, ValueError, FileNotFoundError, KeyError) as e:
        error_log_path = os.path.join(log_dir, 'lotto_error.log')
        with open(error_log_path, 'a') as f:
            f.write(f"{today_datetime} - {str(e)}\n")
        return str(e)

    except Exception as e:
        error_log_path = os.path.join(log_dir, 'lotto_error.log')
        with open(error_log_path, 'a') as f:
            f.write(f"{today_datetime} - {str(e)}\n")
        return str(e)


if __name__ == "__main__":
    msg_str = check_buy_and_report_lotto()
    if DISCORD_BOT:
        send_message(msg_str)
