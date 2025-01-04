from django.urls import path, include
from .views import CustomAuthToken
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', CustomAuthToken.as_view(), name='token_login'),
    path('auth/token/logout/', CustomAuthToken.as_view(), name='token_logout'),
]
