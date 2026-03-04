// Common Dashboard JavaScript
// Reusable functions for all role dashboards

// API Configuration
const API_BASE_URL = '/api';
const AUTH_TOKEN = localStorage.getItem('authToken') || localStorage.getItem('auth_token');
const FETCH_TIMEOUT = 5000; // 5 second timeout

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('-translate-x-full');
    }
}

function switchTab(tabId) {
    document.querySelectorAll('.dashboard-section').forEach(el => el.classList.add('hidden'));
    const section = document.getElementById('section-' + tabId);
    if (section) {
        section.classList.remove('hidden');
    }

    document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('active'));
    const navItem = document.getElementById('nav-' + tabId);
    if (navItem) {
        navItem.classList.add('active');
    }

    const url = new URL(window.location);
    url.searchParams.set('tab', tabId);
    window.history.pushState({}, '', url);

    if (window.innerWidth < 768) {
        toggleSidebar();
    }
}

function initializeTab() {
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    
    const validTabs = ['profile', 'properties', 'open-house', 'perks', 'settings'];
    const activeTab = validTabs.includes(tabParam) ? tabParam : 'profile';
    
    switchTab(activeTab);
}

// Fetch with timeout
async function fetchWithTimeout(url, options, timeout = FETCH_TIMEOUT) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

// Check authentication and redirect if needed
function checkAuth() {
    if (!AUTH_TOKEN) {
        console.warn('No authentication token found. Redirecting to login...');
        setTimeout(() => {
            window.location.href = '/login/';
        }, 1000);
        return false;
    }
    return true;
}

// Load user info from localStorage
function loadUserFromStorage() {
    try {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            const user = JSON.parse(userStr);
            updateUserInfo({
                first_name: user.first_name,
                last_name: user.last_name,
                email: user.email,
                full_name: user.full_name,
                role: user.role
            });
        }
    } catch (error) {
        console.warn('Could not load user from storage:', error);
    }
}

// Update user info in sidebar
function updateUserInfo(data) {
    const fullName = data.full_name || `${data.first_name || ''} ${data.last_name || ''}`.trim() || 'User';
    const role = data.role || 'User';
    
    // Update sidebar user info
    const sidebarUserName = document.querySelector('.p-6.pb-2 .font-semibold');
    const sidebarUserRole = document.querySelector('.p-6.pb-2 .text-xs.text-gray-500');
    
    if (sidebarUserName) sidebarUserName.textContent = fullName;
    if (sidebarUserRole) sidebarUserRole.textContent = role.charAt(0).toUpperCase() + role.slice(1);
    
    // Update avatar
    const avatar = document.querySelector('.p-6.pb-2 img');
    if (avatar && fullName) {
        avatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(fullName)}&background=e0e7ff&color=4f46e5`;
    }
    
    // Update profile photo preview if exists
    if (data.profile_photo) {
        displayProfilePhoto(data.profile_photo);
    }
}

// Display profile photo
function displayProfilePhoto(photoUrl) {
    const preview = document.getElementById('photo-preview');
    const icon = document.getElementById('photo-icon');
    const text = document.getElementById('photo-text');
    
    if (preview && photoUrl) {
        preview.src = photoUrl;
        preview.classList.remove('hidden');
        if (icon) icon.classList.add('hidden');
        if (text) text.classList.add('hidden');
    }
}

// Handle photo upload
async function uploadProfilePhoto(file, profileEndpoint) {
    if (!checkAuth()) return;

    const uploadStatus = document.getElementById('upload-status');
    
    // Validate file size
    if (file.size > 3 * 1024 * 1024) {
        if (uploadStatus) {
            uploadStatus.textContent = 'Error: File size exceeds 3MB';
            uploadStatus.className = 'text-xs mt-1 text-red-600';
        }
        return;
    }

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        if (uploadStatus) {
            uploadStatus.textContent = 'Error: Invalid file type';
            uploadStatus.className = 'text-xs mt-1 text-red-600';
        }
        return;
    }

    // Show uploading status
    if (uploadStatus) {
        uploadStatus.textContent = 'Uploading...';
        uploadStatus.className = 'text-xs mt-1 text-blue-600';
    }

    const formData = new FormData();
    formData.append('photo', file);

    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/${profileEndpoint}/upload_photo/`, {
            method: 'POST',
            headers: {
                'Authorization': `Token ${AUTH_TOKEN}`
            },
            body: formData
        });

        if (response.status === 401 || response.status === 403) {
            alert('Session expired. Please login again.');
            window.location.href = '/login/';
            return;
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        const result = await response.json();
        
        // Display uploaded photo
        displayProfilePhoto(result.photo_url);
        
        if (uploadStatus) {
            uploadStatus.textContent = 'Photo uploaded successfully!';
            uploadStatus.className = 'text-xs mt-1 text-green-600';
            setTimeout(() => {
                uploadStatus.textContent = '';
            }, 3000);
        }
    } catch (error) {
        console.error('Error uploading photo:', error);
        if (uploadStatus) {
            uploadStatus.textContent = `Error: ${error.message}`;
            uploadStatus.className = 'text-xs mt-1 text-red-600';
        }
    }
}

// Initialize dashboard
function initializeDashboard(profileEndpoint) {
    // Initialize tab immediately
    initializeTab();
    
    // Load user info from localStorage first (instant)
    loadUserFromStorage();
    
    // Check authentication
    if (!AUTH_TOKEN) {
        console.warn('No authentication token. Redirecting to login...');
        setTimeout(() => {
            window.location.href = '/login/';
        }, 1000);
        return;
    }

    // Setup photo upload handler if exists
    const photoInput = document.getElementById('profile-photo-input');
    if (photoInput) {
        photoInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Show preview immediately
                const reader = new FileReader();
                reader.onload = function(e) {
                    displayProfilePhoto(e.target.result);
                };
                reader.readAsDataURL(file);
                
                // Upload to server
                uploadProfilePhoto(file, profileEndpoint);
            }
        });
    }
}
