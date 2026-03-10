from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.core.files.storage import default_storage
from django.conf import settings
from .models import (
    UserProfile, RealtorProfile, LenderProfile, BrokerProfile, 
    PartnerProfile, PromoterProfile, Property, PropertyPhoto,
    OpenHouse, Perk, NotificationSettings, PromoCode
)
import os


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('role',)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True, required=True)
    user_role = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2', 'first_name', 'last_name', 'full_name', 'role', 'user_role')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
            'username': {'max_length': 150}
        }

    def get_user_role(self, obj):
        try:
            return obj.profile.role
        except UserProfile.DoesNotExist:
            return None

    def validate_email(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Email cannot be empty.")
        return value

    def validate_first_name(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("First name cannot be empty.")
        return value

    def validate_last_name(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Last name cannot be empty.")
        return value

    def validate_username(self, value):
        if len(value) > 150:
            raise serializers.ValidationError("Username cannot exceed 150 characters.")
        if len(value) > 30:
            raise serializers.ValidationError("Username is too long. Maximum 30 characters allowed.")
        return value

    def validate_password(self, value):
        # Get username from initial data to check similarity
        username = self.initial_data.get('username', '')
        if username and username.lower() in value.lower():
            raise serializers.ValidationError("Password is too similar to the username.")
        return value
    
    def validate_role(self, value):
        valid_roles = [choice[0] for choice in UserProfile.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        role = validated_data.pop('role')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        
        # Create user profile with role
        UserProfile.objects.create(user=user, role=role)
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid username or password.")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Must include username and password.")
        
        return attrs



class RealtorProfileSerializer(serializers.ModelSerializer):
    # Include user basic info
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = RealtorProfile
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'full_name',
            'profile_photo',
            'phone_number_1',
            'phone_number_2',
            'company_name',
            'company_address',
            'address_type',
            'business_website',
            'license_states',
            'serving_states',
            'serving_cities',
            'biography',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'full_name', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        # Update user fields
        user_data = validated_data.pop('user', {})
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            instance.user.last_name = user_data['last_name']
        instance.user.save()
        
        # Update realtor profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class LenderProfileSerializer(serializers.ModelSerializer):
    # Include user basic info
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = LenderProfile
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'full_name',
            'profile_photo',
            'phone_number_1',
            'phone_number_2',
            'company_name',
            'company_address',
            'address_type',
            'business_website',
            'license_nmls',
            'serving_states',
            'serving_cities',
            'biography',
            'business_card_front',
            'business_card_back',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'full_name', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        # Update user fields
        user_data = validated_data.pop('user', {})
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            instance.user.last_name = user_data['last_name']
        instance.user.save()
        
        # Update lender profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class BrokerProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = BrokerProfile
        fields = [
            'id', 'first_name', 'last_name', 'email', 'full_name',
            'profile_photo', 'phone_number_1', 'phone_number_2',
            'company_name', 'company_address', 'address_type', 'business_website',
            'license_number', 'license_states', 'is_international', 'is_nationwide',
            'serving_states', 'serving_cities', 'biography',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'email', 'full_name', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            instance.user.last_name = user_data['last_name']
        instance.user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PartnerProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = PartnerProfile
        fields = [
            'id', 'first_name', 'last_name', 'email', 'full_name',
            'profile_photo', 'phone_number_1', 'phone_number_2',
            'company_name', 'company_address', 'address_type', 'business_website',
            'license_state', 'license_number',
            'serving_states', 'serving_cities', 'biography',
            'business_card_front', 'business_card_back',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'email', 'full_name', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            instance.user.last_name = user_data['last_name']
        instance.user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PromoterProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = PromoterProfile
        fields = [
            'id', 'first_name', 'last_name', 'email', 'full_name',
            'profile_photo', 'phone_number_1', 'phone_number_2',
            'company_name', 'company_address', 'address_type', 'business_website',
            'business_type',
            'serving_states', 'serving_cities', 'biography',
            'business_card_front', 'business_card_back',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'email', 'full_name', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            instance.user.last_name = user_data['last_name']
        instance.user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProfilePhotoUploadSerializer(serializers.Serializer):
    """
    Serializer for handling profile photo uploads with validation
    """
    photo = serializers.ImageField(required=True)
    
    # Configuration
    MAX_FILE_SIZE = 3 * 1024 * 1024  # 3MB
    ALLOWED_CONTENT_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
    
    def validate_photo(self, value):
        """
        Validate the uploaded photo file
        """
        # Validate file size
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f'File size exceeds {self.MAX_FILE_SIZE / (1024 * 1024):.0f}MB limit'
            )
        
        # Validate content type
        if value.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError(
                f'Invalid file type. Allowed types: {", ".join(self.ALLOWED_CONTENT_TYPES)}'
            )
        
        # Validate file extension
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f'Invalid file extension. Allowed extensions: {", ".join(self.ALLOWED_EXTENSIONS)}'
            )
        
        return value
    
    def save_photo(self, user, profile):
        """
        Save the uploaded photo and return the URL
        """
        photo = self.validated_data['photo']
        
        # Generate unique filename
        ext = os.path.splitext(photo.name)[1].lower()
        filename = f'profile_photos/{user.id}_{user.username}{ext}'
        
        # Delete old photo if exists
        if profile.profile_photo:
            old_path = profile.profile_photo.replace(settings.MEDIA_URL, '')
            if default_storage.exists(old_path):
                try:
                    default_storage.delete(old_path)
                except Exception as e:
                    # Log error but don't fail the upload
                    print(f"Warning: Could not delete old photo: {e}")
        
        # Save new photo
        path = default_storage.save(filename, photo)
        photo_url = settings.MEDIA_URL + path
        
        # Update profile
        profile.profile_photo = photo_url
        profile.save()
        
        return photo_url



# Property Photo Serializer
class PropertyPhotoSerializer(serializers.Serializer):
    """Serializer for property photo uploads"""
    photo = serializers.ImageField(required=True)
    order = serializers.IntegerField(required=False, default=0)
    
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_CONTENT_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
    
    def validate_photo(self, value):
        """Validate the uploaded photo file"""
        # Validate file size
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f'File size exceeds {self.MAX_FILE_SIZE / (1024 * 1024):.0f}MB limit'
            )
        
        # Validate content type
        if value.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError(
                f'Invalid file type. Allowed types: {", ".join(self.ALLOWED_CONTENT_TYPES)}'
            )
        
        # Validate file extension
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f'Invalid file extension. Allowed extensions: {", ".join(self.ALLOWED_EXTENSIONS)}'
            )
        
        return value


# Property Serializer
class PropertySerializer(serializers.ModelSerializer):
    realtor_name = serializers.CharField(source='realtor.get_full_name', read_only=True)
    realtor_email = serializers.EmailField(source='realtor.email', read_only=True)
    photos = serializers.SerializerMethodField(read_only=True)
    photo_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Property
        fields = [
            'id',
            'listing_id',
            'realtor',
            'realtor_name',
            'realtor_email',
            'property_type',
            'status',
            'street_address',
            'unit_apt',
            'city',
            'state',
            'zip_code',
            'county',
            'country',
            'bedrooms',
            'bathrooms',
            'garage',
            'sqft',
            'lot_size',
            'year_built',
            'floor_type',
            'kitchen_type',
            'foundation_type',
            'exterior',
            'roof',
            'appliances',
            'price',
            'description',
            'photos',
            'photo_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'listing_id', 'realtor', 'realtor_name', 'realtor_email', 'created_at', 'updated_at']
    
    def get_photos(self, obj):
        photos = PropertyPhoto.objects.filter(property=obj).order_by('order')
        return [{'id': p.id, 'url': p.photo_url, 'order': p.order} for p in photos]
    
    def get_photo_count(self, obj):
        return PropertyPhoto.objects.filter(property=obj).count()


class OpenHouseSerializer(serializers.ModelSerializer):
    property_listing_id = serializers.CharField(source='property.listing_id', read_only=True)
    property_address = serializers.CharField(source='property.street_address', read_only=True)

    class Meta:
        model = OpenHouse
        fields = [
            'id',
            'property',
            'property_listing_id',
            'property_address',
            'is_active',
            'saturday_date',
            'saturday_start_time',
            'saturday_end_time',
            'sunday_date',
            'sunday_start_time',
            'sunday_end_time',
            'virtual_tour_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'property_listing_id', 'property_address']


class PerkSerializer(serializers.ModelSerializer):
    property_listing_id = serializers.CharField(source='property.listing_id', read_only=True)
    property_address = serializers.CharField(source='property.street_address', read_only=True)

    class Meta:
        model = Perk
        fields = [
            'id',
            'property',
            'property_listing_id',
            'property_address',
            'promoter_name',
            'promo_code',
            'description',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'property_listing_id', 'property_address']


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = [
            'id',
            'email_open_house',
            'email_new_perks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': "Password fields didn't match."})
        return attrs

class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = [
            'id', 'promoter', 'code', 'realtor_name', 'realtor_email',
            'description', 'discount_value', 'expiration_date',
            'property_link', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'promoter', 'created_at', 'updated_at']
