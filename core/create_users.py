#!/usr/bin/env python
"""
Script to create test users for all roles in the system.
Run this with: python manage.py shell < create_users.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import UserProfile, RealtorProfile, LenderProfile, BrokerProfile, PartnerProfile, PromoterProfile

# User credentials
users_data = [
    {
        'username': 'realtor1',
        'email': 'realtor1@example.com',
        'password': 'Realtor@123',
        'first_name': 'John',
        'last_name': 'Realtor',
        'role': 'realtor'
    },
    {
        'username': 'lender1',
        'email': 'lender1@example.com',
        'password': 'Lender@123',
        'first_name': 'Sarah',
        'last_name': 'Lender',
        'role': 'lender'
    },
    {
        'username': 'broker1',
        'email': 'broker1@example.com',
        'password': 'Broker@123',
        'first_name': 'Mike',
        'last_name': 'Broker',
        'role': 'broker'
    },
    {
        'username': 'partner1',
        'email': 'partner1@example.com',
        'password': 'Partner@123',
        'first_name': 'Emily',
        'last_name': 'Partner',
        'role': 'partner'
    },
    {
        'username': 'promoter1',
        'email': 'promoter1@example.com',
        'password': 'Promoter@123',
        'first_name': 'David',
        'last_name': 'Promoter',
        'role': 'promoter'
    }
]

print("Creating users...")
print("=" * 60)

for user_data in users_data:
    username = user_data['username']
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists. Skipping...")
        continue
    
    # Create user
    user = User.objects.create_user(
        username=user_data['username'],
        email=user_data['email'],
        password=user_data['password'],
        first_name=user_data['first_name'],
        last_name=user_data['last_name']
    )
    
    # Create UserProfile
    user_profile = UserProfile.objects.create(
        user=user,
        role=user_data['role']
    )
    
    # Create role-specific profile
    role = user_data['role']
    if role == 'realtor':
        RealtorProfile.objects.create(
            user=user,
            phone_number_1='555-0101',
            company_name='Premier Realty',
            serving_states='CA, NY, TX',
            serving_cities='Los Angeles, New York, Houston',
            biography='Experienced realtor with 10+ years in the industry.'
        )
    elif role == 'lender':
        LenderProfile.objects.create(
            user=user,
            phone_number_1='555-0102',
            company_name='First National Lending',
            license_nmls='123456',
            serving_states='CA, NY, FL',
            serving_cities='San Francisco, New York, Miami',
            biography='Trusted lender specializing in residential mortgages.'
        )
    elif role == 'broker':
        BrokerProfile.objects.create(
            user=user,
            phone_number_1='555-0103',
            company_name='Elite Brokerage',
            license_number='BRK-789012',
            license_states='CA, NY, TX, FL',
            serving_states='CA, NY, TX, FL',
            serving_cities='Multiple cities nationwide',
            biography='Full-service brokerage with nationwide coverage.'
        )
    elif role == 'partner':
        PartnerProfile.objects.create(
            user=user,
            phone_number_1='555-0104',
            company_name='Strategic Partners LLC',
            license_state='CA',
            license_number='PTR-345678',
            serving_states='CA, NV',
            serving_cities='Los Angeles, Las Vegas',
            biography='Strategic partner for real estate professionals.'
        )
    elif role == 'promoter':
        PromoterProfile.objects.create(
            user=user,
            phone_number_1='555-0105',
            company_name='PromoMax Marketing',
            business_type='marketing_agency',
            serving_states='CA, NY, TX',
            serving_cities='Los Angeles, New York, Dallas',
            biography='Full-service marketing agency for real estate.'
        )
    
    print(f"✓ Created user: {username} ({user_data['role']})")

print("=" * 60)
print("\nAll users created successfully!")
print("\nCREDENTIALS:")
print("=" * 60)
for user_data in users_data:
    print(f"\nRole: {user_data['role'].upper()}")
    print(f"  Username: {user_data['username']}")
    print(f"  Email: {user_data['email']}")
    print(f"  Password: {user_data['password']}")
print("=" * 60)
