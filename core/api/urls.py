from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'signup', views.SignupViewSet, basename='signup')
router.register(r'login', views.LoginViewSet, basename='login')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'realtor-profile', views.RealtorProfileViewSet, basename='realtor-profile')

urlpatterns = [
    path('', include(router.urls)),
]
