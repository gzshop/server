

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import *
from .webapi import *

router = DefaultRouter(trailing_slash=False)
router.register('', FilterAPIView, base_name='filter')

router1 = DefaultRouter(trailing_slash=False)
router1.register('', FilterWebAPIView, base_name='filterweb')

urlpatterns = [
    path('', include(router.urls)),
    path('web/', include(router1.urls))
]