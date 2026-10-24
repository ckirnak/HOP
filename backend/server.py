"""HOP local AMI monitor. Python 3.6+, standard library only."""
import copy
import json
import os
import re
import socket
import threading
import time
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn


class AMI:
    def __init__(self, secret, events='off', on_event=None):
        self.sock = socket.create_connection(('127.0.0.1', 5038), 5)
        self.buffer = b''
        self.on_event = on_event
        self.seq = 0
        self.sock.settimeout(8)
        while b'\r\n' not in self.buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError('AMI greeting missing')
            self.buffer += chunk
        self.buffer = self.buffer.split(b'\r\n', 1)[1]
        result = self.request('Login', Username='hop', Secret=secret, Events=events)
        if result[0].get('Response') != 'Success':
            self.close()
            raise RuntimeError('AMI authentication failed')

    def close(self):
        self.sock.close()

    def read(self):
        while True:
            self.buffer = self.buffer.lstrip(b'\r\n')
            if b'\r\n\r\n' in self.buffer:
                packet, self.buffer = self.buffer.split(b'\r\n\r\n', 1)
                message = {}
                for line in packet.decode('utf-8', 'replace').split('\r\n'):
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        message[key] = value
                return message
            chunk = self.sock.recv(16384)
            if not chunk:
                raise ConnectionError('AMI disconnected')
            self.buffer += chunk

    def request(self, action, complete=None, **fields):
        self.seq += 1
        aid = str(self.seq)
        fields.update(Action=action, ActionID=aid)
        wire = ''.join('{}: {}\r\n'.format(k, v) for k, v in fields.items())
        self.sock.sendall((wire + '\r\n').encode('utf-8'))
        messages = []
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            msg = self.read()
            if msg.get('ActionID') != aid:
                if self.on_event:
                    self.on_event(msg)
                continue
            messages.append(msg)
            if msg.get('Response') == 'Error':
                raise RuntimeError('{} query failed'.format(action))
            if complete and msg.get('Event') == complete:
                return messages
            if not complete and 'Response' in msg:
                return messages
        raise TimeoutError('{} query timed out'.format(action))


def extension_state(value):
    try:
        value = int(value)
    except (ValueError, TypeError):
        return 'Bilinmiyor'
    if value < 0 or value & 4:
        return 'Çevrimdışı'
    if value & 8:
        return 'Çalıyor'
    if value & 16:
        return 'Beklemede'
    if value & 3:
        return 'Görüşmede'
    return 'Müsait' if value == 0 else 'Bilinmiyor'


def duration_seconds(value):
    try:
        parts = [int(x) for x in value.split(':')]
        if len(parts) != 3:
            return 0
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except (ValueError, AttributeError):
        return 0


def build_calls(extensions, channels, queues, previous=None):
    previous = {c['id']: c for c in (previous or [])}
    groups, channel_ids, unique_ids, members = {}, {}, {}, {}
    for msg in channels:
        if msg.get('Event') != 'CoreShowChannel':
            continue
        uid = msg.get('Linkedid') or msg.get('Uniqueid') or msg.get('Channel')
        groups.setdefault(uid, []).append(msg)
        channel_ids[msg.get('Channel')] = uid
        unique_ids[msg.get('Uniqueid')] = uid
    entries = {}
    for msg in queues:
        name = msg.get('Queue')
        if msg.get('Event') == 'QueueMember':
            interface = msg.get('Location') or msg.get('Interface') or msg.get('StateInterface', '')
            match = re.match(r'(?:Local/|(?:PJSIP|SIP)/)([^@/]+)', interface)
            if match and match.group(1) in extensions:
                members.setdefault(name, set()).add(match.group(1))
        elif msg.get('Event') == 'QueueEntry':
            uid = unique_ids.get(msg.get('Uniqueid')) or channel_ids.get(msg.get('Channel'))
            if uid:
                entries[uid] = msg

    def number(value):
        value = (value or '').strip()
        return value if re.match(r'^\+?[0-9*#]+$', value) else ''

    result = []
    for uid, rows in sorted(groups.items()):
        old = previous.get(uid, {})
        rows = sorted(rows, key=lambda m: (m.get('Uniqueid') != uid, m.get('Uniqueid', ''), m.get('Channel', '')))
        devices, local_targets = [], []
        for msg in rows:
            match = re.match(r'^(?:SIP|PJSIP)/(.+)-[0-9a-f]+$', msg.get('Channel', ''))
            if match and match.group(1) in extensions:
                devices.append((match.group(1), msg))
            local = re.match(r'^Local/([^@]+)@', msg.get('Channel', ''))
            if local and local.group(1) in extensions:
                local_targets.append(local.group(1))
        queue_entry = entries.get(uid)
        queue_name = queue_entry.get('Queue') if queue_entry else None
        if not queue_name:
            queue_name = next((m.get('ApplicationData', '').split(',')[0] for m in rows if m.get('Application') == 'Queue'), None)
        # The oldest external leg identifies the original caller. Never replace
        # it with a local member's caller ID when that leg's fields change.
        external_callers = [number(m.get('CallerIDNum')) for m in rows if number(m.get('CallerIDNum')) and number(m.get('CallerIDNum')) not in extensions]
        root_source = next((number(m.get('CallerIDNum')) for m in rows if m.get('Uniqueid') == uid and number(m.get('CallerIDNum'))), '')
        source = old.get('from') or (number(queue_entry.get('CallerIDNum')) if queue_entry else '') or root_source or next(iter(external_callers), '')
        if not source:
            source = next((number(m.get('CallerIDNum')) for m in rows if number(m.get('CallerIDNum'))), '')
        answered = [(ext, m) for ext, m in devices if m.get('ChannelStateDesc') == 'Up' and m.get('BridgeId')]
        ringing = [(ext, m) for ext, m in devices if m.get('ChannelStateDesc') in ('Ring', 'Ringing')]
        # Prefer the called/answering member, not an already-Up calling phone.
        targets = [ext for ext, m in answered if ext != source] or [ext for ext, m in ringing if ext != source]
        target = next(iter(targets), '')
        if not target:
            target = old.get('to') or next(iter(local_targets), '')
        if not target and queue_name and len(members.get(queue_name, set())) == 1:
            target = next(iter(members[queue_name]))
        if not target:
            target = next((number(m.get('ConnectedLineNum')) for m in rows if number(m.get('ConnectedLineNum')) and number(m.get('ConnectedLineNum')) != source), '')
        if not target:
            target = next((m.get('Exten') for m in rows if m.get('Exten') in extensions and m.get('Exten') != source), '')
        bridged = any(other.get('BridgeId') == m.get('BridgeId') and other.get('Channel') != m.get('Channel') for ext, m in answered for other in rows)
        if answered and (any(ext == target for ext, m in answered) or bridged):
            status = 'Görüşmede'
        elif ringing:
            status = 'Çalıyor'
        elif queue_entry or queue_name:
            status = 'Kuyrukta bekliyor'
        else:
            status = 'Bağlanıyor'
        result.append({'id': uid, 'from': source, 'to': target,
                       'to_name': extensions.get(target, {}).get('name', ''),
                       'seconds': max([old.get('seconds', 0)] + [duration_seconds(m.get('Duration', '')) for m in rows]),
                       'state': status, 'queue': queue_name,
                       'extensions': sorted(set(ext for ext, m in devices)), 'channels': len(rows)})
    return result


def make_snapshot(metadata, hints, peers, endpoints, channels, queues, previous=None, registrations=None):
    extensions = copy.deepcopy(metadata.get('extensions', {}))
    trunks = []
    for p in extensions.values():
        p['status'] = 'Bilinmiyor'
    for msg in hints:
        ext = msg.get('Exten')
        if ext in extensions and msg.get('Context') in ('ext-local', 'from-internal'):
            extensions[ext]['status'] = extension_state(msg.get('Status'))
    for msg in peers:
        if msg.get('Event') != 'PeerEntry':
            continue
        ext = msg.get('ObjectName', '')
        status = msg.get('Status', '')
        offline = status.lower().startswith(('unreachable', 'unknown'))
        if ext in extensions:
            p = extensions[ext]
            p['technology'] = 'SIP'
            p['registration'] = status
            if offline:
                p['status'] = 'Çevrimdışı'
            elif p['status'] == 'Bilinmiyor' and status.lower().startswith(('ok', 'unmonitored')):
                # Unmonitored peers with no address are not registered.
                p['status'] = 'Müsait' if msg.get('IPaddress') not in ('', '-none-', '0.0.0.0', None) else 'Çevrimdışı'
        else:
            trunks.append({'id': ext, 'technology': 'SIP', 'status': status or 'Bilinmiyor'})
    for msg in endpoints:
        if msg.get('Event') != 'EndpointList':
            continue
        ext = msg.get('ObjectName', '')
        if ext == 'dummy_endpoint':
            continue  # Issabel internal fallback endpoint, not a trunk.
        status = msg.get('DeviceState', '')
        if ext in extensions:
            p = extensions[ext]
            p['technology'] = 'PJSIP'
            p['registration'] = status
            if status in ('Unavailable', 'Invalid'):
                p['status'] = 'Çevrimdışı'
            elif p['status'] == 'Bilinmiyor':
                p['status'] = {'Not in use': 'Müsait', 'In use': 'Görüşmede', 'Ringing': 'Çalıyor', 'Busy': 'Görüşmede'}.get(status, 'Bilinmiyor')
        else:
            trunks.append({'id': ext, 'technology': 'PJSIP', 'status': status or 'Bilinmiyor'})
    for msg in channels:
        if msg.get('Event') != 'CoreShowChannel':
            continue
        match = re.match(r'^(?:SIP|PJSIP)/(.+)-[0-9a-f]+$', msg.get('Channel', ''))
        if match and match.group(1) in extensions:
            ext = match.group(1)
            if msg.get('ChannelStateDesc') in ('Ringing', 'Ring'):
                extensions[ext]['status'] = 'Çalıyor'
            elif msg.get('ChannelStateDesc') == 'Up':
                extensions[ext]['status'] = 'Görüşmede'
    queue_map = {}
    for msg in queues:
        name = msg.get('Queue')
        if not name:
            continue
        queue = queue_map.setdefault(name, {'id': name, 'waiting': 0, 'members': 0, 'available': 0})
        if msg.get('Event') == 'QueueParams':
            queue['waiting'] = int(msg.get('Calls', 0))
        elif msg.get('Event') == 'QueueMember':
            queue['members'] += 1
            if msg.get('Status') == '1' and msg.get('Paused') == '0':
                queue['available'] += 1
    for trunk in trunks:
        config = metadata.get('trunks', {}).get(trunk['id'], {})
        matches = []
        for reg in registrations or []:
            if trunk['technology'] == 'SIP' and reg.get('Event') == 'RegistryEntry':
                if config.get('username') and reg.get('Username') == config['username']:
                    host = config.get('host', '').split(':')[0].lower()
                    if not host or host == reg.get('Host', '').split(':')[0].lower():
                        matches.append(reg.get('State', ''))
            elif trunk['technology'] == 'PJSIP' and reg.get('Event') == 'OutboundRegistrationDetail':
                if trunk['id'] in (reg.get('Endpoint'), reg.get('ObjectName')):
                    matches.append(reg.get('Status', ''))
        trunk['registered'] = any(s.lower() == 'registered' for s in matches)
        trunk['registration_state'] = 'Kayıtlı' if trunk['registered'] else 'Kayıtsız'
    return {'extensions': sorted(extensions.values(), key=lambda p: p['id']), 'calls': build_calls(extensions, channels, queues, previous), 'queues': list(queue_map.values()), 'trunks': trunks}


state = {'connected': False, 'updated': None, 'error': 'AMI bağlantısı kuruluyor', 'extensions': [], 'calls': [], 'queues': [], 'trunks': []}
lock = threading.Lock()
changed = threading.Condition(lock)
revision = 0
dirty = threading.Event()
event_online = False
update_info = {'status': 'checking', 'available': False, 'checked_at': None}


def release_version(value):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', str(value))
    if not match:
        raise ValueError('Unsupported release version')
    return tuple(int(n) for n in match.groups())


def release_info(release, current):
    tag = release.get('tag_name', '')
    latest = release_version(tag)
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Not a stable release')
    return {'status': 'ok', 'current': current, 'latest': '.'.join(map(str, latest)),
            'available': latest > release_version(current), 'checked_at': time.time(),
            'url': 'https://github.com/ckirnak/HOP/releases/tag/' + tag}


def fetch_release(current, etag=None, previous=None):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'HOP-Update-Checker',
               'X-GitHub-Api-Version': '2022-11-28'}
    if etag:
        headers['If-None-Match'] = etag
    request = urllib.request.Request('https://api.github.com/repos/ckirnak/HOP/releases/latest', headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            # Only release metadata is requested; no PBX data or credentials leave the server.
            body = response.read(1024 * 1024 + 1)
            if len(body) > 1024 * 1024:
                raise ValueError('Response too large')
            return release_info(json.loads(body.decode('utf-8')), current), response.headers.get('ETag')
    except urllib.error.HTTPError as error:
        if error.code == 304 and previous and previous.get('latest'):
            result = dict(previous, status='ok', checked_at=time.time(), current=current)
            result['available'] = release_version(result['latest']) > release_version(current)
            return result, etag
        raise


def check_updates():
    global update_info, revision
    etag = None
    while True:
        try:
            with open('/opt/hop/VERSION') as file:
                current = file.read().strip()
            result, etag = fetch_release(current, etag, update_info)
        except Exception:
            # Keep the last known release on network/API failure; never block AMI collection.
            result = dict(update_info, status='unavailable')
        with changed:
            update_info = result
            state['update'] = dict(result)
            revision += 1
            changed.notify_all()
        time.sleep(6 * 60 * 60)


def publish(payload):
    global revision
    with changed:
        state.clear()
        state.update(payload)
        state['update'] = dict(update_info)
        revision += 1
        changed.notify_all()


RELEVANT_EVENTS = set('Registry OutboundRegistration Newchannel Newstate Hangup DialBegin DialEnd BridgeEnter BridgeLeave BridgeDestroy NewConnectedLine ExtensionStatus DeviceStateChange PeerStatus ContactStatus EndpointList QueueCallerJoin QueueCallerLeave QueueCallerAbandon AgentCalled AgentRingNoAnswer AgentConnect AgentComplete QueueMemberStatus QueueMemberPause QueueMemberAdded QueueMemberRemoved Hold Unhold FullyBooted Reload'.split())


def ami_event(msg):
    if msg.get('Event') in RELEVANT_EVENTS:
        dirty.set()


def listen_events():
    global event_online
    while True:
        ami = None
        try:
            ami = AMI(os.environ['HOP_AMI_SECRET'], events='system,call,agent,reporting', on_event=ami_event)
            event_online = True
            dirty.set()  # Reconnect always requires a full synchronization.
            while True:
                try:
                    ami_event(ami.read())
                except socket.timeout:
                    ami.request('Ping')
        except Exception as exc:
            print('AMI event listener: {}'.format(type(exc).__name__), flush=True)
            event_online = False
            dirty.set()
            if ami:
                ami.close()
            time.sleep(3)


def collect():
    ami = None
    while True:
        try:
            if ami is None:
                ami = AMI(os.environ['HOP_AMI_SECRET'])
            with open('/opt/hop/metadata.json', encoding='utf-8') as f:
                metadata = json.load(f)
            hints = ami.request('ExtensionStateList', 'ExtensionStateListComplete')
            peers = ami.request('SIPpeers', 'PeerlistComplete')
            endpoints = ami.request('PJSIPShowEndpoints', 'EndpointListComplete')
            channels = ami.request('CoreShowChannels', 'CoreShowChannelsComplete')
            queues = ami.request('QueueStatus', 'QueueStatusComplete')
            registrations = ami.request('SIPshowregistry', 'RegistrationsComplete')
            registrations += ami.request('PJSIPShowRegistrationsOutbound', 'OutboundRegistrationDetailComplete')
            snapshot = make_snapshot(metadata, hints, peers, endpoints, channels, queues, state.get('calls', []), registrations)
            snapshot.update(connected=event_online, updated=time.time(), error=None if event_online else 'AMI olay bağlantısı yeniden kuruluyor.')
            publish(snapshot)
            dirty.wait(60)  # Reconciliation only; ordinary changes wake us immediately.
            dirty.clear()
            time.sleep(.1)  # Coalesce a single call's event burst.
        except Exception as exc:
            # No credentials or AMI payloads are logged.
            print('AMI monitor: {}'.format(type(exc).__name__), flush=True)
            with lock:
                failed = copy.deepcopy(state)
            failed.update(connected=False, error='Santral bağlantısı kesildi; yeniden deneniyor.')
            publish(failed)
            if ami:
                ami.close()
                ami = None
            time.sleep(5)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store')
            self.end_headers()
            last = -1
            try:
                while True:
                    with changed:
                        if last == revision:
                            changed.wait(10)
                        current = revision
                        payload = copy.deepcopy(state)
                    if current != last:
                        packet = 'event: state\ndata: {}\n\n'.format(json.dumps(payload, ensure_ascii=False))
                        last = current
                    else:
                        packet = 'event: heartbeat\ndata: {}\n\n'
                    self.wfile.write(packet.encode('utf-8'))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            return
        if self.path != '/state':
            self.send_error(404)
            return
        with lock:
            payload = copy.deepcopy(state)
        if payload['updated'] and time.time() - payload['updated'] > 90:
            payload['connected'] = False
            payload['error'] = 'Veriler güncel değil; bağlantı kontrol ediliyor.'
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class Server(ThreadingMixIn, HTTPServer):
    daemon_threads = True


if __name__ == '__main__':
    threading.Thread(target=check_updates, daemon=True).start()
    threading.Thread(target=listen_events, daemon=True).start()
    threading.Thread(target=collect, daemon=True).start()
    Server(('127.0.0.1', 8765), Handler).serve_forever()
