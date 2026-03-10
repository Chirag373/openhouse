import re

with open('core/templates/lenders.html', 'r') as f:
    html = f.read()

# Pattern to replace everything from <!-- Lenders Grid --> to </script>
pattern = re.compile(r'<!-- Lenders Grid -->.*?(?=<script>)', re.DOTALL)

new_content = """<!-- Lenders Grid -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">

    {% for profile in lender_profiles %}
    <!-- Lender Card -->
    <div class="bg-white rounded-xl shadow hover:shadow-lg transition relative flex flex-col h-full border border-gray-100 group overflow-hidden">
        <!-- Business Card Carousel -->
        <div class="w-full relative bg-gray-200 card-carousel" style="aspect-ratio: 1.75/1;">
            <!-- Slide 1: Front -->
            <div class="carousel-slide absolute inset-0 w-full h-full bg-white flex items-center justify-center transition-transform duration-300 ease-in-out translate-x-0" data-index="0">
                {% if profile.business_card_front %}
                <img src="{{ profile.business_card_front }}" class="object-cover h-full w-full" alt="Card Front">
                {% else %}
                <img src="https://ui-avatars.com/api/?name={{ profile.company_name|default:profile.user.get_full_name|urlencode }}&background=f0fdf4&color=166534&bold=true&length=2&size=256" class="object-contain h-3/4 w-3/4" alt="Card Front">
                {% endif %}
                <span class="absolute bottom-2 left-3 text-[10px] text-gray-400 font-mono tracking-widest uppercase bg-white/80 px-1 rounded">Front</span>
            </div>
            <!-- Slide 2: Back -->
            <div class="carousel-slide absolute inset-0 w-full h-full bg-gray-50 flex items-center justify-center transition-transform duration-300 ease-in-out translate-x-full" data-index="1">
                {% if profile.business_card_back %}
                <img src="{{ profile.business_card_back }}" class="object-cover h-full w-full" alt="Card Back">
                {% else %}
                <div class="text-center p-4">
                    <div class="text-xs text-gray-500 font-bold mb-2 tracking-wide">SCAN ME</div>
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={{ profile.business_website|default:'#'|urlencode }}" class="mx-auto w-24 h-24 opacity-80 mix-blend-multiply" alt="QR">
                </div>
                {% endif %}
                <span class="absolute bottom-2 left-3 text-[10px] text-gray-400 font-mono tracking-widest uppercase bg-white/80 px-1 rounded">Back</span>
            </div>

            <!-- Controls -->
            <button class="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 p-1.5 rounded-full shadow-md z-20 backdrop-blur-sm transition opacity duration-200" onclick="moveSlide(this, -1)">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
            </button>
            <button class="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 p-1.5 rounded-full shadow-md z-20 backdrop-blur-sm transition opacity duration-200" onclick="moveSlide(this, 1)">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
            </button>

            <!-- Indicators -->
            <div class="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1 z-20">
                <div class="w-1.5 h-1.5 rounded-full bg-emerald-600 transition-colors" data-indicator="0"></div>
                <div class="w-1.5 h-1.5 rounded-full bg-gray-300 transition-colors" data-indicator="1"></div>
            </div>
        </div>

        <div class="p-5 flex-grow flex flex-col gap-3">
            <div>
                <h2 class="font-bold text-xl text-gray-900 leading-tight">{{ profile.company_name|default:profile.user.get_full_name }}</h2>
                <h3 class="text-emerald-600 font-medium mt-1">{{ profile.user.get_full_name }}</h3>
            </div>
            <div class="text-sm text-gray-600 line-clamp-3 leading-relaxed">
                {{ profile.biography|default:"Professional lending services tailored for your needs." }}
            </div>
            <ul class="text-xs text-gray-500 space-y-2 mt-auto pt-3 border-t border-gray-50">
                {% if profile.license_nmls %}
                <li class="flex items-center gap-2">
                    <svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                    </svg>
                    License: NMLS #{{ profile.license_nmls }}
                </li>
                {% endif %}
                {% if profile.serving_states or profile.serving_cities %}
                <li class="flex items-center gap-2">
                    <svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.243-4.243a8 8 0 1111.314 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    Serves: {{ profile.serving_cities|default:"" }} {{ profile.serving_states }}
                </li>
                {% endif %}
            </ul>
            <div class="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
                <a href="tel:{{ profile.phone_number_1 }}" class="flex items-center gap-1.5 text-sm font-medium text-gray-700 hover:text-emerald-600 transition">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
                    </svg>
                    Contact
                </a>
                {% if profile.business_website %}
                <a href="{{ profile.business_website }}" target="_blank" class="text-sm font-semibold text-blue-600 hover:underline flex items-center gap-1">
                    Visit Website
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                </a>
                {% endif %}
            </div>
        </div>
    </div>
    {% empty %}
    <div class="col-span-full py-12 text-center text-gray-500">
        <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
        </svg>
        <p class="text-xl font-medium text-gray-400">No lenders registered yet.</p>
    </div>
    {% endfor %}

</div>

"""

with open('core/templates/lenders.html', 'w') as f:
    f.write(pattern.sub(new_content, html))
