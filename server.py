import imaplib
import email
import re
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

app = Flask(__name__)

def get_valid_keys():
    keys = []
    for name, value in os.environ.items():
        if name.startswith("KEY_"):
            keys.append(value)
    return keys

def delete_used_key(used_key):
    # Environment variables cannot be deleted programmatically on Render Free plan.
    # Instead we just ignore this part – or you can manually remove it inside Render if needed.
    pass

def get_latest_steam_code():

    mail = imaplib.IMAP4_SSL(EMAIL_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("INBOX")

    status, data = mail.search(None, '(FROM "noreply@steampowered.com")')

    if status != "OK":
        return None

    msg_ids = data[0].split()
    if not msg_ids:
        return None

    latest_email_id = msg_ids[-1]

    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
    raw_email = msg_data[0][1]

    msg = email.message_from_bytes(raw_email)

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype in ["text/plain", "text/html"]:
                try:
                    body += part.get_payload(decode=True).decode()
                except:
                    pass
    else:
        body = msg.get_payload(decode=True).decode()

    match = re.search(r"\b([A-Z0-9]{5})\b", body)
    if match:
        return match.group(1)

    return None


@app.post("/getcode")
def get_code():
    data = request.json
    key = data.get("key", "").strip()

    valid_keys = get_valid_keys()

    if key not in valid_keys:
        return jsonify({"error": "Invalid key"}), 400

    code = get_latest_steam_code()

    if not code:
        return jsonify({"error": "No Steam Guard email found"}), 404

    return jsonify({"code": code})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
