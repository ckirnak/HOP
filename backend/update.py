"""Local-package updates. Credentials, AMI and web/service configuration are untouched."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

FILES = {'server.py': '/opt/hop/server.py', 'refresh_metadata.py': '/opt/hop/refresh_metadata.py',
         'live.html': '/opt/hop/live.html', 'gateway.php': '/var/www/html/hop/index.php',
         'live.js': '/var/www/html/hop/live.js', 'operator.css': '/var/www/html/hop/operator.css',
         'live-cards.css': '/var/www/html/hop/live-cards.css', '../VERSION': '/opt/hop/VERSION'}


def version_number(value):
    if not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError('Geçersiz sürüm: ' + value)
    return tuple(int(n) for n in value.split('.'))


def healthy():
    import urllib.request
    for attempt in range(15):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8765/state', timeout=3) as response:
                if json.load(response).get('connected'):
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


class Updater:
    def __init__(self, source, root=Path('/'), run=subprocess.check_call, health=healthy):
        self.source, self.root, self.run, self.health = Path(source), Path(root), run, health
        self.backups = self.target('/root/hop-update-backups')

    def target(self, path):
        return self.root / path.lstrip('/')

    def current(self):
        marker = self.target('/opt/hop/VERSION')
        if marker.exists():
            value = marker.read_text().strip()
        else:
            match = re.search(r'HOP v(\d+\.\d+\.\d+)', self.target('/opt/hop/live.html').read_text())
            if not match:
                raise ValueError('Kurulu sürüm belirlenemedi.')
            value = match.group(1)
        version_number(value)
        return value

    def check(self):
        new = (self.source.parent / 'VERSION').read_text().strip()
        old = self.current()
        if version_number(new) <= version_number(old):
            raise ValueError('Paket daha yeni olmalı: kurulu ' + old + ', paket ' + new)
        for name, dest in FILES.items():
            source, target = self.source / name, self.target(dest)
            if not source.is_file() or source.is_symlink():
                raise ValueError('Eksik/geçersiz paket dosyası: ' + name)
            if target.is_symlink() or any(p.is_symlink() for p in target.parents):
                raise ValueError('Sembolik bağlantı hedefi desteklenmez: ' + dest)
            if name != '../VERSION' and not target.is_file():
                raise ValueError('Eksik kurulum dosyası: ' + dest)
        for required in ['/etc/hop/ami.env', '/etc/systemd/system/hop.service']:
            if not self.target(required).is_file():
                raise ValueError('Mevcut HOP kurulumu bulunamadı: ' + required)
        if 'HOP v' + new not in (self.source / 'live.html').read_text():
            raise ValueError('Paket HTML sürümü VERSION ile uyuşmuyor.')
        for name in ['server.py', 'refresh_metadata.py']:
            compile((self.source / name).read_text(), name, 'exec')
        return old, new

    @staticmethod
    def atomic_copy(source, dest):
        # Stage on the same filesystem; preserve existing ownership and SELinux xattrs.
        fd, temp = tempfile.mkstemp(prefix='.hop-update-', dir=str(dest.parent))
        os.close(fd)
        try:
            if dest.exists():
                stat = dest.stat()
                shutil.copy2(str(dest), temp)
                os.chown(temp, stat.st_uid, stat.st_gid)
            else:
                os.chmod(temp, 0o644)
            with open(source, 'rb') as src, open(temp, 'wb') as dst:
                shutil.copyfileobj(src, dst)
                dst.flush()
                os.fsync(dst.fileno())
            os.replace(temp, str(dest))
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    def restore(self, backup):
        backup = Path(backup).resolve()
        if backup.parent != self.backups.resolve():
            raise ValueError('Yalnızca HOP güncelleme yedekleri kullanılabilir.')
        manifest = json.loads((backup / 'manifest.json').read_text())
        if set(manifest['files']) != set(FILES.values()):
            raise ValueError('Yedek dosya listesi geçersiz.')
        # Validate every backup before changing any live file.
        for dest, exists in manifest['files'].items():
            src = backup / dest.lstrip('/')
            if exists and not src.is_file():
                raise ValueError('Eksik yedek: ' + dest)
        self.run(['systemctl', 'stop', 'hop'])
        for dest, exists in manifest['files'].items():
            target = self.target(dest)
            if exists:
                self.atomic_copy(backup / dest.lstrip('/'), target)
            elif target.exists():
                target.unlink()
        self.run(['systemctl', 'start', 'hop'])
        return manifest['old']

    def apply(self):
        old, new = self.check()
        if not self.health():
            raise RuntimeError('Güncelleme öncesi AMI sağlıklı değil; dosyalar değiştirilmedi.')
        self.backups.mkdir(mode=0o700, parents=True, exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix=time.strftime('%Y%m%d-%H%M%S-'), dir=str(self.backups)))
        manifest = {'old': old, 'new': new, 'files': {}}
        for dest in FILES.values():
            target = self.target(dest)
            manifest['files'][dest] = target.exists()
            if target.exists():
                copy = backup / dest.lstrip('/')
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(target), str(copy))
        (backup / 'manifest.json').write_text(json.dumps(manifest))
        print('Geri dönüş yedeği: ' + str(backup), flush=True)
        try:
            self.run(['systemctl', 'stop', 'hop'])
            for name, dest in FILES.items():
                self.atomic_copy(self.source / name, self.target(dest))
            self.run(['systemctl', 'start', 'hop'])
            if not self.health():
                raise RuntimeError('Yeni sürümün AMI bağlantısı doğrulanamadı.')
        except Exception as error:
            self.restore(backup)
            restored = self.health()
            raise RuntimeError('Güncelleme başarısız; eski dosyalar geri alındı. Eski bağlantı: ' +
                               ('sağlıklı' if restored else 'doğrulanamadı') + '. Neden: ' + str(error))
        return new, backup


def wizard(source, check_only=False, rollback=None):
    import platform
    if platform.system() != 'Linux' or os.geteuid() != 0:
        print('Güncelleme Linux santral üzerinde root gerektirir.')
        return 1
    import fcntl
    with open('/run/lock/hop-update.lock', 'w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            updater = Updater(source)
            if rollback:
                if check_only:
                    raise ValueError('--rollback ve --check birlikte kullanılamaz.')
                if input('Önceki uygulama dosyalarına dönmek için GERI yazın: ') != 'GERI':
                    return 0
                old = updater.restore(rollback)
                if not updater.health():
                    raise RuntimeError('Dosyalar geri alındı fakat AMI doğrulanamadı.')
                print('Geri dönülen sürüm: ' + old)
                return 0
            old, new = updater.check()
            subprocess.check_call(['php', '-l', str(Path(source) / 'gateway.php')])
            print('Kurulu: ' + old + ' → Yeni: ' + new)
            print('Yeni sürümler: GitHub Releases ZIP indir → aç → sudo bash install.sh --update')
            print('AMI hesabı/parolası ve sunucu ayarları korunur. Yalnız HOP kısa süre durur.')
            print('Yerel arayüz/kod düzenlemeleri paketteki dosyalarla değiştirilir; önce yedek alınır.')
            print('Sürüm notları: ' + str(Path(source) / 'CHANGELOG.md'))
            if check_only:
                return 0
            if input('Güncellemek için GUNCELLE yazın: ') != 'GUNCELLE':
                return 0
            version, backup = updater.apply()
            print('Güncellendi: ' + version + '. Tarayıcıyı yenileyip footer ve canlı göstergeyi kontrol edin.')
            print('Geri alma: sudo bash install.sh --rollback ' + str(backup))
            return 0
        except Exception as error:
            print('HATA: ' + str(error))
            return 1
