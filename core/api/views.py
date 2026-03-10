import os
from django.shortcuts import render
from django.core.files.storage import default_storage
from django.conf import settings
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
    ProfilePhotoUploadSerializer,
    OpenHouseSerializer,
    PerkSerializer,
    NotificationSettingsSerializer,
    ChangePasswordSerializer,
    PromoCodeSerializer,
)
from .models import (
    UserProfile,
    RealtorProfile,
    LenderProfile,
    BrokerProfile,
    PartnerProfile,
    PromoterProfile,
    Property,
    PropertyPhoto,
    OpenHouse,
    Perk,
    NotificationSettings,
    PromoCode,
)


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

    @action(detail=False, methods=['post'])
    def upload_business_card(self, request):
        """Upload business card image for front/back side"""
        try:
            profile = LenderProfile.objects.get(user=request.user)
        except LenderProfile.DoesNotExist:
            profile = LenderProfile.objects.create(user=request.user)

        card_file = request.FILES.get('card')
        side = request.data.get('side')
        if side not in ['front', 'back']:
            return Response({'error': 'side must be either "front" or "back".'}, status=status.HTTP_400_BAD_REQUEST)
        if not card_file:
            return Response({'error': 'card file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if card_file.content_type not in allowed_types:
            return Response({'error': 'Invalid file type.'}, status=status.HTTP_400_BAD_REQUEST)
        if card_file.size > 3 * 1024 * 1024:
            return Response({'error': 'File size exceeds 3MB limit.'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(card_file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            return Response({'error': 'Invalid file extension.'}, status=status.HTTP_400_BAD_REQUEST)

        filename = f'business_cards/{request.user.id}_{request.user.username}_{side}{ext}'
        try:
            path = default_storage.save(filename, card_file)
            card_url = settings.MEDIA_URL + path

            if side == 'front':
                profile.business_card_front = card_url
            else:
                profile.business_card_back = card_url
            profile.save()

            return Response({
                'message': f'Business card {side} uploaded successfully',
                'side': side,
                'card_url': card_url,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to upload business card: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

    @action(detail=False, methods=['post'])
    def upload_business_card(self, request):
        """Upload business card image for front/back side"""
        try:
            profile = PartnerProfile.objects.get(user=request.user)
        except PartnerProfile.DoesNotExist:
            profile = PartnerProfile.objects.create(user=request.user)

        card_file = request.FILES.get('card')
        side = request.data.get('side')
        if side not in ['front', 'back']:
            return Response({'error': 'side must be either "front" or "back".'}, status=status.HTTP_400_BAD_REQUEST)
        if not card_file:
            return Response({'error': 'card file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if card_file.content_type not in allowed_types:
            return Response({'error': 'Invalid file type.'}, status=status.HTTP_400_BAD_REQUEST)
        if card_file.size > 3 * 1024 * 1024:
            return Response({'error': 'File size exceeds 3MB limit.'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(card_file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            return Response({'error': 'Invalid file extension.'}, status=status.HTTP_400_BAD_REQUEST)

        filename = f'business_cards/{request.user.id}_{request.user.username}_{side}{ext}'
        try:
            path = default_storage.save(filename, card_file)
            card_url = settings.MEDIA_URL + path

            if side == 'front':
                profile.business_card_front = card_url
            else:
                profile.business_card_back = card_url
            profile.save()

            return Response({
                'message': f'Business card {side} uploaded successfully',
                'side': side,
                'card_url': card_url,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to upload business card: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

    @action(detail=False, methods=['post'])
    def upload_business_card(self, request):
        """Upload business card image for front/back side"""
        try:
            profile = PromoterProfile.objects.get(user=request.user)
        except PromoterProfile.DoesNotExist:
            profile = PromoterProfile.objects.create(user=request.user)

        card_file = request.FILES.get('card')
        side = request.data.get('side')
        if side not in ['front', 'back']:
            return Response({'error': 'side must be either "front" or "back".'}, status=status.HTTP_400_BAD_REQUEST)
        if not card_file:
            return Response({'error': 'card file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if card_file.content_type not in allowed_types:
            return Response({'error': 'Invalid file type.'}, status=status.HTTP_400_BAD_REQUEST)
        if card_file.size > 3 * 1024 * 1024:
            return Response({'error': 'File size exceeds 3MB limit.'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(card_file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            return Response({'error': 'Invalid file extension.'}, status=status.HTTP_400_BAD_REQUEST)

        filename = f'business_cards/{request.user.id}_{request.user.username}_{side}{ext}'
        try:
            path = default_storage.save(filename, card_file)
            card_url = settings.MEDIA_URL + path

            if side == 'front':
                profile.business_card_front = card_url
            else:
                profile.business_card_back = card_url
            profile.save()

            return Response({
                'message': f'Business card {side} uploaded successfully',
                'side': side,
                'card_url': card_url,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to upload business card: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

import random
import string
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


class OpenHouseViewSet(viewsets.ModelViewSet):
    serializer_class = OpenHouseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OpenHouse.objects.filter(property__realtor=self.request.user).select_related('property')

    def _get_user_property(self, property_id):
        try:
            return Property.objects.get(id=property_id, realtor=self.request.user)
        except Property.DoesNotExist:
            return None

    def create(self, request, *args, **kwargs):
        property_id = request.data.get('property')
        if not property_id:
            return Response({'property': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        property_obj = self._get_user_property(property_id)
        if not property_obj:
            return Response(
                {'error': 'Property not found or you do not have permission.'},
                status=status.HTTP_403_FORBIDDEN
            )

        existing = OpenHouse.objects.filter(property=property_obj).first()
        serializer = self.get_serializer(existing, data=request.data, partial=bool(existing))
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(property=property_obj)

        response_status = status.HTTP_200_OK if existing else status.HTTP_201_CREATED
        return Response(self.get_serializer(instance).data, status=response_status)

    @action(detail=False, methods=['get'], url_path='by_property/(?P<property_id>[^/.]+)')
    def by_property(self, request, property_id=None):
        property_obj = self._get_user_property(property_id)
        if not property_obj:
            return Response(
                {'error': 'Property not found or you do not have permission.'},
                status=status.HTTP_403_FORBIDDEN
            )

        open_house = OpenHouse.objects.filter(property=property_obj).first()
        if not open_house:
            return Response({'property': property_obj.id, 'exists': False}, status=status.HTTP_200_OK)
        return Response(self.get_serializer(open_house).data, status=status.HTTP_200_OK)


class PerkViewSet(viewsets.ModelViewSet):
    serializer_class = PerkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        role = getattr(getattr(self.request.user, 'profile', None), 'role', None)
        if role == 'realtor':
            return Perk.objects.filter(property__realtor=self.request.user).select_related('property')
        if role == 'lender':
            return Perk.objects.select_related('property')
        return Perk.objects.none()

    def _get_property_if_allowed(self, property_id):
        role = getattr(getattr(self.request.user, 'profile', None), 'role', None)
        try:
            if role == 'realtor':
                return Property.objects.get(id=property_id, realtor=self.request.user)
            if role == 'lender':
                return Property.objects.get(id=property_id)
            return None
        except Property.DoesNotExist:
            return None

    def create(self, request, *args, **kwargs):
        property_id = request.data.get('property')
        if not property_id:
            return Response({'property': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        property_obj = self._get_property_if_allowed(property_id)
        if not property_obj:
            return Response(
                {'error': 'Property not found or you do not have permission.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if Perk.objects.filter(property=property_obj).count() >= 5:
            return Response(
                {'error': 'Maximum 5 perks allowed per property.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(property=property_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='by_property/(?P<property_id>[^/.]+)')
    def by_property(self, request, property_id=None):
        property_obj = self._get_property_if_allowed(property_id)
        if not property_obj:
            return Response(
                {'error': 'Property not found or you do not have permission.'},
                status=status.HTTP_403_FORBIDDEN
            )

        perks = Perk.objects.filter(property=property_obj).order_by('-created_at')
        serializer = self.get_serializer(perks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        role = getattr(getattr(request.user, 'profile', None), 'role', None)
        if role == 'lender':
            return Response({'error': 'Lenders cannot delete perks.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class NotificationSettingsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_settings(self, user):
        settings_obj, _ = NotificationSettings.objects.get_or_create(user=user)
        return settings_obj

    @action(detail=False, methods=['get'])
    def me(self, request):
        settings_obj = self._get_settings(request.user)
        serializer = NotificationSettingsSerializer(settings_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch', 'put'])
    def update_settings(self, request):
        settings_obj = self._get_settings(request.user)
        serializer = NotificationSettingsSerializer(settings_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        serializer.save(promoter=self.request.user)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']

        if not request.user.check_password(current_password):
            return Response({'current_password': ['Current password is incorrect.']}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response(
            {'message': 'Password updated successfully.', 'token': token.key},
            status=status.HTTP_200_OK
        )


class PromoCodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Promo Codes for Promoters
    """
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PromoCode.objects.filter(promoter=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(promoter=self.request.user)
