"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from api import views as api_views
from api.models import LenderProfile, PromoterProfile, PartnerProfile, BrokerProfile

class LendersView(TemplateView):
    template_name = 'lenders.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lender_profiles'] = LenderProfile.objects.all().order_by('-created_at')
        return context

class PromotersView(TemplateView):
    template_name = 'promoters.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['promoter_profiles'] = PromoterProfile.objects.all().order_by('-created_at')
        return context

class PartnersView(TemplateView):
    template_name = 'partners.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partner_profiles'] = PartnerProfile.objects.all().order_by('-created_at')
        return context

class BrokersView(TemplateView):
    template_name = 'brokers.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Prefetch properties where realtor (which is User) is the broker's user
        context['broker_profiles'] = BrokerProfile.objects.all().prefetch_related('user__properties').order_by('-created_at')
        return context

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('lenders/', LendersView.as_view(), name='lenders'),
    path('brokers/', BrokersView.as_view(), name='brokers'),
    path('partners/', PartnersView.as_view(), name='partners'),
    path('promoters/', PromotersView.as_view(), name='promoters'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('signup/', TemplateView.as_view(template_name='signup.html'), name='signup'),
    path('signup/success/', api_views.signup_success, name='signup_success'),
    path('signup/cancel/', api_views.signup_cancel, name='signup_cancel'),
    path('dashboard/realtor/', TemplateView.as_view(template_name='realtor_dashboard.html'), name='realtor_dashboard'),
    path('dashboard/lender/', TemplateView.as_view(template_name='lender_dashboard.html'), name='lender_dashboard'),
    path('dashboard/broker/', TemplateView.as_view(template_name='broker_dashboard.html'), name='broker_dashboard'),
    path('dashboard/partner/', TemplateView.as_view(template_name='partner_dashboard.html'), name='partner_dashboard'),
    path('dashboard/promoter/', TemplateView.as_view(template_name='promoter_dashboard.html'), name='promoter_dashboard'),
    path('property/<str:listing_id>/', TemplateView.as_view(template_name='property_detail.html'), name='property_detail'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
