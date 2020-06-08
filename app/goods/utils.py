
import os,json
from project.config_include.params import WECHAT_SECRET,WECHAT_APPID
from lib.utils.http_request import send_request_other
from requests import request
from project.settings import IMAGE_PATH
from project.config_include.common import ServerUrl


def get_qrcode_wechat(id):

    params = dict(
        appid=WECHAT_APPID,
        secret=WECHAT_SECRET,
        grant_type="client_credential"
    )

    res = send_request_other(
        url="https://api.weixin.qq.com/cgi-bin/token",
        params=params)


    token = res['access_token']

    data=dict(
        # access_token= token,
        scene=id,
        page="pages/details/index"
    )

    res = request(method='POST',json=data,url="https://api.weixin.qq.com/wxa/getwxacodeunlimit?"+'access_token=%s'%token,
                  headers={
                    "Content-Type": 'application/json'
                    })

    path = os.path.join(IMAGE_PATH, 'goods')

    with open(os.path.join(path, "{}.jpg".format(id)), 'wb') as f:
        f.write(res.content)

    return "{}/statics/images/{}/{}".format(ServerUrl,"goods","{}.jpg".format(id))



