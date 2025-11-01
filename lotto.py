import os
import pytz
import re
import requests
import subprocess
from datetime import datetime, timedelta


# DISCORD_WEBHOOK_URL 환경변수가 설정되어 있으면 Discord 알림봇 사용
DISCORD_BOT = bool(os.getenv("DISCORD_WEBHOOK_URL", "").strip())
DHAPI_PATH = "/usr/local/bin/dhapi"
KST = pytz.timezone('Asia/Seoul')

if not os.path.exists(DHAPI_PATH):
    raise FileNotFoundError(
        f"dhapi executable not found at {DHAPI_PATH}. "
        "LottoBot now targets the Docker runtime; please run via docker-compose."
    )


"""
[필수] 동행복권 로그인: credentials 파일에 환경변수 형식으로 저장
DHLOTTERY_USERNAME="______"
DHLOTTERY_PASSWORD="______"
[선택] 디스코드 알림봇: 환경변수로 웹훅 URL 설정 (설정 시 자동 활성화)
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/______"
"""

def send_message_to_discord(msg):
    """디스코드 메세지 전송"""
    if not DISCORD_BOT:
        return
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not discord_webhook_url:
        print("Discord webhook URL not configured; skipping notification.")
        return
    discord_webhook_url = discord_webhook_url.strip()
    if not discord_webhook_url:
        print("Discord webhook URL empty after parsing; skipping notification.")
        return
    message = {"content": f"{str(msg)}"}
    try:
        requests.post(discord_webhook_url, data=message, timeout=10)
    except requests.exceptions.RequestException as exc:
        print(f"Failed to send Discord notification: {exc}")


"""
1. 최근 로또 구매 내역(예: lotto_log_1000.txt) 열기 -> 당첨 결과 확인 및 기록
"""

def get_latest_log_file(directory="log"):
    """저장된 최근 구매 내역 (최신 회차) 파일을 가져옴"""
    prefix = "lotto_log_"
    files = [f for f in os.listdir(directory) if f.startswith(prefix)]
    if not files:
        raise FileNotFoundError(f"로또 구매 내역({prefix}[회차번호].txt)을 찾을 수 없습니다.")
    # 파일 이름에서 몇 회차인지 숫자 추출
    def extract_number_from_filename(filename):
        match = re.search(r"^lotto_log_(\d+)\.txt$", filename)
        if not match:
            raise AttributeError(f"올바르지 않은 파일명 형식({filename})입니다.")
        return int(match.group(1))
    return max(files, key=extract_number_from_filename)

def get_winning_numbers(round_number):
    """회차별 당첨번호를 가져옴"""
    url = (
        f"https://www.dhlottery.co.kr/common.do?"
        f"method=getLottoNumber&"
        f"drwNo={round_number}"
    )
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        raise requests.RequestException(f"{round_number}회차 당첨 정보를 조회할 수 없습니다.")
    lotto_data = response.json()
    if lotto_data.get("returnValue") != "success":
        raise RuntimeError(f"{round_number}회차 당첨 정보가 아직 없습니다.")
    return lotto_data

def check_prize(numbers, winning_numbers, bonus_number):
    """당첨 여부 판별 및 결과를 확인"""
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

def process_lotto_results(log_dir):
    """1번 프로세스 진행하는 함수"""
    filename = get_latest_log_file(log_dir)
    round_number = re.search(r"^lotto_log_(\d+)\.txt$", filename).group(1)
    lotto_data = get_winning_numbers(round_number)
    draw_date = lotto_data["drwNoDate"]
    winning_numbers = {lotto_data[f"drwtNo{i}"] for i in range(1, 7)}
    bonus_number = lotto_data["bnusNo"]
    # 지난 번 구매한 로또 번호 기록 파일 열어서 처리
    log_path = os.path.join(log_dir, filename)
    with open(log_path, "r+", encoding="utf-8") as f:
        content = f.read()
        if "당첨 결과" in content:
            return "이미 당첨 확인하셨습니다."
        # 구매한 로또 번호 파싱
        pattern = (
            r"│\s+([A-E])\s+│"
            r"\s+(\S+)\s+│"
            r"\s+(\d+)\s+│"
            r"\s+(\d+)\s+│"
            r"\s+(\d+)\s+│"
            r"\s+(\d+)\s+│"
            r"\s+(\d+)\s+│"
            r"\s+(\d+)\s+│"
        )
        matches = re.finditer(pattern, content)
        results = []
        for match in matches:
            slot = match.group(1)  # A, B, C, D, E
            mode = match.group(2)  # 자동/반자동/수동
            # 숫자는 정수형으로 변환하여 당첨 확인에 사용
            numbers = [int(match.group(i)) for i in range(3, 9)]
            prize = check_prize(numbers, winning_numbers, bonus_number)
            # 결과 저장 시 숫자를 두 자리 문자열로 변환
            formatted_numbers = [f"{num:02d}" for num in numbers]
            result = [slot, mode] + formatted_numbers
            result.append(prize)
            results.append(result)
        # 당첨 결과 기록
        output_lines = []
        winning_str = [f"{num:02d}" for num in sorted(list(winning_numbers))]
        bonus_str = f"({bonus_number:02d})"
        output_lines.append(f"\n=== {round_number}회({draw_date} 추첨) 당첨 결과 ===")
        output_lines.append(f"당첨 번호: [{', '.join(winning_str)}, {bonus_str}]")
        for result in results:
            formatted_result = ", ".join(str(x) for x in result)
            output_lines.append(f"[{formatted_result}]")
        overall_results = "\n".join(output_lines) + "\n"
        f.write(overall_results)
        return overall_results


"""
2. dhapi를 활용한 로또 구매 -> 로또 구매 내역(예: lotto_log_1001.txt) 기록
"""

def get_lotto_round_and_target_date(target_date):
    """주어진 날짜의 로또 회차와 추첨일 계산해서 가져옴"""
    # 로또 1회차 추첨일 정의
    first_round_date = KST.localize(datetime(2002, 12, 7))
    # 입력받은 날짜를 datetime 객체로 변환 (이미 datetime인 경우는 그대로 사용)
    if isinstance(target_date, str):
        target_date = KST.localize(datetime.strptime(target_date, "%Y-%m-%d"))
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
    """dhapi 명령어를 subprocess로 실행"""
    cmd[0] = DHAPI_PATH
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stderr:
        check_error_in_stderr(result.stderr)
    return result

def write_to_log(file_path, content, mode="a"):
    """구매한 로또 내역 로그 파일에 기록"""
    with open(file_path, mode) as f:
        f.write(content)

def report_lotto_numbers(log_path, round_number, target_saturday):
    """구매한 로또 번호 파싱하여 디스코드에 보고 준비"""
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
        pattern = (
            r"│\s+([A-E])\s+│"
            r"\s+(\S+)\s+│"
            r"\s+(\d+)\s+│"
            r"\s+(\d+)\s+│"
            r"\s+(\d+)\s+│"
            r"\s+(\d+)\s+│"
            r"\s+(\d+)\s+│"
            r"\s+(\d+)\s+│"
        )
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
    output_lines = []
    target_saturday_ymd = target_saturday.strftime("%Y-%m-%d")
    output_lines.append(f"=== {round_number}회({target_saturday_ymd} 추첨) 구매 완료 ===")
    for result in results:
        formatted_result = ", ".join(str(x) for x in result)
        output_lines.append(f"[{formatted_result}]")
    return "\n".join(output_lines) + "\n"

def check_buy_and_report_lotto(log_dir):
    """2번 프로세스 진행하는 함수"""
    today = datetime.now(KST).strftime("%Y-%m-%d")
    current_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    round_number, target_saturday = get_lotto_round_and_target_date(today)
    log_filename = f"lotto_log_{round_number}.txt"
    log_path = os.path.join(log_dir, log_filename)
    # 잔액 확인 및 로또 구매 실행 (check)
    result_check = run_dhapi_command(["dhapi", "show-balance"])
    # 로그 파일 작성 (buy)
    result_buy = run_dhapi_command([
        "dhapi",
        "buy-lotto645",
        "-y",
        "", # 슬롯 A (비어있으면 자동)
        "", # 슬롯 B
        "", # 슬롯 C
        "", # 슬롯 D
        ""  # 슬롯 E
    ])
    log_content = (
        f"=== {round_number}회 ({target_saturday.strftime('%Y-%m-%d %H:%M:%S')} 추첨)===\n"
        f"현재 시각: {current_time}\n"
        f"{result_check.stdout}\n"
        f"{result_buy.stdout}\n"
    )
    # 오늘 구매한 로또 번호 기록 및 보고 준비 (report)
    write_to_log(log_path, log_content)
    result_report = report_lotto_numbers(log_path, round_number, target_saturday)
    return result_report


if __name__ == "__main__":
    """결과는 log 폴더에 저장됨 + [선택] 디스코드에 알림"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
    os.makedirs(log_dir, exist_ok=True)
    today_datetime = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    def handle_error_1(e, log_dir, today_datetime):
        """에러 로그를 처리하는 함수1"""
        error_message = f"{type(e).__name__}: {str(e)}"
        error_log_path = os.path.join(log_dir, "lotto_error.log")
        with open(error_log_path, "a") as f:
            f.write(f"{today_datetime} - {error_message}\n")
        return error_message

    def handle_error_2(e, log_dir, today_datetime):
        """에러 로그를 처리하는 함수2 (dhapi으로부터 기록된 stderr에서 파싱한 것)"""
        error_log_path = os.path.join(log_dir, "lotto_error.log")
        with open(error_log_path, "a") as f:
            f.write(f"{today_datetime} - {str(e)}\n")
        return str(e)

    try:
        """1번 프로세스"""
        result_1 = process_lotto_results(log_dir)
        send_message_to_discord(result_1)
    except (RuntimeError, ValueError, AttributeError, FileNotFoundError, KeyError) as e:
        error_msg_1 = handle_error_1(e, log_dir, today_datetime)
        send_message_to_discord(error_msg_1)
    except Exception as e:
        error_msg_1 = handle_error_1(e, log_dir, today_datetime)
        send_message_to_discord(error_msg_1)

    try:
        """2번 프로세스"""
        # 실제 로또 구매 알고리즘 작동 주의 (회차당 한도 5000원)
        result_2 = check_buy_and_report_lotto(log_dir)
        send_message_to_discord(result_2)
    except (RuntimeError, ValueError, AttributeError, FileNotFoundError, KeyError) as e:
        error_msg_2 = handle_error_2(e, log_dir, today_datetime)
        send_message_to_discord(error_msg_2)
    except Exception as e:
        error_msg_2 = handle_error_2(e, log_dir, today_datetime)
        send_message_to_discord(error_msg_2)
