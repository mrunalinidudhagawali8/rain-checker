import requests
import os
from datetime import datetime

# === Load env variables from GitHub Actions ===
OWM_API_KEY = os.getenv("OWM_API_KEY")
PUSHBULLET_TOKEN = os.getenv("PUSHBULLET_TOKEN")

# === Test coordinates for current weather ===
LAT = "20.3734"
LON = "78.1245"

def test_openweather():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}"
    try:
        res = requests.get(url)
        print(f"🌐 OpenWeatherMap status: {res.status_code}")
        return res.status_code == 200
    except Exception as e:
        print(f"❌ OpenWeatherMap error: {e}")
        return False

def test_pushbullet():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    headers = {"Access-Token": PUSHBULLET_TOKEN}
    data = {
        "type": "note",
        "title": "🔔 Pushbullet Test Successful",
        "body": f"This message was sent at {now}"
    }
    try:
        res = requests.post("https://api.pushbullet.com/v2/pushes", json=data, headers=headers)
        print(f"📨 Pushbullet status: {res.status_code}")
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Pushbullet error: {e}")
        return False

def main():
    print("🚀 Starting integration test...")
    ow_success = test_openweather()
    pb_success = test_pushbullet()

    if ow_success and pb_success:
        print("✅ Both OpenWeatherMap and Pushbullet are working!")
    elif not ow_success:
        print("⚠️ OpenWeatherMap failed — check API key or endpoint.")
    elif not pb_success:
        print("⚠️ Pushbullet failed — check token or network.")

if __name__ == "__main__":
    main()
