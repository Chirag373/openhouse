#!/usr/bin/env python
"""
Script to check photos for a specific property
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Property, PropertyPhoto

listing_id = 'XW99F1'

try:
    property_obj = Property.objects.get(listing_id=listing_id)
    print(f"Property found: {property_obj}")
    print(f"Realtor: {property_obj.realtor.username}")
    print(f"Address: {property_obj.street_address}, {property_obj.city}")
    print("\nPhotos:")
    
    photos = PropertyPhoto.objects.filter(property=property_obj).order_by('order')
    
    if photos.exists():
        for photo in photos:
            print(f"  - Photo {photo.order}: {photo.photo_url}")
            # Check if file exists
            photo_path = photo.photo_url.replace('/media/', '')
            full_path = os.path.join('media', photo_path)
            exists = os.path.exists(full_path)
            print(f"    File exists: {exists}")
            if exists:
                size = os.path.getsize(full_path)
                print(f"    File size: {size} bytes")
    else:
        print("  No photos found for this property")
        
except Property.DoesNotExist:
    print(f"Property with listing_id '{listing_id}' not found")
