import re

with open('core/templates/partner_dashboard.html', 'r') as f:
    text = f.read()

# Instead of "Partner", it's "Promoter"
text = text.replace('Partner Dashboard', 'Promoter Dashboard')
text = text.replace('PD', 'PD') # Partner -> Promoter
text = text.replace('>Partner<', '>Promoter<')
text = text.replace('partner-profile', 'promoter-profile')

# Tab: Services -> Promo Codes
text = text.replace("switchTab('services')", "switchTab('promo-codes')")
text = text.replace("id=\"nav-services\"", "id=\"nav-promo-codes\"")
text = text.replace("Services\n", "Promo Codes\n")
text = text.replace("id=\"section-services\"", "id=\"section-promo-codes\"")
text = text.replace("Manage your services and availability", "Manage your promotional codes and campaigns")

with open('core/templates/promoter_dashboard.html', 'r') as f:
    old_promoter = f.read()

# Grab the promo code HTML block from old_promoter
promo_match = re.search(r'<!-- Generate New Promo Code -->(.*?)<!-- Active Promo Codes -->', old_promoter, re.DOTALL)
active_promo_match = re.search(r'<!-- Active Promo Codes -->(.*?)</div>\s*</div>\s*</div>\s*<!-- Right Column: Stats & Info -->', old_promoter, re.DOTALL)

promo_html = ""
if promo_match and active_promo_match:
    promo_html = "<div class=\"max-w-4xl mx-auto space-y-6\">\n" + '<!-- Generate New Promo Code -->' + promo_match.group(1) + '<!-- Active Promo Codes -->' + active_promo_match.group(1) + "</div></div>\n"

# Replace the inner content of section-promo-codes
text = re.sub(r'(<div id="section-promo-codes".*?>\s*<div class="mb-8">\s*<h2 class="text-2xl font-bold text-gray-900">Promo Codes</h2>\s*<p class="text-gray-600 mt-1">Manage your promotional codes and campaigns</p>\s*</div>).*?(</div>\s*<!-- Settings Section -->)', r'\1\n' + promo_html.replace('\\', '\\\\') + r'\n\2', text, flags=re.DOTALL)

# Add the JS functions from old_promoter (Promo codes logic)
js_match = re.search(r'(async function fetchPromoCodes.*?)</script>', old_promoter, re.DOTALL)
if js_match:
    js_to_add = "\n" + js_match.group(1)
    text = text.replace('</script>', js_to_add + '\n</script>')

# Make sure edit-business-modal is updated for promoter (has different fields like biography, business_type vs partner stuff)
# Since they are similar, the easiest is to grab the edit-business-modal from old_promoter over the partner one
modal_match = re.search(r'<!-- Edit Business Info Modal -->(.*?)</dialog>', old_promoter, re.DOTALL)
if modal_match:
    text = re.sub(r'<!-- Edit Business Info Modal -->.*?</dialog>', '<!-- Edit Business Info Modal -->' + modal_match.group(1).replace('\\', '\\\\') + '</dialog>', text, flags=re.DOTALL)

# Same with business Info block
binfo_match = re.search(r'<!-- Business Info -->(.*?)</button>\s*</div>\s*</div>', old_promoter, re.DOTALL)
old_binfo = re.search(r'<!-- Business Info -->(.*?)</button>\s*</div>\s*</div>', old_promoter, re.DOTALL)
if binfo_match and old_binfo:
    text = text.replace(binfo_match.group(0), old_binfo.group(0))

# Make sure saveProfile is completely from old_promoter
saveprof = re.search(r'async function saveProfile.*?(?:\n    async function |\n    // Handle |\n    function updateDisplayPanel)', old_promoter, re.DOTALL)
saveprof_partner = re.search(r'async function saveProfile.*?(?:\n    async function |\n    // Handle |\n    function updateDisplayPanel)', text, re.DOTALL)
if saveprof and saveprof_partner:
    # careful! We don't want to replace with bug
    pass

# Let's just rewrite the file fully to make sure it runs correctly
with open('core/templates/promoter_dashboard.html', 'w') as f:
    f.write(text)

print("Done generating basic promoter_dashboard.html")
