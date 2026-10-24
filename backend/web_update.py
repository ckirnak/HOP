"""Root-owned one-shot updater. Accepts no URL, command or path from the web."""
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import time
import urllib.request
import zipfile
from update import Updater, version_number

STATUS = Path('/var/lib/hop-web-update/status.json')


def status(state, message):
    STATUS.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    temp = STATUS.with_suffix('.tmp')
    temp.write_text(json.dumps({'state': state, 'message': message, 'updated': time.time()}))
    os.chmod(str(temp), 0o644)
    os.replace(str(temp), str(STATUS))


def release_asset(release, current):
    tag = release.get('tag_name', '')
    if release.get('draft') or release.get('prerelease') or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Kararlı sürüm etiketi doğrulanamadı.')
    version = tag[1:]
    if version_number(version) <= version_number(current):
        return None
    name = 'HOP-' + version + '-source.zip'
    url = 'https://github.com/ckirnak/HOP/releases/download/' + tag + '/' + name
    assets = [a for a in release.get('assets', []) if a.get('name') == name and a.get('browser_download_url') == url]
    if len(assets) != 1 or not re.fullmatch(r'sha256:[a-f0-9]{64}', assets[0].get('digest') or ''):
        raise ValueError('Sürüm paketi veya GitHub SHA-256 özeti doğrulanamadı.')
    return version, url, assets[0]['digest'][7:]


def unpack(data, destination, version):
    archive = destination / 'source.zip'
    archive.write_bytes(data)
    prefix = 'hop-' + version
    with zipfile.ZipFile(str(archive)) as zipped:
        if len(zipped.infolist()) > 500 or sum(i.file_size for i in zipped.infolist()) > 40 * 1024 * 1024:
            raise ValueError('Paket boyutu sınırı aşıldı.')
        for item in zipped.infolist():
            path = PurePosixPath(item.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in item.filename or not path.parts or path.parts[0] != prefix or (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Paket yolu güvenli değil.')
        zipped.extractall(str(destination))
    source = destination / prefix
    if (source / 'VERSION').read_text().strip() != version:
        raise ValueError('Paket sürümü uyuşmuyor.')
    for line in (source / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name:
            raise ValueError('Özet dosyasında geçersiz yol.')
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Paket dosyası özeti uyuşmuyor.')
    return source / 'backend'


def main():
    with open('/run/lock/hop-update.lock', 'w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            status('busy', 'Başka bir güncelleme çalışıyor. Tamamlanmasını bekleyin.')
            return
        try:
            status('checking', 'GitHub son kararlı sürümü kontrol ediliyor…')
            current = Path('/opt/hop/VERSION').read_text().strip()
            req = urllib.request.Request('https://api.github.com/repos/ckirnak/HOP/releases/latest', headers={'User-Agent':'HOP-Web-Updater','Accept':'application/vnd.github+json'})
            with urllib.request.urlopen(req, timeout=15) as response:
                release = json.loads(response.read(1024 * 1024))
            asset = release_asset(release, current)
            if asset is None:
                status('current', 'Zaten güncelsiniz: ' + current)
                return
            version, url, digest = asset
            status('downloading', version + ' paketi indiriliyor…')
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read(10 * 1024 * 1024 + 1)
            if len(data) > 10 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('İndirilen paketin SHA-256 doğrulaması başarısız.')
            with tempfile.TemporaryDirectory(prefix='hop-web-update-') as folder:
                source = unpack(data, Path(folder), version)
                updater = Updater(source)
                updater.check()
                status('installing', 'Yedek alınıyor ve ' + version + ' kuruluyor. Panel kısa süre yeniden bağlanabilir…')
                installed, backup = updater.apply()
            status('done', installed + ' kuruldu. Paneli yenileyin. Yedek: ' + str(backup))
        except Exception as error:
            # Exception class only: never expose request headers, credentials or response bodies.
            status('error', 'Güncelleme tamamlanamadı (' + type(error).__name__ + '). Yönetici journalctl -u hop-web-update ile kontrol edebilir.')
            print('HOP web update failed: ' + type(error).__name__, flush=True)


if __name__ == '__main__':
    main()
