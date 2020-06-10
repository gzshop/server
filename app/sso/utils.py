

import hmac, base64, hashlib,json,random
from datetime import datetime as pydatetime
from requests import request
from project.config_include.params import Tx_Sms_secretId,Tx_Sms_secretKey
from lib.utils.exceptions import PubErrorCustom

try:
    from urllib import urlencode
    from urllib2 import Request, urlopen
except ImportError:
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

def sendMsg(mobile,vercode):
    # 云市场分配的密钥Id
    secretId = Tx_Sms_secretId
    # 云市场分配的密钥Key
    secretKey = Tx_Sms_secretKey
    source = "market"

    # 签名
    datetime = pydatetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    signStr = "x-date: %s\nx-source: %s" % (datetime, source)
    sign = base64.b64encode(hmac.new(secretKey.encode('utf-8'), signStr.encode('utf-8'), hashlib.sha1).digest())
    auth = 'hmac id="%s", algorithm="hmac-sha1", headers="x-date x-source", signature="%s"' % (secretId, sign.decode('utf-8'))

    # 请求方法
    method = 'GET'
    # 请求头
    headers = {
        'X-Source': source,
        'X-Date': datetime,
        'Authorization': auth,
        'Content-Type':'application/x-www-form-urlencoded'
    }
    # 查询参数
    queryParams = {
        'mobile': mobile,
        'param': '**验证码**:{}'.format(vercode),
        'smsSignId': '6ea1cadc2b164983b63bd6eb15425d65',
        'templateId': '6d5a64b8322d43759cc63f5c51c6a770'
    }
    # body参数（POST方法下存在）
    bodyParams = {
    }
    # url参数拼接
    url = 'http://service-m6t5cido-1256923570.gz.apigw.tencentcs.com/release/sms/send'
    if len(queryParams.keys()) > 0:
        url = url + '?' + urlencode(queryParams)


    res = request(method="GET",headers=headers,url=url)
    try:
        if json.loads(res.content.decode('utf-8'))['code'] != '0':
            raise PubErrorCustom("发送失败,请联系客服!")
    except Exception as e:
        print(str(e))
        raise PubErrorCustom("发送失败,请联系客服!")


if __name__ == '__main__':
    sendMsg()