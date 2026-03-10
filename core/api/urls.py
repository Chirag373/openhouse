from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'signup', views.SignupViewSet, basename='signup')
router.register(r'login', views.LoginViewSet, basename='login')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'realtor-profile', views.RealtorProfileViewSet, basename='realtor-profile')
router.register(r'lender-profile', views.LenderProfileViewSet, basename='lender-profile')
router.register(r'broker-profile', views.BrokerProfileViewSet, basename='broker-profile')
router.register(r'partner-profile', views.PartnerProfileViewSet, basename='partner-profile')
router.register(r'promoter-profile', views.PromoterProfileViewSet, basename='promoter-profile')
router.register(r'properties', views.PropertyViewSet, basename='property')
router.register(r'open-houses', views.OpenHouseViewSet, basename='open-house')
router.register(r'perks', views.PerkViewSet, basename='perk')
router.register(r'notification-settings', views.NotificationSettingsViewSet, basename='notification-settings')

urlpatterns = [
    path('', include(router.urls)),
]
