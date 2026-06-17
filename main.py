from flask import Flask, request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import (
    MessagingApi,
    Configuration,
    ApiClient,
    ReplyMessageRequest,
    TextMessage
)
import requests
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()  # これで.envファイルの中身を読み込みます

# これまで直接書いていた中身を、以下のように書き換えます
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)

# --- あなたの LINE 情報 ---


# --- LINE SDK v3 初期化 ---
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)

handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- Google Places API で二郎系検索（修正版） ---
def search_jiro(area):
    # 「大阪 二郎系 ラーメン」だと弾かれることがあるので、確実にヒットしやすいワードに変更
    query = f"{area} 二郎系 ラーメン" 
    url = (
        "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        f"query={urllib.parse.quote(query)}&key={GOOGLE_API_KEY}"
    )

    res = requests.get(url).json()

    # --- 🔍 ここがポイント：Googleからどんな返事が来ているかログに出す ---
    print("--- Google API Response Status ---")
    print("Status:", res.get("status"))
    if "error_message" in res:
        print("Error:", res.get("error_message"))
    # -----------------------------------------------------------------

    if "results" not in res or len(res["results"]) == 0:
        return f"「{area}」の周辺に次郎系ラーメンが見つかりませんでした。ニンニクが足りていません。"

    shops = res["results"][:5]  # 上位3件

    reply = f"【{area}の周辺の次郎系ラーメン】\n"
    for s in shops:
        name = s.get("name", "店名不明")
        address = s.get("formatted_address", "住所不明")
        reply += f"\n・{name}\n  {address}\n"

    return reply

# --- Webhook のエンドポイント ---
@app.route("/callback", methods=["POST"])
def callback():
    # 署名検証のためのヘッダーを取得
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        abort(400)

    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return "OK"


# --- LINE メッセージ受信時の処理 ---
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # ユーザーが送信してきたテキスト（地名など）
    user_message = event.message.text
    
    # 二郎系を検索
    search_result = search_jiro(user_message)
    
    # 返信を送信
    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=search_result)]
        )
    )


if __name__ == "__main__":
    # 開発環境用にポート5000で起動
    app.run(port=5000, debug=True)
