import ast

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

games = pd.read_csv('game_data_match_database.csv')

# ======= TIỀN XỬ LÝ DATA =========

# Tăng giới hạn hiển thị cột
pd.set_option('display.max_columns', None)  # Hiển thị tất cả các cột
pd.set_option('display.width', None)        # Tự co theo chiều ngang terminal
pd.set_option('display.max_colwidth', 100) # Hiển thị nội dung cột dài

# # games.head()
# print(games.head(10))
#
# # Đếm số ô bị thiếu (NaN) ở mỗi cột — giúp biết cột nào có giá trị bị thiếu.
# # print(games.isnull().sum())
#
# # kiểm tra thì thấy summary là cột có 1 dòng null mà dữ liệu nhiều
# # nên bỏ dòng đó
#
# games = games.dropna(subset=["Summary"])
#
# print(games.isnull().sum())

# mà chỉ lấy ra những thuộc tính quan trọng như: Id, Title, Genres, Summary
# tạo data frame mới chỉ chứa các thuộc tính trên
gamesTrain = games[['game_id', 'game_name', 'Genres', 'description']].copy()

# Chuyển string từ dạng "['action']" sang "action"
# xem thêm ở note
# thêm ", " để khi gom cột tránh bị dính
gamesTrain["Genres"] = gamesTrain["Genres"].apply(
    lambda x: ", ".join(ast.literal_eval(x)) + ", "
)
print(gamesTrain["Genres"])

# kiểm tra type của từng dòng trong cột và đếm
# print(gamesTrain["Genres"].apply(type).value_counts())


# merge 2 cột overview và genre lại thành 1
gamesTrain['GenreDes'] = gamesTrain['Genres'] + gamesTrain['description']
print(gamesTrain)

# xóa 2 cột Summary và Genres vì đã merge lại thành 1
new_data = gamesTrain.drop(columns=['Genres', 'description'])
# print(new_data)

# max_df=0.32 giúp đa dạng:
# Giữ lại từ khóa riêng biệt, ít gặp
# Mô hình dễ phân biệt các game với nhau hơn -> kết quả đa dạng, sát hơn.
countVector = CountVectorizer(max_features=1200, stop_words='english', max_df=0.32)
# print(countVector)

vector = countVector.fit_transform(new_data['GenreDes'].values.astype('U')).toarray()
# print(f"Số từ thực tế được chọn: {len(countVector.vocabulary_)}")

similarity = cosine_similarity(vector)
# print(similarity)

def recommender(game):
    # Tìm dòng trong new_data mà có title == movie.
    # .index[0]: lấy chỉ số đầu tiên trong DataFrame — chính là vị trí của game đó trong bảng.
    index = new_data[new_data['game_name']==game].index[0]
    print(index)
    distance = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda vector: vector[1])
    filter_game(distance, game)

def filter_game(distance, game):
    # ở đây mình cần 1 set vì set nó ko nhận phần tử trùng lặp
    suggested_game_name = set()
    final_suggestions = []
    # đọc thêm trong note
    for i in distance:
        print("i", i)
        print("i[0]", i[0])
        game_name = new_data.iloc[i[0]].game_name
        # new_data['game_name'] == game_name:
        # Tạo một boolean mask (mảng True/False)
        # Trả về True cho các hàng có giá trị cột game_name khớp với biến game_name cần tìm

        # new_data.loc[condition, 'game_id']:
        # loc[]: Truy cập DataFrame bằng label-based indexing
        # Lọc các hàng thỏa mãn điều kiện (có game_name trùng khớp)
        # Chỉ lấy cột 'game_id' từ những hàng đó

        # .values:
        # Chuyển kết quả thành mảng NumPy
        # Ví dụ: array([1327]) nếu tìm thấy

        # [0]:
        # Lấy phần tử đầu tiên trong mảng
        game_id = new_data.loc[new_data['game_name'] == game_name, 'game_id'].values[0]
        print(f"Game ID: {game_id}")
        if game_name not in suggested_game_name and game != game_name:
            suggested_game_name.add(game_name)
            final_suggestions.append(game_name)

        # lấy đúng 6 game không trùng
        if len(final_suggestions) == 6:
            break

    for game_name in final_suggestions:
        print(game_name)

recommender("Back to the Future: The Game")

# lưu data và cosine_similarity dưới dạng pkl
# pickle.dump(new_data, open('games_list.pkl', 'wb'))
# pickle.dump(similarity, open('similarity.pkl', 'wb'))
