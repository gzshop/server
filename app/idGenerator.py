
from lib.utils.db import RedisIdGeneratorForOrder,RedisIdGeneratorForUser,\
    RedisIdGeneratorForGoods,RedisIdGeneratorForGoodsCategory,RedisIdGeneratorForGoodsThemeCategory,RedisIdGeneratorForCard

class idGenerator(object):

    def __init__(self):
        pass

    @staticmethod
    def userid(rolecode):
        return RedisIdGeneratorForUser(key=rolecode).run()

    @staticmethod
    def ordercode():
        return RedisIdGeneratorForOrder().run()

    @staticmethod
    def goodscategory():
        return RedisIdGeneratorForGoodsCategory().run()

    @staticmethod
    def goodsthemecategory():
        return RedisIdGeneratorForGoodsThemeCategory().run()

    @staticmethod
    def getcardid():
        return RedisIdGeneratorForCard().run()

    @staticmethod
    def goods():
        return RedisIdGeneratorForGoods().run()

