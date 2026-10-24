# 0.25.0 doğrulama kaydı — 2026-10-24

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
