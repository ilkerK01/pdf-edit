# pdf-edit

Windows için küçük bir PDF düzenleyici. Bir PDF açıyorsun, metnin içine tıklayıp yazıyorsun, siliyorsun, yerlerini değiştiriyorsun ! Kişisel küçük kullanımlar için ...

Kaydettiğinde kaynak dosyaya dokunulmaz; yanına `-duzenlenmis.pdf` ekiyle yeni dosya çıkar.

## Çalıştırma

Python 3.11 veya üstü gerekli.

    pip install -r requirements.txt
    python -m app.main

Ya da `calistir.cmd` dosyasına çift tıkla. Exe istersen `derle.cmd` çalıştır; çıktı `dist\PdfEdit\PdfEdit.exe` altında oluşur (PyInstaller, klasörlü paket).

## Taşıma

Araç çubuğundaki taşı düğmesi (ya da V tuşu) taşıma moduna geçirir. Bu moddayken sayfadaki her şeye tıklayıp sürükleyebilirsin: bir paragraf, bir başlık, eklediğin resim. Ok tuşları 5 punto, Shift ile birlikte 1 punto kaydırır. Esc seni metin moduna geri döndürür. Modu değiştirmek istemiyorsan Alt basılı tutup sürüklemek de aynı işi görür.

Bir cümlenin sadece bir kısmını taşımak istiyorsan onu seç ve Ctrl+D'ye bas. Seçtiğin metin bulunduğu paragraftan ayrılıp bağımsız bir parçaya dönüşür, geride kalan paragraf kendini yeniden dizer; sonra parçayı istediğin yere sürüklersin.

Taşınan bir blok artık kendi yerinde sabitlenir, alttaki bloklar büyüdüğünde onunla birlikte kaymaz.

## Kısayollar

Ctrl+O aç, Ctrl+S kaydet, Ctrl+Z geri al, Ctrl+M resim ekle, Ctrl+D seçimi ayır, V taşı modu, Esc metin modu, Ctrl+B kalın, Ctrl+I eğik. Sayfa geçişi PgUp / PgDown, yakınlaştırma Ctrl ile fare tekerleği. Resmi köşesinden çekerken Shift basılıysa oran korunur, Delete seçili şeyi siler.


## Sınırlar

Taranmış PDF'lerde (içi resim olan) metin düzenlenemez, OCR yok. Çok sütunlu ya da tablolu sayfalarda bir bloğu uzatınca altındakiler kayabilir; araç çubuğundaki "Blokları it" kutusunu kapatırsan bloklar yerinde kalır. Bir de şu: PDF'e gömülü fontlar çoğu zaman eksik karakter setiyle gelir, o yüzden belgenin kendi fontuyla yazamadığı harflerde en yakın yerel fonta düşülür.

Kod PySide6 ile PyMuPDF üzerine kurulu. Ölçüm ve yazım aynı motordan geçtiği için ekranda gördüğün yerleşim kaydedilen dosyayla aynı çıkar.
