import os
import sys
import json
import time
import requests
import websocket as ws_client  # Alias to avoid conflicts
from flask import Flask

app = Flask(__name__)

# Status variables
status = "dnd"  # Options: "online", "dnd", "idle"
custom_status = ""  # Custom status message; set to "" if not needed

# Fetch user token from environment variables
usertoken = os.getenv("TOKEN")
if not usertoken:
    print("[ERROR] Please add a token inside Secrets.")
    sys.exit()

# Set up headers for API requests
headers = {"Authorization": usertoken, "Content-Type": "application/json"}

# Validate the token by making a request to Discord's API
validate = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers)
if validate.status_code != 200:
    print("[ERROR] Your token might be invalid. Please check it again.")
    sys.exit()

# Fetch user info using the validated token
userinfo = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers).json()
username = userinfo["username"]
discriminator = userinfo["discriminator"]
userid = userinfo["id"]

def onliner(token, status):
    try:
        print("Connecting to WebSocket...")
        ws = ws_client.create_connection("wss://gateway.discord.gg/?v=9&encoding=json")
        print("WebSocket connected.")
        
        start = json.loads(ws.recv())
        heartbeat = start["d"]["heartbeat_interval"]
        
        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "Windows 10",
                    "$browser": "Google Chrome",
                    "$device": "Windows",
                },
                "presence": {
                    "status": status,
                    "afk": False
                },
            },
            "s": None,
            "t": None,
        }
        ws.send(json.dumps(auth))
        
        cstatus = {
            "op": 3,
            "d": {
                "since": 0,
                "activities": [
                    {
                        "type": 4,
                        "state": custom_status,
                        "name": "Custom Status",
                        "id": "custom",
                    }
                ],
                "status": status,
                "afk": False,
            }
        }
        ws.send(json.dumps(cstatus))
        
        online = {"op": 1, "d": "None"}
        time.sleep(heartbeat / 1000)
        ws.send(json.dumps(online))
    except ws_client.WebSocketConnectionClosedException as e:
        print(f"[ERROR] WebSocket connection was closed: {e}")
    except ws_client.WebSocketException as e:
        print(f"[ERROR] WebSocket error occurred: {e}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")

def run_onliner():
    while True:
        onliner(usertoken, status)
        time.sleep(50)

@app.route('/')
def home():
    return "The app is running."

if __name__ == '__main__':
    # Start the onliner function in a separate thread or process if needed
    import threading
    threading.Thread(target=run_onliner).start()

    # Run Flask server on the Railway-assigned port
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
