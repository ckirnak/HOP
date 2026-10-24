# HOP doğrulama kayıtları

## 0.26.0 — 2026-10-24

- Python 3.6.8 üzerinde 24 test geçti; sürüm karşılaştırma, ön sürüm/geçersiz etiket
  reddi, HTTP 304 önbelleği, ağ hatası ve AMI yayınında bildirim koruması dahil.
- JavaScript kontrolünde yeni sürümde görünme, güncel sürümde gizlenme ve geçersiz
  sürüm metnini reddetme doğrulandı.
- Santralden gerçek GitHub Release API isteği ve ETag yanıtı doğrulandı.
- Otomatik kurulum yapılmaz; kontrol hatası AMI toplama iş parçacığını engellemez.

## 0.25.0 doğrulama kaydı — 2026-10-24

## Gerçek kurulumda güncelleme doğrulaması

2026-10-24 tarihinde mevcut bir Issabel/Asterisk 18 kurulumunda, GitHub Release
ZIP paketi indirilip SHA-256 ve dosya özetleri doğrulandı. Sihirbazın
`--update --check` ön kontrolü ve ardından onaylı `--update` akışıyla
0.23.0 → 0.25.0 geçişi başarıyla uygulandı.

- Otomatik uygulama dosyası yedeği oluşturuldu.
- HOP servisi aktif, AMI bağlantısı sağlıklı ve HTTPS üzerinden SSE state olayı alınıyor.
- HTTPS sayfasında 0.25.0 sürümü doğrulandı.
- AMI parolası/hesap dosyaları, systemd, Apache ve cron yapılandırmaları
  güncelleme öncesi/sonrası özetleriyle karşılaştırıldı; değişmediler.
- Gerçek santralde hata tetikleme veya geri dönüş denemesi yapılmadı.
- Sıfırdan kurulum ve farklı Issabel sürümleri için uçtan uca doğrulama hâlâ gereklidir.

Tanıtım ekran görüntüsü ayrı bir önizlemede tamamen kurgusal verilerle hazırlanmıştır.

## Yayın öncesi test kaydı

- Asterisk izleme kodunun 7 testi geçti: AMI parçalı çerçeve okuma, olay tetikleme,
  durum eşleştirme, aynı çağrının kanallarını birleştirme ve eşzamanlı çağrılar.
- Sihirbazın 5 testi geçti: Linux/root gereksinimi, ön kontrol hatasında durma,
  `--check` sırasında kurulum yapmama ve iptal davranışı.
- Güncelleyicinin 7 testi geçti: güncelleme/geri dönüş ve yapılandırma koruması,
  sağlık hatasında otomatik geri dönüş, başlangıç bağlantı hatasında değişiklik yapmama,
  eski sürümü reddetme, VERSION dosyası olmayan kurulum desteği, sembolik hedefi
  reddetme ve eksik yedeği uygulamadan durma. Toplam 19 test geçti.
- Güncelleme testlerinde dosya işlemleri geçici bir sistem dizininde gerçek olarak,
  systemctl ve sağlık sonuçları ise taklit edilerek çalıştırıldı. Gerçek santralde
  uçtan uca güncelleme/geri dönüş uygulanmadı.
- Testler Python 3.6.8 üzerinde geçici kaynak klasöründe çalıştırıldı;
  kurulu servis ve AMI ayarları değiştirilmedi.
- Python sözdizimi ve JavaScript sözdizimi kontrolleri geçti.
- Paket yalnızca 32 açıkça seçilmiş kaynak/belge dosyası ve SHA256SUMS içerir.
  Eski Git geçmişi, yerel barındırma ayarları ve çalışma zamanı sırları dahil değildir.
- Yeni sihirbazın sıfır Issabel üzerinde uçtan uca kurulum testi henüz yapılmadı.
  Tarayıcıdan yeni sürüm görsel doğrulaması ve farklı Issabel sürümleri testi yapılmadı.

Bu kayıt GitHub'a yayın veya canlı santral güncellemesi yapıldığı anlamına gelmez.
