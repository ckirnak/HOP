"""Run as root; publish only extension IDs/names, never SIP credentials."""
import json
import os
import re


def sections(path):
    current = None
    fields = {}
    if not os.path.isfile(path):
        return
    with open(path, encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.strip()
            match = re.match(r'^\[([^\]]+)\]', line)
            if match:
                if current is not None:
                    yield current, fields
                current, fields = match.group(1), {}
            elif '=' in line and not line.startswith((';', '#')):
                key, value = line.split('=', 1)
                if key.strip().lower() in ('type', 'callerid', 'username', 'defaultuser', 'host'):
                    fields[key.strip().lower()] = value.strip()
        if current is not None:
            yield current, fields


def refresh():
    extensions = {}
    trunks = {}
    for tech, path in [('SIP', '/etc/asterisk/sip_additional.conf'), ('PJSIP', '/etc/asterisk/pjsip_additional.conf')]:
        for ext, fields in sections(path):
            if tech == 'SIP' and 'callerid' not in fields:
                trunks[ext] = {'username': fields.get('username') or fields.get('defaultuser', ''), 'host': fields.get('host', '')}
            if not ext.isdigit() or 'callerid' not in fields:
                continue
            if tech == 'PJSIP' and fields.get('type') != 'endpoint':
                continue
            name = re.sub(r'\s*<[^>]*>\s*$', '', fields['callerid']).strip().strip('"')
            extensions[ext] = {'id': ext, 'name': name or ext, 'technology': tech}
    target = '/opt/hop/metadata.json'
    temp = target + '.tmp'
    with open(temp, 'w', encoding='utf-8') as f:
        json.dump({'extensions': extensions, 'trunks': trunks}, f, ensure_ascii=False)
    os.chmod(temp, 0o644)
    os.replace(temp, target)
    print('Extension metadata refreshed: {}'.format(len(extensions)))


if __name__ == '__main__':
    refresh()
