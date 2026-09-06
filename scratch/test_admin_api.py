import urllib.request
import json

# Try different common passwords if needed or log in
login_payload = json.dumps({"username": "Tarang_radio@257", "password": "Tarang_radio@257"}).encode('utf-8')
req = urllib.request.Request("http://localhost:8000/api/auth/login", data=login_payload, headers={"Content-Type": "application/json"})

try:
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode('utf-8'))
    token = data["token"]
    print("Logged in successfully! Token:", token[:10] + "...")

    stats_req = urllib.request.Request("http://localhost:8000/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    stats_res = urllib.request.urlopen(stats_req)
    stats_data = json.loads(stats_res.read().decode('utf-8'))
    print("ADMIN STATS RESPONSE FROM SERVER:")
    print(json.dumps(stats_data, indent=2))
except Exception as e:
    print("Login error:", e)
