# HOP sürüm geçmişi

## 0.27.0 — 2026-10-24

- Aynı sürüm düzeltmesi: Güncelle düğmesi yalnız yeni sürüm bulunduğunda görünür; yeni sürüm numarası ilgili GitHub sürüm sayfasını açar. Güncel kurulumda bu alan tamamen gizlidir.
- Aynı sürümde yenilenen ön yüz dosyaları için içerik tabanlı önbellek anahtarı eklendi.

- Panel başlığına yönetici doğrulamalı web güncelleme düğmesi eklendi.
- Geçerli Issabel administrator oturumu, yeniden şifre doğrulaması, HTTPS ve CSRF kontrolü gerekir.
- Sabit systemd görevi yalnız HOP deposunun son kararlı paketini indirir; SHA-256 doğrular ve yedekli güncelleme yapar.
- İndirme/kurulum/sonuç durumları yönetici penceresinde gösterilir; parola saklanmaz.
- Geçici tanıtım güncelleme bildirimi kaldırıldı; gerçek sürüm kontrolü korunur.

## 0.26.0 — 2026-10-24

- GitHub'daki son kararlı sürüm için panel başlığına güncelleme bildirimi eklendi.
- Kontrol başlangıçta ve 6 saatte bir, santral servisinde yapılır; sonuç tüm panellere SSE ile iletilir.
- ETag önbelleği, 10 saniye bağlantı zaman aşımı ve API hatasında son bilinen sürümü koruma eklendi.
- GitHub'a çağrı/kişi verisi veya AMI kimlik bilgileri gönderilmez; otomatik kurulum yapılmaz.
- Sürüm karşılaştırması, ön sürüm reddi, önbellek ve hata davranışı testleri eklendi.

## 0.25.0 — 2026-10-24 (dağıtım hazırlığı)

- Sihirbaza mevcut kurulumu tanıma, --update ve --rollback seçenekleri eklendi.
- Yeni paketle sürüm karşılaştırma, dosya yedeği ve AMI sağlık kontrolü eklendi.
- Güncelleme hatasında eski uygulama dosyaları otomatik geri yüklenir.
- AMI hesapları/parolaları, metadata ve sunucu yapılandırmaları korunur.
- GitHub'dan yeni sürüm indirme, güncelleme ve geri dönüş rehberi eklendi.

Bu sürüm canlı santrale otomatik kurulmaz.

## 0.24.0 — 2026-10-24 (dağıtım hazırlığı)

- Ücretsiz kullanım açıklaması, mimari ve SSE akış diyagramları eklendi.
- Ön kontrol ve açık kurulum onayı içeren terminal kurulum sihirbazı eklendi.
- Şirkete ait adresler ve gerçek test telefon numaraları dağıtım kaynaklarından çıkarıldı.
- Temiz paket üretimi, yayın kontrolü ve GitHub sürüm notları süreci eklendi.
- VERSION dosyası oluşturuldu; panel sürümü ve önbellek anahtarları buradan üretiliyor.

Bu sürüm canlı santrale otomatik kurulmaz.

## Önceki sürümler


İlk demo 0.1.0 sayıldı. Birlikte uygulanıp yayınlanan değişiklikler tek sürüm
olarak gruplandı; ayrı kullanıcı talepleri aynı yayında tamamlandıysa iki kez
sayılmadı. Bu numaralar geçmiş yayınların geriye dönük kaydıdır.

| Sürüm | Yayınlanan değişiklik |
| --- | --- |
| 0.1.0 | İlk etkileşimli demo |
| 0.2.0 | Referansa uygun mor menü ve kompakt operatör düzeni |
| 0.3.0 | Gerçek Issabel / AMI bağlantısı ve yerel canlı panel |
| 0.4.0 | Dahili kartları, durum ışıkları ve telefon simgeleri |
| 0.5.0 | Mor üst çubuk, telefon içi durum ışığı ve geri sayım |
| 0.6.0 | Üst özet alanı, çağrı/kuyruk düzeni ve footer bilgileri |
| 0.7.0 | Çalma animasyonunun görünürlük düzeltmesi |
| 0.8.0 | dummy_endpoint kaydının trunk listesinden çıkarılması |
| 0.9.0 | Sabit çağrı kimliği, doğru durumlar ve kompakt çağrı satırları |
| 0.10.0 | ckirnak imzası |
| 0.11.0 | Hareketli HOP logosu |
| 0.12.0 | Sabit header |
| 0.13.0 | AMI olayları, SSE akışı ve canlı bağlantı göstergesi |
| 0.14.0 | Footer sayaçları ve dönüşümlü çağrı/kuyruk alanı |
| 0.15.0 | Sayaçların header'a taşınması |
| 0.16.0 | Aktif çağrılar ve kuyrukların yan yana gösterimi |
| 0.17.0 | Arama kutusunun filtrelerle aynı satıra alınması |
| 0.18.0 | Aktif çağrıların iki sütunda gösterimi |
| 0.19.0 | Gerçek trunk kayıt ışıkları ve header sayaçları |
| 0.20.0 | Kullanıcı talebiyle girişsiz salt okunur erişim |
| 0.21.0 | Dahili kartlarının küçültülmesi |
| 0.22.0 | Sade footer, tarih/saat, ortalanmış imza ve Türk bayrağı |
| 0.23.0 | Bayrak geometrisi, footer boşlukları ve sürüm sayımının düzeltilmesi |
