from django.db import models
from django.contrib.auth.models import User

# User Profile Model to store additional user information
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('realtor', 'Realtor'),
        ('lender', 'Lender'),
        ('broker', 'Broker'),
        ('partner', 'Partner'),
        ('promoter', 'Promoter'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


# Realtor Profile Model
class RealtorProfile(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('actual', 'Actual Address'),
        ('po_box', 'PO Box'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='realtor_profile')
    
    # Personal Information
    profile_photo = models.CharField(max_length=500, blank=True, help_text='URL or path to profile photo')
    phone_number_1 = models.CharField(max_length=20, blank=True)
    phone_number_2 = models.CharField(max_length=20, blank=True)
    
    # Business Details
    company_name = models.CharField(max_length=255, blank=True)
    company_address = models.TextField(blank=True)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='actual')
    business_website = models.URLField(blank=True)
    license_states = models.CharField(max_length=255, blank=True, help_text='Comma separated state codes')
    
    # Service Area & Bio
    serving_states = models.CharField(max_length=255, blank=True, help_text='Comma separated state codes')
    serving_cities = models.TextField(blank=True, help_text='Comma separated city names')
    biography = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Realtor Profile"
    
    class Meta:
        verbose_name = 'Realtor Profile'
        verbose_name_plural = 'Realtor Profiles'
