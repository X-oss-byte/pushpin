# this handler responds to every request with "hello world"

import os
import tnetstring
import zmq

instance_id = f'streamhandler.{os.getpid()}'.encode('utf-8')

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

while True:
    socks = dict(poller.poll(None))

    if socks.get(in_sock) == zmq.POLLIN:
        m_raw = in_sock.recv()
    elif socks.get(in_stream_sock) == zmq.POLLIN:
        m_list = in_stream_sock.recv_multipart()
        m_raw = m_list[2]
    else:
        continue

    req = tnetstring.loads(m_raw[1:])
    print(f'IN {req}')

    if req.get(b'type'):
        # skip all non-data messages
        continue

    resp = {b'from': instance_id}
    if req.get(b'uri', b'').startswith(b'ws'):
        resp[b'id'] = req[b'id']
        resp[b'seq'] = 0
        resp[b'code'] = 101
        resp[b'reason'] = b'Switching Protocols'
        resp[b'credits'] = 1024

        print(f"OUT {req[b'from']} {resp}")
        out_sock.send(req[b'from'] + b' T' + tnetstring.dumps(resp))

        resp = {b'from': instance_id}
        resp[b'id'] = req[b'id']
        resp[b'seq'] = 1
        resp[b'body'] = b'hello world'

        print(f"OUT {req[b'from']} {resp}")
        out_sock.send(req[b'from'] + b' T' + tnetstring.dumps(resp))

        resp = {b'from': instance_id}
        resp[b'id'] = req[b'id']
        resp[b'seq'] = 2
        resp[b'type'] = b'close'

        print(f"OUT {req[b'from']} {resp}")
        out_sock.send(req[b'from'] + b' T' + tnetstring.dumps(resp))
    else:
        resp[b'id'] = req[b'id']
        resp[b'seq'] = 0
        resp[b'code'] = 200
        resp[b'reason'] = b'OK'
        resp[b'headers'] = [[b'Content-Type', b'text/plain']]
        resp[b'more'] = True
        resp[b'credits'] = 1024

        print(f"OUT {req[b'from']} {resp}")
        out_sock.send(req[b'from'] + b' T' + tnetstring.dumps(resp))

        resp = {b'from': instance_id}
        resp[b'id'] = req[b'id']
        resp[b'seq'] = 1
        resp[b'body'] = b'hello world\n'

        print(f"OUT {req[b'from']} {resp}")
        out_sock.send(req[b'from'] + b' T' + tnetstring.dumps(resp))
