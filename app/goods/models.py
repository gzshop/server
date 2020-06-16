
import random
from django.db import models
from lib.utils.mytime import UtilTime

from app.idGenerator import idGenerator

from app.goods.utils import get_qrcode_wechat

class GoodsCateGory(models.Model):

    """
    商品分类表: 支持无限级扩展
    """

    id = models.AutoField(primary_key=True)

    userid = models.BigIntegerField(verbose_name="用户代码",null=True)
    gdcgid = models.CharField(max_length=10,default="",verbose_name="分类代码",null=True)
    gdcgname = models.CharField(max_length=120, default="",verbose_name="分类名称",null=True)
    gdcgtitle = models.CharField(max_length=120,default="",verbose_name="标题",null=True,blank=True)
    gdcglastid = models.IntegerField(verbose_name="上级代码",default=0)

    goods = models.TextField(verbose_name="商品ID集合",default="goods:[]",blank=True)
    rolecode = models.CharField(max_length=255, default='', verbose_name="商品对应的用户类型")

    level = models.IntegerField(verbose_name="第几层",default=1,blank=True)
    sort = models.IntegerField(verbose_name="排序",default=0,blank=True)
    status = models.CharField(max_length=1, default="1",verbose_name="是否上架,0-是,1-否",null=True,blank=True)
    url = models.CharField(max_length=255,default="",blank=True)
    createtime = models.BigIntegerField(default=0,blank=True)
    updtime = models.BigIntegerField(default=0,blank=True)

    def save(self, *args, **kwargs):

        if not self.gdcgid:
            self.gdcgid = idGenerator.goodscategory()

        if not self.createtime:
            self.createtime = UtilTime().timestamp
        self.updtime = UtilTime().timestamp
        return super(GoodsCateGory, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '商品分类表'
        verbose_name_plural = verbose_name
        db_table = 'goodscategory'

class Goods(models.Model):

    """
    商品表
    """

    id = models.AutoField(primary_key=True)

    userid = models.BigIntegerField(verbose_name="用户代码",null=True)
    gdid = models.CharField(max_length=10, verbose_name="商品ID", null=True)

    gdcgid = models.CharField(max_length=10,default="",verbose_name="分类代码",null=True)

    gdname = models.CharField(max_length=120, verbose_name="商品名称", default='', null=True,blank=True)
    gdtitle = models.CharField(max_length=120, verbose_name="商品名称", default='', null=True,blank=True)

    gdtext = models.CharField(max_length=255, verbose_name="描述", default='', null=True,blank=True)
    gdlabel = models.CharField(max_length=255, verbose_name="标签", default='', null=True,blank=True)
    gdimg = models.CharField(max_length=2048, verbose_name="封面图", default='[]', null=True,blank=True)
    gdsku = models.CharField(max_length=2048,verbose_name="sku显示",default='[]',null=True,blank=True)
    gdskulist = models.CharField(max_length=2048,verbose_name="sku商品关联id",default='[]',null=True,blank=True)

    rolecode = models.CharField(max_length=4, default='', verbose_name="商品对应的用户类型")

    gdprice = models.DecimalField(max_digits=18,decimal_places=6,default=0.000,verbose_name="商品价格")
    gdnum  = models.IntegerField(verbose_name="商品数量",default=0)
    sort = models.IntegerField(verbose_name="排序",default=0)

    qrcode = models.CharField(verbose_name="商品二维码",default='',max_length=255)
    hb = models.CharField(verbose_name="海报",default="",max_length=255)

    gdsellnum = models.IntegerField(verbose_name="商品售出数量",default=0)
    gdstatus = models.CharField(verbose_name="状态,0-正常,1-下架",default='0',max_length=1)

    virtual = models.CharField(max_length=1,verbose_name="是否虚拟商品:0-是,1-否",default='1')
    code = models.CharField(max_length=1,verbose_name="是否可以提货码购买:0-是,1-否",default='1')
    gdbrowsenum = models.IntegerField(verbose_name="商品浏览量",default=0)

    createtime = models.BigIntegerField(default=0)
    updtime = models.BigIntegerField(default=0)

    detail = models.TextField(default="")
    product = models.TextField(default="")
    shbz = models.TextField(default="")

    yf = models.CharField(max_length=1,verbose_name="邮费,0-5元/件,1-10元/件,2-18元/件,3-36元/件,4-55元/件,5-包邮",default='0')

    limit_unit = models.CharField(max_length=1,verbose_name="限购周期单位,A-不限购,M-月,W-周",default="A")
    limit_count = models.IntegerField(verbose_name="限购周期值",default=0)
    limit_number = models.IntegerField(verbose_name="限购数量",default=0)

    limit_citys = models.CharField(max_length=255,verbose_name="限购地区",default="[]", null=True,blank=True)
    limit_citys_number = models.IntegerField(verbose_name="地区限购数量",default=0,null=True,blank=True)


    isvip = models.CharField(max_length=1,verbose_name="是否仅会员可见,0-是,1-否",default='1')

    jf_type = models.CharField(max_length=1,verbose_name="积分方式 0-未设置 1-按比例,2-按固定",default='0')
    jf_value = models.DecimalField(max_digits=18,decimal_places=6,default=0.000,verbose_name="积分值")

    def save(self, *args, **kwargs):

        if not self.gdid:
            self.gdid = idGenerator.goods()
            # self.qrcode = get_qrcode_wechat(self.gdid)

        if not self.createtime:
            self.createtime = UtilTime().timestamp
        self.updtime = UtilTime().timestamp
        # self.qrcode = get_qrcode_wechat(self.gdid)
        return super(Goods, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '商品表'
        verbose_name_plural = verbose_name
        db_table = 'goods'

class GoodsTheme(models.Model):

    """
    商品主题分类表
    """

    id = models.AutoField(primary_key=True)

    userid = models.BigIntegerField(verbose_name="用户代码",null=True)
    typeid = models.CharField(max_length=10,default="",verbose_name="分类代码",null=True,blank=True)
    type = models.CharField(max_length=1,default="0",verbose_name="0-热门分类,1-推荐分类,2-热门分类1",blank=True)
    name = models.CharField(max_length=120, default="",verbose_name="分类名称",null=True,blank=True)
    sort = models.IntegerField(verbose_name="排序",default=0,blank=True)
    rolecode = models.CharField(max_length=255, default='', verbose_name="商品对应的用户类型")
    status = models.CharField(max_length=1, default="1",verbose_name="是否上架,0-是,1-否",null=True,blank=True)
    goods = models.TextField(verbose_name="商品ID集合",default="goods:[]",blank=True)
    url = models.CharField(max_length=255,default="",blank=True)
    url1 = models.CharField(max_length=255,default="",blank=True)
    createtime = models.BigIntegerField(default=0,blank=True)
    updtime = models.BigIntegerField(default=0,blank=True)

    def save(self, *args, **kwargs):

        if not self.typeid:
            self.typeid = idGenerator.goodsthemecategory()

        if not self.createtime:
            self.createtime = UtilTime().timestamp
        self.updtime = UtilTime().timestamp
        return super(GoodsTheme, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '商品主题分类表'
        verbose_name_plural = verbose_name
        db_table = 'goodstheme'

class Cardvirtual(models.Model):

    """
    卡片
    """

    id = models.AutoField(primary_key=True)

    userid = models.BigIntegerField(verbose_name="用户代码",null=True)

    useuserid = models.BigIntegerField(verbose_name="使用用户",default=0)
    status = models.CharField(max_length=1,verbose_name="使用状态,0-使用,1-未使用",default='1')

    account = models.CharField(verbose_name="卡号",max_length=60,default="")
    password = models.CharField(verbose_name="密码",max_length=60,default="")

    createtime = models.BigIntegerField(default=0,blank=True)
    updtime = models.BigIntegerField(default=0,blank=True)

    gdid = models.CharField(max_length=10, verbose_name="商品ID", null=True)

    username=None

    def save(self, *args, **kwargs):

        if not self.createtime:
            self.createtime = UtilTime().timestamp
            print(self.createtime)
        self.updtime = UtilTime().timestamp
        return super(Cardvirtual, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '虚拟商品卡密'
        verbose_name_plural = verbose_name
        db_table = 'cardvirtual'


class Card(models.Model):

    """
    卡片
    """

    id = models.AutoField(primary_key=True)

    userid = models.BigIntegerField(verbose_name="用户代码",null=True)
    type = models.CharField(verbose_name="0-充值卡,1-商品卷",default='0',max_length=1)

    useuserid = models.BigIntegerField(verbose_name="使用用户",default=0)
    status = models.CharField(max_length=1,verbose_name="使用状态,0-使用,1-未使用",default='1')

    account = models.CharField(verbose_name="卡号",max_length=60,default="")
    password = models.CharField(verbose_name="密码",max_length=60,default="")
    bal  = models.DecimalField(max_digits=18,decimal_places=6,default=0.000,verbose_name="面值")

    rolecode = models.CharField(max_length=4, default='',verbose_name="卡号对应的用户类型")

    createtime = models.BigIntegerField(default=0,blank=True)
    updtime = models.BigIntegerField(default=0,blank=True)

    username=None

    def save(self, *args, **kwargs):

        if not self.account:
            self.account = idGenerator.getcardid()

        if not self.password:
            self.password = random.randint(10000000,99999999)

        if not self.createtime:
            self.createtime = UtilTime().timestamp
            print(self.createtime)
        self.updtime = UtilTime().timestamp
        return super(Card, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '卡片'
        verbose_name_plural = verbose_name
        db_table = 'card'

class DeliveryCode(models.Model):

    """
    提货码
    """

    id = models.AutoField(primary_key=True)

    userid = models.BigIntegerField(verbose_name="用户代码",null=True)

    useuserid = models.BigIntegerField(verbose_name="使用用户",default=0)
    status = models.CharField(max_length=1,verbose_name="使用状态,0-使用,1-未使用",default='1')

    account = models.CharField(verbose_name="卡号",max_length=60,default="")
    password = models.CharField(verbose_name="密码",max_length=60,default="")

    rolecode = models.CharField(max_length=4, default='',verbose_name="发卡企业")
    rolename = models.CharField(max_length=60,default="",verbose_name="企业名称")

    createtime = models.BigIntegerField(default=0,blank=True)
    updtime = models.BigIntegerField(default=0,blank=True)
    bal = models.DecimalField(max_digits=18,decimal_places=6,default=0.000,verbose_name="面值")
    gdid = models.CharField(max_length=10, verbose_name="商品ID", null=True)

    username=None

    def save(self, *args, **kwargs):

        if not self.createtime:
            self.createtime = UtilTime().timestamp
            print(self.createtime)
        self.updtime = UtilTime().timestamp
        return super(DeliveryCode, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '虚拟商品卡密'
        verbose_name_plural = verbose_name
        db_table = 'deliverycode'
        
class GoodsLinkSku(models.Model):

    id = models.BigAutoField(primary_key=True)
    gdid = models.CharField(max_length=10, verbose_name="商品ID", null=True)
    valueid1 = models.BigIntegerField(verbose_name="sku值ID", default=0)
    valueid2 = models.BigIntegerField(verbose_name="sku值ID", default=0)
    valueid3 = models.BigIntegerField(verbose_name="sku值ID", default=0)
    img = models.CharField(verbose_name="图片",max_length=255,default="")
    price = models.DecimalField(max_digits=18,decimal_places=6,default=0.000,verbose_name="价格")
    stock = models.IntegerField(verbose_name="库存",default=0)
    code = models.CharField(max_length=60,verbose_name="规格编码",default="")
    cost_price = models.DecimalField(max_digits=18,decimal_places=6,default=0.000,verbose_name="成本价")
    number = models.IntegerField(verbose_name="销量",default=0)
    sort = models.IntegerField(verbose_name="排序",default=0)
    jf = models.DecimalField(max_digits=18,decimal_places=6,default=0.000,verbose_name="积分")

    class Meta:
        db_table = 'goodslinksku'

class SkuKey(models.Model):

    id = models.BigAutoField(primary_key=True)

    userid = models.BigIntegerField(verbose_name="用户代码",null=True,default=0)
    key = models.CharField(verbose_name="sku组名称",default='',max_length=60)

    class Meta:
        db_table = 'skukey'

class SkuValue(models.Model):
    id = models.BigAutoField(primary_key=True)

    userid = models.BigIntegerField(verbose_name="用户代码", null=True,default=0)
    keyid = models.BigIntegerField(verbose_name="sku组名称", default=0)
    value = models.CharField(verbose_name="sku值名称",default="",max_length=60)

    class Meta:
        db_table = 'skuvalue'