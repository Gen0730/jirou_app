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

app = Flask(__name__)

# --- あなたの LINE 情報 ---
LINE_CHANNEL_ACCESS_TOKEN = "Q65xfAllf77uxbZDfucOZ2/iVQr4TSFweGK8/NVSQ+PciUPh1UEXTVzjY9XBb6qNuKP1tgSs7/VVXqcoLX3j0zONcXTJQrPOSk93DkhgwBAPf0VKAwWR2X1VPHWsUsQemKfZj6lvVoOv33uNUxlwlwdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "c4f3aa68fcb4e56e0fc1ebef9433da19"
GOOGLE_API_KEY = "AIzaSyDzUY8_uLTo9YlgX6VnrKI--yeoaL33DYs"

# --- LINE SDK v3 初期化 ---
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)

handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- Google Places API で二郎系検索（修正版） ---
def search_jiro(area):
    # 「大阪 二郎系 ラーメン」だと弾かれることがあるので、確実にヒットしやすいワードに変更
    query = f"{area} ラーメン " 
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
        return f"「{area}」の周辺に二郎系ラーメンが見つかりませんでした。ニンニクが足りていません。"

    shops = res["results"][:3]  # 上位3件

    reply = f"【{area}周辺の二郎系ラーメン】\n"
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
print("実行してますよ＾－")