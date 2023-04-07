import os, boto3, openai
from linebot import (
    LineBotApi, WebhookHandler
)

class LINEBox:
    def __init__(self,role_setting:str):
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=os.environ["AWS_ACCESS_KEY"],
            aws_secret_access_key=os.environ["AWS_SECRET_KEY"],
            region_name=os.environ["AWS_REGION"]
        )

        self.role_setting = role_setting
        self.table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])
        self.line_bot_api = LineBotApi(os.environ["LINE_ACCESS_TOKEN"])
        self.handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
        openai.api_key = os.environ["OPENAI_SECRET_KEY"]

    def query_message_list(self,user_id:str):
        query_msg_list = self.table.get_item(
            Key = { "user_id" : user_id }
        )
        
        return query_msg_list['Item']['msg_list'] if query_msg_list.get('Item') else None
        
    def update_message_list(self,user_id:str,chat_msg_list:list):
        return self.table.update_item(
            Key = { "user_id" : user_id },
            UpdateExpression = "SET #msg_list = list_append(if_not_exists(#msg_list, :empty_list),:new_resp)",
            ExpressionAttributeNames = {
                "#msg_list" : "msg_list"
            },
            ExpressionAttributeValues = {
                ":empty_list" : [],
                ":new_resp" : chat_msg_list
            },
            ReturnValues = "UPDATED_NEW"
        )

    def empty_message_list(self,user_id:str):
        return self.table.delete_item(
            Key = { "user_id" : user_id }
        )

    def chat_completion(self,input_msg:str):
        resp_chatgpt = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=input_msg
        )   
        return resp_chatgpt['choices'][0]['message']['content'].strip()

    def send_message(self,reply_token:str,resp_text:str):
        self.line_bot_api.reply_message(reply_token,resp_text)

    def get_audio_data(self,message_id:str):
        try:
            message_content = self.line_bot_api.get_message_content(message_id)
            with open(os.environ['AUDIO_SAVE_LOCATION'] + "audio.m4a", 'wb') as fd:
                for chunk in message_content.iter_content():
                    fd.write(chunk)
            return True
        except Exception as e:
            print(e)
            return False
        
    def speech_to_text(self,user_audio_path:str=None):
        if user_audio_path is None:
            user_audio_path = os.environ['AUDIO_SAVE_LOCATION'] + "audio.m4a"
    
        audio_file= open(user_audio_path, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript['text']


    def text_handle(self,user_id:str,user_input:str):
        if user_input == "新對話":
            self.empty_message_list(user_id)
            resp_text = "已成功建立新對話！😄"
        else:
            print("============== Query START ================")
            chat_msg_list = self.query_message_list(user_id)
            if chat_msg_list is None:
                chat_msg_list = [{"role": "user", "content": self.role_setting + user_input }]
            else:
                chat_msg_list.append({"role": "user", "content": user_input })
            print("============== Query END ================")
        
            print("============== ChatGPT START ================")
            if len(chat_msg_list) > 10:
                msg_input = chat_msg_list[-4:]
                msg_input.insert(0,{"role": "user", "content": self.role_setting })
            else:
                msg_input = chat_msg_list
            resp_text = self.chat_completion(msg_input)
            print("============== ChatGPT END ================")
                
            print("============== Update START ================")
            chat_msg_list.append({ "role": "assistant", "content": resp_text })
            self.update_message_list(user_id,chat_msg_list)
            print("============== Update END ================")
        return resp_text