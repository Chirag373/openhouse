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
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('lenders/', TemplateView.as_view(template_name='lenders.html'), name='lenders'),
    path('brokers/', TemplateView.as_view(template_name='brokers.html'), name='brokers'),
    path('partners/', TemplateView.as_view(template_name='partners.html'), name='partners'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('signup/', TemplateView.as_view(template_name='signup.html'), name='signup'),
    path('dashboard/realtor/', TemplateView.as_view(template_name='realtor_dashboard.html'), name='realtor_dashboard'),
    path('dashboard/lender/', TemplateView.as_view(template_name='lender_dashboard.html'), name='lender_dashboard'),
    path('dashboard/broker/', TemplateView.as_view(template_name='broker_dashboard.html'), name='broker_dashboard'),
    path('dashboard/partner/', TemplateView.as_view(template_name='partner_dashboard.html'), name='partner_dashboard'),
]
