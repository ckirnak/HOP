"""Interactive first-install wizard; Python 3.6+, no external dependencies."""
import argparse
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
TARGETS = ['/opt/hop', '/etc/hop', '/var/www/html/hop',
           '/etc/systemd/system/hop.service', '/etc/cron.d/hop-metadata',
           '/etc/httpd/conf.d/zz-hop-stream.conf']


def preflight():
    errors = []
    if platform.system() != 'Linux' or os.geteuid() != 0:
        return ['Kurulum Linux santral üzerinde root yetkisi gerektirir.']
    for command in ['asterisk', 'systemctl', 'httpd', 'php', 'useradd']:
        if not shutil.which(command):
            errors.append('Eksik komut: ' + command)
    for path in ['/etc/asterisk/manager.conf', '/etc/asterisk/manager_custom.conf',
                 '/run/php-fpm/www.sock', '/usr/bin/python3', '/var/www/html']:
        if not os.path.exists(path):
            errors.append('Desteklenen kurulum yolu bulunamadı: ' + path)
    for path in TARGETS:
        if os.path.exists(path):
            errors.append('Mevcut kurulumun üzerine yazılmayacak: ' + path)
    import pwd
    try:
        pwd.getpwnam('hop')
        errors.append('hop sistem kullanıcısı zaten var.')
    except KeyError:
        pass
    for path in Path('/etc/asterisk').glob('manager*.conf'):
        if re.search(r'^\s*\[hop\]\s*$', path.read_text(errors='replace'), re.M):
            errors.append('Mevcut hop AMI hesabı bulundu: ' + str(path))
    manager = Path('/etc/asterisk/manager.conf')
    if manager.exists() and not re.search(r'^\s*#(?:try)?include\s+["<]?manager_custom\.conf', manager.read_text(), re.M):
        errors.append('manager.conf doğrudan manager_custom.conf içermeli; otomatik değiştirilmez.')
    try:
        with socket.create_connection(('127.0.0.1', 5038), 3):
            pass
    except OSError:
        errors.append('Yerel AMI 127.0.0.1:5038 erişilemiyor.')
    try:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 8765))
    except OSError:
        errors.append('HOP portu 8765 kullanımda.')
    if shutil.which('httpd'):
        result = subprocess.run(['httpd', '-M'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        modules = result.stdout.decode(errors='replace')
        if result.returncode or 'proxy_fcgi_module' not in modules:
            errors.append('Apache proxy_fcgi modülü gerekli.')
    if shutil.which('php'):
        result = subprocess.run(['php', '-r', 'exit(ini_get("allow_url_fopen") ? 0 : 1);'])
        if result.returncode:
            errors.append('PHP allow_url_fopen açık olmalı; FPM ayarını da doğrulayın.')
    for name in ['server.py', 'refresh_metadata.py', 'live.html', 'live.js',
                 'live-cards.css', 'operator.css', 'gateway.php', 'hop.service', 'hop-stream.conf']:
        if not (BASE / name).is_file():
            errors.append('Paket dosyası eksik: ' + name)
    return errors


def main():
    parser = argparse.ArgumentParser(description='HOP kurulum ve güncelleme sihirbazı')
    parser.add_argument('--check', action='store_true', help='Sadece ön kontroller; değişiklik yapmaz')
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--update', action='store_true', help='İndirilen paketle mevcut HOP kurulumunu güncelle')
    actions.add_argument('--rollback', metavar='YEDEK', help='Güncelleme yedeğine geri dön')
    args = parser.parse_args()
    print('HOP — Ücretsiz HTML Operator Panel | Kurulum ve güncelleme sihirbazı')
    if sys.version_info < (3, 6):
        print('Python 3.6 veya daha yeni bir sürüm gerekir.')
        return 1
    if args.update or args.rollback:
        from update import wizard
        return wizard(BASE, args.check, args.rollback)
    if Path('/opt/hop/live.html').exists():
        print('Mevcut HOP bulundu. Güncelleme: sudo bash install.sh --update')
        if not args.check and input('Güncelleme sihirbazına geçmek için G yazın: ').strip().upper() == 'G':
            from update import wizard
            return wizard(BASE)
        return 1
    print('1/3 Uyumluluk ve çakışma kontrolü')
    errors = preflight()
    if errors:
        for error in errors:
            print('  HATA: ' + error)
        return 1
    print('Ön kontroller başarılı.')
    if args.check:
        return 0
    print('\n2/3 Kurulum özeti')
    print('Yerel hop AMI hesabı ve rastgele parola oluşturulacak. Mevcut hesaplar korunur.')
    print('Dosyalar: /opt/hop, /etc/hop, /var/www/html/hop; systemd servisi ve dakika cron görevi.')
    print('AMI ayarları yeniden yüklenir; Asterisk yeniden başlatılmaz. Apache yeniden yüklenir.')
    print('Panel giriş istemez: URL erişimi olanlar çağrı numaralarını ve dahili adlarını görebilir.')
    print('Erişimi kurum ağı/VPN veya mevcut reverse proxy ile sınırlandırın.')
    if input('Bu kurulum için KUR yazın (diğer yanıtlar iptal): ').strip() != 'KUR':
        print('İptal edildi; değişiklik yapılmadı.')
        return 0
    print('\n3/3 Kurulum ve bağlantı kontrolü')
    result = subprocess.run([sys.executable, str(BASE / 'install.py'), '--wizard-confirmed'])
    if result.returncode:
        print('Kurulum tamamlanmadı. Tekrar çalıştırmadan önce docs/INSTALL.md geri alma bölümünü izleyin.')
        return result.returncode
    import json
    import time
    import urllib.request
    connected = False
    for attempt in range(10):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8765/state', timeout=3) as response:
                connected = bool(json.load(response).get('connected'))
            if connected:
                break
        except Exception:
            pass
        time.sleep(1)
    if not connected:
        print('Dosyalar kuruldu ancak AMI bağlantısı doğrulanamadı. journalctl -u hop ile inceleyin.')
        return 1
    print('AMI bağlantısı doğrulandı. Mevcut santral HTTPS adresinizin /hop/ yolunu açın.')
    print('Tarayıcıda canlı göstergeyi doğrulayın; HTTPS/FPM/SELinux kontrolü için kurulum rehberine bakın.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
