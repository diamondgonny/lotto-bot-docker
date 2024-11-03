import subprocess
import os
import re
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

"""
1. dhapi를 활용한 구매 -> 구매 내역 기록(lotto_log_OOOO.txt) -> 디스코드 알림
"""

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
    """dhapi 사용 후 표준 에러 출력을 확인하고 해당되는 예외를 발생"""
    error_types = {
        "FileNotFoundError": FileNotFoundError,
        "KeyError": KeyError,
        "RuntimeError": RuntimeError,
        "ValueError": ValueError
    }
    error_message = stderr_output.strip()
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

def extract_lotto_numbers(log_path, round_number, target_saturday):
    """구매한 로또 번호 파싱"""
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
        pattern = r'│\s+([A-E])\s+│\s+(\S+)\s+│\s+(\d+)\s+│\s+(\d+)\s+│\s+(\d+)\s+│\s+(\d+)\s+│\s+(\d+)\s+│\s+(\d+)\s+│'
        matches = re.finditer(pattern, content)
        results = []
        for match in matches:
            slot = match.group(1)  # A, B, C, D, E
            mode = match.group(2)  # 자동/반자동/수동
            # 숫자는 정수형으로 변환하여 당첨 확인에 사용
            numbers = [int(match.group(i)) for i in range(3, 9)]
            # 결과 저장 시 숫자를 두 자리 문자열로 변환
            formatted_numbers = [f"{num:02d}" for num in numbers]
            result = [slot, mode] + formatted_numbers
            results.append(result)
        # 구매 번호만 기록
        output_lines = []
        target_saturday_ymd = target_saturday.strftime('%Y-%m-%d')
        output_lines.append(f"=== {round_number}회({target_saturday_ymd} 추첨) 구매 완료 ===")
        for result in results:
            formatted_result = ", ".join(str(x) for x in result)
            output_lines.append(f"[{formatted_result}]")
        overall_results = '\n'.join(output_lines) + '\n'
        return overall_results

def check_buy_and_report_lotto(log_dir):
    """에치금 확인, 로또 구매 및 결과 기록을 수행"""
    today = datetime.now().strftime('%Y-%m-%d')
    round_number, target_saturday = get_lotto_round_and_target_date(today)
    log_filename = f'lotto_log_{round_number}.txt'
    log_path = os.path.join(log_dir, log_filename)
    result_check = run_dhapi_command(['dhapi', 'show-balance'])
    result_buy = run_dhapi_command(['dhapi', 'buy-lotto645', '-y'])
    log_content = (
        f"=== {round_number}회 ({target_saturday} 추첨)==="
        f"\n{result_check.stdout}\n{result_buy.stdout}\n"
    )
    write_to_log(log_path, log_content)
    res = extract_lotto_numbers(log_path, round_number, target_saturday)
    return res

"""
2. 최근 구매 내역 파일(lotto_log_OOOO.txt) 열기 -> 당첨 결과 확인 및 기록 -> 디스코드 알림
"""

def get_latest_log_file(directory='log'):
    """저장된 최근 구매 내역 (최신 회차) 파일을 반환"""
    try:
        prefix = "lotto_log_"
        files = [f for f in os.listdir(directory) if f.startswith(prefix)]
        if not files:
            raise FileNotFoundError(f"Lotto log file ({prefix}OOOO) not found.")
        return max(files, key=lambda x: int(re.search(r'(\d+)\.txt$', x).group(1)))
    except (ValueError, AttributeError):
        raise ValueError("Invalid log file name format found.")
    except Exception as e:
        raise Exception(str(e))

def process_lotto_results(filename, log_dir):
    """구매한 최신 회차 중 당첨 여부 확인"""
    round_num = re.search(r'lotto_log_(\d+)\.txt', filename).group(1)
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={round_num}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"{round_num}회차 당첨 정보를 조회할 수 없습니다.")
    lotto_data = response.json()
    if lotto_data.get("returnValue") != "success":
        raise Exception(f"{round_num}회차 당첨 정보가 아직 없습니다.")

    # 당첨 번호 세트 및 당첨 번호 확인 알고리즘 생성
    draw_date = lotto_data['drwNoDate']
    winning_numbers = {lotto_data[f'drwtNo{i}'] for i in range(1, 7)}
    bonus_number = lotto_data['bnusNo']
    def check_prize(numbers):
        matched = len(set(numbers) & winning_numbers)
        prize_dict = {
            6: "1등!(6)",
            5: "2등!(5+)" if bonus_number in numbers else "3등!(5)",
            4: "4등!(4)",
            3: "5등!(3)",
            2: "낙첨(2)",
            1: "낙첨(1)",
            0: "낙첨(0)"
        }
        return prize_dict[matched]

    # 파일 읽기 및 파싱
    log_path = os.path.join(log_dir, filename)
    with open(log_path, 'r+', encoding='utf-8') as f:
        content = f.read()
        if "당첨 결과" in content:
            return "이미 당첨 확인하셨습니다."

        # 구매한 로또 번호 파싱
        pattern = r'│\s+([A-E])\s+│\s+(\S+)\s+│\s+(\d+)\s+│\s+(\d+)\s+│\s+(\d+)\s+│\s+(\d+)\s+│\s+(\d+)\s+│\s+(\d+)\s+│'
        matches = re.finditer(pattern, content)
        results = []
        for match in matches:
            slot = match.group(1)  # A, B, C, D, E
            mode = match.group(2)  # 자동/반자동/수동
            # 숫자는 정수형으로 변환하여 당첨 확인에 사용
            numbers = [int(match.group(i)) for i in range(3, 9)]
            prize = check_prize(numbers)
            # 결과 저장 시 숫자를 두 자리 문자열로 변환
            formatted_numbers = [f"{num:02d}" for num in numbers]
            result = [slot, mode] + formatted_numbers
            result.append(prize)
            results.append(result)

        # 당첨 결과 기록
        output_lines = []
        winning_str = [f"{num:02d}" for num in sorted(list(winning_numbers))]
        bonus_str = f"({bonus_number:02d})"
        output_lines.append(f"\n=== {round_num}회({draw_date} 추첨) 당첨 결과 ===")
        output_lines.append(f"당첨 번호: [{', '.join(winning_str)}, {bonus_str}]")
        for result in results:
            formatted_result = ", ".join(str(x) for x in result)
            output_lines.append(f"[{formatted_result}]")
        overall_results = '\n'.join(output_lines) + '\n'
        f.write(overall_results)
        return overall_results


if __name__ == "__main__":
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
    os.makedirs(log_dir, exist_ok=True)
    today_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def handle_error_1(e, log_dir, today_datetime):
        """에러 로깅 및 출력을 처리하는 함수1 (dhapi으로부터 기록된 stderr에서 파싱한 것)"""
        error_log_path = os.path.join(log_dir, 'lotto_error.log')
        with open(error_log_path, 'a') as f:
            f.write(f"{today_datetime} - {str(e)}\n")
        print(str(e))

    def handle_error_2(e, log_dir, today_datetime):
        """에러 로깅 및 출력을 처리하는 함수2 """
        error_message = f"{type(e).__name__}: {str(e)}"
        error_log_path = os.path.join(log_dir, 'lotto_error.log')
        with open(error_log_path, 'a') as f:
            f.write(f"{today_datetime} - {error_message}\n")
        print(error_message)

    try:
        msg_str = check_buy_and_report_lotto(log_dir)
        print(msg_str)
        round_number, target_saturday = get_lotto_round_and_target_date(datetime.now().strftime('%Y-%m-%d'))
        res = extract_lotto_numbers('log/lotto_log_1144.txt', round_number, target_saturday)
        print(res)
    except (RuntimeError, ValueError, AttributeError, FileNotFoundError, KeyError) as e:
        handle_error_1(e, log_dir, today_datetime)
    except Exception as e:
        handle_error_1(e, log_dir, today_datetime)

    try:
        file = get_latest_log_file()
        res = process_lotto_results(file, log_dir)
        print(res)
    except (RuntimeError, ValueError, AttributeError, FileNotFoundError, KeyError) as e:
        handle_error_2(e, log_dir, today_datetime)
    except Exception as e:
        handle_error_2(e, log_dir, today_datetime)
