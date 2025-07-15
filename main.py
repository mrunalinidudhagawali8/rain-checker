import requests
import json
import os
import subprocess
import pytz
from datetime import datetime, timedelta

# ========== CONFIG ==========
OWM_API_KEY = os.getenv("OWM_API_KEY")
PUSHBULLET_TOKEN = os.getenv("PUSHBULLET_TOKEN")
LAT = "20.462055502572074"
LON = "78.27376256445771"
STATE_FILE = "rain_state.json"

def to_ist(dt_utc):
    ist = pytz.timezone('Asia/Kolkata')
    return dt_utc.astimezone(ist).strftime('%Y-%m-%d %I:%M %p IST')
    
def get_current_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
    res = requests.get(url)
    res.raise_for_status()
    return res.json()

def is_raining_now(data):
    return 'rain' in data and data['rain'].get('1h', 0) > 0

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
    print(f"🔔 Sent: {title} | Status: {res.status_code}")

def commit_state_file():
    try:
        subprocess.run(["git", "config", "--global", "user.email", "action@github.com"])
        subprocess.run(["git", "config", "--global", "user.name", "GitHub Action"])
        subprocess.run(["git", "add", STATE_FILE])
        subprocess.run(["git", "commit", "-m", f"Update rain state {datetime.utcnow().isoformat()}"])
        subprocess.run(["git", "push", "origin", "main"])
        print("💾 State file committed and pushed.")
    except Exception as e:
        print(f"⚠️ Could not commit state file: {e}")

def main():
    print("📡 Checking current weather...")
    try:
        weather = get_current_weather()
        rain_now = is_raining_now(weather)
        state = load_rain_state()
        now = datetime.utcnow()

        if rain_now:
            if not state["raining"]:
                state["raining"] = True
                state["start_time"] = now.isoformat()
                state["last_alert"] = now.isoformat()
                send_push_notification("🌧️ Rain Started", f"Rain started at your farm at {now.strftime('%Y-%m-%d %H:%M UTC')}")
            else:
                start_time = datetime.fromisoformat(state["start_time"])
                last_alert = datetime.fromisoformat(state["last_alert"])
                duration = now - start_time
                since_alert = now - last_alert

                if duration > timedelta(hours=1) and since_alert >= timedelta(hours=1):
                    send_push_notification("🌧️ Still Raining", f"Rain has continued for {int(duration.total_seconds() / 3600)} hour(s)")
                    state["last_alert"] = now.isoformat()
                elif duration > timedelta(hours=3) and since_alert >= timedelta(hours=6):
                    send_push_notification("🌧️ Long Rain Alert", f"Rain has continued for more than 3 hours. Last alert at {last_alert.strftime('%H:%M UTC')}")
                    state["last_alert"] = now.isoformat()

        else:
            if state["raining"]:
                send_push_notification("☀️ Rain Stopped", f"Rain stopped at your farm at {now.strftime('%Y-%m-%d %H:%M UTC')}")
                state = {"raining": False, "start_time": None, "last_alert": None}

        save_rain_state(state)
        commit_state_file()

    except Exception as e:
        print(f"⚠️ Error during execution: {e}")

if __name__ == "__main__":
    main()
