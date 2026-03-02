"""
Ana bot sınıfı - Tüm işlemleri koordine eder
"""

import asyncio
import random
import logging
from typing import List
from scraper import SansibotScraper
from config import (
    CATEGORIES, BETS_PER_CATEGORY_MIN, BETS_PER_CATEGORY_MAX,
    ACTION_DELAY_MIN, ACTION_DELAY_MAX
)

logger = logging.getLogger(__name__)


class Sansibot:
    """Sansi bot ana sınıfı"""
    
    def __init__(self):
        self.scraper = SansibotScraper()
        self.is_running = False
        
    async def _random_delay(self):
        """Rastgele bekleme süresi"""
        delay = random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX)
        await asyncio.sleep(delay)
        
    async def initialize(self) -> bool:
        """Bot'u başlat"""
        try:
            logger.info("Bot başlatılıyor...")
            await self.scraper.init_browser()
            await self._random_delay()
            
            # Giriş yap
            login_success = await self.scraper.login()
            if not login_success:
                logger.error("Giriş başarısız - Bot durduruluyor")
                return False
            
            self.is_running = True
            logger.info("Bot başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logger.error(f"Bot başlatılırken hata: {e}")
            return False
            
    async def shutdown(self):
        """Bot'u durdur ve tüm Chromium process'lerini öldür"""
        try:
            logger.info("Bot durduruluyor...")
            self.is_running = False
            await self.scraper.close_browser()  # Bu fonksiyon zaten Chromium process'lerini öldürüyor
            logger.info("Bot durduruldu ve tüm Chromium process'leri temizlendi")
        except Exception as e:
            logger.error(f"Bot durdurulurken hata: {e}")
            # Hata olsa bile Chromium process'lerini öldürmeyi dene
            try:
                await self.scraper._kill_all_chromium_processes()
            except:
                pass
            
    async def process_category(self, category_name: str) -> int:
        """Bir kategoriyi işle - En az 5 kupon yap (veya maç kalmayana kadar)"""
        try:
            logger.info(f"Kategori işleniyor: {category_name}")
            
            # Kategoriye git
            success = await self.scraper.navigate_to_category(category_name)
            if not success:
                logger.warning(f"Kategoriye gidilemedi: {category_name}")
                return 0
            
            await asyncio.sleep(0.05)
            
            if category_name == "Canlı Bülten":
                matches = await self.scraper.get_available_matches_live()
            else:
                matches = await self.scraper.get_available_matches()
            
            if not matches:
                logger.warning(f"Kategoride maç bulunamadı: {category_name}")
                return 0
            
            tried_match_ids = set()
            coupons_created = 0
            target_coupons = 20 if category_name in ("Canlı Bülten", "Uzun Vadeli") else 5
            max_attempts = 40 if category_name in ("Canlı Bülten", "Uzun Vadeli") else 20
            attempt = 0
            
            if category_name in ("Canlı Bülten", "Uzun Vadeli"):
                logger.info(f"Kategoride {len(matches)} maç var, her maç için 1 seçimli kupon yapılacak (hedef: {target_coupons})")
            else:
                logger.info(f"Kategoride {len(matches)} maç var, {target_coupons} kupon yapılacak (her kupon 3-5 rastgele seçim)")
            
            while coupons_created < target_coupons and attempt < max_attempts:
                attempt += 1
                
                # Her kupon için maçları yeniden al (sayfa güncellenmiş olabilir)
                if category_name == "Canlı Bülten":
                    current_matches = await self.scraper.get_available_matches_live()
                else:
                    current_matches = await self.scraper.get_available_matches()
                
                if not current_matches:
                    if category_name == "Canlı Bülten":
                        logger.warning("Canlı Bülten: Maç bulunamadı - kategori değişmiş olabilir, Canlı'ya yeniden gidiliyor")
                        await self.scraper.navigate_to_category(category_name)
                        await asyncio.sleep(1.0)
                        current_matches = await self.scraper.get_available_matches_live()
                    if not current_matches:
                        logger.warning("Maç kalmadı, kategori tamamlandı")
                        break
                
                if category_name in ("Canlı Bülten", "Uzun Vadeli"):
                    available_count = sum(1 for m in current_matches if self.scraper._get_match_key(m) not in tried_match_ids)
                    if available_count == 0:
                        break
                
                # Kupon yap - tüm maçları sırayla dener
                success, needs_return, failed_key, used_keys, tried_no_market = await self.scraper.create_single_coupon(current_matches, category_name, tried_match_ids)
                
                tried_match_ids.update(tried_no_market)
                if failed_key:
                    tried_match_ids.add(failed_key)
                
                if not success and not needs_return and tried_no_market:
                    break
                
                if needs_return:
                    # Para yatırma gerekmiş, kategoriye geri dön
                    logger.info("Para yatırıldı, kategoriye geri dönülüyor...")
                    # Önce ana sayfaya git (para yatırma sonrası sayfa değişmiş olabilir)
                    try:
                        from config import BASE_URL
                        await self.scraper.page.goto(BASE_URL, wait_until="domcontentloaded", timeout=10000)
                        await asyncio.sleep(0.5)
                    except:
                        pass
                    # Sonra kategoriye git
                    success = await self.scraper.navigate_to_category(category_name)
                    if not success:
                        logger.warning(f"Kategoriye geri dönülemedi: {category_name}")
                        break
                    await asyncio.sleep(0.3)  # Kategori yüklenmesi için bekleme
                    # Maçları tekrar al
                    if category_name == "Canlı Bülten":
                        current_matches = await self.scraper.get_available_matches_live()
                    else:
                        current_matches = await self.scraper.get_available_matches()
                    
                    if not current_matches:
                        logger.warning("Kategoriye dönüldü ama maç bulunamadı")
                        break
                    continue
                
                if success:
                    coupons_created += 1
                    if category_name in ("Canlı Bülten", "Uzun Vadeli"):
                        tried_match_ids.update(used_keys)
                    logger.info(f"Kupon {coupons_created}/{target_coupons} tamamlandı")
                else:
                    # Seçim yapılamadı - bülten değiştirme, tekrar dene (stabilizasyon)
                    logger.warning(f"Kupon başarısız (seçim yapılamadı), tekrar deneniyor...")
                    await asyncio.sleep(0.2)  # Sayfa stabilizasyonu için kısa bekleme
                
                # Kısa bekleme (sistem nefes alsın)
                await asyncio.sleep(0.1)
            
            logger.info(f"Kategori tamamlandı: {category_name} - {coupons_created} kupon yapıldı")
            return coupons_created
            
        except Exception as e:
            logger.error(f"Kategori işlenirken hata ({category_name}): {e}")
            return 0
            
    async def create_bet_slip(self) -> bool:
        """Tüm kategorileri dolaş - Her kategoride 5 kupon yap"""
        try:
            logger.info("Kupon oluşturma döngüsü başlatılıyor...")
            total_coupons = 0
            
            # Tüm kategorileri dolaş
            for category in CATEGORIES:
                if not self.is_running:
                    break
                    
                try:
                    coupons_created = await self.process_category(category)
                    total_coupons += coupons_created
                    await asyncio.sleep(0.05)  # Çok kısa bekleme
                    
                except Exception as e:
                    logger.error(f"Kategori işlenirken hata ({category}): {e}")
                    continue
            
            if total_coupons == 0:
                logger.warning("Hiç kupon oluşturulamadı")
                return False
            
            logger.info(f"Toplam {total_coupons} kupon oluşturuldu")
            return True
            
        except Exception as e:
            logger.error(f"Kupon oluşturulurken hata: {e}")
            return False
            
    async def run_once(self) -> bool:
        """Tek seferlik kupon yapma işlemi"""
        if not self.is_running:
            logger.warning("Bot çalışmıyor")
            return False
            
        try:
            return await self.create_bet_slip()
        except Exception as e:
            logger.error(f"Kupon yapma işlemi sırasında hata: {e}")
            return False
