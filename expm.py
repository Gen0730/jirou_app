from flask import Flask, request, abort, jsonify
import requests
import urllib.parse

app = Flask(__name__)

# --- Google の API キーだけ入れてください ---
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"


# --- Google Places API で二郎系検索 ---
def search_jiro(area):
    query = f"{area} 二郎系 ラーメン"
    url = (
        "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        f"query={urllib.parse.quote(query)}&key={GOOGLE_API_KEY}"
    )

    res = requests.get(url).json()

    if "results" not in res or len(res["results"]) == 0:
        return f"「{area}」の周辺に二郎系ラーメンが見つかりませんでした。ニンニクが足りていません。"

    shops = res["results"][:3]  # 上位3件

    reply = f"【{area}周辺の二郎系ラーメン】\n"
    for s in shops:
        name = s.get("name", "店名不明")
        address = s.get("formatted_address", "住所不明")
        reply += f"\n・{name}\n  {address}\n"

    return reply


# --- 🌐 ブラウザ確認用のテスト窓口 ---
@app.route("/", methods=["GET"])
def index():
    # ブラウザから http://127.0.0.1:5000/?area=新宿 のようにアクセスされたら地名を取得
    area = request.args.get("area")
    
    if not area:
        return (
            "<h1>二郎系検索テスト用ページ</h1>"
            "<p>URLの末尾に <b>?area=地名</b> をつけてアクセスしてね！</p>"
            "<p>例: <a href='http://127.0.0.1:5000/?area=新宿'>http://127.0.0.1:5000/?area=新宿</a></p>"
        )
    
    # 検索を実行して、結果をブラウザにテキストで表示
    result = search_jiro(area)
    # 改行コード（\n）をブラウザ用に（<br>）に変換して読みやすくする
    return f"<pre>{result}</pre>"


if __name__ == "__main__":
    app.run(port=5000, debug=True)