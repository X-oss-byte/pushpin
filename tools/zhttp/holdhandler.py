# this handler holds all connections open

import os
import time
import datetime
import calendar
import tnetstring
import zmq

CONN_TTL = 60000
EXPIRE_INTERVAL = 60000

instance_id = f'holdhandler.{os.getpid()}'.encode('utf-8')

ctx = zmq.Context()
in_sock = ctx.socket(zmq.PULL)
in_sock.connect('ipc://client-out')
in_stream_sock = ctx.socket(zmq.ROUTER)
in_stream_sock.identity = instance_id
in_stream_sock.connect('ipc://client-out-stream')
out_sock = ctx.socket(zmq.PUB)
out_sock.connect('ipc://client-in')

poller = zmq.Poller()
poller.register(in_sock, zmq.POLLIN)
poller.register(in_stream_sock, zmq.POLLIN)

class Connection(object):
    def __init__(self, rid):
        self.rid = rid
        self.seq = 0
        self.exp_time = None

    def send_msg(self, msg):
        msg[b'from'] = instance_id
        msg[b'id'] = self.rid[1]
        msg[b'seq'] = self.seq
        self.seq += 1

        print(f'OUT {self.rid[0]} {msg}')
        out_sock.send(self.rid[0] + b' T' + tnetstring.dumps(msg))

    def send_header(self):
        msg = {
            b'code': 200,
            b'reason': b'OK',
            b'headers': [[b'Content-Type', b'text/plain']],
            b'more': True,
        }
        self.send_msg(msg)

    def send_body(self, data):
        msg = {b'body': data, b'more': True}
        self.send_msg(msg)

def send_body(to_addr, conns, data):
    ids = []
    for c in conns:
        ids.append({b'id': c.rid[1], b'seq': c.seq})
        c.seq += 1

    msg = {b'from': instance_id, b'id': ids, b'body': data, b'more': True}
    print(f'OUT {to_addr} {msg}')
    out_sock.send(to_addr + b' T' + tnetstring.dumps(msg))

conns = {}
last_exp_time = int(time.time())

while True:
    socks = dict(poller.poll(1000))

    if socks.get(in_sock) == zmq.POLLIN:
        m_raw = in_sock.recv()
    elif socks.get(in_stream_sock) == zmq.POLLIN:
        m_list = in_stream_sock.recv_multipart()
        m_raw = m_list[2]
    else:
        m_raw = None

    now = int(time.time() * 1000)

    if m_raw is not None:
        req = tnetstring.loads(m_raw[1:])
        print(f'IN {req}')

        m_from = req[b'from']
        m_id = req[b'id']
        m_type = req.get(b'type', b'')

        ids = []
        if isinstance(m_id, list):
            ids.extend(id_seq[b'id'] for id_seq in m_id)
        else:
            ids.append(m_id)

        new_ids = []
        known_conns = []
        for i in ids:
            rid = (m_from, i)

            c = conns.get(rid)
            if c:
                c.exp_time = now + CONN_TTL
                known_conns.append(c)
            else:
                new_ids.append(rid)

        # data
        if not m_type:
            for rid in new_ids:
                c = Connection(rid)
                conns[rid] = c
                c.exp_time = now + CONN_TTL
                c.send_header()
        elif c:
            if m_type == b'keep-alive':
                dt = datetime.datetime.utcnow()
                ts = calendar.timegm(dt.timetuple())

                body = (
                    'id: TCPKaliMsgTS-{:016x}.\n'
                    'event: message\n'
                    'data: {:04}-{:02}-{:02}T{:02}:{:02}:{:02}\n\n'
                ).format(
                    (ts * 1000000) + dt.microsecond,
                    dt.year,
                    dt.month,
                    dt.day,
                    dt.hour,
                    dt.minute,
                    dt.second
                ).encode()

                send_body(m_from, known_conns, body)
            elif m_type == b'cancel':
                for c in known_conns:
                    del conns[c.rid]

    if now >= last_exp_time + EXPIRE_INTERVAL:
        last_exp_time = now

        to_remove = []
        for rid, c in conns.items():
            if last_exp_time >= c.exp_time:
                to_remove.append(rid)
        for rid in to_remove:
            print(f'expired {rid}')
            del conns[rid]
