

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
AliPay_Appid = os.getenv("AliPay_Appid","2021001166685516")
AliPay_alipay_private_key = os.getenv("AliPay_app_private_key","""-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAxIBpCXiRiVgJMBmzmS1hwV2XyVXwH1DRBG1JUC1Rjaae2ios
LlQDSQs9+WOLSILhExZtzLhh0WVUnYw2g7IJztyPUXDknBw8s1ciNaBTfDX4zreI
rN42y9cVWGznLyv+5LCmyjAhS5NtlJlYnsMxM5ykKj/D6qpVaSROpRvEuyoe1EV0
eisHkfzS/Mk/szNnz1Y544IuX5YQwcy21P+gXwH/FZ/NvcaJq44fCXa+vyOAbtSz
lxHhFQxvuZ448hydxdw13ZfklnW3kcfudslzv2YeZ0Y8m3QK6azbGPCUAVxQ645r
qb7BijxQJEnOf/QDzKA+iH82iwxNssT6Q7gblQIDAQABAoIBAH8/BEW8zMnat4Bt
dE7iA2abO/qF6wvsYp3yQ0JnRmNrHXz7SEbr4oC/he9kFcLr9eJNaObkE3vsmWG4
dWjMtus9CpXbfD7XTjt4Vk/RtZ4+uRLr6NbAw002x7zOMNrsK5BeEHPnvPfazWAn
+So+DjN04R320uC4UrzWZRMoKzpjRa+Ets7tmG2mYHWDOFS00ZvdGw9gxQmvvvHP
UUZhmi5X4nEMjtJhaUiKplBD/2B3J5WrpMMsUwe95uOXMJ8pCvFaU4RrqcCPu7t7
CmP5m1oZik75BfSYPZsEsGhdPX59eS9didWcFRujNNmcJUMC5eK4Oc7XkYSRvBQo
I6YSYKECgYEA9EKiXrbqsSQd9aWjOMxtbVs1Co8X1QaR94uOcx1tzz9h9SiLPuRR
0O0Lx7TKI+wbCRuvpv5RWeo5MHjkjB2fDnvJ6Ctz3QDOG23ik7xLQfClTIQW6JVh
3cJvKFONO5wCjWZHpozPnLdC8MKZLpS4Xu4yMP2Rhmk7ZKB6n9pUuu0CgYEAzfIn
2frXbgBhqni+ZRm9B9vr0Y51SfT0lHPAeYzVEPyT5z9Y50mnOaPmzVOu3nds0Tk5
GPtcFbaoYOjS42zdlFeIobUpalL41OCvyIhE201CyXOLkRuiiAz+QVdq2aYyZMSa
oNQaHmz3ygmuK5x/+i2peQkuDJ3j/gvHyBf6RkkCgYBk1elP7nVeoYlYsoN6XDJE
deWksUPmZmr15X/uF9UQPJtE6PLrCLiZ5nH5hLH6OGtEzFAsQUr2MpJfZ1j6WvQh
t4q3tNCFCOMNQcTKtm3fD+g9eT430Atxz+WxoSRp2lLXasTjhbfje2hAGiXArBac
4fqIbPWZpnGlbfaRbUGTVQKBgC2H4OmfPGuUaANBSI6ffxwysdMVlLayEjST1rTI
vv5PaP+SELypmu/yXX99hcanToZ/CTGNuNEQHe+26ZDgK6i1JX7ix3I7P8oIlrRV
9CsrzJ0vD2cYXfmILdoSUowl4zRGBw2RdujNHIctVrVLlzufRr18mxKtAY/T2OpS
6sEJAoGBAIw4xea9/w0BgHQMq2me4SQOy36ihJtau3akLb+SUHlViF9yClVMWncX
7+LzLeIEeNAfxDLMBBtv8kB/R8xTwalBwiEwBsZpd+t7kTbhE/i66kX8L8lp6AJv
CrRF4yJgvA415AG00g6JA8FrHH+ULH8kjeVm9CbHH1mwaMkl1FaB
-----END RSA PRIVATE KEY-----""")
AliPay_alipay_public_key = os.getenv("AliPay_alipay_public_key","""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAr65OBLyXJ/zKcNH6DmPG2UntbwMevqLDu2jSTH1neLV4q5Xm2xjP+z1A7kN7LcjmOFLKnVXG3pms0KoCMcRKEXUZuj4Rxb30moC9OYHeiO3AO3m853uo9MewW6GbcDGenD2r5ypeZSJmT2zR94XkxdlBWu9zxPRaSxaesS8e8si04z2KNxS0cH7lhxE5x5pqwB0sYJSorW5BUL5dyrihB2xRFYP7Bzrb99SOmAjzO3N54bJSaoBD0a90yp0fqBrcdID6aI490Vsag9wNEz36glOS57ojDqRiLkfA6NSbXFNnojGkUKywtmIr9YQOfYffzcPEP+2ONKyCNTsTNGh1OQIDAQAB
-----END PUBLIC KEY-----""")
AliPay_way = os.getenv("AliPay_way","https://openapi.alipaydev.com/gateway.do")

#小程序
WECHAT_APPID = os.getenv("WECHAT_APPID","")
WECHAT_SECRET = os.getenv("WECHAT_SECRET","")
WECHAT_PAY_MCHID = os.getenv("WECHAT_PAY_MCHID",None)
WECHAT_PAY_KEY = os.getenv("WECHAT_PAY_KEY",None)
WECHAT_PAY_RETURN_KEY = os.getenv("WECHAT_PAY_RETURN_KEY",None)
