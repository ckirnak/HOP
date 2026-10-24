import unittest
import socket
from server import AMI, ami_event, dirty
from server import extension_state, make_snapshot, duration_seconds, build_calls


class MonitorTests(unittest.TestCase):
    def test_ami_parser_keeps_partial_frames_after_timeout(self):
        reader, writer = socket.socketpair()
        ami = AMI.__new__(AMI)
        ami.sock, ami.buffer = reader, b''
        reader.settimeout(.02)
        try:
            writer.sendall(b'Event: Newstate\r\nChannel: SIP/300')
            with self.assertRaises(socket.timeout):
                ami.read()
            writer.sendall(b'-0001\r\n\r\nEvent: Hangup\r\nUniqueid: 1\r\n\r\n')
            self.assertEqual(ami.read()['Event'], 'Newstate')
            self.assertEqual(ami.read()['Event'], 'Hangup')
        finally:
            reader.close()
            writer.close()

    def test_only_relevant_events_wake_snapshot_queries(self):
        dirty.clear()
        ami_event({'Event': 'PeerlistComplete'})
        self.assertFalse(dirty.is_set())
        ami_event({'Event': 'Newstate'})
        self.assertTrue(dirty.is_set())
        dirty.clear()
    def test_inbound_queue_ring_answer_retry_and_order(self):
        ext = {'300': {'id': '300', 'name': 'Santral'}}
        root = dict(Event='CoreShowChannel', Uniqueid='1', Linkedid='1', Channel='SIP/carrier-0001', CallerIDNum='12025550123', ConnectedLineNum='<unknown>', Application='Queue', ApplicationData='500,t', ChannelStateDesc='Up', Duration='00:00:10')
        device = dict(Event='CoreShowChannel', Uniqueid='4', Linkedid='1', Channel='PJSIP/300-000a', CallerIDNum='300', ConnectedLineNum='12025550123', ChannelStateDesc='Ringing', Duration='00:00:02')
        queues = [dict(Event='QueueMember', Queue='500', Location='Local/300@from-queue/n'), dict(Event='QueueEntry', Queue='500', Channel=root['Channel'], Uniqueid='1', CallerIDNum='12025550123')]
        waiting = build_calls(ext, [root], queues)
        self.assertEqual(waiting[0]['state'], 'Kuyrukta bekliyor')
        self.assertEqual(waiting[0]['to'], '300')
        ring = build_calls(ext, [device, root], queues, waiting)
        reversed_ring = build_calls(ext, [root, device], queues, waiting)
        self.assertEqual(ring, reversed_ring)
        self.assertEqual(ring[0]['state'], 'Çalıyor')
        self.assertEqual((ring[0]['from'], ring[0]['to_name']), ('12025550123', 'Santral'))
        retry = build_calls(ext, [dict(root, CallerIDNum='<unknown>')], queues, ring)
        self.assertEqual((retry[0]['from'], retry[0]['to'], retry[0]['state']), ('12025550123', '300', 'Kuyrukta bekliyor'))
        answered = build_calls(ext, [dict(device, ChannelStateDesc='Up', BridgeId='bridge'), dict(root, BridgeId='bridge')], [], ring)
        self.assertEqual(answered[0]['state'], 'Görüşmede')
        self.assertEqual(build_calls(ext, [], [], answered), [])

    def test_two_calls_same_member_do_not_share_status(self):
        ext = {'300': {'id': '300', 'name': 'Santral'}}
        root = dict(Event='CoreShowChannel', Uniqueid='1', Linkedid='1', Channel='SIP/carrier-0001', CallerIDNum='12025550101', Application='Queue', ApplicationData='500', ChannelStateDesc='Up')
        other = dict(root, Uniqueid='2', Linkedid='2', Channel='SIP/carrier-0002', CallerIDNum='12025550102')
        device = dict(root, Uniqueid='3', Linkedid='1', Channel='PJSIP/300-000a', CallerIDNum='300', ChannelStateDesc='Ringing')
        calls = build_calls(ext, [root, other, device], [dict(Event='QueueMember', Queue='500', Location='Local/300@from-queue/n')])
        self.assertEqual([c['state'] for c in calls], ['Çalıyor', 'Kuyrukta bekliyor'])
        self.assertEqual([c['from'] for c in calls], ['12025550101', '12025550102'])
    def test_combined_states_and_invalid(self):
        self.assertEqual(extension_state(9), 'Çalıyor')
        self.assertEqual(extension_state(-1), 'Çevrimdışı')
        self.assertEqual(extension_state(16), 'Beklemede')
        self.assertEqual(extension_state(None), 'Bilinmiyor')

    def test_group_channels_by_linkedid_and_no_secret_leak(self):
        meta = {'extensions': {'101': {'id': '101', 'name': '<b>A</b>'}}}
        channels = [dict(Event='CoreShowChannel', Linkedid='call1', Channel='SIP/101-00000a', ChannelStateDesc='Up', Duration='00:01:05'), dict(Event='CoreShowChannel', Linkedid='call1', Channel='SIP/trunk-00000b', ChannelStateDesc='Up', Duration='00:01:02')]
        result = make_snapshot(meta, [], [], [], channels, [])
        self.assertEqual(len(result['calls']), 1)
        self.assertEqual(result['calls'][0]['channels'], 2)
        self.assertEqual(result['calls'][0]['seconds'], 65)
        self.assertEqual(result['extensions'][0]['status'], 'Görüşmede')
        self.assertNotIn('status', meta['extensions']['101'])

    def test_unknown_not_treated_as_available_and_trunks_separate(self):
        meta = {'extensions': {'101': {'id': '101'}}}
        result = make_snapshot(meta, [], [{'Event': 'PeerEntry', 'ObjectName': 'carrier', 'Status': 'OK (5 ms)'}], [], [], [])
        self.assertEqual(result['extensions'][0]['status'], 'Bilinmiyor')
        self.assertEqual(result['trunks'][0]['id'], 'carrier')
        self.assertEqual(duration_seconds('garbage'), 0)


if __name__ == '__main__':
    unittest.main()
