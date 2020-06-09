

import os

# #腾讯对象存储
# TX_SECRET_ID = os.getenv("TX_SECRET_ID",None)
# TX_SECRET_KEY = os.getenv("TX_SECRET_KEY",None)


import os

BASEURL = os.getenv("BASEURL","http://localhost:9018")
VERSION = os.getenv("VERSION","v1")
APIURL = "{}/{}{}".format(BASEURL,VERSION,"/api")
CALLBACKURL = "{}{}".format(APIURL,"/order/txPayCallback")

#COS
COS_secret_id = os.getenv("COS_secret_id","")
COS_secret_key = os.getenv("COS_secret_key","")

"""
支付宝支付
"""
AliPay_Appid = os.getenv("AliPay_Appid","")
AliPay_alipay_private_key = os.getenv("AliPay_alipay_private_key","")
AliPay_alipay_public_key = os.getenv("AliPay_alipay_public_key","")

#小程序
WECHAT_APPID = os.getenv("WECHAT_APPID","")
WECHAT_SECRET = os.getenv("WECHAT_SECRET","")
WECHAT_PAY_MCHID = os.getenv("WECHAT_PAY_MCHID",None)
WECHAT_PAY_KEY = os.getenv("WECHAT_PAY_KEY",None)
WECHAT_PAY_RETURN_KEY = os.getenv("WECHAT_PAY_RETURN_KEY",None)
