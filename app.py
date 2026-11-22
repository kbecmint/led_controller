import json
import os
from flask import Flask, jsonify, render_template_string, request
import RPi.GPIO as GPIO

app = Flask(__name__)

# GPIOピンの設定 (GPIO 17 = 物理11番ピン)
LED_PIN = 17
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "schedule_config.json")

DEFAULT_CONFIG = {
    "always_on": False,
    "weekly": {
        "mon": {"morning_on": "06:00", "morning_off": "08:00", "evening_on": "17:00", "evening_off": "22:00"},
        "tue": {"morning_on": "06:00", "morning_off": "08:00", "evening_on": "17:00", "evening_off": "22:00"},
        "wed": {"morning_on": "06:00", "morning_off": "08:00", "evening_on": "17:00", "evening_off": "22:00"},
        "thu": {"morning_on": "06:00", "morning_off": "08:00", "evening_on": "17:00", "evening_off": "22:00"},
        "fri": {"morning_on": "06:00", "morning_off": "08:00", "evening_on": "17:00", "evening_off": "22:00"},
        "sat": {"morning_on": "07:00", "morning_off": "09:00", "evening_on": "17:00", "evening_off": "23:00"},
        "sun": {"morning_on": "07:00", "morning_off": "09:00", "evening_on": "17:00", "evening_off": "23:00"},
    },
    "holidays": {},
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("always_on", False)
            data.setdefault("weekly", DEFAULT_CONFIG["weekly"])
            data.setdefault("holidays", {})
            return data
    return DEFAULT_CONFIG


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LEDイルミネーション制御</title>
    <style>
        body { font-family: sans-serif; margin: 0; padding: 15px; background: #f4f4f9; color: #333; }
        h1 { font-size: 1.2rem; text-align: center; margin-top: 0; }
        h3 { margin-top: 0; font-size: 1rem; }
        .card { background: #fff; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .day-group, .holiday-item { margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
        .switch-row { display: flex; align-items: center; gap: 8px; font-weight: bold; }
        input[type="time"], input[type="date"] { padding: 5px; font-size: 0.9rem; margin-bottom: 5px; }
        input[type="checkbox"] { transform: scale(1.2); }
        button { background: #007bff; color: #fff; border: none; padding: 10px 15px; font-size: 1rem; border-radius: 5px; width: 100%; cursor: pointer; }
        button:active { background: #0056b3; }
        .manual-btn { background: #28a745; }
        .manual-off { background: #dc3545; margin-top: 10px; }
        .del-btn { background: #dc3545; width: auto; padding: 5px 10px; font-size: 0.8rem; margin-top: 5px; }
        .add-btn { background: #17a2b8; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>LEDイルミネーション制御 (GPIO 17)</h1>

    <div class="card">
        <h3>手動操作</h3>
        <button type="button" class="manual-btn" onclick="manualControl('on')">強制ON</button>
        <button type="button" class="manual-btn manual-off" onclick="manualControl('off')">強制OFF</button>
    </div>

    <div class="card">
        <h3>モード切替</h3>
        <label class="switch-row">
            <input type="checkbox" id="alwaysOnCheck" onchange="toggleAlwaysOn(this)" {% if config.always_on %}checked{% endif %}>
            終日つけっぱなしモード (常時ON)
        </label>
    </div>

    <form id="scheduleForm" onsubmit="saveSchedule(event)">
        <div class="card">
            <h3>祝日・特別日設定</h3>
            <div id="holidayContainer">
                {% for date, times in config.holidays.items() %}
                <div class="holiday-item">
                    日付: <input type="date" class="h-date" value="{{ date }}"><br>
                    朝 ON: <input type="time" class="h-m-on" value="{{ times.morning_on }}">
                    OFF: <input type="time" class="h-m-off" value="{{ times.morning_off }}"><br>
                    夕 ON: <input type="time" class="h-e-on" value="{{ times.evening_on }}">
                    OFF: <input type="time" class="h-e-off" value="{{ times.evening_off }}"><br>
                    <button type="button" class="del-btn" onclick="this.parentElement.remove()">この祝日を削除</button>
                </div>
                {% endfor %}
            </div>
            <button type="button" class="add-btn" onclick="addHolidayRow()">＋ 祝日・特別日を追加</button>
        </div>

        <div class="card">
            <h3>曜日別スケジュール設定</h3>
            {% for day, times in config.weekly.items() %}
            <div class="day-group">
                <strong>{{ day.upper() }}</strong><br>
                朝 ON: <input type="time" name="{{ day }}_m_on" value="{{ times.morning_on }}">
                OFF: <input type="time" name="{{ day }}_m_off" value="{{ times.morning_off }}"><br>
                夕 ON: <input type="time" name="{{ day }}_e_on" value="{{ times.evening_on }}">
                OFF: <input type="time" name="{{ day }}_e_off" value="{{ times.evening_off }}">
            </div>
            {% endfor %}
            <button type="submit" style="margin-top: 10px;">全設定を保存</button>
        </div>
    </form>

    <script>
        function manualControl(action) {
            fetch('/api/manual/' + action, { method: 'POST' })
                .then(res => res.json())
                .then(() => alert('LEDを ' + (action === 'on' ? 'ON' : 'OFF') + ' にしました'));
        }

        function toggleAlwaysOn(checkbox) {
            fetch('/api/always_on', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ always_on: checkbox.checked })
            })
            .then(res => res.json())
            .then(() => alert('常時ONモードを ' + (checkbox.checked ? '有効' : '無効') + ' にしました'));
        }

        function addHolidayRow() {
            const container = document.getElementById('holidayContainer');
            const div = document.createElement('div');
            div.className = 'holiday-item';
            div.innerHTML = `
                日付: <input type="date" class="h-date"><br>
                朝 ON: <input type="time" class="h-m-on" value="07:00">
                OFF: <input type="time" class="h-m-off" value="09:00"><br>
                夕 ON: <input type="time" class="h-e-on" value="17:00">
                OFF: <input type="time" class="h-e-off" value="23:00"><br>
                <button type="button" class="del-btn" onclick="this.parentElement.remove()">この祝日を削除</button>
            `;
            container.appendChild(div);
        }

        function saveSchedule(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const weekly = {};

            for (let [key, value] of formData.entries()) {
                const parts = key.split('_');
                if (parts.length === 3) {
                    const day = parts[0];
                    const type = parts[1] + '_' + parts[2];
                    if (!weekly[day]) weekly[day] = {};
                    if (type === 'm_on') weekly[day].morning_on = value;
                    if (type === 'm_off') weekly[day].morning_off = value;
                    if (type === 'e_on') weekly[day].evening_on = value;
                    if (type === 'e_off') weekly[day].evening_off = value;
                }
            }

            const holidays = {};
            document.querySelectorAll('.holiday-item').forEach(item => {
                const dateVal = item.querySelector('.h-date').value;
                if (dateVal) {
                    holidays[dateVal] = {
                        morning_on: item.querySelector('.h-m-on').value,
                        morning_off: item.querySelector('.h-m-off').value,
                        evening_on: item.querySelector('.h-e-on').value,
                        evening_off: item.querySelector('.h-e-off').value
                    };
                }
            });

            fetch('/api/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ weekly: weekly, holidays: holidays })
            })
            .then(res => res.json())
            .then(() => alert('スケジュールを保存しました！'));
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    config = load_config()
    return render_template_string(HTML_TEMPLATE, config=config)


@app.route("/api/manual/<action>", methods=["POST"])
def manual(action):
    if action == "on":
        GPIO.output(LED_PIN, GPIO.HIGH)
        return jsonify({"status": "success", "action": "on"})
    elif action == "off":
        GPIO.output(LED_PIN, GPIO.LOW)
        return jsonify({"status": "success", "action": "off"})
    return jsonify({"status": "error", "message": "invalid action"}), 400


@app.route("/api/always_on", methods=["POST"])
def update_always_on():
    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("always_on", False))
    config = load_config()
    config["always_on"] = enabled
    save_config(config)

    if enabled:
        GPIO.output(LED_PIN, GPIO.HIGH)

    return jsonify({"status": "success", "always_on": enabled})


@app.route("/api/schedule", methods=["POST"])
def update_schedule():
    data = request.get_json(silent=True) or {}
    config = load_config()
    if "weekly" in data:
        config["weekly"] = data["weekly"]
    if "holidays" in data:
        config["holidays"] = data["holidays"]
    save_config(config)
    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
