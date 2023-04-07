from dotenv import load_dotenv
from ChatGPT.Line import LINEBox
from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextSendMessage,
    TextMessage, AudioMessage
)

load_dotenv()
app = Flask(__name__)
line = LINEBox(role_setting="請你扮演英文老師，與我進行對話")

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        line.handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'


@line.handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("============== Text START ================")
    print(event)
    user_input = event.message.text
    user_id = event.source.user_id
    print("============== Text END ================")

    resp_text = line.text_handle(user_id,user_input)
    line.send_message(event.reply_token,TextSendMessage(text=resp_text))

@line.handler.add(MessageEvent, message=AudioMessage)
def handle_message(event):
    print("============== Audio START ================")
    print(event)
    print("============== Audio END ================")

    is_download = line.get_audio_data(event.message.id)
    if is_download:
        user_input = line.speech_to_text()
        user_id = event.source.user_id
        resp_text = line.text_handle(user_id,user_input)
    else:
        resp_text = "Audio download failed!"
    line.send_message(event.reply_token,TextSendMessage(text=resp_text))

if __name__ == "__main__":
    app.run("0.0.0.0",port=5000)