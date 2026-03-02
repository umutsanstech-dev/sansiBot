# Sansi Bot - Windows EXE Oluşturma Rehberi

Bu rehber, Sansi Bot'u Windows 11'de çalışan tek dosya `.exe` haline getirmek için gereken adımları açıklar.

## Önemli Not

**EXE oluşturmak için Windows bilgisayar gereklidir.** macOS veya Linux'tan Windows EXE oluşturamazsınız. Aşağıdaki seçeneklerden birini kullanın:

- Windows 11 bilgisayar
- Windows sanal makine (VMware, VirtualBox, Parallels)
- GitHub Actions ile uzaktan build (ileride eklenebilir)

---

## Hızlı Başlangıç (Windows'ta)

### Gereksinimler

- **Windows 11** (veya Windows 10)
- **Python 3.10 veya üzeri** - [python.org](https://www.python.org/downloads/) adresinden indirin
  - Kurulumda **"Add Python to PATH"** kutusunu işaretleyin!

### Adımlar

1. **Projeyi Windows'a kopyalayın** (tüm dosyalar: main.py, bot.py, scraper.py, scheduler.py, config.py, build.spec, runtime_hook.py, build_windows.bat)

2. **Komut İstemi (CMD) veya PowerShell** açın ve proje klasörüne gidin:
   ```
   cd C:\path\to\sansiBot
   ```

3. **Build script'ini çalıştırın:**
   ```
   build_windows.bat
   ```

4. **Bekleyin** - İşlem 5-10 dakika sürebilir (Chromium indirilir ~150MB)

5. **EXE hazır!** - `dist\SansiBot.exe` dosyasını bulacaksınız

---

## Manuel Build (Alternatif)

Script çalışmazsa adımları manuel yapın:

```batch
REM 1. Sanal ortam
python -m venv venv_build
venv_build\Scripts\activate

REM 2. Bağımlılıklar
pip install playwright pyinstaller

REM 3. Chromium (zorunlu!)
playwright install chromium

REM 4. EXE oluştur
pyinstaller -y build.spec
```

---

## EXE Kullanımı

1. `SansiBot.exe` dosyasını istediğiniz yere kopyalayın
2. Çift tıklayarak çalıştırın
3. **İlk çalıştırmada** Windows Defender/SmartScreen uyarı verebilir:
   - "Daha fazla bilgi" → "Yine de çalıştır" tıklayın
   - Bu normaldir; imzasız EXE'ler için standart uyarıdır

4. Konsol penceresi açılacak ve bot çalışmaya başlayacak
5. Chromium tarayıcı otomatik açılacak
6. Durdurmak için konsol penceresinde `Ctrl+C` kullanın

---

## Sorun Giderme

### "Python bulunamadı"
- Python'u PATH'e ekleyerek yeniden kurun
- Veya tam yol kullanın: `C:\Python311\python.exe -m venv venv_build`

### "Chromium bulunamadı" uyarısı
- `playwright install chromium` komutunu manuel çalıştırın
- İnternet bağlantınızı kontrol edin (Chromium indirilir)

### EXE çalışmıyor / Hemen kapanıyor
- CMD'den çalıştırın: `SansiBot.exe` - hata mesajını göreceksiniz
- `config.py` dosyasındaki ayarları kontrol edin

### Antivirüs EXE'yi siliyor
- Sansi Bot açık kaynak bir projedir
- Antivirüse istisna ekleyin veya "güvenli" olarak işaretleyin

---

## Dosya Boyutu

- **SansiBot.exe**: ~150-200 MB (Chromium dahil)
- Tek dosya - ek kurulum gerekmez
