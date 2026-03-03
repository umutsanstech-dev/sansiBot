import asyncio
import random
import logging
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from typing import List, Dict, Optional, Tuple
from config import (
    BASE_URL, USERNAME, PASSWORD, BROWSER_TIMEOUT,
    ELEMENT_WAIT_TIMEOUT, PAGE_LOAD_TIMEOUT, HEADLESS, ACTION_DELAY_MIN,
    ACTION_DELAY_MAX, MAX_RETRIES, RETRY_DELAY, LIVE_COUPONS_PER_MATCH
)

logger = logging.getLogger(__name__)


class SansibotScraper:
    """Sansi site için web scraper sınıfı"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def _random_delay(self):
        """Rastgele bekleme süresi (insan benzeri davranış)"""
        delay = random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX)
        await asyncio.sleep(delay)
        
    async def _retry_action(self, action_func, *args, **kwargs):
        """Retry mekanizması ile action çalıştırma"""
        for attempt in range(MAX_RETRIES):
            try:
                return await action_func(*args, **kwargs)
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Action başarısız (deneme {attempt + 1}/{MAX_RETRIES}): {e}")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    logger.error(f"Action başarısız (tüm denemeler tükendi): {e}")
                    raise
                    
    async def init_browser(self):
        """Browser'ı başlat - Tam ekran modunda"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=HEADLESS,
                timeout=BROWSER_TIMEOUT,
                args=[
                    '--start-maximized',
                    '--start-fullscreen',
                    '--window-position=0,0',
                    '--disable-infobars',
                    '--disable-extensions',
                    '--no-first-run'
                ]
            )
            self.context = await self.browser.new_context(
                no_viewport=True,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(ELEMENT_WAIT_TIMEOUT)
            
            # Sayfa yüklendikten sonra window'u maksimize et
            # (Sayfa henüz yüklenmediği için burada yapmıyoruz, login sonrası yapacağız)
            
            logger.info("Browser tam ekran modunda başlatıldı")
        except Exception as e:
            logger.error(f"Browser başlatılamadı: {e}")
            raise
            
    async def close_browser(self):
        """Browser'ı kapat ve tüm Chromium process'lerini öldür"""
        try:
            if self.page:
                try:
                    await self.page.close()
                except:
                    pass
            if self.context:
                try:
                    await self.context.close()
                except:
                    pass
            if self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
            if self.playwright:
                try:
                    await self.playwright.stop()
                except:
                    pass
            
            # Tüm Chromium process'lerini öldür
            await self._kill_all_chromium_processes()
            
            logger.info("Browser kapatıldı ve tüm Chromium process'leri temizlendi")
        except Exception as e:
            logger.error(f"Browser kapatılırken hata: {e}")
            # Hata olsa bile Chromium process'lerini öldürmeyi dene
            try:
                await self._kill_all_chromium_processes()
            except:
                pass
    
    async def _kill_all_chromium_processes(self):
        """Tüm Chromium process'lerini öldür (macOS için)"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Chromium ve Chrome process'lerini öldür
                commands = [
                    ["pkill", "-9", "-f", "chromium"],
                    ["pkill", "-9", "-f", "chrome"],
                    ["pkill", "-9", "-f", "Chromium"],
                    ["pkill", "-9", "-f", "Chrome"],
                    ["killall", "-9", "chromium", "2>/dev/null"],
                    ["killall", "-9", "chrome", "2>/dev/null"],
                ]
            elif system == "Linux":
                commands = [
                    ["pkill", "-9", "-f", "chromium"],
                    ["pkill", "-9", "-f", "chrome"],
                ]
            elif system == "Windows":
                commands = [
                    ["taskkill", "/F", "/IM", "chromium.exe"],
                    ["taskkill", "/F", "/IM", "chrome.exe"],
                ]
            else:
                logger.warning(f"Bilinmeyen işletim sistemi: {system}")
                return
            
            for cmd in commands:
                try:
                    subprocess.run(cmd, capture_output=True, timeout=5)
                except:
                    pass
            
            logger.info("Tüm Chromium process'leri temizlendi")
        except Exception as e:
            logger.debug(f"Chromium process'leri öldürülürken hata: {e}")
            
    async def login(self) -> bool:
        """Siteye giriş yap"""
        try:
            logger.info(f"Siteye gidiliyor: {BASE_URL}")
            # Daha esnek bekleme stratejisi - önce domcontentloaded, sonra elementleri bekle
            await self.page.goto(BASE_URL, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await asyncio.sleep(0.08)
            await self._random_delay()
            
            # "Giriş Yap" butonunu bul ve tıkla
            logger.info("Giriş butonu aranıyor...")
            
            # Önce sayfanın yüklenmesini bekle
            await asyncio.sleep(0.05)
            
            # Strateji 1: CSS seçici ile span elementi (verilen elemente özel)
            login_button = None
            try:
                # Span elementi - class'lara göre
                login_button = self.page.locator('span.text-base.font-semibold.text-white:has-text("Giriş Yap")').first
                await login_button.wait_for(state="visible", timeout=5000)
                logger.info("Giriş butonu CSS seçici ile bulundu")
            except:
                try:
                    # Alternatif: Sadece text-based
                    login_button = self.page.get_by_text("Giriş Yap", exact=True).first
                    await login_button.wait_for(state="visible", timeout=5000)
                    logger.info("Giriş butonu text-based seçici ile bulundu")
                except:
                    # Son çare: Genel text arama
                    login_button = await self._retry_action(
                        lambda: self.page.get_by_text("Giriş Yap", exact=False).first
                    )
                    logger.info("Giriş butonu genel text arama ile bulundu")
            
            # Butona tıkla
            await login_button.scroll_into_view_if_needed()
            await login_button.click()
            await self._random_delay()
            
            # Kullanıcı adı ve şifre alanlarını bul
            logger.info("Giriş formu dolduruluyor...")
            
            # Kullanıcı adı alanı - placeholder'a göre bul
            try:
                username_input = self.page.locator('input[type="text"][placeholder*="Kullanıcı adınızı girin"]').first
                await username_input.wait_for(state="visible", timeout=5000)
                logger.info("Kullanıcı adı alanı bulundu")
            except:
                # Alternatif: class'lara göre
                username_input = self.page.locator('input[type="text"].bg-dark-700').first
                await username_input.wait_for(state="visible", timeout=5000)
                logger.info("Kullanıcı adı alanı alternatif yöntemle bulundu")
            
            await username_input.clear()
            await username_input.fill(USERNAME)
            await self._random_delay()
            
            # Şifre alanı - önce password type'ı dene, sonra text type'ı
            try:
                password_input = self.page.locator('input[type="password"]').first
                await password_input.wait_for(state="visible", timeout=5000)
                logger.info("Şifre alanı (password type) bulundu")
            except:
                # Alternatif: text type ama ikinci input olabilir
                try:
                    password_input = self.page.locator('input[type="text"].bg-dark-700').nth(1)  # İkinci input
                    await password_input.wait_for(state="visible", timeout=5000)
                    logger.info("Şifre alanı (text type, ikinci input) bulundu")
                except:
                    # Son çare: placeholder'a göre (eğer "Şifrenizi girin" gibi bir şey varsa)
                    password_input = await self._retry_action(
                        lambda: self.page.locator('input[type="text"], input[type="password"]').nth(1)
                    )
                    logger.info("Şifre alanı fallback yöntemle bulundu")
            
            await password_input.clear()
            await password_input.fill(PASSWORD)
            await self._random_delay()
            
            # Giriş butonunu bul ve tıkla
            logger.info("Giriş submit butonu aranıyor...")
            submit_button = None
            try:
                # Spesifik CSS seçici - type="submit" ve "Giriş Yap" metni
                submit_button = self.page.locator('button[type="submit"]:has-text("Giriş Yap")').first
                await submit_button.wait_for(state="visible", timeout=5000)
                logger.info("Giriş submit butonu spesifik seçici ile bulundu")
            except:
                try:
                    # Alternatif: Sadece type="submit" butonu
                    submit_button = self.page.locator('button[type="submit"]').first
                    await submit_button.wait_for(state="visible", timeout=5000)
                    logger.info("Giriş submit butonu type seçici ile bulundu")
                except:
                    # Son çare: Text-based
                    submit_button = await self._retry_action(
                        lambda: self.page.get_by_role("button", name="Giriş Yap", exact=True).first
                    )
                    logger.info("Giriş submit butonu text-based seçici ile bulundu")
            
            await submit_button.scroll_into_view_if_needed()
            await submit_button.click()
            
            logger.info("Giriş işlemi bekleniyor...")
            await asyncio.sleep(0.1)
            
            # "Giriş Yap" butonunun kaybolmasını bekle (giriş başarılı olduğunda kaybolur)
            try:
                login_button_check = self.page.get_by_text("Giriş Yap", exact=True).first
                # Butonun kaybolmasını bekle (maksimum 10 saniye)
                await login_button_check.wait_for(state="hidden", timeout=10000)
                logger.info("Giriş Yap butonu kayboldu - Giriş başarılı")
            except:
                # Buton hala görünüyorsa kontrol et
                try:
                    if await login_button_check.is_visible(timeout=2000):
                        logger.warning("Giriş Yap butonu hala görünüyor - Giriş başarısız olabilir")
                        # Hata mesajı var mı kontrol et
                        try:
                            error_message = self.page.locator('text=/hata|yanlış|başarısız|error/i').first
                            if await error_message.is_visible(timeout=1000):
                                error_text = await error_message.text_content()
                                logger.error(f"Giriş hatası: {error_text}")
                                return False
                        except:
                            pass
                        return False
                except:
                    # Buton bulunamadı, muhtemelen başarılı
                    logger.info("Giriş Yap butonu bulunamadı - Giriş başarılı olabilir")
            
            # Ek kontrol: URL değişti mi veya sayfa yüklendi mi?
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=3000)
            except:
                pass  # Timeout olsa bile devam et
            
            # Son kontrol: Kullanıcı adı veya profil görünüyor mu?
                await asyncio.sleep(0.05)
            current_url = self.page.url
            logger.info(f"Mevcut URL: {current_url}")
            
            # Giriş başarılı - "Giriş Yap" butonu kayboldu
            logger.info("Giriş başarılı")
            
            # Giriş sonrası browser'ı kesinlikle tam ekran yap
            try:
                # Önce JavaScript ile window'u maksimize et
                await self.page.evaluate("""
                    window.moveTo(0, 0);
                    window.resizeTo(screen.availWidth, screen.availHeight);
                """)
                await asyncio.sleep(0.05)
                
                # CDP (Chrome DevTools Protocol) ile window'u maksimize et
                try:
                    cdp = await self.page.context.new_cdp_session(self.page)
                    # Target ID'yi al
                    targets = await cdp.send('Target.getTargets')
                    if targets and 'targetInfos' in targets:
                        target_id = targets['targetInfos'][0]['targetId'] if targets['targetInfos'] else None
                        if target_id:
                            # Window bounds'u al ve maksimize et
                            await cdp.send('Browser.setWindowBounds', {
                                'windowId': 1,  # Genellikle 1
                                'bounds': {
                                    'windowState': 'maximized'
                                }
                            })
                except Exception as cdp_error:
                    logger.debug(f"CDP maksimize hatası (normal): {cdp_error}")
                
                await asyncio.sleep(0.05)
                
                # Sonra fullscreen API ile tam ekran yap
                await self.page.evaluate("""
                    if (document.documentElement.requestFullscreen) {
                        document.documentElement.requestFullscreen().catch(() => {});
                    } else if (document.documentElement.webkitRequestFullscreen) {
                        document.documentElement.webkitRequestFullscreen();
                    } else if (document.documentElement.mozRequestFullScreen) {
                        document.documentElement.mozRequestFullScreen();
                    } else if (document.documentElement.msRequestFullscreen) {
                        document.documentElement.msRequestFullscreen();
                    }
                """)
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.debug(f"Tam ekran yapma hatası (devam ediliyor): {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Giriş yapılırken hata: {e}")
            return False

    async def is_session_valid(self) -> bool:
        """Oturumun geçerli olup olmadığını kontrol et - Giriş Yap butonu görünürse geçersiz"""
        try:
            if not self.page:
                return False
            login_btn = self.page.get_by_text("Giriş Yap", exact=True).first
            visible = await login_btn.is_visible(timeout=2000)
            return not visible
        except Exception:
            return True

    async def ensure_session(self) -> bool:
        """Oturum geçersizse yeniden giriş yap"""
        if await self.is_session_valid():
            return True
        logger.warning("Oturum sonlandı tespit edildi, yeniden giriş yapılıyor...")
        try:
            await self.page.goto(BASE_URL, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            await asyncio.sleep(0.08)
            return await self.login()
        except Exception as e:
            logger.error(f"Yeniden giriş başarısız: {e}")
            return False

    async def navigate_to_category(self, category_name: str) -> bool:
        """Belirtilen kategoriye git"""
        try:
            logger.info(f"Kategoriye gidiliyor: {category_name}")
            
            category_mapping = {
                "Canlı Bülten": "Canlı",
                "Futbol": "Futbol",
                "Basketbol": "Basketbol",
                "E-Futbol": "E-Futbol",
                "Voleybol": "Voleybol",
                "Tenis": "Tenis",
                "Masa Tenisi": "Masa Tenisi",
                "Buz Hokeyi": "Buz Hokeyi",
                "Hentbol": "Hentbol",
                "Uzun Vadeli": "Uzun Vadeli"
            }
            span_text = category_mapping.get(category_name, category_name)
            
            category_span = None
            try:
                category_span = self.page.locator(f'span.font-medium.text-xs:has-text("{span_text}")').first
                await category_span.wait_for(state="visible", timeout=5000)
                logger.info(f"Kategori span bulundu (CSS seçici): {span_text}")
            except:
                try:
                    category_span = self.page.get_by_text(span_text, exact=True).first
                    await category_span.wait_for(state="visible", timeout=5000)
                    logger.info(f"Kategori span bulundu (text-based): {span_text}")
                except:
                    category_span = self.page.get_by_text(span_text, exact=False).first
                    await category_span.wait_for(state="visible", timeout=5000)
                    logger.info(f"Kategori span bulundu (genel text): {span_text}")
            
            try:
                await category_span.scroll_into_view_if_needed()
                await category_span.click()
            except:
                try:
                    parent = category_span.locator('..')
                    await parent.click()
                except:
                    parent = self.page.locator(f'xpath=//span[text()="{span_text}"]/parent::*')
                    await parent.click()
            
            await self._random_delay()
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
            except:
                await asyncio.sleep(0.08)
            
            logger.info(f"Kategoriye gidildi: {category_name}")
            return True
            
        except Exception as e:
            logger.error(f"Kategoriye gidilemedi ({category_name}): {e}")
            return False
            
    def _is_live_page(self) -> bool:
        """Sayfanın live sayfası olup olmadığını kontrol et"""
        current_url = self.page.url
        return '/live' in current_url or 'live' in current_url.lower()

    def _get_match_key(self, match: Dict) -> tuple:
        """Maç için benzersiz kimlik oluştur (tried_match_ids için)"""
        teams = match.get('teams') or []
        text = match.get('text', '')
        if teams:
            return tuple(teams)
        return (text[:80] if text else str(id(match)),)
    
    async def get_available_matches_live(self) -> List[Dict]:
        """Live sayfası için maçları bul"""
        try:
            logger.info("Live sayfasında maçlar aranıyor...")
            
            match_containers = await self.page.locator(
                'div.p-2.hover\\:bg-dark-600.transition-colors.cursor-pointer.rounded'
            ).all()
            if not match_containers:
                match_containers = await self.page.locator('div.p-2.hover\\:bg-dark-600').all()
            
            matches = []
            for container in match_containers:
                try:
                    teams = []
                    team_elements = await container.locator('span.text-white.font-bold.text-sm').all()
                    for team_elem in team_elements:
                        team_text = await team_elem.text_content()
                        if team_text and team_text.strip():
                            teams.append(team_text.strip())
                    if teams:
                        matches.append({'container': container, 'teams': teams})
                except Exception as e:
                    logger.debug(f"Maç bilgisi alınırken hata: {e}")
                    continue
            
            logger.info(f"Live sayfasında {len(matches)} maç bulundu")
            return matches
            
        except Exception as e:
            logger.error(f"Live sayfasında maçlar alınırken hata: {e}")
            return []
    
    async def get_available_matches(self) -> List[Dict]:
        """Mevcut maçları listele"""
        try:
            matches = []
            await self._random_delay()
            
            match_containers = await self.page.locator(
                'div.bg-gradient-to-br.from-dark-800.to-dark-900'
            ).all()
            
            logger.info(f"Bulunan maç container sayısı: {len(match_containers)}")
            
            for container in match_containers:
                try:
                    # Container'ın içinde maç bilgilerini kontrol et
                    container_text = await container.text_content()
                    if not container_text or len(container_text.strip()) < 20:
                        continue
                    
                    # Takım isimlerini bul - text-orange-400 class'ına sahip span'ler
                    team_spans = await container.locator('span.text-orange-400.font-medium').all()
                    teams = []
                    for team_span in team_spans[:2]:  # İlk 2 takım
                        team_text = await team_span.text_content()
                        if team_text and len(team_text.strip()) > 2:
                            teams.append(team_text.strip())
                    
                    # Maç bilgilerini topla
                    if teams or container_text:
                        matches.append({
                            'container': container,
                            'teams': teams,
                            'text': container_text.strip()[:100] if container_text else ''
                        })
                        
                except Exception as e:
                    logger.debug(f"Maç container işlenirken hata: {e}")
                    continue
            
            logger.info(f"Toplam {len(matches)} maç bulundu")
            return matches
            
        except Exception as e:
            logger.error(f"Maçlar alınırken hata: {e}")
            return []
            
    async def _random_mouse_movement(self):
        """Rastgele mouse hareketleri yap - Kaldırıldı (hız için)"""
        # Hız için mouse hareketleri kaldırıldı
        pass
    
    async def _close_live_event(self, container=None):
        """Event açıksa kapat - SADECE ESC veya container toggle. Geri butonu KATEGORİ DEĞİŞTİRİR, kullanma!"""
        try:
            # 1. ESC - en güvenli, kategori değiştirmez
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(0.03)
            logger.info("Canlı Bülten: ESC ile event kapatıldı")
        except:
            pass
        try:
            # 2. Container'a tekrar tıkla (toggle) - sadece container kullanılıyorsa
            if container:
                await container.click(timeout=2000)
                await self._random_delay()
        except Exception as e:
            logger.debug(f"Event kapatılamadı: {e}")
    
    async def _select_market_and_odds_live(self, container=None) -> bool:
        """Live sayfası için market seç ve odds'a tıkla - TEK outcome (1 buton)
        
        Canlı Bülten'de event'e tıklanınca odds butonları şu yapıda:
        button: px-2 py-1.5 rounded min-w-16 bg-gradient-to-r from-dark-600 to-dark-700
        container verilirse sadece o event içinde ara - tek outcome garantisi
        """
        try:
            # Önce tıklanan event içinde ara (container scope - TEK outcome)
            search_root = container if container else self.page
            if search_root is None:
                search_root = self.page
            
            live_odds_buttons = await search_root.locator(
                'button[class*="from-dark-600"][class*="to-dark-700"]:has(span.font-bold.text-white)'
            ).all()
            
            if live_odds_buttons:
                # Tıklanabilir olanları filtrele
                clickable_buttons = []
                for btn in live_odds_buttons:
                    try:
                        classes = await btn.get_attribute('class') or ''
                        if ('cursor-not-allowed' not in classes and 
                            'opacity-80' not in classes and 
                            'opacity-60' not in classes and
                            'bg-amber-900' not in classes and 
                            'bg-stone-900' not in classes and
                            await btn.is_visible()):
                            clickable_buttons.append(btn)
                    except:
                        continue
                
                if clickable_buttons:
                    selected = random.choice(clickable_buttons)
                    await selected.scroll_into_view_if_needed()
                    await self._random_delay()
                    await selected.click()
                    logger.info("Canlı Bülten: Özel odds butonu tıklandı (event içi)")
                    return True
            
            # Fallback: Market container üzerinden (event içinde - tek outcome)
            try:
                search_root_fb = container if container else self.page
                market_container = search_root_fb.locator(
                    'div.mt-1.border-t.border-dark-600.pt-1.animate-fadeIn'
                ).first
                await market_container.wait_for(state="visible", timeout=1000)
            except:
                logger.warning("Live market container bulunamadı")
                return False
            
            market_cards = await market_container.locator(
                'div.bg-gradient-to-br.from-dark-700.to-dark-800'
            ).all()
            
            if not market_cards:
                market_cards = await market_container.locator(
                    'div[class*="from-dark-700"][class*="to-dark-800"]'
                ).all()
            
            if not market_cards:
                return False
            
            max_attempts = min(5, len(market_cards))
            random.shuffle(market_cards)
            
            for attempt, market_card in enumerate(market_cards[:max_attempts]):
                try:
                    await market_card.scroll_into_view_if_needed()
                    odds_buttons = []
                    all_buttons = await market_card.locator('button').all()
                    
                    for btn in all_buttons:
                        try:
                            classes = await btn.get_attribute('class') or ''
                            is_clickable = (
                                'from-dark-600' in classes and 
                                'to-dark-700' in classes and 
                                'cursor-not-allowed' not in classes and
                                'opacity-80' not in classes and 
                                'opacity-60' not in classes and
                                'bg-amber-900' not in classes and
                                'bg-stone-900' not in classes
                            )
                            if is_clickable:
                                inner_div = await btn.locator('div.flex.flex-col.items-center.space-y-0\\.5').count()
                                if inner_div > 0:
                                    odds_buttons.append(btn)
                        except:
                            continue
                    
                    if odds_buttons:
                        selected_odds = random.choice(odds_buttons)
                        await selected_odds.scroll_into_view_if_needed()
                        await selected_odds.click()
                        logger.info(f"Live sayfasında odds seçildi (market container)")
                        return True
                except Exception as e:
                    logger.debug(f"Live market {attempt + 1} işlenirken hata: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Live sayfasında market ve odds seçilirken hata: {e}")
            return False
    
    async def _select_market_and_odds(self, category_name: str = "", container=None) -> bool:
        """Market seç ve odds'a tıkla - Canlı/Uzun Vadeli hariç yeni buton yapısı öncelikli.
        container verilirse sadece o maçın market panelinde ara (yanlış maça seçim eklenmesini önler)."""
        try:
            # Arama kapsamı: container varsa sadece o maçın içinde ara, yoksa sayfa genelinde
            search_root = container if container else self.page
            
            # Canlı Bülten ve Uzun Vadeli hariç: div.max-h-96.overflow-y-auto içindeki tıklanabilir butonları ara
            if category_name and category_name not in ("Canlı Bülten", "Uzun Vadeli"):
                try:
                    # Önce max-h-96 overflow-y-auto - container içinde ara (tıklanan maça özel)
                    market_area = search_root.locator('div.max-h-96.overflow-y-auto').first
                    if await market_area.is_visible(timeout=1500):
                        all_odds_btns = await market_area.locator(
                            'button[class*="from-dark-600"][class*="to-dark-700"]:has(span.font-bold.text-white)'
                        ).all()
                        clickable_btns = []
                        for btn in all_odds_btns:
                            try:
                                classes = await btn.get_attribute('class') or ''
                                if ('cursor-not-allowed' not in classes and
                                    'opacity-60' not in classes and
                                    'opacity-80' not in classes and
                                    'bg-stone-900' not in classes and
                                    'bg-gray-700' not in classes and
                                    'bg-amber-900' not in classes and
                                    await btn.is_visible()):
                                    clickable_btns.append(btn)
                            except Exception:
                                continue
                        if clickable_btns:
                            selected = random.choice(clickable_btns)
                            await selected.scroll_into_view_if_needed()
                            await self._random_delay()
                            await selected.click()
                            logger.info("Odds butonu tıklandı (max-h-96 container içi)")
                            return True
                except Exception as e:
                    logger.debug(f"max-h-96 odds butonu bulunamadı, fallback deneniyor: {e}")

            # Marketlerin açılmasını bekleme - fallback: market container ara (search_root kapsamında)
            market_container = None
            
            try:
                # Öncelik: max-h-96 overflow-y-auto (container içinde - tıklanan maça özel)
                market_container = search_root.locator('div.max-h-96.overflow-y-auto').first
                await market_container.wait_for(state="visible", timeout=1500)
                logger.info("Market container bulundu (max-h-96)")
            except:
                try:
                    # Alternatif: border-t border-dark-700/50
                    market_container = search_root.locator(
                        'div.border-t.border-dark-700\\/50.bg-dark-900\\/40.p-3'
                    ).first
                    await market_container.wait_for(state="visible", timeout=1000)
                    logger.info("Market container bulundu (border-t)")
                except:
                    logger.warning("Market container bulunamadı")
                    return False
            
            # Market kartlarını bul - from-dark-800/60 ve from-dark-800/80 dahil
            market_cards = await market_container.locator(
                'div[class*="from-dark-800"][class*="to-dark-900"]'
            ).all()
            if not market_cards:
                market_cards = await market_container.locator(
                    'div.rounded-lg[class*="border"]'
                ).all()
            if not market_cards:
                market_cards = await market_container.locator(
                    'div[class*="bg-gradient"]'
                ).all()
            if not market_cards:
                # Market kartı yoksa direkt container içinde odds butonları ara
                all_buttons = await market_container.locator(
                    'button[class*="from-dark-600"][class*="to-dark-700"]'
                ).all()
                for btn in all_buttons:
                    try:
                        classes = await btn.get_attribute('class') or ''
                        if ('cursor-not-allowed' not in classes and 'opacity-80' not in classes and
                            'bg-amber-900' not in classes and 'bg-stone-900' not in classes):
                            await btn.scroll_into_view_if_needed()
                            await btn.click()
                            logger.info("Odds butonu tıklandı (market container direkt)")
                            return True
                    except:
                        continue
                logger.warning("Market kartı ve odds butonu bulunamadı")
                return False
            
            logger.info(f"Bulunan market sayısı: {len(market_cards)}")
            
            # Tıklanabilir market bulana kadar dene (maksimum 5 deneme)
            max_attempts = min(5, len(market_cards))
            random.shuffle(market_cards)
            
            for attempt, market_card in enumerate(market_cards[:max_attempts]):
                try:
                    await market_card.scroll_into_view_if_needed()
                    # Bekleme yok - hemen devam
                    
                    # Market başlığını al (log için - sadece debug)
                    # try:
                    #     market_title = await market_card.locator('span.text-amber-300, span.text-stone-300').first.text_content()
                    #     logger.info(f"Denenen market ({attempt + 1}/{max_attempts}): {market_title}")
                    # except:
                    #     pass
                    
                    # Odds butonlarını bul - tıklanabilir olanları
                    # Doğru yapı: button içinde div.flex.flex-col.items-center.space-y-0.5
                    odds_buttons = []
                    
                    # Tüm butonları al
                    all_buttons = await market_card.locator('button').all()
                    
                    for btn in all_buttons:
                        try:
                            classes = await btn.get_attribute('class') or ''
                            
                            # Tıklanabilir buton kontrolü:
                            # - from-dark-600 to-dark-700 içermeli (tıklanabilir butonlar)
                            # - cursor-not-allowed olmamalı
                            # - opacity-80 veya opacity-60 olmamalı (kilitli/kapalı)
                            # - bg-amber-900 olmamalı (kilitli marketler)
                            # - bg-stone-900 olmamalı (kapalı marketler)
                            is_clickable = (
                                'from-dark-600' in classes and 
                                'to-dark-700' in classes and 
                                'cursor-not-allowed' not in classes and
                                'opacity-80' not in classes and 
                                'opacity-60' not in classes and
                                'bg-amber-900' not in classes and
                                'bg-stone-900' not in classes
                            )
                            
                            if is_clickable:
                                # İçinde oran gösteren span olmalı (veya flex div)
                                has_content = (
                                    await btn.locator('div.flex.flex-col.items-center.space-y-0\\.5').count() > 0 or
                                    await btn.locator('span.font-bold').count() > 0 or
                                    len((await btn.text_content() or '').strip()) > 0
                                )
                                if has_content:
                                    odds_buttons.append(btn)
                        except Exception as e:
                            logger.debug(f"Buton kontrolü sırasında hata: {e}")
                            continue
                    
                    # Eğer tıklanabilir buton bulunduysa
                    if odds_buttons:
                        # Rastgele bir odds butonu seç
                        selected_odds = random.choice(odds_buttons)
                        
                        # Odds metnini al (div.flex.flex-col içindeki span'den) - hızlı
                        # try:
                        #     odds_span = selected_odds.locator('span.font-bold.text-white').first
                        #     odds_value = await odds_span.text_content()
                        #     odds_label = await selected_odds.locator('span.text-gray-300').first.text_content()
                        #     odds_text = f"{odds_label}: {odds_value}"
                        # except:
                        #     odds_text = await selected_odds.text_content()
                        
                        await selected_odds.scroll_into_view_if_needed()
                        # Bekleme yok - hemen tıkla
                        await selected_odds.click()
                        # Bekleme yok - hemen return
                        
                        logger.info(f"Odds seçildi ve tıklandı")
                        return True
                    else:
                        logger.debug(f"Market {attempt + 1} tıklanabilir odds içermiyor, bir sonrakine geçiliyor")
                        continue
                        
                except Exception as e:
                    logger.debug(f"Market {attempt + 1} işlenirken hata: {e}")
                    continue
            
            logger.warning("Hiçbir markette tıklanabilir odds bulunamadı")
            return False
            
        except Exception as e:
            logger.error(f"Market ve odds seçilirken hata: {e}")
            return False
    
    async def _click_play_button(self) -> bool:
        """HEMEN OYNA butonuna tıkla"""
        try:
            # "HEMEN OYNA" butonunu bul
            play_button = self.page.locator(
                'button:has-text("HEMEN OYNA")'
            ).first
            
            if not await play_button.is_visible(timeout=5000):
                logger.warning("HEMEN OYNA butonu bulunamadı")
                return False
            
            await play_button.scroll_into_view_if_needed()
            # Bekleme yok - hemen tıkla
            
            # Butona tıkla - API response bekleme _check_api_response'da yapılacak
            await play_button.click()
            
            logger.info("HEMEN OYNA butonuna tıklandı")
            # Bekleme yok - hemen return
            
            return True
            
        except Exception as e:
            logger.error(f"HEMEN OYNA butonuna tıklanırken hata: {e}")
            return False
    
    async def _click_tamam_button(self) -> bool:
        """Kupon sonrası seçim onay dialogunu kapat - Tamam butonuna tıkla"""
        try:
            tamam_btn = self.page.locator('button:has-text("Tamam")').first
            if await tamam_btn.is_visible(timeout=3000):
                await tamam_btn.click()
                await self._random_delay()
                logger.info("Tamam butonuna tıklandı (seçimler temizlendi)")
                return True
        except Exception as e:
            logger.debug(f"Tamam butonu bulunamadı veya tıklanamadı: {e}")
        return False

    async def _handle_kupon_oynanamadi(self) -> bool:
        """Kupon oynanamadı hatası: Kapat butonuna tıkla, sonra Kuponu Temizle ile kuponu temizle"""
        try:
            await asyncio.sleep(0.5)
            kapat_clicked = False
            for selector in [
                'button.bg-dark-600:has-text("Kapat")',
                '[role="dialog"] button:has-text("Kapat")',
                'button.w-full.bg-dark-600',
                'button:has-text("Kapat")',
            ]:
                try:
                    kapat_btn = self.page.locator(selector).first
                    if await kapat_btn.is_visible(timeout=1500):
                        await kapat_btn.scroll_into_view_if_needed()
                        await kapat_btn.click(force=True)
                        logger.info("Kupon oynanamadı - Kapat butonuna tıklandı")
                        kapat_clicked = True
                        break
                except Exception:
                    continue
            if not kapat_clicked:
                logger.warning("Kapat butonu bulunamadı")
            await asyncio.sleep(0.2)
            clear_clicked = False
            for selector in [
                'button[title="Kuponu Temizle"]',
                'button[title*="Temizle"]',
                'button:has(svg path[d*="M3 6h18"])',
            ]:
                try:
                    clear_btn = self.page.locator(selector).first
                    if await clear_btn.is_visible(timeout=1500):
                        await clear_btn.scroll_into_view_if_needed()
                        await clear_btn.click(force=True)
                        logger.info("Kuponu Temizle butonuna tıklandı")
                        clear_clicked = True
                        break
                except Exception:
                    continue
            await asyncio.sleep(0.1)
            return kapat_clicked or clear_clicked
        except Exception as e:
            logger.warning(f"Kupon oynanamadı işlemi sırasında hata: {e}")
            return False
    
    async def _check_api_response(self) -> Tuple[bool, bool, bool]:
        """API response'unu kontrol et - (başarılı, para yatırma gerekli, oturum sonlandı)"""
        try:
            response = None
            try:
                async with self.page.expect_response(
                    lambda r: 'ticket/place' in r.url,
                    timeout=3000
                ) as response_info:
                    response = await response_info.value
            except Exception as e:
                logger.debug(f"API response bekleme timeout: {e}")
                return True, False, False

            if response:
                response_text = await response.text()
                logger.info(f"API Response Status: {response.status}")
                logger.info(f"API Response: {response_text[:300]}")

                if response.status == 200:
                    try:
                        response_json = await response.json()
                        if 'ticketId' in str(response_json) or 'id' in str(response_json):
                            logger.info("Kupon başarıyla oluşturuldu")
                            return True, False, False
                    except Exception:
                        if 'ticketId' in response_text or '"id"' in response_text:
                            logger.info("Kupon başarıyla oluşturuldu (text kontrolü)")
                            return True, False, False

                response_lower = response_text.lower()
                if response.status in (401, 403):
                    logger.warning("Oturum sonlandı (401/403) - Yeniden giriş gerekli")
                    return False, False, True
                if 'insufficient balance' in response_lower or 'account issue' in response_lower:
                    logger.warning("Yetersiz bakiye hatası - Para yatırma gerekli")
                    return False, True, False

                if response.status >= 400:
                    logger.warning(f"API hatası: {response.status} - {response_text[:200]}")
                    return False, False, False

            return True, False, False

        except Exception as e:
            logger.debug(f"API response kontrolü sırasında hata: {e}")
            return True, False, False
    
    async def _deposit_money(self) -> bool:
        """Para yatırma işlemi"""
        try:
            logger.info("Para yatırma işlemi başlatılıyor...")
            
            # 1. Kullanıcı profil butonuna tıkla - playwright_bot_user içeren buton
            try:
                profile_button = self.page.locator(
                    'button:has-text("playwright_bot_user")'
                ).first
                await profile_button.wait_for(state="visible", timeout=5000)
            except:
                # Alternatif: SVG içeren buton veya div
                profile_button = self.page.locator(
                    'button, div'
                ).filter(has_text="playwright_bot_user").first
                await profile_button.wait_for(state="visible", timeout=5000)
            
            await profile_button.scroll_into_view_if_needed()
            await asyncio.sleep(0.02)
            await profile_button.click()
            await asyncio.sleep(0.02)
            
            # 2. "Para Yatır" menü öğesine tıkla
            deposit_menu = self.page.locator(
                'button:has-text("Para Yatır")'
            ).first
            
            await deposit_menu.wait_for(state="visible", timeout=5000)
            await deposit_menu.click()
            await asyncio.sleep(0.02)
            
            # 3. Input alanına 1000 yaz - Para yatır input'u
            # Önce input'u bul, eğer yoksa form içindeki input'u bul
            try:
                amount_input = self.page.locator(
                    'input[type="number"], input[type="text"]'
                ).filter(has_not_text="").first
                await amount_input.wait_for(state="visible", timeout=5000)
            except:
                # Tüm input'ları al ve uygun olanı seç
                all_inputs = self.page.locator('input').all()
                amount_input = all_inputs[0] if all_inputs else None
                if not amount_input:
                    raise Exception("Input alanı bulunamadı")
            
            await amount_input.clear()
            await amount_input.fill("1000")
            await self._random_delay()
            
            # 4. "Para Yatır" submit butonuna tıkla
            deposit_submit = self.page.locator(
                'button[type="submit"]:has-text("Para Yatır")'
            ).first
            
            await deposit_submit.wait_for(state="visible", timeout=5000)
            await deposit_submit.click()
            await asyncio.sleep(0.1)
            
            # Para yatırdıktan sonra modal/dialog kapanabilir, sayfayı yenile veya ana sayfaya dön
            try:
                # Modal'ı kapatmak için ESC tuşuna bas veya dışarı tıkla
                await self.page.keyboard.press('Escape')
                await asyncio.sleep(0.05)
            except:
                pass
            
            # Ana sayfaya dön (kategoriye geri dönmek için)
            try:
                await self.page.goto(BASE_URL, wait_until="domcontentloaded", timeout=10000)
                await asyncio.sleep(0.08)
                logger.info("Para yatırma sonrası ana sayfaya dönüldü")
            except Exception as e:
                logger.warning(f"Ana sayfaya dönülürken hata: {e}")
            
            logger.info("Para yatırma işlemi tamamlandı")
            return True
            
        except Exception as e:
            logger.error(f"Para yatırma işlemi sırasında hata: {e}")
            return False
    
    async def create_single_coupon(self, matches: List[Dict], category_name: str, tried_match_ids: Optional[set] = None) -> Tuple[int, bool, Optional[tuple], List[tuple], List[tuple]]:
        """Tek bir kupon yap - Tüm maçları sırayla dene, market bulunamazsa sonrakine geç
        Returns: (coupons_count, needs_category_return, failed_match_key, used_match_keys, tried_no_market_keys)
        """
        try:
            if not matches:
                logger.warning("Seçilecek maç bulunamadı")
                return 0, False, None, [], []

            available = [m for m in matches if self._get_match_key(m) not in (tried_match_ids or set())]
            if not available:
                logger.warning("Tüm maçlar zaten denenmiş")
                return 0, False, None, [], []
            
            matches_to_use = available
            
            # Live sayfası kontrolü
            is_live = self._is_live_page()
            if is_live:
                coupons_count, needs_return, failed_key, used = await self._create_single_coupon_live(matches_to_use, category_name, tried_match_ids)
                return coupons_count, needs_return, failed_key, used, [], []

            # Uzun Vadeli: tüm maçları tek tek gez, her kupon 1 seçim, grid butonlarına tıkla
            if category_name == "Uzun Vadeli":
                success, needs_return, failed_key, used = await self._create_single_coupon_outright(matches_to_use, tried_match_ids)
                return (1 if success else 0), needs_return, failed_key, used, [], []
            
            # 1-2 maç varsa 3+ seçim yapılamaz - sonraki kategoriye geç
            if len(matches_to_use) < 3:
                logger.warning(f"Sadece {len(matches_to_use)} maç var, 3+ seçim için yeterli değil - sonraki kategoriye geçiliyor")
                tried = [self._get_match_key(m) for m in matches_to_use]
                return 0, False, None, [], tried
            
            # Hedef seçim sayısı (3-5 arası rastgele)
            target_selections = random.randint(3, 5)
            logger.info(f"Kupon için {len(matches_to_use)} maç sırayla deneniyor (hedef: {target_selections} seçim)")
            bets_added = 0
            used_match_keys = []
            tried_no_market_keys = []
            
            for match in matches_to_use:
                if bets_added >= target_selections:
                    break
                try:
                    container = match['container']
                    
                    await container.scroll_into_view_if_needed()
                    
                    try:
                        clickable_area = container.locator(
                            'div[class*="from-dark-700"][class*="to-dark-800"]'
                        ).first
                        await clickable_area.click()
                    except:
                        await container.click()
                    # Panel güncellenene kadar bekle (yanlış maça seçim eklenmesini önler)
                    await asyncio.sleep(0.1)
                    
                    market_success = await self._select_market_and_odds(category_name, container)
                    if not market_success:
                        logger.warning(f"Market seçilemedi, sonraki maça geçiliyor - {' vs '.join(match.get('teams', []) or ['?'])}")
                        tried_no_market_keys.append(self._get_match_key(match))
                        continue
                    
                    bets_added += 1
                    used_match_keys.append(self._get_match_key(match))
                    logger.info(f"Bahis eklendi ({bets_added}/{target_selections}) - Maç: {' vs '.join(match['teams']) if match.get('teams') else 'Bilinmiyor'}")
                    
                except Exception as e:
                    logger.warning(f"Bahis eklenirken hata: {e}")
                    tried_no_market_keys.append(self._get_match_key(match))
                    continue
            
            # En az 3 seçim yapıldıysa kuponu oluştur
            if bets_added >= 3:
                play_success = await self._click_play_button()
                if not play_success:
                    logger.warning("HEMEN OYNA butonuna tıklanamadı")
                    return 0, False, None, used_match_keys, tried_no_market_keys
                
                # API response kontrolü (tıklamadan sonra) - kısa timeout
                success, needs_deposit, session_expired = await self._check_api_response()

                if session_expired:
                    await self.ensure_session()
                    return 0, True, None, used_match_keys, tried_no_market_keys
                if needs_deposit:
                    logger.info("Para yatırma gerekiyor, işlem başlatılıyor...")
                    deposit_success = await self._deposit_money()
                    if deposit_success:
                        logger.info("Para yatırıldı, kategoriye geri dönülecek")
                        return 0, True, None, used_match_keys, tried_no_market_keys

                if success:
                    logger.info(f"Kupon başarıyla oluşturuldu ({bets_added} bahis)")
                    await asyncio.sleep(0.05)
                    await self._click_tamam_button()
                else:
                    logger.warning("Kupon oluşturulamadı - Kapat ve Kuponu Temizle işlemi yapılıyor")
                    await self._handle_kupon_oynanamadi()
                
                return 1 if success else 0, False, None, used_match_keys, tried_no_market_keys
            elif bets_added > 0:
                logger.warning(f"Yetersiz seçim ({bets_added}/3) - 3+ seçim için yeterli maç yok, sonraki kategoriye geçiliyor")
                tried_no_market_keys.extend(used_match_keys)
                return 0, False, None, used_match_keys, tried_no_market_keys
            else:
                logger.warning(f"Tüm {len(matches_to_use)} maç denendi, hiçbirinde market bulunamadı - sonraki kategoriye geçiliyor")
                return 0, False, None, [], tried_no_market_keys

        except Exception as e:
            logger.error(f"Kupon oluşturulurken hata: {e}")
            return 0, False, None, [], []
    
    async def _create_single_coupon_live(self, matches: List[Dict], category_name: str, tried_match_ids: set = None) -> Tuple[int, bool, Optional[tuple], List[tuple]]:
        """Live sayfası: Market bulunan her maçtan LIVE_COUPONS_PER_MATCH (10) adet kupon yap - her kupon 1 seçim"""
        try:
            if not matches:
                logger.warning("Live sayfasında seçilecek maç bulunamadı")
                return 0, False, None, []

            available = [m for m in matches if self._get_match_key(m) not in (tried_match_ids or set())]
            if not available:
                logger.warning("Live: Tüm maçlar denenmiş")
                return 0, False, None, []

            for match in available:
                coupons_count, needs_return, failed_key = await self._place_coupons_from_match_live(match)
                if needs_return:
                    return coupons_count, True, None, []
                if coupons_count > 0:
                    return coupons_count, False, None, [self._get_match_key(match)]
                if failed_key:
                    pass
                await self._close_live_event(match.get('container'))
                await asyncio.sleep(0.05)

            logger.warning("Live: Tüm maçlar denendi, hiçbirinde bahis yapılamadı")
            return 0, False, None, []

        except Exception as e:
            logger.error(f"Live sayfasında kupon oluşturulurken hata: {e}")
            return 0, False, None, []

    async def _place_coupons_from_match_live(self, match: Dict) -> Tuple[int, bool, Optional[tuple]]:
        """Live: Bir maçta market bulunursa 10 adet tek seçimli kupon yap.
        Returns: (coupons_count, needs_return, failed_key)
        """
        try:
            container = match['container']
            await container.scroll_into_view_if_needed()
            await container.click()
            await asyncio.sleep(0.05)

            market_success = await self._select_market_and_odds_live(container)
            if not market_success:
                return 0, False, self._get_match_key(match)

            coupons_count = 0
            for i in range(LIVE_COUPONS_PER_MATCH):
                if i > 0:
                    market_success = await self._select_market_and_odds_live(container)
                    if not market_success:
                        break

                play_success = await self._click_play_button()
                if not play_success:
                    break

                success, needs_deposit, session_expired = await self._check_api_response()

                if session_expired:
                    await self.ensure_session()
                    return coupons_count, True, None
                if needs_deposit:
                    deposit_success = await self._deposit_money()
                    if deposit_success:
                        return coupons_count, True, None
                    break

                if success:
                    coupons_count += 1
                    await asyncio.sleep(0.05)
                    await self._click_tamam_button()
                else:
                    await self._handle_kupon_oynanamadi()

            return coupons_count, False, None

        except Exception as e:
            logger.warning(f"Live sayfasında kupon yapılırken hata: {e}")
            return 0, False, None
    
    async def _create_single_coupon_outright(self, matches: List[Dict], tried_match_ids: set = None) -> Tuple[bool, bool, Optional[tuple], List[tuple]]:
        """Uzun Vadeli için tek kupon - TEK seçim, tüm maçları sırayla gez, grid butonlarına tıkla"""
        try:
            if not matches:
                return False, False, None, []
            
            available = [m for m in matches if self._get_match_key(m) not in (tried_match_ids or set())]
            if not available:
                logger.warning("Uzun Vadeli: Tüm maçlar denenmiş")
                return False, False, None, []
            
            match = available[0]
            container = match['container']
            
            await container.scroll_into_view_if_needed()
            try:
                clickable_area = container.locator('div[class*="from-dark-700"][class*="to-dark-800"]').first
                await clickable_area.click()
            except:
                await container.click()
            await asyncio.sleep(0.1)
            
            # div.grid.grid-cols-3.gap-2.mb-2 içindeki butonlara tıkla (önce container içinde, sonra sayfa)
            grid = container.locator('div.grid.grid-cols-3.gap-2.mb-2').first
            try:
                if not await grid.is_visible(timeout=1500):
                    grid = self.page.locator('div.grid.grid-cols-3.gap-2.mb-2').first
            except:
                grid = self.page.locator('div.grid.grid-cols-3.gap-2.mb-2').first
            if not await grid.is_visible(timeout=2000):
                grid = self.page.locator('div.grid[class*="grid-cols-3"]').first
            
            btns = await grid.locator(
                'button[class*="from-dark-600"][class*="to-dark-700"]:has(span.font-bold.text-white)'
            ).all()
            
            clickable = []
            for btn in btns:
                try:
                    classes = await btn.get_attribute('class') or ''
                    if 'cursor-not-allowed' not in classes and 'opacity-60' not in classes and 'opacity-80' not in classes:
                        if await btn.is_visible():
                            clickable.append(btn)
                except:
                    continue
            
            if not clickable:
                logger.warning("Uzun Vadeli: Tıklanabilir oran butonu bulunamadı")
                return False, False, self._get_match_key(match), []
            
            selected = random.choice(clickable)
            await selected.scroll_into_view_if_needed()
            await self._random_delay()
            await selected.click()
            logger.info("Uzun Vadeli: Oran butonu tıklandı")
            
            play_success = await self._click_play_button()
            if not play_success:
                return False, False, None, []
            
            success, needs_deposit, session_expired = await self._check_api_response()
            if session_expired:
                await self.ensure_session()
                return False, True, None, []
            if needs_deposit:
                deposit_success = await self._deposit_money()
                if deposit_success:
                    return False, True, None, []

            if success:
                await asyncio.sleep(0.05)
                await self._click_tamam_button()
            else:
                await self._handle_kupon_oynanamadi()

            used = [self._get_match_key(match)] if success else []
            return success, False, None, used

        except Exception as e:
            logger.error(f"Uzun Vadeli kupon oluşturulurken hata: {e}")
            return False, False, None, []
    
    async def _place_bet_from_match(self, match: Dict, category_name: str) -> Tuple[bool, bool, Optional[tuple]]:
        """Tek bir maçtan bahis yap - Helper fonksiyon
        Returns: (success, needs_category_return, failed_match_key)
        """
        try:
            container = match['container']
            
            # Maça tıkla - hızlı
            await container.scroll_into_view_if_needed()
            
            # Maç container'ının tıklanabilir kısmına tıkla
            clickable_area = container.locator(
                'div[class*="from-dark-700"][class*="to-dark-800"]'
            ).first
            
            await clickable_area.click()
            await asyncio.sleep(0.1)
            
            # Market seç ve odds'a tıkla - container ile maça özel panel
            market_success = await self._select_market_and_odds(category_name, container)
            if not market_success:
                logger.warning("Market seçilemedi")
                return False, False, self._get_match_key(match)
            
            # HEMEN OYNA butonuna tıkla - hemen
            play_success = await self._click_play_button()
            if not play_success:
                logger.warning("HEMEN OYNA butonuna tıklanamadı")
                return False, False, None
            
            # API response kontrolü
            success, needs_deposit, session_expired = await self._check_api_response()

            if session_expired:
                await self.ensure_session()
                return False, True, None
            if needs_deposit:
                logger.info("Para yatırma gerekiyor, işlem başlatılıyor...")
                deposit_success = await self._deposit_money()
                if deposit_success:
                    logger.info("Para yatırıldı, kategoriye geri dönülecek")
                    return False, True, None
            if not success:
                await self._handle_kupon_oynanamadi()

            return success, False, None

        except Exception as e:
            logger.warning(f"Bahis yapılırken hata: {e}")
            return False, False, None
    
    async def select_random_bets(self, matches: List[Dict], count: int) -> int:
        """Rastgele bahisler seç - Eski fonksiyon (artık kullanılmıyor, create_single_coupon kullanılıyor)"""
        try:
            if not matches:
                logger.warning("Seçilecek maç bulunamadı")
                return 0
                
            selected_count = 0
            selected_matches = random.sample(matches, min(count, len(matches)))
            
            for match in selected_matches:
                try:
                    container = match['container']
                    
                    # Maça tıkla - hızlı
                    await container.scroll_into_view_if_needed()
                    # Bekleme yok
                    
                    # Maç container'ının tıklanabilir kısmına tıkla
                    # CSS'te / karakteri için farklı seçici kullan
                    clickable_area = container.locator(
                        'div[class*="from-dark-700"][class*="to-dark-800"]'
                    ).first
                    
                    await clickable_area.click()
                    await asyncio.sleep(0.08)
                    
                    # Market seç ve odds'a tıkla - container ile maça özel panel
                    market_success = await self._select_market_and_odds(category_name="", container=container)
                    if not market_success:
                        logger.warning("Market seçilemedi, başka maça geçiliyor")
                        continue
                    
                    # HEMEN OYNA butonuna tıkla - hemen
                    play_success = await self._click_play_button()
                    if not play_success:
                        logger.warning("HEMEN OYNA butonuna tıklanamadı")
                        continue
                    
                    # API response kontrolü (tıklamadan sonra) - kısa timeout
                    success, needs_deposit, session_expired = await self._check_api_response()

                    if session_expired:
                        await self.ensure_session()
                        return False, True
                    if needs_deposit:
                        # Para yatır
                        logger.info("Para yatırma gerekiyor, işlem başlatılıyor...")
                        deposit_success = await self._deposit_money()
                        if deposit_success:
                            # Para yatırdıktan sonra kategoriye geri dön
                            logger.info("Para yatırıldı, kategoriye geri dönülüyor...")
                            # Kategoriye geri dönme işlemi çağıran fonksiyonda yapılacak
                            # Burada sadece False döndür, böylece üst seviye kategoriye geri dönebilir
                            return False, True  # (success, needs_category_return)
                    
                    if success:
                        selected_count += 1
                        logger.info(f"Bahis başarıyla seçildi (Maç: {' vs '.join(match['teams']) if match['teams'] else 'Bilinmiyor'})")
                    else:
                        logger.warning("Bahis seçimi başarısız - Kupon temizleniyor")
                        await self._handle_kupon_oynanamadi()
                    
                    # Bekleme yok - hemen bir sonraki maça geç
                    
                except Exception as e:
                    logger.warning(f"Bahis seçilirken hata: {e}")
                    continue
            
            logger.info(f"Toplam {selected_count} bahis seçildi")
            return selected_count
            
        except Exception as e:
            logger.error(f"Rastgele bahis seçilirken hata: {e}")
            return 0
            
    async def confirm_bet_slip(self) -> bool:
        """Kuponu onayla - Artık HEMEN OYNA butonu ile yapılıyor, bu fonksiyon boş"""
        # Artık bahis seçimi sırasında "HEMEN OYNA" butonuna tıklanıyor
        # Bu fonksiyon eski akış için kalmış, şimdilik True döndürüyoruz
        logger.info("Kupon onayı select_random_bets içinde yapılıyor")
        return True
