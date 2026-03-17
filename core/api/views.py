import json
import os
from datetime import datetime, timezone as dt_timezone

import stripe
from django.db import transaction
from django.shortcuts import render
from django.core.files.storage import default_storage
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .serializers import (
    UserSerializer,
    PaidSignupSerializer,
    LoginSerializer,
    RealtorProfileSerializer,
    LenderProfileSerializer,
    BrokerProfileSerializer,
    PartnerProfileSerializer,
    PartnerServiceSerializer,
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
    PartnerService,
    PromoterProfile,
    Property,
    PropertyPhoto,
    OpenHouse,
    Perk,
    NotificationSettings,
    PromoCode,
    PendingSignup,
    UserSubscription,
)


PLAN_CONFIG = {
    'starter': {'amount': 0, 'label': 'Starter'},
    'growth': {'amount': 4900, 'label': 'Growth'},
    'premium': {'amount': 9900, 'label': 'Premium'},
}


def _configure_stripe():
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError('Stripe is not configured. Set STRIPE_SECRET_KEY.')
    stripe.api_key = settings.STRIPE_SECRET_KEY


def _build_user_payload(user):
    try:
        user_role = user.profile.role
    except UserProfile.DoesNotExist:
        user_role = None

    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
        'role': user_role,
    }


def _get_dashboard_path(role):
    return f'/dashboard/{role}/' if role else '/'


def _finalize_pending_signup(pending_signup, session_payload=None):
    if pending_signup.status == 'completed' and pending_signup.user_id:
        user = pending_signup.user
        token, _ = Token.objects.get_or_create(user=user)
        return user, token, False

    with transaction.atomic():
        pending_signup = PendingSignup.objects.select_for_update().get(pk=pending_signup.pk)

        if pending_signup.status == 'completed' and pending_signup.user_id:
            user = pending_signup.user
            token, _ = Token.objects.get_or_create(user=user)
            return user, token, False

        if pending_signup.status not in ['pending', 'cancelled']:
            raise ValueError(f'Pending signup is not payable in its current state: {pending_signup.status}')

        if User.objects.filter(username__iexact=pending_signup.username).exists():
            pending_signup.status = 'failed'
            pending_signup.failure_reason = 'Username is no longer available.'
            pending_signup.save(update_fields=['status', 'failure_reason', 'updated_at'])
            raise ValueError(pending_signup.failure_reason)

        if User.objects.filter(email__iexact=pending_signup.email).exists():
            pending_signup.status = 'failed'
            pending_signup.failure_reason = 'Email is already associated with another account.'
            pending_signup.save(update_fields=['status', 'failure_reason', 'updated_at'])
            raise ValueError(pending_signup.failure_reason)

        user = User(
            username=pending_signup.username,
            email=pending_signup.email,
            first_name=pending_signup.first_name,
            last_name=pending_signup.last_name,
            password=pending_signup.password_hash,
        )
        user.save()
        UserProfile.objects.create(user=user, role=pending_signup.role)
        token, _ = Token.objects.get_or_create(user=user)

        session_payload = session_payload or {}
        stripe_customer_id = (
            session_payload.get('customer')
            or pending_signup.stripe_customer_id
            or ''
        )
        stripe_subscription_id = (
            session_payload.get('subscription')
            or pending_signup.stripe_subscription_id
            or None
        )
        current_period_end = None
        subscription_obj = session_payload.get('subscription_object')
        if subscription_obj and subscription_obj.get('current_period_end'):
            current_period_end = datetime.fromtimestamp(
                subscription_obj['current_period_end'],
                tz=dt_timezone.utc,
            )

        UserSubscription.objects.update_or_create(
            user=user,
            defaults={
                'plan': pending_signup.plan,
                'status': 'active',
                'stripe_customer_id': stripe_customer_id,
                'stripe_subscription_id': stripe_subscription_id,
                'stripe_checkout_session_id': pending_signup.stripe_checkout_session_id or '',
                'current_period_end': current_period_end,
            },
        )

        pending_signup.user = user
        pending_signup.status = 'completed'
        pending_signup.completed_at = timezone.now()
        pending_signup.failure_reason = ''
        if stripe_customer_id:
            pending_signup.stripe_customer_id = stripe_customer_id
        if stripe_subscription_id:
            pending_signup.stripe_subscription_id = stripe_subscription_id
        pending_signup.save()
        return user, token, True


class SignupViewSet(viewsets.ViewSet):
    """
    ViewSet for user signup/registration
    """
    permission_classes = [AllowAny]
    
    def create(self, request):
        if request.data.get('plan', 'starter') != 'starter':
            return Response(
                {'plan': ['Paid plans must use checkout before account creation.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': _build_user_payload(user),
                'token': token.key,
                'message': 'User created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='create-checkout-session')
    def create_checkout_session(self, request):
        serializer = PaidSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = serializer.validated_data['plan']
        if plan not in ['growth', 'premium']:
            return Response(
                {'plan': ['Only paid plans use Stripe checkout.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            _configure_stripe()
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        pending_signup = PendingSignup.objects.create(**serializer.build_pending_signup_data())
        success_url = request.build_absolute_uri(
            f'/signup/success/?session_id={{CHECKOUT_SESSION_ID}}&pending_signup={pending_signup.id}'
        )
        cancel_url = request.build_absolute_uri(f'/signup/cancel/?pending_signup={pending_signup.id}')

        try:
            checkout_session = stripe.checkout.Session.create(
                mode='subscription',
                customer_email=pending_signup.email,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f"{PLAN_CONFIG[plan]['label']} Plan",
                            'description': f"{PLAN_CONFIG[plan]['label']} membership for OpenHouse",
                        },
                        'unit_amount': PLAN_CONFIG[plan]['amount'],
                        'recurring': {'interval': 'month'},
                    },
                    'quantity': 1,
                }],
                metadata={
                    'pending_signup_id': str(pending_signup.id),
                    'plan': pending_signup.plan,
                    'role': pending_signup.role,
                },
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except Exception as exc:
            pending_signup.status = 'failed'
            pending_signup.failure_reason = str(exc)
            pending_signup.save(update_fields=['status', 'failure_reason', 'updated_at'])
            return Response(
                {'error': 'Unable to start checkout right now. Please try again.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        pending_signup.stripe_checkout_session_id = checkout_session.id
        pending_signup.save(update_fields=['stripe_checkout_session_id', 'updated_at'])
        return Response({'checkout_url': checkout_session.url}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='checkout-status')
    def checkout_status(self, request):
        session_id = request.query_params.get('session_id')
        pending_signup_id = request.query_params.get('pending_signup')
        pending_signup = None

        if pending_signup_id:
            pending_signup = PendingSignup.objects.filter(pk=pending_signup_id).select_related('user').first()

        if session_id == '{CHECKOUT_SESSION_ID}':
            session_id = None

        if not session_id and pending_signup:
            session_id = pending_signup.stripe_checkout_session_id

        if not session_id:
            return Response({'error': 'session_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            _configure_stripe()
            session = stripe.checkout.Session.retrieve(session_id, expand=['subscription'])
        except Exception:
            return Response({'error': 'Unable to verify checkout session.'}, status=status.HTTP_400_BAD_REQUEST)

        if not pending_signup:
            pending_signup = PendingSignup.objects.filter(stripe_checkout_session_id=session_id).select_related('user').first()
        if not pending_signup:
            return Response({'status': 'not_found'}, status=status.HTTP_404_NOT_FOUND)

        if pending_signup.status == 'completed' and pending_signup.user_id:
            token, _ = Token.objects.get_or_create(user=pending_signup.user)
            return Response({
                'status': 'completed',
                'token': token.key,
                'user': _build_user_payload(pending_signup.user),
                'redirect_url': _get_dashboard_path(pending_signup.role),
            }, status=status.HTTP_200_OK)

        if session.get('status') == 'expired':
            pending_signup.status = 'expired'
            pending_signup.save(update_fields=['status', 'updated_at'])
            return Response({'status': 'expired'}, status=status.HTTP_200_OK)

        if session.get('payment_status') in ['paid', 'no_payment_required'] and session.get('status') == 'complete':
            payload = {
                'customer': session.get('customer'),
                'subscription': session.get('subscription').get('id') if isinstance(session.get('subscription'), dict) else session.get('subscription'),
                'subscription_object': session.get('subscription') if isinstance(session.get('subscription'), dict) else None,
            }
            try:
                user, token, _ = _finalize_pending_signup(pending_signup, payload)
            except ValueError as exc:
                return Response({'status': 'failed', 'error': str(exc)}, status=status.HTTP_409_CONFLICT)

            return Response({
                'status': 'completed',
                'token': token.key,
                'user': _build_user_payload(user),
                'redirect_url': _get_dashboard_path(user.profile.role),
            }, status=status.HTTP_200_OK)

        return Response({'status': pending_signup.status}, status=status.HTTP_200_OK)


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


class PartnerServiceViewSet(viewsets.ModelViewSet):
    serializer_class = PartnerServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            partner = PartnerProfile.objects.get(user=self.request.user)
            return PartnerService.objects.filter(partner=partner)
        except PartnerProfile.DoesNotExist:
            return PartnerService.objects.none()

    def perform_create(self, serializer):
        partner, _ = PartnerProfile.objects.get_or_create(user=self.request.user)
        serializer.save(partner=partner)


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


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return Response({'error': 'Stripe webhook is not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    payload = request.body
    signature = request.META.get('HTTP_STRIPE_SIGNATURE')
    if not signature:
        return Response({'error': 'Missing Stripe signature.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        return Response({'error': 'Invalid payload.'}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError:
        return Response({'error': 'Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        pending_signup_id = session.get('metadata', {}).get('pending_signup_id')
        pending_signup = PendingSignup.objects.filter(pk=pending_signup_id).select_related('user').first()
        if pending_signup:
            subscription_data = None
            subscription_id = session.get('subscription')
            if subscription_id:
                try:
                    _configure_stripe()
                    subscription_data = stripe.Subscription.retrieve(subscription_id)
                except Exception:
                    subscription_data = None
            payload_data = {
                'customer': session.get('customer'),
                'subscription': subscription_id,
                'subscription_object': subscription_data,
            }
            try:
                _finalize_pending_signup(pending_signup, payload_data)
            except ValueError:
                pass

    return Response({'received': True}, status=status.HTTP_200_OK)


def signup_success(request):
    session_id = request.GET.get('session_id')
    pending_signup_id = request.GET.get('pending_signup')
    if session_id == '{CHECKOUT_SESSION_ID}':
        session_id = ''

    if not session_id and not pending_signup_id:
        return HttpResponseBadRequest('Missing session_id.')

    return render(request, 'signup_success.html', {
        'session_id': session_id,
        'pending_signup_id': pending_signup_id or '',
    })


def signup_cancel(request):
    pending_signup_id = request.GET.get('pending_signup')
    if pending_signup_id:
        pending_signup = PendingSignup.objects.filter(pk=pending_signup_id, status='pending').first()
        if pending_signup:
            pending_signup.status = 'cancelled'
            pending_signup.save(update_fields=['status', 'updated_at'])

    return render(request, 'signup_cancel.html')
