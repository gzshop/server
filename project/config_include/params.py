

import os

# #腾讯对象存储
# TX_SECRET_ID = os.getenv("TX_SECRET_ID",None)
# TX_SECRET_KEY = os.getenv("TX_SECRET_KEY",None)


import os

BASEURL = os.getenv("BASEURL","http://localhost:9018")
VERSION = os.getenv("VERSION","v2")
APIURL = "{}/{}{}".format(BASEURL,VERSION,"/api")
CALLBACKURL = "{}{}".format(APIURL,"/order/txPayCallback")

#COS
COS_secret_id = os.getenv("COS_secret_id","")
COS_secret_key = os.getenv("COS_secret_key","")

#短信
Tx_Sms_secretId = os.getenv("Tx_Sms_secretId","")
Tx_Sms_secretKey = os.getenv("Tx_Sms_secretKey","")

#taskserver
TASKSERVERURL = "{}v1/taskapi/order".format(BASEURL)

#物流
FASTMAIL_Key = os.getenv("FASTMAIL_Key","ba89e3a3-54d2-413b-98f1-13402e3a9f78")

"""
支付宝支付
"""
AliPay_signature = os.getenv("AliPay_signature","")
AliPay_Appid = os.getenv("AliPay_Appid","")
Alipay_callbackUrl = os.getenv("Alipay_callbackUrl","")
Alipay_callbackUrlForVip = os.getenv("Alipay_callbackUrlForVip","")
AliPay_app_private_key = os.getenv("AliPay_app_private_key","")
AliPay_alipay_public_key = os.getenv("AliPay_alipay_public_key","")
AliPay_way = os.getenv("AliPay_way","https://openapi.alipaydev.com/gateway.do")

#小程序
WECHAT_APPID = os.getenv("WECHAT_APPID","")
WECHAT_SECRET = os.getenv("WECHAT_SECRET","")
WECHAT_PAY_MCHID = os.getenv("WECHAT_PAY_MCHID",None)
WECHAT_PAY_KEY = os.getenv("WECHAT_PAY_KEY",None)
WECHAT_PAY_RETURN_KEY = os.getenv("WECHAT_PAY_RETURN_KEY",None)
