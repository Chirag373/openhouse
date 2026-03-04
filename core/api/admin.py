from django.contrib import admin
from .models import UserProfile, RealtorProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at', 'updated_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RealtorProfile)
class RealtorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'phone_number_1', 'created_at', 'updated_at')
    list_filter = ('address_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'company_name', 'serving_cities')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('profile_photo', 'phone_number_1', 'phone_number_2')
        }),
        ('Business Details', {
            'fields': ('company_name', 'company_address', 'address_type', 'business_website', 'license_states')
        }),
        ('Service Area & Bio', {
            'fields': ('serving_states', 'serving_cities', 'biography')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
