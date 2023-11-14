import logging
import time
import requests
import json
import markdown
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

    def send_message(self, msg, title, url='', to_user='@all'):
        msgtype = 'textcard'
        title = title
        msg = msg.replace('\r\n\r\n', '\r\n')
        time = '通知时间：' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{time}\n通知内容：{msg}"
        msg = markdown.markdown(msg)
        url = url if url else self._host + '?msg=' + msg.replace('#', '%23').replace('\r', '%0D').replace('\n', '%0A')\
            .replace('\t', '%09').replace('     ', '%09')
        to_user = to_user
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.get_access_token()
        urls = ''
        n = 0
        for u in url:
            if ord(u) > 127:
                if n < 2048:
                    urls = urls + u
                n += 2
            else:
                if n < 2048:
                    urls = urls + u
                n += 1
        if n > 2048:
            logging.debug('url字节数：' + str(n) + '已截取前2048个字节数据。')
        else:
            logging.debug('url字节数：' + str(n))
        msg = {"title": title, "description": message[0:168], "url": urls, "btntxt": "详情"}

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


@app.route('/', methods=['GET'])
def msg():
    msg = request.args.get('msg') if request.args.get('msg') else 'Hello, World!'
    msg = parse.unquote(msg)
    # msg = markdown.markdown(msg)
    # 简单粗暴的手机页面适应
    mobile_page = '<!doctype html><html><head>' \
                  '<meta charset="UTF-8" name="viewport" content="width=device-width,' \
                  'initial-scale=1.0,user-scalable=no">' \
                  '</head><body><div id="content">' \
                  '<view style=”white-space:pre-wrap”>' + msg + '</view></div></body></html>'
    ret = mobile_page
    return ret


@app.route('/' + SCKEY + '.send', methods=['POST', 'GET'])
def send():
    text = request.args.get('text') if request.args.get('text') else request.form['text']
    desp = request.args.get('desp') if request.args.get('desp') else request.form['desp']
    HOST = request.host_url
    wwpush = WeWorkPush(HOST, CORP_ID, AGENT_ID, SECRET)
    res = wwpush.send_message(desp, text)
    return res


if __name__ == '__main__':
    app.run('0.0.0.0', 8899)
