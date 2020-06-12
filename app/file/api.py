
import os,uuid

import base64
from rest_framework import viewsets
from lib.core.decorator.response import Core_connector
from project.settings import IMAGE_PATH
from project.config_include.common import ServerUrl
from lib.utils.mytime import UtilTime
from lib.utils.exceptions import PubErrorCustom
from rest_framework.decorators import list_route
from lib.utils.txCos import CosBase

class FileAPIView(viewsets.ViewSet):

    @list_route(methods=['POST','OPTIONS'])
    @Core_connector()
    def upload(self,request, *args, **kwargs):

        file_obj = request.FILES.get('file')
        img_type = file_obj.name.split('.')[1]
        img_type = img_type.lower()

        new_file = "{}_{}".format(uuid.uuid4().hex, file_obj.name)
        file_strem = file_obj.read()

        url = CosBase().set(file_strem, new_file)

        return {"data": {
            "path": url,
            "name": new_file
        }}


    @list_route(methods=['POST','OPTIONS'])
    @Core_connector(isPasswd=True, isTicket=True)
    def upload_bin(self,request):

        file=request.data_format['file'].split("data:image/png;base64,")[1]

        timestr = UtilTime().arrow_to_string(format_v="YYYYMMDD")
        path=os.path.join(IMAGE_PATH, '{}'.format(timestr))

        name = UtilTime().arrow_to_string(format_v="YYYYMMDDHHmmss")+".jpg"

        if os.path.exists(os.path.join(path, name)):
            c = 0
            while True:
                if len(name.split('images_teshudaima_images')) > 1:
                    name = name.split('images_teshudaima_images')[1]
                name = "copy{}images_teshudaima_images{}".format(c, name)
                c = c + 1
                if not os.path.exists(os.path.join(path, name.replace("images_teshudaima_images", "_"))):
                    name = name.replace("images_teshudaima_images", "_")
                    break

        if not os.path.exists(path):
            os.makedirs(path)

        with open(os.path.join(path, name), 'wb') as f:
            f.write(base64.b64decode(file))

        return {"data": {
            "path": "{}/statics/images/{}/{}".format(ServerUrl, timestr, name)
        }}
