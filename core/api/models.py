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
