from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import UserProfile


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
