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


# Abstract Base Profile with common fields shared across all role profiles
class BaseProfile(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('actual', 'Actual Address'),
        ('po_box', 'PO Box'),
    ]
    
    # Personal Information
    profile_photo = models.CharField(max_length=500, blank=True, help_text='URL or path to profile photo')
    phone_number_1 = models.CharField(max_length=20, blank=True)
    phone_number_2 = models.CharField(max_length=20, blank=True)
    
    # Business Details
    company_name = models.CharField(max_length=255, blank=True)
    company_address = models.TextField(blank=True)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='actual')
    business_website = models.URLField(blank=True)
    
    # Service Area & Bio
    serving_states = models.CharField(max_length=255, blank=True, help_text='Comma separated state codes')
    serving_cities = models.TextField(blank=True, help_text='Comma separated city names')
    biography = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


# Realtor Profile Model
class RealtorProfile(BaseProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='realtor_profile')
    
    # Realtor-specific fields
    license_states = models.CharField(max_length=255, blank=True, help_text='Comma separated state codes')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Realtor Profile"
    
    class Meta:
        verbose_name = 'Realtor Profile'
        verbose_name_plural = 'Realtor Profiles'


# Lender Profile Model
class LenderProfile(BaseProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lender_profile')
    
    # Lender-specific fields
    license_nmls = models.CharField(max_length=50, blank=True, help_text='NMLS license number')
    business_card_front = models.CharField(max_length=500, blank=True, help_text='URL or path to front of business card')
    business_card_back = models.CharField(max_length=500, blank=True, help_text='URL or path to back of business card')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Lender Profile"
    
    class Meta:
        verbose_name = 'Lender Profile'
        verbose_name_plural = 'Lender Profiles'


# Broker Profile Model
class BrokerProfile(BaseProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='broker_profile')
    
    # Broker-specific fields
    license_number = models.CharField(max_length=100, blank=True, help_text='Broker license number')
    license_states = models.CharField(max_length=255, blank=True, help_text='Comma separated state codes')
    is_international = models.BooleanField(default=False)
    is_nationwide = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Broker Profile"
    
    class Meta:
        verbose_name = 'Broker Profile'
        verbose_name_plural = 'Broker Profiles'


# Partner Profile Model
class PartnerProfile(BaseProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='partner_profile')
    
    # Partner-specific fields
    license_state = models.CharField(max_length=10, blank=True, help_text='2-letter state code')
    license_number = models.CharField(max_length=100, blank=True)
    business_card_front = models.CharField(max_length=500, blank=True, help_text='URL or path to front of business card')
    business_card_back = models.CharField(max_length=500, blank=True, help_text='URL or path to back of business card')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Partner Profile"
    
    class Meta:
        verbose_name = 'Partner Profile'
        verbose_name_plural = 'Partner Profiles'


# Promoter Profile Model
class PromoterProfile(BaseProfile):
    BUSINESS_TYPE_CHOICES = [
        ('photography', 'Photography'),
        ('marketing_agency', 'Marketing Agency'),
        ('social_media', 'Social Media Management'),
        ('videography', 'Videography'),
        ('staging', 'Staging Services'),
        ('virtual_tour', 'Virtual Tour Provider'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='promoter_profile')
    
    # Promoter-specific fields
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPE_CHOICES, blank=True)
    business_card_front = models.CharField(max_length=500, blank=True, help_text='URL or path to front of business card')
    business_card_back = models.CharField(max_length=500, blank=True, help_text='URL or path to back of business card')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Promoter Profile"
    
    class Meta:
        verbose_name = 'Promoter Profile'
        verbose_name_plural = 'Promoter Profiles'

