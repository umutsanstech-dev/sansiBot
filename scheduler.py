"""
Zamanlayıcı - Sürekli bot çalıştırma (interval yok)
"""

import asyncio
import logging
from datetime import datetime
from bot import Sansibot

logger = logging.getLogger(__name__)


class Scheduler:
    """Zamanlayıcı sınıfı - Sürekli çalışır, interval yok"""
    
    def __init__(self, bot: Sansibot):
        self.bot = bot
        self.is_running = False
        
    async def start(self):
        """Zamanlayıcıyı başlat - Sürekli çalışır"""
        self.is_running = True
        logger.info("Zamanlayıcı başlatıldı - Sürekli kupon yapılacak (interval yok)")
        
        # Döngüyü başlat - her kupon sonrası hemen yeni kupon
        while self.is_running:
            try:
                await self._run_bet_cycle()
                # Kupon tamamlandıktan sonra çok kısa bir bekleme (sadece sistem nefes alsın)
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                logger.info("Zamanlayıcı iptal edildi")
                break
            except Exception as e:
                logger.error(f"Zamanlayıcı döngüsünde hata: {e}")
                # Hata olsa bile devam et - kısa bekleme
                await asyncio.sleep(1)
                
    async def _run_bet_cycle(self):
        """Bir kupon yapma döngüsü"""
        try:
            logger.info(f"=== Yeni kupon döngüsü başlatılıyor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            success = await self.bot.run_once()
            
            if success:
                logger.info("Kupon döngüsü başarıyla tamamlandı")
            else:
                logger.warning("Kupon döngüsü tamamlandı ancak başarısız olabilir")
                
        except Exception as e:
            logger.error(f"Kupon döngüsü sırasında hata: {e}")
            
    def stop(self):
        """Zamanlayıcıyı durdur"""
        logger.info("Zamanlayıcı durduruluyor...")
        self.is_running = False
