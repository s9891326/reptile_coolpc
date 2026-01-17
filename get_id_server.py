import os
import json
from flask import Flask, request, abort

app = Flask(__name__)


@app.route("/callback", methods=["POST"])
def callback():
    # 1. Get the request body
    body = request.get_data(as_text=True)
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return "Invalid JSON", 400

    # 2. Print the full event log to console so User can see the ID
    print("\n" + "=" * 30)
    print("Received LINE Webhook Event:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("=" * 30 + "\n")

    # 3. Parse events to assist user in finding the ID
    events = data.get("events", [])
    for event in events:
        source = event.get("source", {})
        source_type = source.get("type")

        if source_type == "group":
            group_id = source.get("groupId")
            print(
                f"!!! FOUND GROUP ID !!!\nGroupId: {group_id}\nPLEASE COPY THIS ID TO YOUR .env FILE\n"
            )
        elif source_type == "user":
            user_id = source.get("userId")
            print(f"User ID: {user_id}")
        elif source_type == "room":
            room_id = source.get("roomId")
            print(f"Room ID: {room_id}")

    return "OK"


if __name__ == "__main__":
    print("Server starting on port 5000...")
    print("Please use ngrok to expose this port: ngrok http 5000")
    print(
        "Then set the Webhook URL in LINE Developers Console to: https://<your-ngrok-url>/callback"
    )
    app.run(port=5000)
