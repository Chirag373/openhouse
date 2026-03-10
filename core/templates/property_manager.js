// Property Management JavaScript for Realtor Dashboard

// Fetch and display properties
async function fetchProperties() {
    if (!checkAuth()) return;

    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/properties/`, {
            method: 'GET',
            headers: {
                'Authorization': `Token ${AUTH_TOKEN}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 401 || response.status === 403) {
            console.warn('Authentication failed');
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to fetch properties');
        }

        const properties = await response.json();
        displayProperties(properties);
    } catch (error) {
        console.error('Error fetching properties:', error);
    }
}

// Display properties in grid
function displayProperties(properties) {
    const grid = document.getElementById('properties-grid');
    if (!grid) return;

    if (properties.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-500">
                <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path>
                </svg>
                <p class="text-lg font-medium mb-2">No properties listed yet</p>
                <p class="text-sm">Click "Add New Listing" to create your first property</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = properties.map(property => {
        const firstPhoto = property.photos && property.photos.length > 0
            ? property.photos[0].url
            : "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect fill='%23e5e7eb' width='400' height='300'/%3E%3Ctext fill='%239ca3af' font-family='sans-serif' font-size='24' x='50%25' y='50%25' text-anchor='middle' dominant-baseline='middle'%3ENo Image%3C/text%3E%3C/svg%3E";

        const price = property.price ? `$${Number(property.price).toLocaleString()}` : 'Price TBD';

        return `
            <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition">
                <div class="h-48 bg-gray-200 relative">
                    <img src="${firstPhoto}" class="w-full h-full object-cover" alt="${property.street_address}">
                    <span class="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded font-mono">
                        ${property.listing_id}
                    </span>
                    <span class="absolute top-2 left-2 bg-indigo-600 text-white text-xs px-2 py-1 rounded capitalize">
                        ${property.status}
                    </span>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-lg text-gray-900 truncate">${property.street_address}</h3>
                    <p class="text-gray-500 text-sm mb-2">${property.city}, ${property.state} ${property.zip_code}</p>
                    <p class="text-indigo-600 font-bold text-lg mb-3">${price}</p>
                    <div class="flex gap-4 text-sm text-gray-700 mb-4 border-t border-gray-100 pt-3">
                        <span><b>${property.bedrooms || 0}</b> Bed</span>
                        <span><b>${property.bathrooms || 0}</b> Bath</span>
                        <span><b>${property.sqft || 0}</b> SqFt</span>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="editProperty(${property.id})" 
                            class="flex-1 bg-gray-50 hover:bg-gray-100 text-gray-700 py-2 rounded-lg border border-gray-200 text-sm font-medium transition">
                            Edit
                        </button>
                        <button onclick="deleteProperty(${property.id})" 
                            class="flex-1 bg-white hover:bg-red-50 text-red-600 py-2 rounded-lg border border-red-100 text-sm font-medium transition">
                            Remove
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Save property (create or update)
async function saveProperty(event) {
    event.preventDefault();
    if (!checkAuth()) return;

    const formData = {
        property_type: document.getElementById('prop_property_type').value,
        status: document.getElementById('prop_status').value,
        street_address: document.getElementById('prop_street_address').value,
        unit_apt: document.getElementById('prop_unit_apt').value,
        city: document.getElementById('prop_city').value,
        state: document.getElementById('prop_state').value,
        zip_code: document.getElementById('prop_zip_code').value,
        county: document.getElementById('prop_county').value,
        country: document.getElementById('prop_country').value || 'USA',
        bedrooms: document.getElementById('prop_bedrooms').value || null,
        bathrooms: document.getElementById('prop_bathrooms').value || null,
        garage: document.getElementById('prop_garage').value || 0,
        sqft: document.getElementById('prop_sqft').value || null,
        lot_size: document.getElementById('prop_lot_size').value,
        year_built: document.getElementById('prop_year_built').value || null,
        floor_type: document.getElementById('prop_floor_type').value,
        kitchen_type: document.getElementById('prop_kitchen_type').value,
        foundation_type: document.getElementById('prop_foundation_type').value,
        exterior: document.getElementById('prop_exterior').value,
        roof: document.getElementById('prop_roof').value,
        appliances: getSelectedAppliances(),
        price: document.getElementById('prop_price').value || null,
        description: document.getElementById('prop_description').value
    };

    const propertyId = document.getElementById('property-form-modal').dataset.propertyId;
    const isEdit = !!propertyId;
    const url = isEdit
        ? `${API_BASE_URL}/properties/${propertyId}/`
        : `${API_BASE_URL}/properties/`;
    const method = isEdit ? 'PATCH' : 'POST';

    try {
        const response = await fetchWithTimeout(url, {
            method: method,
            headers: {
                'Authorization': `Token ${AUTH_TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.status === 401 || response.status === 403) {
            alert('Session expired. Please login again.');
            window.location.href = '/login/';
            return;
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(JSON.stringify(error));
        }

        const result = await response.json();

        // Handle photo uploads if any
        const photoInput = document.getElementById('prop_photos');
        if (photoInput && photoInput.files.length > 0) {
            await uploadPropertyPhotos(result.id, photoInput.files);
        }

        alert(isEdit ? 'Property updated successfully!' : 'Property created successfully!');
        document.getElementById('property-form-modal').close();
        resetPropertyForm();
        fetchProperties();
    } catch (error) {
        console.error('Error saving property:', error);
        alert('Failed to save property. Please try again.');
    }
}

// Upload property photos
async function uploadPropertyPhotos(propertyId, files) {
    if (!checkAuth()) return;

    const formData = new FormData();
    for (let i = 0; i < Math.min(files.length, 5); i++) {
        formData.append('photos', files[i]);
    }

    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/properties/${propertyId}/upload_photos/`, {
            method: 'POST',
            headers: {
                'Authorization': `Token ${AUTH_TOKEN}`
            },
            body: formData,
            timeout: 60000 // 60 seconds timeout for photo uploads
        });

        if (!response.ok) {
            const error = await response.json();
            console.error('Photo upload error:', error);
            alert('Property was saved, but photo upload failed. Please try again.');
        }
    } catch (error) {
        console.error('Error uploading photos:', error);
        alert('Property was saved, but there was a network error while uploading photos.');
    }
}

// Get selected appliances
function getSelectedAppliances() {
    const checkboxes = document.querySelectorAll('input[name="appliances"]:checked');
    return Array.from(checkboxes).map(cb => cb.value).join(', ');
}

// Edit property
async function editProperty(propertyId) {
    if (!checkAuth()) return;

    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/properties/${propertyId}/`, {
            method: 'GET',
            headers: {
                'Authorization': `Token ${AUTH_TOKEN}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch property');
        }

        const property = await response.json();
        populatePropertyForm(property);
        document.getElementById('property-form-modal').dataset.propertyId = propertyId;
        document.getElementById('property-form-modal').showModal();
    } catch (error) {
        console.error('Error fetching property:', error);
        alert('Failed to load property details');
    }
}

// Populate property form
function populatePropertyForm(property) {
    document.getElementById('modal-title').textContent = 'Edit Property';
    document.getElementById('prop_property_type').value = property.property_type || '';
    document.getElementById('prop_status').value = property.status || 'active';
    document.getElementById('prop_street_address').value = property.street_address || '';
    document.getElementById('prop_unit_apt').value = property.unit_apt || '';
    document.getElementById('prop_city').value = property.city || '';
    document.getElementById('prop_state').value = property.state || '';
    document.getElementById('prop_zip_code').value = property.zip_code || '';
    document.getElementById('prop_county').value = property.county || '';
    document.getElementById('prop_country').value = property.country || 'USA';
    document.getElementById('prop_bedrooms').value = property.bedrooms || '';
    document.getElementById('prop_bathrooms').value = property.bathrooms || '';
    document.getElementById('prop_garage').value = property.garage || 0;
    document.getElementById('prop_sqft').value = property.sqft || '';
    document.getElementById('prop_lot_size').value = property.lot_size || '';
    document.getElementById('prop_year_built').value = property.year_built || '';
    document.getElementById('prop_floor_type').value = property.floor_type || '';
    document.getElementById('prop_kitchen_type').value = property.kitchen_type || '';
    document.getElementById('prop_foundation_type').value = property.foundation_type || '';
    document.getElementById('prop_exterior').value = property.exterior || '';
    document.getElementById('prop_roof').value = property.roof || '';
    document.getElementById('prop_price').value = property.price || '';
    document.getElementById('prop_description').value = property.description || '';

    // Set appliances checkboxes
    if (property.appliances) {
        const appliances = property.appliances.split(',').map(a => a.trim());
        document.querySelectorAll('input[name="appliances"]').forEach(cb => {
            cb.checked = appliances.includes(cb.value);
        });
    }
}

// Reset property form
function resetPropertyForm() {
    document.getElementById('modal-title').textContent = 'Add New Property';
    document.getElementById('property-form').reset();
    document.getElementById('property-form-modal').removeAttribute('data-property-id');
    document.querySelectorAll('input[name="appliances"]').forEach(cb => cb.checked = false);
}

// Delete property
async function deleteProperty(propertyId) {
    if (!checkAuth()) return;

    if (!confirm('Are you sure you want to delete this property?')) {
        return;
    }

    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/properties/${propertyId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Token ${AUTH_TOKEN}`
            }
        });

        if (response.status === 401 || response.status === 403) {
            alert('Session expired. Please login again.');
            window.location.href = '/login/';
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to delete property');
        }

        alert('Property deleted successfully!');
        fetchProperties();
    } catch (error) {
        console.error('Error deleting property:', error);
        alert('Failed to delete property. Please try again.');
    }
}

// Initialize properties section
function initializePropertiesSection() {
    // Fetch properties when properties tab is opened
    const propertiesTab = document.getElementById('nav-properties');
    if (propertiesTab) {
        propertiesTab.addEventListener('click', function () {
            fetchProperties();
        });
    }

    // Setup form submission
    const propertyForm = document.getElementById('property-form');
    if (propertyForm) {
        propertyForm.addEventListener('submit', saveProperty);
    }

    // Setup modal close to reset form
    const modal = document.getElementById('property-form-modal');
    if (modal) {
        modal.addEventListener('close', resetPropertyForm);
    }
}
