

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import *

router = DefaultRouter(trailing_slash=False)
router.register('', GoodsAPIView, base_name='goods')

urlpatterns = [
    path('', include(router.urls))
]