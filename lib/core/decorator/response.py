import time,jsonfrom functools import wrapsfrom django.db import transactionfrom django.core.serializers.json import DjangoJSONEncoderfrom lib.core.http.response import HttpResponsefrom lib.core.paginator import Paginationfrom lib.utils.log import loggerfrom lib.utils.exceptions import PubErrorCustom,InnerErrorCustomfrom lib.utils.passwd import decrypt,encryptfrom lib.utils.db import RedisTokenHandler,RedisAppHandler,RedisAppHandlerAdminfrom app.cache.utils import RedisCaCheHandlerfrom include import error as errorlistfrom app.user.models import Usersfrom project.config_include.params import ADDRESS_LIMITclass Core_connector:    def __init__(self,**kwargs):        #是否加数据库事务        self.isTransaction = kwargs.get('isTransaction',False)        #是否分页        self.isPagination = kwargs.get('isPagination',False)        #是否加密        self.isPasswd = kwargs.get('isPasswd', False)        #是否校验ticket        self.isTicket = kwargs.get('isTicket', False)        #是否校验小程序Ticket        self.isWechatTicket = kwargs.get('isWechatTicket', False)        #是否同步到缓存系统(如果同步到缓存系统,数据通过request.cache_save同步,isCach是数组)        self.isCache = kwargs.get("isCache",False)        self.serializer_class = kwargs.get("serializer_class",False)        self.model_class = kwargs.get("model_class",False)    #前置处理    def __request_validate(self,request,**kwargs):        terminal = request.META.get('HTTP_TERMINAL')        version = request.META.get('HTTP_VERSION1')        address = request.META.get("HTTP_ADDRESS")        if len(address):            address = address.decode("UTF-8")        if len(address) and ADDRESS_LIMIT in address:            request.addressBool = True        else:            request.addressBool = False        logger.info("终端:[{}],版本号:[{}],地址[{},{}]".format(terminal,version,address,request.addressBool))        print("终端:[{}],版本号:[{}]".format(terminal,version))        if terminal == 'Android_Manage':            appHandler = RedisAppHandlerAdmin()            res = appHandler.isUpdate(request.META.get('HTTP_VERSION1'))            if res:                raise InnerErrorCustom(code="77777", msg=res)        elif terminal == 'Pc_Manage':            #暂时未处理            pass        elif terminal == 'Android_User':            appHandler = RedisAppHandler()            res = appHandler.isUpdate(request.META.get('HTTP_VERSION1'))            if res:                raise InnerErrorCustom(code="77777", msg=res)        else:            appHandler = RedisAppHandler()            res = appHandler.isUpdate(request.META.get('HTTP_VERSION1'))            if res:                raise InnerErrorCustom(code="77777", msg=res)        #校验凭证并获取用户数据        if self.isTicket:            ticket = request.META.get('HTTP_TICKET')            if not ticket:                raise InnerErrorCustom(code="40001",msg="登录令牌不存在!")            result = RedisTokenHandler(key=ticket).redis_dict_get()            if not result:                raise InnerErrorCustom(code="40002",msg="登录令牌已失效!")            try:                user = Users.objects.get(userid=result['userid'])                if user.status == '1':                    raise InnerErrorCustom(code="40001", msg="账户已到期!")                elif user.status == '2':                    raise InnerErrorCustom(code="40001", msg="账户已冻结!")            except Users.DoesNotExist:                raise InnerErrorCustom(code="40001",msg="登录令牌不存在!")            request.user = result            request.ticket = ticket        if self.isPasswd:            if request.method == 'GET':                if 'data' not in request.query_params:                    raise PubErrorCustom("拒绝访问!!")                if request.query_params.get('data') and len(                    request.query_params.get('data')) and request.query_params.get('data') != '{}':                    request.query_params_format = json.loads(decrypt(request.query_params.get('data')))                else:                    request.query_params_format = {}            if request.method == 'POST':                if 'data' not in request.data:                    raise PubErrorCustom("拒绝访问!!")                if request.data.get('data') and len(request.data.get('data')):                    request.data_format = json.loads(decrypt(request.data.get('data')))                else:                    request.data_format = {}        else:            request.query_params_format = request.query_params            request.data_format = request.data        # print(self.isWechatTicket)        # if self.isWechatTicket:        #     if request.method == 'GET':        #         userid = request.query_params_format['userid']        #     elif request.method == 'POST':        #         userid = request.data_format['userid']        #        #     print(userid)        #     res = RedisCaCheHandler(        #         method="get",        #         table="user",        #         must_key_value=userid,        #     ).run()        #     print(res)        #     if not res:        #         raise PubErrorCustom("拒绝访问!")        #     else:        #         request.user = res        #         print(request.user)        if self.serializer_class:            # pk = kwargs.get('pk')            instance = None            if request.data_format.get("updKey"):                try:                    instance = self.model_class.objects.get(**{                        request.data_format.get("updKey"):request.data_format.get("key")                    })                except TypeError:                    raise PubErrorCustom('serializer_class类型错误')                except Exception:                    raise PubErrorCustom('未找到')            serializer = self.serializer_class(data=request.data_format, instance=instance)            if not serializer.is_valid():                errors = [key + ':' + value[0] for key, value in serializer.errors.items() if isinstance(value, list)]                if errors:                    error = errors[0]                    error = error.lstrip(':').split(':')                    try:                        error = "{}:{}".format( getattr( errorlist,error[0]) , error[1])                    except AttributeError as e:                        error = error[1]                else:                    for key, value in serializer.errors.items():                        if isinstance(value, dict):                            key, value = value.popitem()                            error = key + ':' + value[0]                            break                raise PubErrorCustom(error)            kwargs.setdefault('serializer',serializer)            kwargs.setdefault('instance', instance)        return kwargs    def __run(self,func,outside_self,request,*args, **kwargs):        if self.isTransaction:            with transaction.atomic():                res = func(outside_self, request, *args, **kwargs)        else:            res = func(outside_self, request, *args, **kwargs)        if res and 'data' in res and \            ((self.isPagination and isinstance(res['data'], list)) or (                self.isPagination and isinstance(res['data'], dict) and 'data' in res['data'])):            if 'header' in res:                header = res['header']                res = Pagination().get_paginated(data=res['data'], request=request)                res['header'] = {**res['header'], **header}            else:                res = Pagination().get_paginated(data=res['data'], request=request)        if not isinstance(res, dict):            res = {'data': None, 'msg': None, 'header': None}        if 'data' not in res:            res['data'] = None        if 'msg' not in res:            res['msg'] = {}        if 'header' not in res:            res['header'] = None        if self.isPasswd:            res['data'] = encrypt(json.dumps(res['data'], cls=DjangoJSONEncoder))        else:            res['data'] = res['data']        logger.info("返回报文:{}".format(res['data']))        return HttpResponse(data=res['data'], headers=res['header'], msg=res['msg'])    #后置处理    def __response__validate(self,outside_self,func,response,request):        if self.isCache:            for cash_save_item in request.cache_save:                RedisCaCheHandler(**request.cash_save_item).run()        logger.info('[%s : %s]Training complete in %lf real seconds' % (outside_self.__class__.__name__, getattr(func, '__name__'), self.end - self.start))        return response    def __call__(self,func):        @wraps(func)        def wrapper(outside_self,request,*args, **kwargs):            try:                self.start = time.time()                kwargs=self.__request_validate(request,**kwargs)                response=self.__run(func,outside_self,request,*args, **kwargs)                self.end=time.time()                return self.__response__validate(outside_self,func,response,request)            except PubErrorCustom as e:                logger.error('[%s : %s  ] : [%s]'%(outside_self.__class__.__name__, getattr(func, '__name__'),e.msg))                return HttpResponse(success=False, msg=e.msg, data=None)            except InnerErrorCustom as e:                logger.error('[%s : %s  ] : [%s]'%(outside_self.__class__.__name__, getattr(func, '__name__'),e.msg))                return HttpResponse(success=False, msg=e.msg, rescode=e.code, data=None)            except Exception as e:                logger.error('[%s : %s  ] : [%s]'%(outside_self.__class__.__name__, getattr(func, '__name__'),str(e)))                return HttpResponse(success=False, msg=str(e), data=None)        return wrapper