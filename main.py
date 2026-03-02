"""
Ana giriş noktası - Bot'u başlatır
"""

import asyncio
import logging
import signal
import sys
from bot import Sansibot
from scheduler import Scheduler

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('sansi_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global değişkenler
bot = None
scheduler = None
shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """Signal handler (Ctrl+C)"""
    logger.info("Durdurma sinyali alındı...")
    shutdown_event.set()
    
    # Chromium process'lerini öldür
    try:
        import subprocess
        import platform
        system = platform.system()
        
        if system == "Darwin":  # macOS
            subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True, timeout=2)
            subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True, timeout=2)
        elif system == "Linux":
            subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True, timeout=2)
        elif system == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "chromium.exe"], capture_output=True, timeout=2)
    except:
        pass


async def main():
    """Ana fonksiyon"""
    global bot, scheduler
    
    try:
        # Signal handler'ları ayarla
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("=" * 50)
        logger.info("Sansi Bot Başlatılıyor...")
        logger.info("=" * 50)
        
        # Bot'u oluştur ve başlat
        bot = Sansibot()
        success = await bot.initialize()
        
        if not success:
            logger.error("Bot başlatılamadı - Çıkılıyor")
            return
        
        # Zamanlayıcıyı başlat
        scheduler = Scheduler(bot)
        
        # Zamanlayıcıyı arka planda çalıştır
        scheduler_task = asyncio.create_task(scheduler.start())
        
        # Shutdown event'ini bekle
        try:
            await shutdown_event.wait()
        except asyncio.CancelledError:
            pass
        
        # Temizlik
        logger.info("Temizlik yapılıyor...")
        scheduler.stop()
        scheduler_task.cancel()
        
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        
        await bot.shutdown()
        
        logger.info("Bot başarıyla durduruldu")
        
    except Exception as e:
        logger.error(f"Ana fonksiyonda hata: {e}", exc_info=True)
    finally:
        if bot:
            try:
                await bot.shutdown()
            except:
                pass
        
        # Son kontrol: Tüm Chromium process'lerini öldür
        try:
            import subprocess
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True, timeout=2)
                subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True, timeout=2)
            elif system == "Linux":
                subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True, timeout=2)
            elif system == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "chromium.exe"], capture_output=True, timeout=2)
        except:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"Program hatası: {e}", exc_info=True)
