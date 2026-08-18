# pdf-edit

Windows için küçük bir PDF düzenleyici. Bir PDF açıyorsun, metnin içine tıklayıp yazıyorsun, siliyorsun; eklediğin harfler o satırın yazı tipiyle devam ediyor. Sayfaya resim atıp fareyle istediğin yere sürükleyebiliyorsun. Bulut yok, hesap yok, her şey bilgisayarda kalıyor.

Kaydettiğinde kaynak dosyaya dokunulmaz; yanına `-duzenlenmis.pdf` ekiyle yeni dosya çıkar.

## Çalıştırma

Python 3.11 veya üstü gerekli.

    pip install -r requirements.txt
    python -m app.main

Ya da `calistir.cmd` dosyasına çift tıkla. Exe istersen `derle.cmd` çalıştır; çıktı `dist\PdfEdit\PdfEdit.exe` altında oluşur (PyInstaller, klasörlü paket).

## Kısayollar

Ctrl+O aç, Ctrl+S kaydet, Ctrl+Z geri al, Ctrl+M resim ekle, Ctrl+B kalın, Ctrl+I eğik. Sayfa geçişi PgUp / PgDown, yakınlaştırma Ctrl ile fare tekerleği. Seçili resmi ok tuşlarıyla piksel piksel taşıyabilirsin, Shift basılıyken köşeden çekersen oran korunur.

## Yazı tipleri

Varsayılan dört aile: Times New Roman, Arial, Courier New ve JetBrains Mono. İlk üçü Microsoft fontu olduğu için depoda yok; program onları Windows'un kendi font klasöründen okur, exe derlerken de oradan kopyalar. Açtığın PDF başka bir fontla yazılmışsa (Georgia, Calibri gibi) ve o font Windows'ta kuruluysa program onu bulup kullanır; listeye de ekler. Yeni font eklemek için `fonts/` klasörüne .ttf dosyalarını at ve `app/fonts.py` içindeki `GOMULU` sözlüğüne bir satır yaz.

## Sınırlar

Taranmış PDF'lerde (içi resim olan) metin düzenlenemez, OCR yok. Çok sütunlu ya da tablolu sayfalarda bir bloğu uzatınca altındakiler kayabilir; araç çubuğundaki "Blokları it" kutusunu kapatırsan bloklar yerinde kalır. Bir de şu: PDF'e gömülü fontlar çoğu zaman eksik karakter setiyle gelir, o yüzden belgenin kendi fontuyla yazamadığı harflerde en yakın yerel fonta düşülür.

Kod PySide6 ile PyMuPDF üzerine kurulu. Ölçüm ve yazım aynı motordan geçtiği için ekranda gördüğün yerleşim kaydedilen dosyayla aynı çıkar.
