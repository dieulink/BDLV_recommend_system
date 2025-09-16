import requests
import time
from dotenv import load_dotenv
import os

# Tự động tìm và load file .env
load_dotenv()

# Lấy giá trị biến từ .env
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")


def fetch_access_token(TOKEN_CACHE):

    # Nếu token còn hạn và có tồn tại thì dùng lại
    if TOKEN_CACHE["access_token"] and time.time() < TOKEN_CACHE["expires_at"]:
        return TOKEN_CACHE["access_token"]

    # Gửi request đến Twitch để lấy token
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    response = requests.post(url, params=params)
    response.raise_for_status()
    data = response.json()

    TOKEN_CACHE["access_token"] = data["access_token"]
    # lấy thời gian hiện tại + tg hết hạn - 60s để lưu
    TOKEN_CACHE["expires_at"] = time.time() + data["expires_in"] - 60  # Trừ 60s buffer
    print(TOKEN_CACHE["access_token"])
    return TOKEN_CACHE["access_token"]
