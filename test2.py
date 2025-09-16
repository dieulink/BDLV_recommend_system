from concurrent.futures import ThreadPoolExecutor
import time
games = ["A", "B", "C", "D", "E", "F"]

def fetch(game):
    print(f"Fetching {game}...")
    time.sleep(1)  # Giả lập gọi API mất 1 giây
    return f"Done {game}"


with ThreadPoolExecutor(max_workers=6) as executor:
    results = list(executor.map(fetch, games))

print(results)