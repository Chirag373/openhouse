from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .serializers import UserSerializer, LoginSerializer, RealtorProfileSerializer
from .models import UserProfile, RealtorProfile
from django.core.files.storage import default_storage
from django.conf import settings
import os


class SignupViewSet(viewsets.ViewSet):
    """
    ViewSet for user signup/registration
    """
    permission_classes = [AllowAny]
    
    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            # Get user role
            user_role = None
            try:
                user_role = user.profile.role
            except UserProfile.DoesNotExist:
                pass
            
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.get_full_name(),
                    'role': user_role
                },
                'token': token.key,
                'message': 'User created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginViewSet(viewsets.ViewSet):
    """
    ViewSet for user login/authentication
    """
    permission_classes = [AllowAny]
    
    def create(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            
            # Get user role
            user_role = None
            try:
                user_role = user.profile.role
            except UserProfile.DoesNotExist:
                pass
            
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.get_full_name(),
                    'role': user_role
                },
                'token': token.key,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management (CRUD operations)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]



class RealtorProfileViewSet(viewsets.ModelViewSet):
    serializer_class = RealtorProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can only access their own profile
        return RealtorProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's realtor profile"""
        try:
            profile = RealtorProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except RealtorProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = RealtorProfile.objects.create(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def upload_photo(self, request):
        """Upload profile photo"""
        try:
            profile = RealtorProfile.objects.get(user=request.user)
        except RealtorProfile.DoesNotExist:
            profile = RealtorProfile.objects.create(user=request.user)
        
        if 'photo' not in request.FILES:
            return Response(
                {'error': 'No photo file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        photo = request.FILES['photo']
        
        # Validate file size (max 3MB)
        if photo.size > 3 * 1024 * 1024:
            return Response(
                {'error': 'File size exceeds 3MB limit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if photo.content_type not in allowed_types:
            return Response(
                {'error': 'Invalid file type. Allowed: JPEG, JPG, PNG, WEBP'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create unique filename
        ext = os.path.splitext(photo.name)[1]
        filename = f'profile_photos/{request.user.id}_{request.user.username}{ext}'
        
        # Delete old photo if exists
        if profile.profile_photo:
            old_path = profile.profile_photo.replace(settings.MEDIA_URL, '')
            if default_storage.exists(old_path):
                default_storage.delete(old_path)
        
        # Save new photo
        path = default_storage.save(filename, photo)
        profile.profile_photo = settings.MEDIA_URL + path
        profile.save()
        
        return Response({
            'message': 'Photo uploaded successfully',
            'photo_url': profile.profile_photo
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user's realtor profile"""
        try:
            profile = RealtorProfile.objects.get(user=request.user)
        except RealtorProfile.DoesNotExist:
            profile = RealtorProfile.objects.create(user=request.user)
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)