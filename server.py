from flask import Flask, request, jsonify
from imapclient import IMAPClient
from email import message_from_bytes
import re, json, os
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

app = Flask(__name__)

def load_keys():
    with open("keys.json", "r") as f:
        return json.load(f)

def save_keys(data):
    with open("keys.json", "w") as f:
        json.dump(data, f, indent=4)

def get_latest_steam_code():
    with IMAPClient(EMAIL_HOST) as client:
        client.login(EMAIL_USER, EMAIL_PASS)
        client.select_folder("INBOX")

        messages = client.search(['FROM', 'noreply@steampowered.com', 'SUBJECT', 'Your Steam account: Access from new computer'])

        if not messages:
            return None

        latest_msg_id = messages[-1]
        msg_data = client.fetch(latest_msg_id, ['RFC822'])

        raw = msg_data[latest_msg_id][b'RFC822']
        msg = message_from_bytes(raw)

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        # extract the 5 digit code
        match = re.search(r"\b([A-Z0-9]{5})\b", body)
        if match:
            return match.group(1)

        return None

@app.post("/getcode")
def get_code():
    data = request.json
    key = data.get("key")

    keys_data = load_keys()

    if key not in keys_data["keys"]:
        return jsonify({"error": "Invalid key"}), 400

    if keys_data["keys"][key] == True:
        return jsonify({"error": "Key already used"}), 400

    code = get_latest_steam_code()

    if not code:
        return jsonify({"error": "No Steam Guard email found"}), 404

    # mark key as used
    keys_data["keys"][key] = True
    save_keys(keys_data)

    return jsonify({"code": code})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
