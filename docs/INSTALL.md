# Kurulum sihirbazı

Sihirbaz terminalde çalışan, **kurulum ve güncelleme** aracıdır. Desteklenen
sunucuda ilk kurulumda dosyaları yerleştirir, ayrı bir hop hesabı ve rastgele AMI parolası
üretir. Sizin şirketinizin adresini, kullanıcılarını veya parolasını içermez.

## Hazırlık

- Mevcut PBX yedeğinizi alın ve bakım zamanı seçin.
- Issabel sunucusunda root/sudo erişimi, Python 3.6+, systemd, Apache `httpd`,
  `proxy_fcgi`, PHP-FPM `/run/php-fpm/www.sock`, yerel AMI `127.0.0.1:5038` gerekir.
- PHP-FPM'de `allow_url_fopen` etkin olmalıdır; CLI kontrolü FPM ayarının garantisi değildir.
- `/etc/asterisk/manager.conf`, `manager_custom.conf` dosyasını doğrudan içermeli.
- HTTPS mevcut Issabel web sunucusu tarafından sağlanır; kurucu sertifika üretmez.
- Paket yöneticisi çalıştırılmaz, firewall/SELinux kapatılmaz, santral yeniden başlatılmaz.

## İndirme ve çalıştırma

GitHub'da Releases → sürüm → kaynak ZIP veya Code → Download ZIP ile indirin.
ZIP'i açın. WinSCP/SFTP ile klasörü sunucunuzda örneğin `/root/hop-source`
altına aktarın. Gerçek sunucu adresinizi ve SSH hesabınızı kendiniz kullanın.

```sh
cd /root/hop-source
sudo bash install.sh --check
sudo bash install.sh
```

1. **Uyumluluk:** Komutlar, dosyalar, portlar, Apache ve çakışmalar kontrol edilir.
   `--check` sistemde değişiklik yapmaz. Hata varsa kurulum başlamaz.
2. **Özet:** Kurulacak yollar ve giriş istemeyen panelin erişim modeli gösterilir.
   `KUR` yazarsanız devam eder; Enter veya başka yanıt iptal eder.
3. **Kurulum:** AMI dosyaları root erişimli yedeklenir; ayrı hesap, servis,
   web dosyaları ve cron görevi kurulur. `manager reload` ve Apache reload
   uygulanır. Yerel AMI bağlantısı doğrulanır.

Sonrasında `https://SANTRAL-ADRESINIZ/hop/` adresini açın. Bu bir örnek adres;
SANTRAL-ADRESINIZ yerine mevcut santralinizin alan adını yazın. Panelin canlı
göstergesini, dahili sayısını ve normal bir çağrıdaki durum değişimini kontrol edin.
Kurulum bitti mesajı tarayıcı/HTTPS katmanını tek başına doğrulamaz.

## Oluşturulan dosyalar

| Yol | İçerik |
| --- | --- |
| `/opt/hop` | Python servis, HTML ve üretilen metadata |
| `/etc/hop/ami.env` | Sunucuda üretilen parola; 0600, GitHub'a yüklenmez |
| `/var/www/html/hop` | PHP geçidi ve tarayıcı dosyaları |
| `/etc/systemd/system/hop.service` | HOP servis tanımı |
| `/etc/cron.d/hop-metadata` | Dakikada bir ad/envanter güncellemesi |
| `/etc/httpd/conf.d/zz-hop-stream.conf` | SSE FastCGI yapılandırması |
| `/root/hop-backups/ZAMAN` | Mevcut AMI dosyalarının özel yedeği |

Mevcut AMI hesapları değiştirilmez; custom dosyasına yalnızca `[hop]` eklenir.
Mevcut hop kullanıcısı/dosyaları varsa sihirbaz durur; güncelleme için `--update` kullanılır.

## Sorun giderme

```sh
systemctl status hop --no-pager
journalctl -u hop --no-pager -n 30
httpd -t
curl -N --max-time 15 http://127.0.0.1:8765/events
```

Son komut çağrı verileri gösterebilir; çıktıyı herkese açık issue'ya yapıştırmayın.
Servis canlı ama tarayıcı güncellenmiyorsa PHP-FPM socket yolu, izinler,
`allow_url_fopen`, SSE tamponlama, proxy zaman aşımı ve SELinux AVC kayıtlarını
inceleyin. SELinux'u kapatmayın; kullanılan dağıtımın politikasına uygun izin verin.

## Başarısız kurulum ve geri alma

Kurulum çok adımlıdır; hata sonrası otomatik tam geri alma yapmaz. Önce
`systemctl disable --now hop` ile HOP'u durdurun. Yedek dizinini bulun.
`manager_custom.conf` içindeki yalnızca kurucu tarafından eklenen `[hop]`
bölümünü kaldırın ve `asterisk -rx 'manager reload'` çalıştırın.
Sonradan yapılmış değişiklikler olabileceğinden tüm AMI yedeğini körlemesine geri yazmayın.

Yukarıdaki tabloda listelenen HOP'a ait cron, servis, web ve Apache dosyalarını
inceleyip kaldırın/karantinaya taşıyın. `systemctl daemon-reload`, `httpd -t`
ve başarılıysa `systemctl reload httpd` uygulayın. Gerekirse yalnızca HOP için
oluşturulan işletim sistemi kullanıcısını kaldırın. Santrali yeniden başlatmayın.

## Mevcut kurulumu güncellemek

### Web arayüzünden (0.27.0 ve sonrası)

Panelde **Güncelle** düğmesine basın. Yönetici oturumunuz yoksa penceredeki
**Issabel yönetici girişi** bağlantısından normal Issabel girişini (varsa 2FA dahil)
tamamlayın, HOP'a dönüp **Oturumu kontrol et** seçin. Issabel administrator grubundaki
hesabınızın şifresini yeniden girip **Şifreyle doğrula ve güncelle** düğmesine basın.
Bu parola SSH/root veya AMI parolası değil, Issabel web yönetici parolasıdır.

Pencere kontrol, indirme, yedek/kurulum ve sonuç durumlarını gösterir. Pencereyi
kapatmak başlamış sunucu işlemini iptal etmez. Kurulum bitince sayfayı yenileyin.
Zaten güncelseniz dosyalar değiştirilmez. Parola işlem isteğinden sonra tarayıcı
alanından temizlenir, HOP tarafından kaydedilmez. İstek HTTPS ile yapılır.

0.26.0 ve daha eski kurulumlar web yöneticisi bileşenlerini henüz içermez;
önce aşağıdaki SSH sihirbazıyla 0.27.0'a geçin. İlk kurucu/yükseltici, yalnızca
`hop-web-update.service` başlatmaya izin veren dar kapsamlı sudoers kuralını kurar.
Servis root olarak sabit HOP deposunu kontrol eder; kullanıcıdan komut/URL almaz.
PHP-FPM işletim sistemi kullanıcısı `asterisk`, sudo ve visudo gereklidir.
PHP `exec` devre dışıysa web güncellemesi çalışmaz; SSH yolu kullanılabilir.

Hata halinde `journalctl -u hop-web-update --no-pager -n 50` komutunu kullanın.
Web güncelleme durumu `/var/lib/hop-web-update/status.json` dosyasındadır; yalnız
yetkili yönetim uç noktası üzerinden gösterilir. Geri dönüş SSH sihirbazıyla yapılır.

### SSH üzerinden

1. GitHub deposundaki Releases bölümünden daha yeni sürümün kaynak ZIP paketini indirin.
   Bildirim için Watch → Custom → Releases seçeneğini açabilirsiniz.
2. Sürüm notlarını okuyun. ZIP'i sunucuda **ayrı bir kaynak klasörüne** açın;
   dosyaları doğrudan /opt/hop üzerine çıkarmayın. ZIP içindeki install.sh dosyasının
   bulunduğu klasöre geçin. Git ile kaynak kullananlar temiz kaynak kopyasında
   git pull --ff-only çalıştırabilir; kurulu dosyaları yine sihirbaz günceller.
3. Ön kontrolü çalıştırın:

```sh
sudo bash install.sh --update --check
sudo bash install.sh --update
```

4. Kurulu → yeni sürüm bilgisini okuyun. GUNCELLE yazınca işlem başlar.
   Parametresiz sihirbaz da mevcut kurulumu bulunca güncelleme seçeneğini sunar.
5. İşlem sonunda tarayıcıyı yenileyin. Footer sürümünü, canlı göstergeyi ve normal
   bir çağrıdaki bilgileri kontrol edin.

### Neler olur?

- Aynı/eski sürüm, eksik dosya, sürüm uyuşmazlığı ve sembolik hedefler reddedilir.
- Python sözdizimi ve PHP geçidi kontrol edilir; mevcut AMI sağlıklı değilse uygulanmaz.
- Değişecek dosyalar /root/hop-update-backups altında özel bir dizine yedeklenir.
- Yalnızca uygulama kodu, HTML/CSS/JS ve VERSION değiştirilir. Dosya değişimleri atomiktir;
  bütün güncelleme boyunca tarayıcı kısa süre karışık sürüm görebilir, sonunda yenileyin.
- Yalnız HOP durdurulup başlatılır. Asterisk ve Apache yeniden başlatılmaz.
- AMI parolası, hesapları, dahili yapılandırmaları, metadata, cron, systemd ve Apache
  ayarları değiştirilmez. Yerel **kod/tema düzenlemeleri** yeni paketle değiştirilir.
- Yeni AMI bağlantısı doğrulanamazsa eski dosyalar otomatik geri yüklenir ve HOP başlatılır.
- Sunucu kapanması/güç kesilmesi otomatik hata yakalamayı atlayabilir; yedekle manuel geri dönün.

Bu güncelleyici aynı kurulum düzenindeki uygulama sürümleri içindir. Gelecekte servis,
Apache ayarı veya veri şeması değişirse sürüm notlarında ek geçiş adımları gerekir.
Paket otomatik olarak internetten çekilmez; yalnızca güvendiğiniz proje deposundan indirin.
Paket SHA256SUMS dosyası bozulma kontrolüne yarar, yayıncı kimliğini tek başına doğrulamaz.

### Önceki sürüme geri dönme

Sihirbazın yazdırdığı gerçek yedek yolunu kullanın; YEDEK-DIZINI bir yer tutucudur:

```sh
sudo bash install.sh --rollback /root/hop-update-backups/YEDEK-DIZINI
```

GERI yazarak onaylayın. Seçilen yedekteki uygulama dosyaları ve sürüm geri yüklenir;
AMI hesabı/parolası değişmez. Geri dönüş sonrasında da tarayıcıyı yenileyin.
Eski bir yedeği seçmek daha sonraki uygulama değişikliklerini geri alır.
Geri yükleme veya bağlantı kontrolü başarısızsa HATA mesajı görünür; journalctl -u hop
ile inceleyin. Yedekleri doğrulamadan silmeyin ve herkese açık paylaşmayın.
