"""
Uploads publish/Montka.zip to AI Arena.

Requires environment variables:
    AIARENA_API_TOKEN  — your AI Arena API token (from aiarena.net/profile/token)
    AIARENA_BOT_ID     — your bot's numeric ID on aiarena.net
"""
import os
import sys
import requests

API_TOKEN = os.environ.get("AIARENA_API_TOKEN")
BOT_ID = os.environ.get("AIARENA_BOT_ID")
ZIP_PATH = os.path.join(os.path.dirname(__file__), "..", "publish", "Montka.zip")

if not API_TOKEN or not BOT_ID:
    print("AIARENA_API_TOKEN and AIARENA_BOT_ID must be set.")
    sys.exit(1)

if not os.path.isfile(ZIP_PATH):
    print(f"Zip not found: {ZIP_PATH}")
    sys.exit(1)

url = f"https://aiarena.net/api/bots/{BOT_ID}/"
headers = {"Authorization": f"Token {API_TOKEN}"}

with open(ZIP_PATH, "rb") as f:
    response = requests.patch(url, headers=headers, files={"bot_zip": f})

if response.status_code == 200:
    print("Upload successful.")
else:
    print(f"Upload failed: {response.status_code}")
    print(response.text)
    sys.exit(1)
