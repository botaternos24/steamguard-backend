import json, uuid

def load_keys():
    with open("keys.json", "r") as f:
        return json.load(f)

def save_keys(data):
    with open("keys.json", "w") as f:
        json.dump(data, f, indent=4)

data = load_keys()

new_key = str(uuid.uuid4()).replace("-", "")[:12]  # 12 char key
data["keys"][new_key] = False

save_keys(data)

print("Your new key:", new_key)
