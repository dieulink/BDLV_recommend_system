import pandas as pd
from sqlalchemy import create_engine
from datetime import  datetime
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import schedule
import time

# config.py

RELOAD_INTERVAL = 60

# Khởi tạo biến toàn cục
games = pd.DataFrame()
similarity = None
countVector = None
engine = None

def init_database():

    global engine
    engine = create_engine('mysql+pymysql://root:29092003@localhost/dashboard')
    print("Đã kết nối với database")

def load_and_preprocess_data():

    global games, countVector, similarity

    print(f"{datetime.now()} - Đang tải dữ liệu từ database...")\

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
    pd.set_option('display.max_columns', None)  # Hiển thị tất cả các cột
    pd.set_option('display.width', None)  # Tự co theo chiều ngang terminal
    pd.set_option('display.max_colwidth', 100)  # Hiển thị nội dung cột dài

    print(games)

    games['GenreDes'] = games['genres'] + " " + games['description'].fillna('')
    countVector = CountVectorizer(max_features=len(games), stop_words='english', max_df=0.32)
    # print(countVector)

    vector = countVector.fit_transform(games['GenreDes'].values.astype('U')).toarray()
    # print(f"Số từ thực tế được chọn: {len(countVector.vocabulary_)}")

    similarity = cosine_similarity(vector)
    # print(similarity)
    print(f"Đã cập nhật dữ liệu thành công. Tổng số game: {len(games)}")

def reload_data():

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
init_database()
load_and_preprocess_data()