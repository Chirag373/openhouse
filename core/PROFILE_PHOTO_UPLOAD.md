# Profile Photo Upload Implementation

## Features Implemented

### 1. Backend Setup

#### Media Configuration (settings.py)
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

#### URL Configuration (core/urls.py)
- Added media file serving in development mode
- Files accessible at `/media/profile_photos/`

#### Upload Endpoint (api/views.py)
**Endpoint:** `POST /api/realtor-profile/upload_photo/`

**Features:**
- File validation (type and size)
- Unique filename generation
- Old photo deletion
- Secure file storage

**Validations:**
- Max file size: 3MB
- Allowed types: JPEG, JPG, PNG, WEBP
- Authentication required

### 2. Frontend Implementation

#### Photo Upload UI
- Click-to-upload interface
- Drag-and-drop ready container
- Real-time preview
- Upload status messages
- File type restrictions in input

#### JavaScript Functions

**uploadProfilePhoto(file)**
- Validates file size and type
- Shows upload progress
- Handles errors gracefully
- Updates UI on success

**displayProfilePhoto(photoUrl)**
- Shows uploaded photo
- Hides placeholder icon
- Updates preview instantly

**Event Handlers**
- File input change listener
- Immediate preview on selection
- Automatic upload to server

## Usage

### For Users

1. **Navigate to Profile Tab**
   - Go to dashboard
   - Click "Profile" in sidebar

2. **Upload Photo**
   - Click on the circular photo placeholder
   - Select image file (JPEG, PNG, WEBP)
   - File must be under 3MB
   - Photo uploads automatically

3. **View Result**
   - Preview shows immediately
   - Success message appears
   - Photo persists on page refresh

### For Developers

#### Test Upload via cURL
```bash
# Get auth token first (from login)
TOKEN="your-auth-token"

# Upload photo
curl -X POST http://127.0.0.1:8000/api/realtor-profile/upload_photo/ \
  -H "Authorization: Token $TOKEN" \
  -F "photo=@/path/to/image.jpg"
```

#### Expected Response
```json
{
  "message": "Photo uploaded successfully",
  "photo_url": "/media/profile_photos/1_username.jpg"
}
```

## File Structure

```
project/
├── media/
│   └── profile_photos/
│       └── {user_id}_{username}.{ext}
├── api/
│   └── views.py (upload_photo endpoint)
├── core/
│   ├── settings.py (MEDIA_URL, MEDIA_ROOT)
│   └── urls.py (media file serving)
└── templates/
    └── realtor_dashboard.html (upload UI)
```

## Security Features

1. **Authentication Required**
   - Only logged-in users can upload
   - Users can only update their own profile

2. **File Validation**
   - Type checking (MIME type)
   - Size limit enforcement (3MB)
   - Extension validation

3. **Secure Storage**
   - Unique filenames prevent conflicts
   - Old files automatically deleted
   - Files stored outside web root in production

4. **Error Handling**
   - Graceful failure messages
   - No sensitive data exposure
   - Proper HTTP status codes

## API Endpoints

### Upload Photo
```
POST /api/realtor-profile/upload_photo/
Headers: Authorization: Token {token}
Body: multipart/form-data
  - photo: file

Response 200:
{
  "message": "Photo uploaded successfully",
  "photo_url": "/media/profile_photos/1_username.jpg"
}

Response 400:
{
  "error": "File size exceeds 3MB limit"
}
```

### Get Profile (includes photo URL)
```
GET /api/realtor-profile/me/
Headers: Authorization: Token {token}

Response 200:
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "profile_photo": "/media/profile_photos/1_john.jpg",
  ...
}
```

## Troubleshooting

### Issue: Photo not uploading
**Check:**
1. File size < 3MB
2. File type is JPEG/PNG/WEBP
3. User is authenticated
4. media/profile_photos/ directory exists

### Issue: Photo not displaying
**Check:**
1. MEDIA_URL configured in settings
2. Media files being served (DEBUG=True)
3. Photo URL in database is correct
4. Browser console for errors

### Issue: 404 on photo URL
**Check:**
1. `urlpatterns += static(...)` in urls.py
2. MEDIA_ROOT path is correct
3. File actually exists in media folder

## Production Considerations

### For Production Deployment:

1. **Use Cloud Storage**
   - AWS S3
   - Google Cloud Storage
   - Azure Blob Storage

2. **Configure django-storages**
```python
# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
```

3. **Add Image Processing**
   - Resize images (e.g., 400x400)
   - Compress for web
   - Generate thumbnails

4. **Security Enhancements**
   - Scan for malware
   - Add rate limiting
   - Implement CDN

## Testing Checklist

- [ ] Upload JPEG file
- [ ] Upload PNG file
- [ ] Upload WEBP file
- [ ] Try file > 3MB (should fail)
- [ ] Try invalid file type (should fail)
- [ ] Upload without auth (should fail)
- [ ] Upload replaces old photo
- [ ] Photo persists after refresh
- [ ] Photo displays in profile
- [ ] Photo URL is accessible

## Next Steps

1. Add image cropping tool
2. Implement drag-and-drop
3. Add multiple photo support
4. Generate thumbnails
5. Add photo gallery
