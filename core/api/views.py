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



import random
import string
from .models import Property, PropertyPhoto
from .serializers import PropertySerializer, PropertyPhotoSerializer


def generate_listing_id():
    """Generate a unique 6-character alphanumeric listing ID"""
    while True:
        listing_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Property.objects.filter(listing_id=listing_id).exists():
            return listing_id


class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Realtors can only see their own properties
        if self.action == 'list':
            return Property.objects.filter(realtor=self.request.user)
        return Property.objects.all()
    
    def perform_create(self, serializer):
        # Auto-generate listing ID and set realtor
        serializer.save(
            realtor=self.request.user,
            listing_id=generate_listing_id()
        )
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public_listings(self, request):
        """Get all active properties for public display"""
        properties = Property.objects.filter(status='active').select_related('realtor')
        serializer = self.get_serializer(properties, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def by_listing_id(self, request, pk=None):
        """Get property by listing ID (public access)"""
        try:
            property_obj = Property.objects.get(listing_id=pk)
            serializer = self.get_serializer(property_obj)
            return Response(serializer.data)
        except Property.DoesNotExist:
            return Response({'error': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def upload_photos(self, request, pk=None):
        """Upload photos for a property (max 5 photos)"""
        property_obj = self.get_object()
        
        # Check if user owns this property
        if property_obj.realtor != request.user:
            return Response(
                {'error': 'You do not have permission to upload photos for this property'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check current photo count
        current_count = PropertyPhoto.objects.filter(property=property_obj).count()
        
        # Get uploaded files
        files = request.FILES.getlist('photos')
        
        if not files:
            return Response({'error': 'No photos provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if adding these photos would exceed limit
        if current_count + len(files) > 5:
            return Response(
                {'error': f'Cannot upload {len(files)} photos. Maximum 5 photos allowed. Current: {current_count}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_photos = []
        errors = []
        
        for idx, file in enumerate(files):
            serializer = PropertyPhotoSerializer(data={'photo': file, 'order': current_count + idx})
            
            if not serializer.is_valid():
                errors.append({f'photo_{idx}': serializer.errors})
                continue
            
            try:
                # Generate filename
                ext = os.path.splitext(file.name)[1].lower()
                filename = f'property_photos/{property_obj.listing_id}_{current_count + idx}{ext}'
                
                # Save file
                path = default_storage.save(filename, file)
                photo_url = settings.MEDIA_URL + path
                
                # Create PropertyPhoto record
                photo = PropertyPhoto.objects.create(
                    property=property_obj,
                    photo_url=photo_url,
                    order=current_count + idx
                )
                
                uploaded_photos.append({
                    'id': photo.id,
                    'url': photo.photo_url,
                    'order': photo.order
                })
            except Exception as e:
                errors.append({f'photo_{idx}': str(e)})
        
        response_data = {
            'message': f'Uploaded {len(uploaded_photos)} photo(s)',
            'photos': uploaded_photos
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data, status=status.HTTP_200_OK if uploaded_photos else status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def delete_photo(self, request, pk=None):
        """Delete a specific photo"""
        property_obj = self.get_object()
        
        # Check if user owns this property
        if property_obj.realtor != request.user:
            return Response(
                {'error': 'You do not have permission to delete photos for this property'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        photo_id = request.data.get('photo_id')
        if not photo_id:
            return Response({'error': 'photo_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            photo = PropertyPhoto.objects.get(id=photo_id, property=property_obj)
            
            # Delete file from storage
            photo_path = photo.photo_url.replace(settings.MEDIA_URL, '')
            if default_storage.exists(photo_path):
                default_storage.delete(photo_path)
            
            photo.delete()
            
            return Response({'message': 'Photo deleted successfully'}, status=status.HTTP_200_OK)
        except PropertyPhoto.DoesNotExist:
            return Response({'error': 'Photo not found'}, status=status.HTTP_404_NOT_FOUND)
