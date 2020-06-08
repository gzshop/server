
from rest_framework import serializers
from app.public.models import Sysparams

class SysparamsModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sysparams
        fields = '__all__'