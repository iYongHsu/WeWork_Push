import logging
import time
import requests
import json
from datetime import datetime
from flask import Flask, request
from urllib import parse


# 自定义推送请求接口SCKEY
SCKEY = 'ABCDEFG'
# 企业ID
CORP_ID = 'Your corpid'
# 企业应用ID
AGENT_ID = 'Your agentid'
# 企业凭证密钥
SECRET = 'Your corpsecret'
# 接收人，默认为全部@all，多人格式为XXX|YYY
TOUSER = '@all'
# 缩略图路径
IMAGESFILE = './images.jpg'

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG, filename='wwpush.log')
logging = logging.getLogger(__name__)


class WeWorkPush():
    def __init__(self, host, corp_id, agent_id, secret):
        self._host = host
        self._corp_id = corp_id
        self._agent_id = agent_id
        self._secret = secret
        self._token = ''
        self._token_expires_time = 0

    def get_access_token(self):
        if self._token == '' or self._token_expires_time < time.time():
            logging.info('获取AccessToken！')
            gettoken_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
            data = {
                'corpid': self._corp_id,
                'corpsecret': self._secret
            }
            res = requests.post(gettoken_url, params=data)
            res_data = json.loads(res.text)
            if not res_data['access_token'] or res_data['errcode'] != 0:
                logging.error('获取AccessToken失败！详细错误： ')
                logging.error(res_data)
            else:
                self._token = res_data['access_token']
                self._token_expires_time = time.time() + res_data["expires_in"]
        return self._token

    def upload_file(self, imagesfile, media_type='image'):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/media/upload'
        params = {
            "access_token": self.get_access_token(),
            "type": media_type
        }
        files = {
            "media": open(imagesfile, "rb")
        }
        response = requests.post(url, params=params, files=files)
        media_id = response.json()["media_id"]
        return media_id

    def send_message(self, msg, title, url='', to_user='@all'):
        msgtype = 'mpnews'
        title = title
        msg = msg.replace('\r\n\r\n', '\r\n')
        time = '通知时间：' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        digest = f"{time}\n通知内容：{msg}"
        message = f"{time}<br/>通知内容：{msg}"
        message = message.replace('\n', '<br/>')
        to_user = to_user
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.get_access_token()
        media_id = self.upload_file(IMAGESFILE,'image')
        msg = {
                "articles":[
                    {
                        "title": title,
                        "thumb_media_id": media_id,
                        "content": message,
                        "digest": digest
                    }
                ]
            }
        send_data = {
            "touser": to_user,
            "msgtype": msgtype,
            "agentid": self._agent_id,
            msgtype: msg,
            "safe": "0"
        }
        logging.debug(send_data)
        send_msges = json.dumps(send_data)
        response = requests.post(send_url, send_msges).json()
        if response["errcode"] != 0:
            logging.error(response)
        else:
            logging.debug(response)
        return response


@app.route('/' + SCKEY + '.send', methods=['POST', 'GET'])
def send():
    text = request.args.get('title') if request.args.get('title') else request.form['title']
    desp = request.args.get('desp') if request.args.get('desp') else request.form['desp']
    HOST = request.host_url
    wwpush = WeWorkPush(HOST, CORP_ID, AGENT_ID, SECRET)
    res = wwpush.send_message(desp, text, to_user = TOUSER)
    return res


if __name__ == '__main__':
    app.run('0.0.0.0', 8899)
