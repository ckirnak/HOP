# GitHub yayını ve sürüm notları

## İlk yükleme

Proje kökünde `node scripts/package.cjs` çalıştırın. Yalnızca izin verilen kaynak
dosyaları `release/hop-SURUM` dizinine kopyalanır. Eski `.git`, `.openai`,
barındırma kimlikleri, runtime metadata, parolalar ve loglar taşınmaz.
`SHA256SUMS` dosya özetlerini, `hop-SURUM-notes.md` sürüm açıklamasını içerir.

GitHub'da boş bir depo açın. **Temiz klasörde** yeni Git geçmişi başlatın:

```sh
cd release/hop-0.25.0
git init -b main
git add .
git commit -m "HOP 0.25.0: kurulum, güncelleme ve geri dönüş sihirbazı"
git remote add origin UZAK-DEPO-URL
git push -u origin main
```

UZAK-DEPO-URL yerine kendi GitHub depo adresinizi kullanın. Alternatif olarak
GitHub Add file → Upload files ile yalnızca temiz klasörün içeriğini yükleyin.
Eski çalışma klasörünün Git geçmişini göndermeyin. `.gitignore` geçmişte commit
edilmiş sırrı silmez. Yayımlanmış bir sır varsa parola değişimi ve geçmiş
temizliği gerekir; yalnızca yeni commit yeterli değildir.

GitHub About açıklaması:

> Free, open-source HTML operator panel for Issabel/Asterisk. Live extensions,
> calls, queues and trunk registrations via AMI + SSE. No Flash. MIT licensed.

## Her güncellemede

1. `VERSION` değerini artırın (0.25.0 → 0.26.0).
2. `backend/CHANGELOG.md` başına `## SURUM — YYYY-AA-GG` ekleyin; İstanbul tarihini,
   değişen davranışı, düzeltmeleri ve gerekiyorsa geçiş adımlarını yazın.
3. `node backend/build-live.cjs` ile footer ve önbellek anahtarlarını üretin.
4. Python testlerini ve `node scripts/package.cjs` kontrolünü çalıştırın.
5. Temiz GitHub çalışma kopyasında diff'i inceleyin, açıklayıcı commit ve push yapın.
6. Releases → Draft a new release ekranında `vSURUM` etiketi açın.
   Başlık `HOP SURUM`; açıklama üretilen `hop-SURUM-notes.md` içeriğidir.
   Kurulum rehberini bağlayın, test kapsamını ve sınırlamaları yazın.

Paket aracı GitHub'a yükleme yapmaz. Değişiklik geçmişi, commit mesajı ve Release
açıklaması birlikte ne değiştiğini anlatır. Canlıya kurduğunuzda footer ve
bağlantıyı ayrıca doğrulayın.

## Özel bilgiler

Paket üreticisi izin listesi ve temel sır/IP kontrolleri kullanır; bütün sırları
bulma garantisi değildir. Yayın öncesi kaynakları inceleyin. Sunucunun `/etc`,
`/root`, metadata ve yedeklerini eklemeyin. `127.0.0.1`, `0.0.0.0` ve ağ maskeleri
şirket IP'si değil, yerel uygulama ayarlarıdır. `hop` genel servis adı,
`ckirnak` ise paylaşılması istenen yazar imzasıdır.

MIT telif ve lisans bildirimini korur; arayüzde bayrağı zorunlu kılmaz.
Bkz. [MIT](https://choosealicense.com/licenses/mit/) ve
[Açık kaynak tanımı](https://opensource.org/osd).
