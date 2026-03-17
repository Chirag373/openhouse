from unittest.mock import patch

from django.test import override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import PendingSignup, UserProfile, UserSubscription


class RealtorDashboardFlowTests(APITestCase):
    def setUp(self):
        self.password = 'OldPass123!'
        self.user = User.objects.create_user(
            username='realtor1',
            email='realtor1@example.com',
            password=self.password,
            first_name='Real',
            last_name='Tor'
        )
        UserProfile.objects.create(user=self.user, role='realtor')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        property_payload = {
            'property_type': 'single_family',
            'status': 'active',
            'street_address': '123 Main Street',
            'city': 'Allen',
            'state': 'TX',
            'zip_code': '75002',
        }
        response = self.client.post('/api/properties/', property_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.property_id = response.data['id']

    def test_open_house_create_and_fetch_by_property(self):
        payload = {
            'property': self.property_id,
            'is_active': True,
            'saturday_date': '2026-03-14',
            'saturday_start_time': '10:00:00',
            'saturday_end_time': '14:00:00',
            'sunday_date': '2026-03-15',
            'sunday_start_time': '11:00:00',
            'sunday_end_time': '15:00:00',
            'virtual_tour_url': 'https://example.com/tour',
        }
        create_response = self.client.post('/api/open-houses/', payload, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        fetch_response = self.client.get(f'/api/open-houses/by_property/{self.property_id}/')
        self.assertEqual(fetch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(fetch_response.data['property'], self.property_id)
        self.assertEqual(fetch_response.data['virtual_tour_url'], payload['virtual_tour_url'])

    def test_perks_flow_with_limit_and_delete(self):
        for i in range(5):
            perk_response = self.client.post('/api/perks/', {
                'property': self.property_id,
                'promoter_name': f'Promoter {i}',
                'promo_code': f'CODE{i}',
                'description': f'Description {i}',
                'is_active': True,
            }, format='json')
            self.assertEqual(perk_response.status_code, status.HTTP_201_CREATED)

        limit_response = self.client.post('/api/perks/', {
            'property': self.property_id,
            'promoter_name': 'Overflow',
            'promo_code': 'OVER6',
            'description': 'Should fail',
            'is_active': True,
        }, format='json')
        self.assertEqual(limit_response.status_code, status.HTTP_400_BAD_REQUEST)

        list_response = self.client.get(f'/api/perks/by_property/{self.property_id}/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 5)

        perk_id = list_response.data[0]['id']
        delete_response = self.client.delete(f'/api/perks/{perk_id}/')
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        list_after_delete = self.client.get(f'/api/perks/by_property/{self.property_id}/')
        self.assertEqual(len(list_after_delete.data), 4)

    def test_settings_notifications_and_password_change_end_to_end(self):
        me_response = self.client.get('/api/notification-settings/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertTrue(me_response.data['email_open_house'])
        self.assertFalse(me_response.data['email_new_perks'])

        update_response = self.client.patch('/api/notification-settings/update_settings/', {
            'email_open_house': False,
            'email_new_perks': True,
        }, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertFalse(update_response.data['email_open_house'])
        self.assertTrue(update_response.data['email_new_perks'])

        new_password = 'NewPass123!'
        change_password_response = self.client.post('/api/notification-settings/change_password/', {
            'current_password': self.password,
            'new_password': new_password,
            'confirm_password': new_password,
        }, format='json')
        self.assertEqual(change_password_response.status_code, status.HTTP_200_OK)
        self.assertIn('token', change_password_response.data)

        self.client.credentials()
        login_response = self.client.post('/api/login/', {
            'username': self.user.username,
            'password': new_password,
        }, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)


class LenderDashboardFlowTests(APITestCase):
    def setUp(self):
        self.password = 'LenderPass123!'
        self.realtor = User.objects.create_user(
            username='realtor_for_lender',
            email='realtor@example.com',
            password='RealtorPass123!',
            first_name='Real',
            last_name='Tor'
        )
        UserProfile.objects.create(user=self.realtor, role='realtor')

        self.lender = User.objects.create_user(
            username='lender1',
            email='lender1@example.com',
            password=self.password,
            first_name='Len',
            last_name='Der'
        )
        UserProfile.objects.create(user=self.lender, role='lender')
        self.token = Token.objects.create(user=self.lender)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        property_payload = {
            'property_type': 'single_family',
            'status': 'active',
            'street_address': '44 Lake Drive',
            'city': 'Plano',
            'state': 'TX',
            'zip_code': '75024',
        }
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=self.realtor).key}')
        prop_response = self.client.post('/api/properties/', property_payload, format='json')
        self.assertEqual(prop_response.status_code, status.HTTP_201_CREATED)
        self.property_id = prop_response.data['id']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_lender_business_card_perks_and_settings_flow(self):
        front = SimpleUploadedFile('front.jpg', b'front-image-bytes', content_type='image/jpeg')
        card_response = self.client.post('/api/lender-profile/upload_business_card/', {
            'side': 'front',
            'card': front
        }, format='multipart')
        self.assertEqual(card_response.status_code, status.HTTP_200_OK)
        self.assertEqual(card_response.data['side'], 'front')

        perk_response = self.client.post('/api/perks/', {
            'property': self.property_id,
            'promoter_name': 'Lender Promo Co',
            'promo_code': 'LEND50',
            'description': 'Get $50 credit',
            'is_active': True,
        }, format='json')
        self.assertEqual(perk_response.status_code, status.HTTP_201_CREATED)

        list_response = self.client.get(f'/api/perks/by_property/{self.property_id}/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(list_response.data), 1)

        settings_response = self.client.patch('/api/notification-settings/update_settings/', {
            'email_open_house': True,
            'email_new_perks': True,
        }, format='json')
        self.assertEqual(settings_response.status_code, status.HTTP_200_OK)
        self.assertTrue(settings_response.data['email_new_perks'])

        new_password = 'LenderNewPass123!'
        password_response = self.client.post('/api/notification-settings/change_password/', {
            'current_password': self.password,
            'new_password': new_password,
            'confirm_password': new_password,
        }, format='json')
        self.assertEqual(password_response.status_code, status.HTTP_200_OK)

        self.client.credentials()
        login_response = self.client.post('/api/login/', {
            'username': self.lender.username,
            'password': new_password,
        }, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

class BrokerDashboardFlowTests(APITestCase):
    def setUp(self):
        self.password = 'BrokerPass123!'
        self.user = User.objects.create_user(
            username='broker123',
            email='broker@example.com',
            password=self.password,
            first_name='Brok',
            last_name='Er'
        )
        UserProfile.objects.create(user=self.user, role='broker')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_property_create_as_broker(self):
        property_payload = {
            'property_type': 'condo',
            'status': 'active',
            'street_address': '55 Broker Ave',
            'city': 'Dallas',
            'state': 'TX',
            'zip_code': '75001',
        }
        create_response = self.client.post('/api/properties/', property_payload, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data['street_address'], '55 Broker Ave')
        self.assertEqual(create_response.data['realtor'], self.user.id)


@override_settings(
    STRIPE_SECRET_KEY='sk_test_example',
    STRIPE_PUBLISHABLE_KEY='pk_test_example',
    STRIPE_WEBHOOK_SECRET='whsec_example',
)
class SignupBillingFlowTests(APITestCase):
    def test_starter_signup_creates_user_immediately(self):
        response = self.client.post('/api/signup/', {
            'username': 'starter-user',
            'email': 'starter@example.com',
            'password': 'StarterPass123!',
            'password2': 'StarterPass123!',
            'first_name': 'Start',
            'last_name': 'Er',
            'role': 'realtor',
            'plan': 'starter',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='starter-user').exists())
        self.assertEqual(response.data['user']['role'], 'realtor')

    def test_paid_signup_requires_checkout_endpoint(self):
        response = self.client.post('/api/signup/', {
            'username': 'growth-user',
            'email': 'growth@example.com',
            'password': 'GrowthPass123!',
            'password2': 'GrowthPass123!',
            'first_name': 'Grow',
            'last_name': 'Th',
            'role': 'broker',
            'plan': 'growth',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='growth-user').exists())

    @patch('api.views.stripe.checkout.Session.create')
    def test_create_checkout_session_for_paid_plan(self, create_session_mock):
        create_session_mock.return_value = type('Session', (), {
            'id': 'cs_test_123',
            'url': 'https://checkout.stripe.test/session/cs_test_123',
        })()

        response = self.client.post('/api/signup/create-checkout-session/', {
            'username': 'growth-user',
            'email': 'growth@example.com',
            'password': 'GrowthPass123!',
            'password2': 'GrowthPass123!',
            'first_name': 'Grow',
            'last_name': 'Th',
            'role': 'broker',
            'plan': 'growth',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('checkout_url', response.data)
        pending_signup = PendingSignup.objects.get(username='growth-user')
        self.assertEqual(pending_signup.status, 'pending')
        self.assertEqual(pending_signup.plan, 'growth')
        self.assertFalse(User.objects.filter(username='growth-user').exists())

    @patch('api.views.stripe.checkout.Session.retrieve')
    def test_checkout_status_completes_user_and_subscription(self, retrieve_session_mock):
        pending_signup = PendingSignup.objects.create(
            username='premium-user',
            email='premium@example.com',
            first_name='Pre',
            last_name='Mium',
            role='lender',
            plan='premium',
            password_hash='pbkdf2_sha256$1000000$abc$hash',
            stripe_checkout_session_id='cs_test_complete',
        )
        retrieve_session_mock.return_value = {
            'id': 'cs_test_complete',
            'status': 'complete',
            'payment_status': 'paid',
            'customer': 'cus_123',
            'subscription': {
                'id': 'sub_123',
                'current_period_end': 1794614400,
            },
        }

        with patch('api.views._finalize_pending_signup') as finalize_mock:
            user = User.objects.create_user(
                username='premium-user',
                email='premium@example.com',
                password='PremiumPass123!',
                first_name='Pre',
                last_name='Mium',
            )
            UserProfile.objects.create(user=user, role='lender')
            token = Token.objects.create(user=user)
            pending_signup.user = user
            pending_signup.status = 'completed'
            pending_signup.save(update_fields=['user', 'status'])
            UserSubscription.objects.create(
                user=user,
                plan='premium',
                status='active',
                stripe_customer_id='cus_123',
                stripe_subscription_id='sub_123',
            )
            finalize_mock.return_value = (user, token, False)

            response = self.client.get('/api/signup/checkout-status/', {'session_id': 'cs_test_complete'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['user']['role'], 'lender')
        self.assertEqual(response.data['redirect_url'], '/dashboard/lender/')

    @patch('api.views.stripe.checkout.Session.retrieve')
    def test_checkout_status_falls_back_to_pending_signup_when_session_placeholder_is_literal(self, retrieve_session_mock):
        pending_signup = PendingSignup.objects.create(
            username='fallback-user',
            email='fallback@example.com',
            first_name='Fall',
            last_name='Back',
            role='realtor',
            plan='growth',
            password_hash='pbkdf2_sha256$1000000$abc$hash',
            stripe_checkout_session_id='cs_test_fallback',
        )
        retrieve_session_mock.return_value = {
            'id': 'cs_test_fallback',
            'status': 'complete',
            'payment_status': 'paid',
            'customer': 'cus_fallback',
            'subscription': {
                'id': 'sub_fallback',
                'current_period_end': 1794614400,
            },
        }

        with patch('api.views._finalize_pending_signup') as finalize_mock:
            user = User.objects.create_user(
                username='fallback-user',
                email='fallback@example.com',
                password='FallbackPass123!',
                first_name='Fall',
                last_name='Back',
            )
            UserProfile.objects.create(user=user, role='realtor')
            token = Token.objects.create(user=user)
            finalize_mock.return_value = (user, token, True)

            response = self.client.get('/api/signup/checkout-status/', {
                'session_id': '{CHECKOUT_SESSION_ID}',
                'pending_signup': pending_signup.id,
            })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['redirect_url'], '/dashboard/realtor/')

    def test_signup_cancel_marks_pending_signup_cancelled(self):
        pending_signup = PendingSignup.objects.create(
            username='cancel-user',
            email='cancel@example.com',
            first_name='Can',
            last_name='Cel',
            role='partner',
            plan='growth',
            password_hash='pbkdf2_sha256$1000000$abc$hash',
            stripe_checkout_session_id='cs_test_cancel',
        )

        response = self.client.get(f'/signup/cancel/?pending_signup={pending_signup.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending_signup.refresh_from_db()
        self.assertEqual(pending_signup.status, 'cancelled')

    def test_billing_summary_returns_starter_for_free_user(self):
        user = User.objects.create_user(
            username='free-user',
            email='free@example.com',
            password='FreePass123!',
            first_name='Free',
            last_name='User',
        )
        UserProfile.objects.create(user=user, role='partner')
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.get('/api/billing/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subscription']['plan'], 'starter')
        self.assertFalse(response.data['subscription']['portal_available'])

    @patch('api.views.stripe.billing_portal.Session.create')
    def test_billing_portal_returns_url_for_paid_user(self, create_portal_mock):
        user = User.objects.create_user(
            username='paid-user',
            email='paid@example.com',
            password='PaidPass123!',
            first_name='Paid',
            last_name='User',
        )
        UserProfile.objects.create(user=user, role='broker')
        UserSubscription.objects.create(
            user=user,
            plan='growth',
            status='active',
            stripe_customer_id='cus_paid_123',
            stripe_subscription_id='sub_paid_123',
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        create_portal_mock.return_value = type('PortalSession', (), {'url': 'https://billing.stripe.test/session'})()

        response = self.client.post('/api/billing/create-portal-session/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['url'], 'https://billing.stripe.test/session')
