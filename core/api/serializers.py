from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import UserProfile, RealtorProfile


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
