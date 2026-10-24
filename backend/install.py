"""Initial installation on the PBX. Abort on any existing HOP account/files."""
import sys
if __name__ != "__main__" or "--wizard-confirmed" not in sys.argv:
    raise SystemExit("Run: python3 backend/setup.py")

import hashlib
import json
import os
import pwd
import re
import secrets
import shutil
import subprocess
import time

base = os.path.dirname(os.path.abspath(__file__))
custom = '/etc/asterisk/manager_custom.conf'
with open(custom, 'rb') as f:
    original = f.read()
for path in ['/etc/asterisk/manager.conf', '/etc/asterisk/manager_additional.conf', custom]:
    with open(path, 'r') as f:
        if re.search(r'^\s*\[hop\]\s*$', f.read(), re.M):
            raise SystemExit('Existing hop AMI account; refusing to overwrite')
for path in ['/opt/hop', '/var/www/html/hop', '/etc/hop', '/etc/systemd/system/hop.service', '/etc/cron.d/hop-metadata', '/etc/httpd/conf.d/zz-hop-stream.conf']:
    if os.path.exists(path):
        raise SystemExit('Existing HOP installation: ' + path)
try:
    pwd.getpwnam('hop')
    raise SystemExit('Existing OS user hop; refusing to reuse')
except KeyError:
    pass

backup_dir = '/root/hop-backups/' + time.strftime('%Y%m%d-%H%M%S')
os.makedirs(backup_dir, mode=0o700)
print('AMI backup directory: ' + backup_dir, flush=True)
for path in ['/etc/asterisk/manager.conf', '/etc/asterisk/manager_additional.conf', custom]:
    dest = os.path.join(backup_dir, os.path.basename(path))
    shutil.copy2(path, dest)
    os.chmod(dest, 0o600)
subprocess.check_call(['useradd', '--system', '--home-dir', '/opt/hop', '--shell', '/sbin/nologin', 'hop'])
os.makedirs('/etc/hop', mode=0o700)
os.makedirs('/opt/hop', mode=0o755)
os.makedirs('/var/www/html/hop', mode=0o755)
secret = secrets.token_hex(32)
with open('/etc/hop/ami.env', 'w') as f:
    f.write('HOP_AMI_SECRET=' + secret + '\n')
os.chmod('/etc/hop/ami.env', 0o600)
for name in ['server.py', 'refresh_metadata.py', 'live.html']:
    dest = '/opt/hop/' + name
    shutil.copyfile(os.path.join(base, name), dest)
    os.chmod(dest, 0o644)
shutil.copyfile(os.path.join(base, '..', 'VERSION'), '/opt/hop/VERSION')
os.chmod('/opt/hop/VERSION', 0o644)
for src, name in [('gateway.php', 'index.php'), ('live.js', 'live.js'), ('operator.css', 'operator.css'), ('live-cards.css', 'live-cards.css')]:
    dest = '/var/www/html/hop/' + name
    shutil.copyfile(os.path.join(base, src), dest)
    os.chmod(dest, 0o644)
shutil.copyfile(os.path.join(base, 'hop.service'), '/etc/systemd/system/hop.service')
with open('/etc/cron.d/hop-metadata', 'w') as f:
    f.write('* * * * * root /usr/bin/python3 /opt/hop/refresh_metadata.py >/dev/null 2>&1\n')
os.chmod('/etc/cron.d/hop-metadata', 0o644)
subprocess.check_call(['/usr/bin/python3', '/opt/hop/refresh_metadata.py'])
block = ('\n; HOP dedicated local monitoring account\n[hop]\nsecret=' + secret + '\ndeny=0.0.0.0/0.0.0.0\npermit=127.0.0.1/255.255.255.255\nread=system,call,agent,reporting\nwrite=system,reporting\n').encode('ascii')
# Preserve every existing byte, owner and permission in the custom file.
with open(custom, 'ab') as f:
    f.write(block)
with open(custom, 'rb') as f:
    assert f.read() == original + block
subprocess.check_call(['asterisk', '-rx', 'manager reload'])
subprocess.check_call(['systemctl', 'daemon-reload'])
subprocess.check_call(['systemctl', 'enable', '--now', 'hop.service'])
shutil.copyfile(os.path.join(base, 'hop-stream.conf'), '/etc/httpd/conf.d/zz-hop-stream.conf')
subprocess.check_call(['httpd', '-t'])
subprocess.check_call(['systemctl', 'reload', 'httpd'])
with open(os.path.join(backup_dir, 'installation.json'), 'w') as f:
    json.dump({'backup': backup_dir, 'original_custom_sha256': hashlib.sha256(original).hexdigest()}, f)
print('HOP installed. Existing AMI configuration preserved. Backup: ' + backup_dir)
