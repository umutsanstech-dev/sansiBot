BASE_URL = "https://test-sansi.sanstech.dev"
LOGIN_URL = f"{BASE_URL}/login"

# Kullanıcı bilgileri
USERNAME = "playwright_bot_user2"
PASSWORD = "Password123!!"

# Kupon yapma ayarları
BETS_PER_CATEGORY_MIN = 2  # Her kategoriden minimum bahis sayısı
BETS_PER_CATEGORY_MAX = 10  # Her kategoriden maksimum bahis sayısı

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

# Bekleme süreleri (%35 hızlandırılmış)
ACTION_DELAY_MIN = 0.33  # Minimum bekleme süresi (saniye)
ACTION_DELAY_MAX = 0.65  # Maksimum bekleme süresi (saniye)

# Retry ayarları
MAX_RETRIES = 3  # Maksimum deneme sayısı
RETRY_DELAY = 2  # Retry arası bekleme süresi (saniye)
