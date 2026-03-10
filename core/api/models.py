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


# Property Model
class Property(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ('single_family', 'Single Family'),
        ('condo', 'Condo'),
        ('townhouse', 'Townhouse'),
        ('multi_family', 'Multi Family'),
        ('land', 'Land'),
        ('commercial', 'Commercial'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('sold', 'Sold'),
        ('off_market', 'Off Market'),
    ]
    
    # Unique listing ID (6 characters alphanumeric)
    listing_id = models.CharField(max_length=6, unique=True, db_index=True)
    
    # Owner/Realtor
    realtor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    
    # Basic Info
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='single_family')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Address
    street_address = models.CharField(max_length=255)
    unit_apt = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    county = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='USA')
    
    # Property Details
    bedrooms = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    garage = models.IntegerField(default=0)
    sqft = models.IntegerField(null=True, blank=True)
    lot_size = models.CharField(max_length=50, blank=True)
    year_built = models.IntegerField(null=True, blank=True)
    
    # Features
    floor_type = models.CharField(max_length=100, blank=True)
    kitchen_type = models.CharField(max_length=100, blank=True)
    foundation_type = models.CharField(max_length=100, blank=True)
    exterior = models.CharField(max_length=100, blank=True)
    roof = models.CharField(max_length=100, blank=True)
    appliances = models.TextField(blank=True, help_text='Comma separated list')
    
    # Pricing
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Description
    description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.listing_id} - {self.street_address}, {self.city}"
    
    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']


# Property Photo Model (Max 5 photos per property)
class PropertyPhoto(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='photos')
    photo_url = models.CharField(max_length=500)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Photo {self.order} for {self.property.listing_id}"
    
    class Meta:
        verbose_name = 'Property Photo'
        verbose_name_plural = 'Property Photos'
        ordering = ['order']


# Open House Model - Schedule for property open houses
class OpenHouse(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='open_houses')
    is_active = models.BooleanField(default=True, help_text='Whether open house is currently running')
    
    # Saturday schedule
    saturday_date = models.DateField(null=True, blank=True)
    saturday_start_time = models.TimeField(null=True, blank=True)
    saturday_end_time = models.TimeField(null=True, blank=True)
    
    # Sunday schedule
    sunday_date = models.DateField(null=True, blank=True)
    sunday_start_time = models.TimeField(null=True, blank=True)
    sunday_end_time = models.TimeField(null=True, blank=True)
    
    # Virtual tour link
    virtual_tour_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Open House for {self.property.listing_id}"
    
    class Meta:
        verbose_name = 'Open House'
        verbose_name_plural = 'Open Houses'
        ordering = ['-created_at']


# Perk Model - Promotions/discounts tied to properties (max 5 per property)
class Perk(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='perks')
    promoter_name = models.CharField(max_length=255, help_text='Name of the promoter/company')
    promo_code = models.CharField(max_length=50, help_text='Promotional code')
    description = models.TextField(help_text='Description of the perk')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.promo_code} - {self.promoter_name} for {self.property.listing_id}"
    
    class Meta:
        verbose_name = 'Perk'
        verbose_name_plural = 'Perks'
        ordering = ['-created_at']


# Notification Settings Model
class NotificationSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    email_open_house = models.BooleanField(default=True, help_text='Email when an Open House is upcoming')
    email_new_perks = models.BooleanField(default=False, help_text='Email about new Perk providers')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification Settings for {self.user.username}"
    
    class Meta:
        verbose_name = 'Notification Settings'
        verbose_name_plural = 'Notification Settings'
