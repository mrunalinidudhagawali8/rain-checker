import requests
import time
import json
from datetime import datetime, timedelta
import os

# ========== CONFIG ==========
OWM_API_KEY = "34f13aa28a7e972cf4a845af5fe17ded"
PUSHBULLET_TOKEN = "o.vf7AYrpxK3HJ1YalJfRzQwnPfPFQKrmu"
LAT = "20.3734936678724"
LON = "78.12452536561916"
STATE_FILE = "rain_state.json"
CHECK_INTERVAL_MINUTES = 10  # stays well below 900 API calls/day

# ========== FUNCTIONS ==========

def get_hourly_forecast():
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={LAT}&lon={LON}&appid={OWM_API_KEY}"
    res = requests.get(url)
    res.raise_for_status()
    return res.json()["hourly"]

def is_rain_in_next_hour(hourly_data):
    return 'rain' in hourly_data[0] and hourly_data[0]['rain'].get('1h', 0) > 0

def load_rain_state():
    if not os.path.exists(STATE_FILE):
        return {"raining": False, "start_time": None, "last_alert": None}
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_rain_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def send_push_notification(title, body):
    headers = {'Access-Token': PUSHBULLET_TOKEN}
    data = {'type': 'note', 'title': title, 'body': body}
    res = requests.post('https://api.pushbullet.com/v2/pushes', json=data, headers=headers)
    if res.status_code == 200:
        print(f"✅ Notification sent: {title}")
    else:
        print(f"❌ Failed to send notification: {res.text}")

# ========== MAIN LOOP ==========

def run_loop():
    print("🌤️ Starting Rain Monitoring Loop")
    while True:
        try:
            forecast = get_hourly_forecast()
            rain_now = is_rain_in_next_hour(forecast)
            state = load_rain_state()
            now = datetime.now()

            if rain_now:
                if not state["raining"]:
                    # Rain just started
                    state["raining"] = True
                    state["start_time"] = now.isoformat()
                    state["last_alert"] = now.isoformat()
                    send_push_notification("🌧️ Rain Started", f"Rain started at your farm at {now.strftime('%Y-%m-%d %H:%M')}")
                else:
                    start_time = datetime.fromisoformat(state["start_time"])
                    duration = now - start_time
                    last_alert = datetime.fromisoformat(state["last_alert"])

                    if duration > timedelta(hours=1) and last_alert < now - timedelta(hours=1):
                        send_push_notification("🌧️ Still Raining", f"Rain has continued for {int(duration.total_seconds()/3600)} hour(s)")
                        state["last_alert"] = now.isoformat()

                    if duration > timedelta(hours=3) and last_alert < now - timedelta(hours=6):
                        send_push_notification("🌧️ Long Rain", f"Rain has continued for over 3 hours. Last alert sent at {last_alert.strftime('%H:%M')}")
                        state["last_alert"] = now.isoformat()

            else:
                if state["raining"]:
                    send_push_notification("☀️ Rain Stopped", f"Rain has stopped at your farm as of {now.strftime('%Y-%m-%d %H:%M')}")
                    state = {"raining": False, "start_time": None, "last_alert": None}

            save_rain_state(state)
            print(f"[{now.strftime('%H:%M')}] ✅ Checked forecast. Sleeping {CHECK_INTERVAL_MINUTES} min.\n")

        except Exception as e:
            print(f"⚠️ Error: {e}")

        time.sleep(CHECK_INTERVAL_MINUTES * 60)

# ========== RUN ==========
if __name__ == "__main__":
    run_loop()
