
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from project.config_include.params import COS_secret_id,COS_secret_key

class CosBase(object):

    def __init__(self):
        secret_id = COS_secret_id
        secret_key  =  COS_secret_key
        region = 'ap-beijing'

        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=None)

        self.client = CosS3Client(config)
        self.bucket = "shop911-1302338678"

    def set(self,stream,filename):
        response = self.client.put_object(
            Bucket=self.bucket,
            Body=stream,
            Key=filename
        )
        return self.createUrl(filename)

    def createUrl(self,filename):
        return "https://shop911-1302338678.cos.ap-beijing.myqcloud.com/{}".format(filename)