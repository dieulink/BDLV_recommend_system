import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from fetch_access_token import fetch_access_token
from flask_cors import CORS
import threading
import pandas as pd
from sqlalchemy import create_engine
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import schedule
import time

# PERIODIC_UPDATE (cập nhật định kì)

RELOAD_INTERVAL = 3600  # 1 giờ (tính bằng giây)

# Khởi tạo biến toàn cục
games = pd.DataFrame()
similarity = None
countVector = None
engine = None
games_list = None
games_id_list = None

def init_database():
    # Trong Python, khi gán giá trị cho biến trong hàm, mặc định nó sẽ tạo biến cục bộ
    # Dùng global để chỉ định muốn thay đổi biến toàn cục đã tồn tại
    global engine
    engine = create_engine('mysql+pymysql://root:123456@localhost/dashboard')
    print("Đã kết nối với database")

def load_and_preprocess_data():
    """Tải dữ liệu từ database và tiền xử lý"""
    global games, countVector, similarity

    # print(f"{datetime.now()} - Đang tải dữ liệu từ database...")

    # Lấy dữ liệu từ database
    query = """
       SELECT 
            g.game_id,
            g.game_name,
            g.description,
            GROUP_CONCAT(c.category_name SEPARATOR ', ') AS genres
        FROM 
            game g
        LEFT JOIN 
            category_game cg ON g.game_id = cg.game_id
        LEFT JOIN 
            category c ON cg.category_id = c.category_id
        GROUP BY 
            g.game_id, g.game_name, g.description;
       """

    games = pd.read_sql(query, engine)
    # pd.set_option('display.max_columns', None)  # Hiển thị tất cả các cột
    # pd.set_option('display.width', None)  # Tự co theo chiều ngang terminal
    # pd.set_option('display.max_colwidth', 100)  # Hiển thị nội dung cột dài

    # print(games)

    games['GenreDes'] = games['genres'] + " " + games['description'].fillna('')
    countVector = CountVectorizer(max_features=len(games), stop_words='english', max_df=0.32)
    # print(countVector)

    vector = countVector.fit_transform(games['GenreDes'].values.astype('U')).toarray()
    # print(f"Số từ thực tế được chọn: {len(countVector.vocabulary_)}")

    similarity = cosine_similarity(vector)
    # print(similarity)
    global games_list
    games_list = games['game_name'].values
    global games_id_list
    games_id_list = games['game_id'].values

    print(f"Đã cập nhật danh sách game. Số lượng game hiện tại: {len(games_list)}")

def reload_data():
    """Wrapper function để xử lý ngoại lệ khi reload"""
    try:
        load_and_preprocess_data()
    except Exception as e:
        print(f"Lỗi khi reload dữ liệu: {str(e)}")

# định kì cập nhật dữ liệu
def scheduler_thread():
    """
    RELOAD_INTERVAL được định nghĩa là 3600 giây (1 giờ)
    Dòng này lập lịch để gọi hàm reload_data() cứ mỗi 3600 giây một lần
    schedule.every() là một API của thư viện schedule để tạo các tác vụ định kỳ
    .do(reload_data) chỉ định hàm sẽ được thực thi theo lịch
    """
    schedule.every(RELOAD_INTERVAL).seconds.do(reload_data)
    while True:
        # kiểm tra và thực thi các tác vụ đã đến thời điểm chạy
        schedule.run_pending()

        #  tạm dừng 1 giây trước khi kiểm tra lại, giúp giảm tải CPU
        time.sleep(1)


# Khởi tạo khi chạy ứng dụng
init_database()
# Load dữ liệu lần đầu
reload_data()

"""
threading.Thread() Đây là constructor để tạo một thread mới
target=scheduler_thread: chỉ định hàm sẽ được chạy trong thread này
daemon=True: đây là một tham số quan trọng:
Khi một thread được đánh dấu là daemon, nó sẽ tự động kết thúc khi chương 
trình chính kết thúc
"""
thread = threading.Thread(target=scheduler_thread, daemon=True)

# Khởi động thread mới
# hàm scheduler_thread chạy trong một luồng riêng biệt
# Chương trình chính có thể tiếp tục thực thi các tác vụ khác mà không bị block
thread.start()


# API
app = Flask(__name__)
# Tự động tìm và load file .env
load_dotenv()

# Cho phép tất cả origins truy cập tất cả routes
CORS(app)

# Lấy giá trị biến từ .env
client_id = os.getenv("CLIENT_ID")


TOKEN_CACHE = {
    "access_token": None,
    "expires_at": 0
}
# 264 × 374;  889 × 500;  284 × 160;  1280 × 720; 920 × 1080 (px)
size_img = ["t_cover_big", "t_screenshot_big", "t_logo_med", "t_720p", "t_1080p"]

def fetch_game(game_title):
    access_token_igdb = fetch_access_token(TOKEN_CACHE)
    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token_igdb}",
        "Content-Type": "text/plain",
    }

    data = f'fields name, summary, cover.url, genres.name, screenshots.url; search "{game_title}"; limit 10;'
    response = requests.post(url, headers=headers, data=data)
    # báo lỗi nếu có lỗi xảy ra
    response.raise_for_status()
    game = response.json()
    return  game

def fetch_thumbnail(game_title):

    # gọi hàm này để nhận access token từ igdb
    access_token_igdb = fetch_access_token(TOKEN_CACHE)
    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token_igdb}",
        "Content-Type": "text/plain",
    }

    data = f'fields name, summary, cover.url; search "{game_title}"; limit 1;'
    response = requests.post(url, headers = headers, data=data)
    # báo lỗi nếu có lỗi xảy ra
    response.raise_for_status()
    game = response.json()

    if game[0]['cover']:
        game_url_img = game[0]['cover']['url'].replace("t_thumb", f"{size_img[3]}")
        # print(game_url_img['url'])
        return f"https:{game_url_img}"
    return "Game không tồn tại"

    # print("response: %s" % str(response.json()))

def filter_game(distance, game_id_input):
    digit_game_recommend = 6

    # ở đây mình cần 1 set vì set nó ko nhận phần tử trùng lặp
    suggested_game_id = set()
    final_suggestions = []
    # đọc thêm trong note
    for i in distance:
        # mỗi i này nó trả về game id được recommend và độ tương đồng
        game_name = games.iloc[i[0]].game_name
        # từ đối tượng pandas phải ép kiểu quan int của python
        game_id = int(games.loc[games['game_name'] == game_name, 'game_id'].values[0])
        print(game_id, game_id_input)
        if game_id not in suggested_game_id and game_id_input != game_id:
            suggested_game_id.add(game_id)
            final_suggestions.append(game_id)

        # lấy đúng 6 game không trùng
        if len(final_suggestions) == digit_game_recommend:
            break

    return final_suggestions

def recommender(game_name, game_id):
    # Tìm dòng trong new_data mà có game_name == game.
    # .index[0]: lấy chỉ số đầu tiên trong DataFrame — chính là vị trí của phim đó trong bảng.
    index = games[games['game_name']==game_name].index[0]
    distance = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda vector: vector[1])
    return filter_game(distance, game_id)

@app.route("/recommend", methods=["GET"])
def recommend_api():
    # request: Là đối tượng Flask cung cấp, chứa toàn bộ thông tin request từ client
    # .args: Truy cập các tham số dạng URL query (vd: /recommend?title=...)
    # .get("title"): Lấy giá trị của tham số title nếu có (trả về None nếu không có)
    game_name = request.args.get("gameName")
    game_id =  int(request.args.get("gameId"))

    if game_name is None or game_id is None:
        return jsonify({"error": "Thiếu tham số tên game và game id"}), 400

    # games_list: có trong danh sách game đã train hay không
    if game_name not in games_list or game_id not in games_id_list:
        return jsonify({"error": f"Game '{game_name}' hoặc '{game_id}' không có trong hệ thống"}), 404

    game_id_recommended= recommender(game_name, game_id)
    print(game_id_recommended)
    return jsonify({
        "game_id": game_id_recommended,
    })

@app.route("/add-game-igdb", methods=["GET"])
def get_game_igdb():
    # request: Là đối tượng Flask cung cấp, chứa toàn bộ thông tin request từ client
    # .args: Truy cập các tham số dạng URL query (vd: /recommend?title=...)
    # .get("title"): Lấy giá trị của tham số title nếu có (trả về None nếu không có)
    game_title = request.args.get("gameTitle")

    if not game_title:
        return jsonify({"error": "Thiếu tham số title"}), 400


    game_igdb = fetch_game(game_title)
    return jsonify({
        "game" : game_igdb
    })
if __name__ == "__main__":
    # Khởi động server Flask (mặc định port 5000)
    app.run(port=5000, debug=True)