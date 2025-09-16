from fetch_access_token import fetch_access_token
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Lấy giá trị biến từ .env
client_id = os.getenv("CLIENT_ID")
# print(fetch_access_token())

def fetch_thumbnail():
    access_token_igdb = "o2zmmgss6vdms8yyoe5a1urgss4crk"
    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token_igdb}",
        "Content-Type": "text/plain",
    }

    data = 'fields name, summary, cover.url; search "Lisa the Joyful"; limit 1;'
    response = requests.post(url, headers = headers, data=data)
    response.raise_for_status()
    game = response.json()

    print(game)
    if game[0]:
        game_url_img = game[0]['cover']['url']
        game = game_url_img
        game = game.replace("t_thumb", "t_720p")
        print(game)
        return f"https:{game}"


fetch_thumbnail()