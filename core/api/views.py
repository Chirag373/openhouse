from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .serializers import (
    UserSerializer,
    LoginSerializer,
    RealtorProfileSerializer,
    LenderProfileSerializer,
    BrokerProfileSerializer,
    PartnerProfileSerializer,
    PromoterProfileSerializer,
    ProfilePhotoUploadSerializer
)
from .models import UserProfile, RealtorProfile, LenderProfile, BrokerProfile, PartnerProfile, PromoterProfile


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

        # Use serializer for validation and processing
        serializer = ProfilePhotoUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Save photo using serializer
            photo_url = serializer.save_photo(request.user, profile)

            return Response({
                'message': 'Photo uploaded successfully',
                'photo_url': photo_url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Failed to save photo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
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


class LenderProfileViewSet(viewsets.ModelViewSet):
    serializer_class = LenderProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LenderProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's lender profile"""
        try:
            profile = LenderProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except LenderProfile.DoesNotExist:
            profile = LenderProfile.objects.create(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def upload_photo(self, request):
        """Upload profile photo"""
        try:
            profile = LenderProfile.objects.get(user=request.user)
        except LenderProfile.DoesNotExist:
            profile = LenderProfile.objects.create(user=request.user)

        serializer = ProfilePhotoUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            photo_url = serializer.save_photo(request.user, profile)
            return Response({
                'message': 'Photo uploaded successfully',
                'photo_url': photo_url
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Failed to save photo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user's lender profile"""
        try:
            profile = LenderProfile.objects.get(user=request.user)
        except LenderProfile.DoesNotExist:
            profile = LenderProfile.objects.create(user=request.user)
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BrokerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = BrokerProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BrokerProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            profile = BrokerProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except BrokerProfile.DoesNotExist:
            profile = BrokerProfile.objects.create(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def upload_photo(self, request):
        try:
            profile = BrokerProfile.objects.get(user=request.user)
        except BrokerProfile.DoesNotExist:
            profile = BrokerProfile.objects.create(user=request.user)
        serializer = ProfilePhotoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            photo_url = serializer.save_photo(request.user, profile)
            return Response({'message': 'Photo uploaded successfully', 'photo_url': photo_url})
        except Exception as e:
            return Response({'error': f'Failed to save photo: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        try:
            profile = BrokerProfile.objects.get(user=request.user)
        except BrokerProfile.DoesNotExist:
            profile = BrokerProfile.objects.create(user=request.user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PartnerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = PartnerProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PartnerProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            profile = PartnerProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except PartnerProfile.DoesNotExist:
            profile = PartnerProfile.objects.create(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def upload_photo(self, request):
        try:
            profile = PartnerProfile.objects.get(user=request.user)
        except PartnerProfile.DoesNotExist:
            profile = PartnerProfile.objects.create(user=request.user)
        serializer = ProfilePhotoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            photo_url = serializer.save_photo(request.user, profile)
            return Response({'message': 'Photo uploaded successfully', 'photo_url': photo_url})
        except Exception as e:
            return Response({'error': f'Failed to save photo: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        try:
            profile = PartnerProfile.objects.get(user=request.user)
        except PartnerProfile.DoesNotExist:
            profile = PartnerProfile.objects.create(user=request.user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PromoterProfileViewSet(viewsets.ModelViewSet):
    serializer_class = PromoterProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PromoterProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            profile = PromoterProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except PromoterProfile.DoesNotExist:
            profile = PromoterProfile.objects.create(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def upload_photo(self, request):
        try:
            profile = PromoterProfile.objects.get(user=request.user)
        except PromoterProfile.DoesNotExist:
            profile = PromoterProfile.objects.create(user=request.user)
        serializer = ProfilePhotoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            photo_url = serializer.save_photo(request.user, profile)
            return Response({'message': 'Photo uploaded successfully', 'photo_url': photo_url})
        except Exception as e:
            return Response({'error': f'Failed to save photo: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        try:
            profile = PromoterProfile.objects.get(user=request.user)
        except PromoterProfile.DoesNotExist:
            profile = PromoterProfile.objects.create(user=request.user)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)