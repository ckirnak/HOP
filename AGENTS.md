# HOP proje talimatları

## Sürüm ve güncelleme geçmişi

Kullanıcının kalıcı talebi: Her yayınlanan uygulama güncellemesinde sürümü artır
ve yapılan değişiklikleri `backend/CHANGELOG.md` dosyasına Türkçe yaz.

- Canlı ve GitHub son yayın: 0.25.0; sonraki uygulama değişikliği 0.26.0.
  Gerçek son sürümü her zaman güncelleme geçmişinden ve kaynaklardan doğrula.
- Aynı yayında tamamlanan değişiklikler tek sürümdür. Sadece soru yanıtlama,
  salt okunur inceleme veya çalışma talimatını kaydetme için sürüm artırma.
- Her kayıtta sürüm, Europe/Istanbul tarihine göre yayın tarihi ve ne değiştiği
  yer alsın. Yeni kayıtları geçmişe ekle; eski kayıtları silme.
- Footer'daki sürüm, kaynakta üretilen HTML ve santralde yayınlanan HTML birbiriyle
  aynı olmalı. Önbellek anahtarları uygulama sürümünün yerine geçmez.
- Yayın sonrası sunulan sürümü kontrol et. Başarısız veya tamamlanmamış yayını
  tamamlanmış bir sürüm olarak bildirme.

## Herkese açık dağıtım

- MIT lisansını ve telif bildirimini koru.
- Şirket adresleri, telefonları, hesap/parolaları, metadata ve yedekleri kaynaklara ekleme.
- GitHub için scripts/package.cjs ile temiz kaynak paketi üret; eski Git geçmişini taşıma.
- Yayın notlarını changelog üzerinden hazırla; sadece paket üretildiğinde canlıya veya GitHub’a yayınlandı deme.
