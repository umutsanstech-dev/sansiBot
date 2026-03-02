# Sansi Bot - Otomatik Kupon Yapma Botu

dev-sansi.sanstech.dev sitesi için otomatik kupon yapan Python botu.

## Özellikler

- Playwright ile web scraping
- Çoklu spor kategorilerinde gezinme (Futbol, Basketbol, E-Futbol, Voleybol, Tenis, vb.)
- Rastgele bahis seçimi
- Otomatik kupon oluşturma ve onaylama
- Zamanlayıcı ile belirli aralıklarla çalışma
- Detaylı loglama

## Kurulum

1. Python 3.8+ yüklü olmalıdır

2. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

3. Playwright browser'larını yükleyin:
```bash
playwright install chromium
```

## Yapılandırma

`config.py` dosyasında şu ayarları yapabilirsiniz:

- `BETTING_INTERVAL_MINUTES`: Kupon yapma aralığı (dakika)
- `BETS_PER_CATEGORY_MIN/MAX`: Her kategoriden seçilecek bahis sayısı
- `HEADLESS`: Browser'ı görünür/gizli modda çalıştırma
- `CATEGORIES`: İşlenecek spor kategorileri listesi

## Kullanım

Bot'u çalıştırmak için:

```bash
python main.py
```

Bot'u durdurmak için `Ctrl+C` tuşlarına basın.

## Loglar

Tüm işlemler `sansi_bot.log` dosyasına kaydedilir.

## Notlar

- Bot, insan benzeri davranış için rastgele bekleme süreleri kullanır
- Element bulunamazsa otomatik retry mekanizması devreye girer
- Her kategori için maç bulunamazsa o kategori atlanır ve devam edilir
