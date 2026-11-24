import datetime
import json
import os
import requests
from pathlib import Path
# import RPi.GPIO as GPIO

# GPIOピンの設定 (GPIO 17 = 物理11番ピン)
# LED_PIN = 17
# GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(LED_PIN, GPIO.OUT)

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = Path(os.environ.get("LED_CONFIG_FILE", BASE_DIR / "schedule_config.json"))
days_map = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}

on_url="http://localhost:5000/api/manual/on"
off_url="http://localhost:5000/api/manual/off"

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    # 1. 「終日つけっぱなしモード（常時ON）」が有効な場合
    if config.get("always_on", False):
        res = requests.post(on_url)
        # GPIO.output(LED_PIN, GPIO.HIGH)
        exit()

    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")  # 例: "2026-11-23"
    current_time_str = now.strftime("%H:%M")

    holidays = config.get("holidays", {})
    weekly = config.get("weekly", {})

    # 2. 優先して「祝日・特定日」のスケジュールがあるかチェック
    if today_str in holidays:
        day_schedule = holidays[today_str]
    else:
        # 3. なければ通常の曜日スケジュールを使用
        current_day = days_map[now.weekday()]
        day_schedule = weekly.get(current_day, {})

    m_on = day_schedule.get("morning_on")
    m_off = day_schedule.get("morning_off")
    e_on = day_schedule.get("evening_on")
    e_off = day_schedule.get("evening_off")

    # 4. 指定時刻と一致したらON/OFFを切り替え
    if current_time_str == m_on or current_time_str == e_on:
        requests.post(on_url)
        # GPIO.output(LED_PIN, GPIO.HIGH)
    elif current_time_str == m_off or current_time_str == e_off:
        requests.post(off_url)
        # GPIO.output(LED_PIN, GPIO.LOW)

