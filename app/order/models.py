
from django.db import models
from lib.utils.mytime import UtilTime

from app.idGenerator import idGenerator

class ShopCart(models.Model):

    """
    购物车表
    """

    id = models.BigAutoField(primary_key=True,verbose_name="ID")

    userid = models.BigIntegerField(verbose_name="用户代码",null=True)
    gdid = models.CharField(max_length=10, verbose_name="商品ID", null=True)
    gdimg = models.CharField(max_length=255, verbose_name="封面图", default='', null=True, blank=True)
    gdname = models.CharField(max_length=120, verbose_name="商品名称", default='', null=True, blank=True)
    gdprice = models.DecimalField(max_digits=18,decimal_places=6,default=0.000,verbose_name="商品价格")
    gdnum  = models.IntegerField(verbose_name="商品数量",default=0)

    createtime = models.BigIntegerField(default=0)
    updtime = models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):

        if not self.createtime:
            self.createtime = UtilTime().timestamp
        self.updtime = UtilTime().timestamp
        return super(ShopCart, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '购物车表'
        verbose_name_plural = verbose_name
        db_table = 'shopcart'

class OrderGoodsLink(models.Model):

    """
    订单商品关联表
    """

    linkid = models.BigAutoField(primary_key=True,verbose_name="ID")
    userid = models.BigIntegerField(verbose_name="用户代码",null=True)
    orderid = models.CharField(max_length=19,verbose_name="订单ID",null=True,default="")
    gdid = models.CharField(max_length=10, verbose_name="商品ID", null=True)
    gdimg = models.CharField(max_length=255, verbose_name="封面图", default='', null=True, blank=True)
    gdname = models.CharField(max_length=120, verbose_name="商品名称", default='', null=True, blank=True)
    virtual = models.CharField(max_length=1,verbose_name="是否虚拟商品:0-是,1-否",default='1')
    virtualids = models.CharField(max_length=2048,verbose_name="卡密集合",default='{"ids":[]}')

    thm = models.CharField(max_length=1,verbose_name="是否提货码商品:0-是,1-否",default='1')
    thms = models.CharField(max_length=2048,verbose_name="提货码",default='{"thms":[]}')
    gdprice = models.DecimalField(max_digits=18,decimal_places=6,default=0.000,verbose_name="商品价格")
    gdnum  = models.IntegerField(verbose_name="商品数量",default=0)

    skugoodslinkid = models.IntegerField(verbose_name="商品sku关联表id",default=0)
    skugoodslabel = models.CharField(max_length=60,verbose_name="说明")

    createtime = models.BigIntegerField(default=0)
    updtime = models.BigIntegerField(default=0)


    count = None

    def save(self, *args, **kwargs):

        if not self.createtime:
            self.createtime = UtilTime().timestamp
        self.updtime = UtilTime().timestamp
        return super(OrderGoodsLink, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '订单商品关联表'
        verbose_name_plural = verbose_name
        db_table = 'ordergoodslink'


class Order(models.Model):

    """
    订单表
    """

    id = models.BigAutoField(primary_key=True,verbose_name="ID")

    orderid = models.CharField(max_length=19,verbose_name="订单ID",null=True)
    linkid = models.CharField(max_length=255,verbose_name="关联表集合",default="")

    userid = models.BigIntegerField(verbose_name="用户代码", null=True)

    amount = models.DecimalField(verbose_name="交易金额",max_digits=18,decimal_places=6,default=0.0)
    payamount = models.DecimalField(verbose_name="微信支付金额",max_digits=18,decimal_places=6,default=0.0)
    balamount = models.DecimalField(verbose_name="余额支付金额",max_digits=18,decimal_places=6,default=0.0)
    memo = models.CharField(max_length=255,verbose_name="备注",default="")

    before_status = models.CharField(max_length=1,verbose_name="状态,1-申请退款,2-已退款,3-拒绝退款",default="")
    refundmsg = models.CharField(max_length=60,verbose_name="申请退款理由!",default="")
    status = models.CharField(max_length=1,verbose_name="状态,0-待付款,1-已付款(待发货),2-已发货(待收货),3-已收货,4-已退款,9-取消订单,8-已删除",default="0")
    fhstatus = models.CharField(max_length=1,verbose_name="0-已发货,1-未发货",default="1")
    paymsg = models.TextField(default="")
    address = models.TextField(default="{}")

    use_jf = models.DecimalField(verbose_name="交易使用积分",max_digits=18,decimal_places=6,default=0.0)
    get_jf = models.DecimalField(verbose_name="获得积分",max_digits=18,decimal_places=6,default=0.0)

    isvirtual = models.CharField(max_length=1,verbose_name="是否都是虚拟商品 0-是,1-否",default="1")
    isthm = models.CharField(max_length=1,verbose_name="是否提货码兑换 0-是,1-否",default="1")

    createtime = models.BigIntegerField(default=0,verbose_name="订单创建时间")
    updtime = models.BigIntegerField(default=0)

    yf = models.DecimalField(verbose_name="运费",max_digits=18,decimal_places=6,default=0.0)

    kdno = models.CharField(max_length=60,verbose_name="快递单号",default="")
    kdname = models.CharField(max_length=60,verbose_name="快递公司简称",default="")

    paytype = models.CharField(max_length=1,verbose_name="支付方式 2-支付宝",default='2')

    mobile = None

    def save(self, *args, **kwargs):

        if not self.orderid:
            self.orderid = idGenerator.ordercode()


        if not self.createtime:
            self.createtime = UtilTime().timestamp
        self.updtime = UtilTime().timestamp
        return super(Order, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '订单表'
        verbose_name_plural = verbose_name
        db_table = 'order'

def viphandler(time,unit,term):
    ut = UtilTime()
    exprise= 0
    paytime_arrow = ut.timestamp_to_arrow(time)
    if unit == '0':
        exprise = paytime_arrow.shift(weeks=term).timestamp
    elif unit == '1':
        exprise = paytime_arrow.shift(months=term).timestamp
    elif unit == '2':
        exprise = paytime_arrow.shift(years=term).timestamp

    return exprise

class OrderVip(models.Model):

    """
    会员订单充值表
    """

    id = models.BigAutoField(primary_key=True,verbose_name="ID")
    orderid = models.CharField(max_length=19,verbose_name="订单ID",null=True)
    userid = models.BigIntegerField(verbose_name="用户代码", null=True)
    amount = models.DecimalField(verbose_name="交易金额",max_digits=18,decimal_places=6,default=0.0)
    status = models.CharField(max_length=1,verbose_name="状态,0-待付款,1-已付款",default="0")
    createtime = models.BigIntegerField(default=0,verbose_name="订单创建时间")
    paytime = models.BigIntegerField(default=0, verbose_name="付款时间")
    paytype = models.CharField(max_length=1, verbose_name="支付方式 2-支付宝", default='2')
    exprise = models.BigIntegerField(default=0, verbose_name="到期时间")
    term = models.IntegerField(default=0,verbose_name="期限")
    unit = models.CharField(max_length=1,verbose_name="周期单位,0-周,1-月,Y-年",default='1')

    def save(self, *args, **kwargs):

        ut = UtilTime()

        if not self.orderid:
            self.orderid = idGenerator.ordercode()

        if not self.exprise and self.paytime:
            self.exprise = viphandler(self.paytime,self.unit,self.term)

        if not self.createtime:
            self.createtime = ut.timestamp
        return super(OrderVip, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '会员充值订单表'
        verbose_name_plural = verbose_name
        db_table = 'ordervip'

class Address(models.Model):

    """
    地址表
    """

    id = models.BigAutoField(primary_key=True,verbose_name="ID")
    userid = models.BigIntegerField(verbose_name="用户代码",null=True)

    name = models.CharField(max_length=60,verbose_name="收获人",default='')
    phone = models.CharField(max_length=60,verbose_name="收获电话",default='')
    detail = models.CharField(max_length=1024,verbose_name="详细地址",default="")
    label = models.CharField(max_length=1024,verbose_name="地址",default="")
    moren = models.CharField(max_length=1,verbose_name="默认,0-是,1-否",default='0')

    createtime = models.BigIntegerField(default=0)
    updtime = models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):

        if not self.createtime:
            self.createtime = UtilTime().timestamp
        self.updtime = UtilTime().timestamp
        return super(Address, self).save(*args, **kwargs)

    class Meta:
        verbose_name = '地址表'
        verbose_name_plural = verbose_name
        db_table = 'address'