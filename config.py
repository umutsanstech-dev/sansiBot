BASE_URL = "https://test-sansi.sanstech.dev"
LOGIN_URL = f"{BASE_URL}/login"

# Kullanıcı bilgileri
USERNAME = "playwright_bot_user"
PASSWORD = "Password123!!"

# Kupon yapma ayarları
BETS_PER_CATEGORY_MIN = 2  # Her kategoriden minimum bahis sayısı
BETS_PER_CATEGORY_MAX = 10  # Her kategoriden maksimum bahis sayısı
LIVE_COUPONS_PER_MATCH = 10  # Canlı Bülten'de market bulunduğunda aynı maçtan yapılacak kupon sayısı

# Spor kategorileri
CATEGORIES = [
    "Canlı Bülten",
    "Futbol",
    "Basketbol",
    "E-Futbol",
    "Voleybol",
    "Tenis",
    "Masa Tenisi",
    "Buz Hokeyi",
    "Hentbol",
    "Uzun Vadeli"
]

# Playwright ayarları
BROWSER_TIMEOUT = 60000  # 60 saniye (milisaniye)
ELEMENT_WAIT_TIMEOUT = 30000  # 30 saniye (milisaniye)
PAGE_LOAD_TIMEOUT = 60000  # 60 saniye (milisaniye)
HEADLESS = False  # Browser'ı görünür modda çalıştır (True yaparsanız arka planda çalışır)

# Bekleme süreleri (minimum - maksimum hız)
ACTION_DELAY_MIN = 0.02  # Minimum bekleme (saniye)
ACTION_DELAY_MAX = 0.06  # Maksimum bekleme (saniye)

# Retry ayarları
MAX_RETRIES = 3
RETRY_DELAY = 0.4  # Retry arası (saniye)
