"""
Localized SEO metadata for corridor and country pages.
Each corridor has titles/descriptions in the relevant local languages.
"""

# Map: corridor -> {lang_code: {title, description}}
CORRIDOR_SEO = {
    "USD-MXN": {
        "en": {"title": "Send USD to MXN — Cheapest Routes Today", "desc": "Compare 20+ providers to send money from USA to Mexico. Real-time rates, no fees."},
        "es": {"title": "Enviar dólares a México — Las rutas más baratas hoy", "desc": "Compara 20+ proveedores para enviar dinero de EE.UU. a México. Tasas en tiempo real, sin comisiones."},
    },
    "USD-INR": {
        "en": {"title": "Send USD to INR — Cheapest Routes Today", "desc": "Compare providers to send money from USA to India."},
        "hi": {"title": "USD से INR भेजें — आज की सबसे सस्ती दरें", "desc": "अमेरिका से भारत पैसे भेजने के लिए 20+ प्रोवाइडर की तुलना करें।"},
    },
    "USD-PHP": {
        "en": {"title": "Send USD to PHP — Cheapest Routes Today", "desc": "Compare providers to send money from USA to Philippines."},
        "tl": {"title": "Magpadala ng USD sa PHP — Pinakamurang Paraan Ngayon", "desc": "Ihambing ang 20+ provider para magpadala ng pera mula USA papuntang Pilipinas."},
    },
    "USD-NGN": {
        "en": {"title": "Send USD to NGN — Cheapest Routes Today", "desc": "Compare providers to send money from USA to Nigeria."},
    },
    "USD-BRL": {
        "en": {"title": "Send USD to BRL — Cheapest Routes Today", "desc": "Compare providers to send money from USA to Brazil."},
        "pt": {"title": "Enviar dólares para o Brasil — Rotas mais baratas hoje", "desc": "Compare 20+ provedores para enviar dinheiro dos EUA para o Brasil."},
    },
    "USD-COP": {
        "en": {"title": "Send USD to COP — Cheapest Routes Today", "desc": "Compare providers to send money to Colombia."},
        "es": {"title": "Enviar dólares a Colombia — Las rutas más baratas", "desc": "Compara proveedores para enviar dinero a Colombia."},
    },
    "USD-PKR": {
        "en": {"title": "Send USD to PKR — Cheapest Routes Today", "desc": "Compare providers to send money to Pakistan."},
        "ur": {"title": "USD سے PKR بھیجیں — آج کی سب سے سستی شرحیں", "desc": "پاکستان پیسے بھیجنے کے لیے 20+ فراہم کنندگان کا موازنہ کریں۔"},
    },
    "USD-BDT": {
        "en": {"title": "Send USD to BDT — Cheapest Routes Today", "desc": "Compare providers to send money to Bangladesh."},
        "bn": {"title": "USD থেকে BDT পাঠান — আজকের সবচেয়ে সস্তা রুট", "desc": "বাংলাদেশে টাকা পাঠাতে 20+ প্রোভাইডারের তুলনা করুন।"},
    },
    "USD-KES": {
        "en": {"title": "Send USD to KES — Cheapest Routes Today", "desc": "Compare providers to send money to Kenya. M-Pesa and bank routes."},
        "sw": {"title": "Tuma USD hadi KES — Njia za bei nafuu zaidi leo", "desc": "Linganisha watoa huduma 20+ kutuma pesa Kenya."},
    },
    "USD-GHS": {
        "en": {"title": "Send USD to GHS — Cheapest Routes Today", "desc": "Compare providers to send money to Ghana."},
    },
    "EUR-MXN": {
        "en": {"title": "Send EUR to MXN — Cheapest Routes", "desc": "Compare providers to send euros to Mexico."},
        "es": {"title": "Enviar euros a México — Las rutas más baratas", "desc": "Compara proveedores para enviar euros a México."},
    },
    "EUR-NGN": {
        "en": {"title": "Send EUR to NGN — Cheapest Routes", "desc": "Compare providers to send euros to Nigeria."},
    },
    "EUR-PHP": {
        "en": {"title": "Send EUR to PHP — Cheapest Routes", "desc": "Compare providers to send euros to Philippines."},
    },
    "EUR-INR": {
        "en": {"title": "Send EUR to INR — Cheapest Routes", "desc": "Compare providers to send euros to India."},
        "hi": {"title": "EUR से INR भेजें — सबसे सस्ती दरें", "desc": "यूरोप से भारत पैसे भेजने की तुलना।"},
    },
    "EUR-TRY": {
        "en": {"title": "Send EUR to TRY — Cheapest Routes", "desc": "Compare providers to send euros to Turkey."},
        "tr": {"title": "EUR'dan TRY'ye gönder — En ucuz yollar", "desc": "Avrupa'dan Türkiye'ye para göndermek için 20+ sağlayıcıyı karşılaştırın."},
    },
    "GBP-INR": {
        "en": {"title": "Send GBP to INR — Cheapest Routes", "desc": "Compare providers to send pounds to India."},
        "hi": {"title": "GBP से INR भेजें — सबसे सस्ती दरें", "desc": "UK से भारत पैसे भेजने की तुलना।"},
    },
    "GBP-PHP": {
        "en": {"title": "Send GBP to PHP — Cheapest Routes", "desc": "Compare providers to send pounds to Philippines."},
    },
    "GBP-NGN": {
        "en": {"title": "Send GBP to NGN — Cheapest Routes", "desc": "Compare providers to send pounds to Nigeria."},
    },
    "GBP-PKR": {
        "en": {"title": "Send GBP to PKR — Cheapest Routes", "desc": "Compare providers to send pounds to Pakistan."},
        "ur": {"title": "GBP سے PKR بھیجیں — سب سے سستی شرحیں", "desc": "UK سے پاکستان پیسے بھیجنے کا موازنہ۔"},
    },
    "AED-INR": {
        "en": {"title": "Send AED to INR — Cheapest Routes", "desc": "Compare providers to send dirhams to India from UAE."},
        "hi": {"title": "AED से INR भेजें — UAE से भारत", "desc": "UAE से भारत पैसे भेजने के लिए सबसे सस्ते तरीके।"},
    },
    "AED-PHP": {
        "en": {"title": "Send AED to PHP — Cheapest Routes", "desc": "Compare providers to send dirhams to Philippines from UAE."},
    },
    "AED-PKR": {
        "en": {"title": "Send AED to PKR — Cheapest Routes", "desc": "Compare providers to send dirhams to Pakistan from UAE."},
        "ur": {"title": "AED سے PKR بھیجیں — UAE سے پاکستان", "desc": "UAE سے پاکستان پیسے بھیجنے کا موازنہ۔"},
    },
    "CAD-PHP": {
        "en": {"title": "Send CAD to PHP — Cheapest Routes", "desc": "Compare providers to send Canadian dollars to Philippines."},
    },
    "CAD-INR": {
        "en": {"title": "Send CAD to INR — Cheapest Routes", "desc": "Compare providers to send Canadian dollars to India."},
    },
    "MXN-USD": {
        "en": {"title": "Send MXN to USD — Cheapest Routes", "desc": "Compare providers to send pesos to USA."},
        "es": {"title": "Enviar pesos a dólares — Las rutas más baratas", "desc": "Compara proveedores para enviar pesos mexicanos a EE.UU."},
    },
    "BRL-USD": {
        "en": {"title": "Send BRL to USD — Cheapest Routes", "desc": "Compare providers to send reais to USA."},
        "pt": {"title": "Enviar reais para dólares — Rotas mais baratas", "desc": "Compare provedores para enviar reais para os EUA."},
    },
    "PHP-USD": {
        "en": {"title": "Send PHP to USD — Cheapest Routes", "desc": "Send money from Philippines to USA."},
    },
    "INR-USD": {
        "en": {"title": "Send INR to USD — Cheapest Routes", "desc": "Send money from India to USA."},
    },
    "NGN-USD": {
        "en": {"title": "Send NGN to USD — Cheapest Routes", "desc": "Send money from Nigeria to USA."},
    },
    "KES-USD": {
        "en": {"title": "Send KES to USD — Cheapest Routes", "desc": "Send money from Kenya to USA."},
    },
    "USD-PYG": {
        "en": {"title": "Send USD to Paraguay (PYG) — Cheapest Routes", "desc": "Compare providers to send money from USA to Paraguay."},
        "es": {"title": "Enviar dólares a Paraguay — Rutas más baratas", "desc": "Compara proveedores para enviar dinero de EE.UU. a Paraguay."},
    },
    "USD-UYU": {
        "en": {"title": "Send USD to Uruguay (UYU) — Cheapest Routes", "desc": "Compare providers to send money from USA to Uruguay."},
        "es": {"title": "Enviar dólares a Uruguay — Rutas más baratas", "desc": "Compara proveedores para enviar dinero de EE.UU. a Uruguay."},
    },
    "PYG-USD": {
        "en": {"title": "Send PYG to USD — Cheapest Routes from Paraguay", "desc": "Compare providers to send money from Paraguay to USA."},
        "es": {"title": "Enviar guaraníes a dólares — Rutas más baratas", "desc": "Compara proveedores para enviar dinero de Paraguay a EE.UU."},
    },
    "UYU-USD": {
        "en": {"title": "Send UYU to USD — Cheapest Routes from Uruguay", "desc": "Compare providers to send money from Uruguay to USA."},
        "es": {"title": "Enviar pesos uruguayos a dólares — Rutas más baratas", "desc": "Compara proveedores para enviar dinero de Uruguay a EE.UU."},
    },
}

# Map: country slug -> {name, currencies, languages, flag}
COUNTRY_SEO = {
    "mexico": {"name": "Mexico", "flag": "🇲🇽", "currencies": ["MXN"], "lang": "es",
        "title_en": "Send Money to Mexico — Compare All Routes", "title_local": "Enviar dinero a México — Compara todas las rutas",
        "desc_en": "Find the cheapest way to send money to Mexico. Compare Wise, Remitly, Western Union and 20+ more.", "desc_local": "Encuentra la forma más barata de enviar dinero a México."},
    "india": {"name": "India", "flag": "🇮🇳", "currencies": ["INR"], "lang": "hi",
        "title_en": "Send Money to India — Compare All Routes", "title_local": "भारत में पैसे भेजें — सभी रास्तों की तुलना करें",
        "desc_en": "Find the cheapest way to send money to India.", "desc_local": "भारत में पैसे भेजने का सबसे सस्ता तरीका खोजें।"},
    "philippines": {"name": "Philippines", "flag": "🇵🇭", "currencies": ["PHP"], "lang": "tl",
        "title_en": "Send Money to Philippines — Compare All Routes", "title_local": "Magpadala ng Pera sa Pilipinas — Ihambing Lahat ng Paraan",
        "desc_en": "Find the cheapest way to send money to Philippines.", "desc_local": "Hanapin ang pinakamurang paraan ng pagpapadala ng pera sa Pilipinas."},
    "nigeria": {"name": "Nigeria", "flag": "🇳🇬", "currencies": ["NGN"], "lang": "en",
        "title_en": "Send Money to Nigeria — Compare All Routes", "title_local": "Send Money to Nigeria — Compare All Routes",
        "desc_en": "Find the cheapest way to send money to Nigeria.", "desc_local": "Find the cheapest way to send money to Nigeria."},
    "brazil": {"name": "Brazil", "flag": "🇧🇷", "currencies": ["BRL"], "lang": "pt",
        "title_en": "Send Money to Brazil — Compare All Routes", "title_local": "Enviar Dinheiro para o Brasil — Compare Todas as Rotas",
        "desc_en": "Find the cheapest way to send money to Brazil.", "desc_local": "Encontre a forma mais barata de enviar dinheiro para o Brasil."},
    "colombia": {"name": "Colombia", "flag": "🇨🇴", "currencies": ["COP"], "lang": "es",
        "title_en": "Send Money to Colombia — Compare All Routes", "title_local": "Enviar Dinero a Colombia — Compara Todas las Rutas",
        "desc_en": "Find the cheapest way to send money to Colombia.", "desc_local": "Encuentra la forma más barata de enviar dinero a Colombia."},
    "pakistan": {"name": "Pakistan", "flag": "🇵🇰", "currencies": ["PKR"], "lang": "ur",
        "title_en": "Send Money to Pakistan — Compare All Routes", "title_local": "پاکستان پیسے بھیجیں — تمام راستوں کا موازنہ",
        "desc_en": "Find the cheapest way to send money to Pakistan.", "desc_local": "پاکستان پیسے بھیجنے کا سب سے سستا طریقہ تلاش کریں۔"},
    "bangladesh": {"name": "Bangladesh", "flag": "🇧🇩", "currencies": ["BDT"], "lang": "bn",
        "title_en": "Send Money to Bangladesh — Compare All Routes", "title_local": "বাংলাদেশে টাকা পাঠান — সব রুটের তুলনা",
        "desc_en": "Find the cheapest way to send money to Bangladesh.", "desc_local": "বাংলাদেশে টাকা পাঠানোর সবচেয়ে সস্তা উপায় খুঁজুন।"},
    "kenya": {"name": "Kenya", "flag": "🇰🇪", "currencies": ["KES"], "lang": "sw",
        "title_en": "Send Money to Kenya — Compare All Routes", "title_local": "Tuma Pesa Kenya — Linganisha Njia Zote",
        "desc_en": "Find the cheapest way to send money to Kenya.", "desc_local": "Pata njia ya bei nafuu zaidi ya kutuma pesa Kenya."},
    "ghana": {"name": "Ghana", "flag": "🇬🇭", "currencies": ["GHS"], "lang": "en",
        "title_en": "Send Money to Ghana — Compare All Routes", "title_local": "Send Money to Ghana — Compare All Routes",
        "desc_en": "Find the cheapest way to send money to Ghana.", "desc_local": "Find the cheapest way to send money to Ghana."},
    "turkey": {"name": "Turkey", "flag": "🇹🇷", "currencies": ["TRY"], "lang": "tr",
        "title_en": "Send Money to Turkey — Compare All Routes", "title_local": "Türkiye'ye Para Gönder — Tüm Yolları Karşılaştır",
        "desc_en": "Find the cheapest way to send money to Turkey.", "desc_local": "Türkiye'ye para göndermenin en ucuz yolunu bulun."},
    "argentina": {"name": "Argentina", "flag": "🇦🇷", "currencies": ["ARS"], "lang": "es",
        "title_en": "Send Money to Argentina — Compare All Routes", "title_local": "Enviar Dinero a Argentina — Compará Todas las Rutas",
        "desc_en": "Find the cheapest way to send money to Argentina. Blue dollar rates included.", "desc_local": "Encontrá la forma más barata de enviar dinero a Argentina. Incluye cotización dólar blue."},
    "uk": {"name": "United Kingdom", "flag": "🇬🇧", "currencies": ["GBP"], "lang": "en",
        "title_en": "Send Money from UK — Compare All Routes", "title_local": "Send Money from UK — Compare All Routes",
        "desc_en": "Compare providers to send money from the UK.", "desc_local": "Compare providers to send money from the UK."},
    "usa": {"name": "United States", "flag": "🇺🇸", "currencies": ["USD"], "lang": "en",
        "title_en": "Send Money from USA — Compare All Routes", "title_local": "Send Money from USA — Compare All Routes",
        "desc_en": "Compare providers to send money from the US.", "desc_local": "Compare providers to send money from the US."},
    "canada": {"name": "Canada", "flag": "🇨🇦", "currencies": ["CAD"], "lang": "en",
        "title_en": "Send Money from Canada — Compare All Routes", "title_local": "Send Money from Canada — Compare All Routes",
        "desc_en": "Compare providers to send money from Canada.", "desc_local": "Compare providers to send money from Canada."},
    "uae": {"name": "UAE", "flag": "🇦🇪", "currencies": ["AED"], "lang": "ar",
        "title_en": "Send Money from UAE — Compare All Routes", "title_local": "أرسل المال من الإمارات — قارن جميع الطرق",
        "desc_en": "Compare providers to send money from UAE.", "desc_local": "قارن مقدمي الخدمات لإرسال الأموال من الإمارات."},
    "germany": {"name": "Germany", "flag": "🇩🇪", "currencies": ["EUR"], "lang": "de",
        "title_en": "Send Money from Germany — Compare All Routes", "title_local": "Geld senden aus Deutschland — Alle Wege vergleichen",
        "desc_en": "Compare providers to send money from Germany.", "desc_local": "Vergleichen Sie Anbieter für Geldtransfers aus Deutschland."},
    "france": {"name": "France", "flag": "🇫🇷", "currencies": ["EUR"], "lang": "fr",
        "title_en": "Send Money from France — Compare All Routes", "title_local": "Envoyer de l'argent depuis la France — Comparer toutes les options",
        "desc_en": "Compare providers to send money from France.", "desc_local": "Comparez les fournisseurs pour envoyer de l'argent depuis la France."},
    "japan": {"name": "Japan", "flag": "🇯🇵", "currencies": ["JPY"], "lang": "ja",
        "title_en": "Send Money from Japan — Compare All Routes", "title_local": "日本から送金 — すべてのルートを比較",
        "desc_en": "Compare providers to send money from Japan.", "desc_local": "日本からの送金プロバイダーを比較。"},
    "south-africa": {"name": "South Africa", "flag": "🇿🇦", "currencies": ["ZAR"], "lang": "en",
        "title_en": "Send Money from South Africa — Compare All Routes", "title_local": "Send Money from South Africa — Compare All Routes",
        "desc_en": "Compare providers to send money from South Africa.", "desc_local": "Compare providers to send money from South Africa."},
    "paraguay": {"name": "Paraguay", "flag": "🇵🇾", "currencies": ["PYG"], "lang": "es",
        "title_en": "Send Money to Paraguay — Best Rates", "title_local": "Enviar dinero a Paraguay — Mejores tasas",
        "desc_en": "Compare the cheapest ways to send money to Paraguay. Real-time rates from 30+ providers.", "desc_local": "Compara las formas más baratas de enviar dinero a Paraguay. Tasas en tiempo real de 30+ proveedores."},
    "uruguay": {"name": "Uruguay", "flag": "🇺🇾", "currencies": ["UYU"], "lang": "es",
        "title_en": "Send Money to Uruguay — Best Rates", "title_local": "Enviar dinero a Uruguay — Mejores tasas",
        "desc_en": "Compare the cheapest ways to send money to Uruguay. Real-time rates from 30+ providers.", "desc_local": "Compara las formas más baratas de enviar dinero a Uruguay. Tasas en tiempo real de 30+ proveedores."},
}
