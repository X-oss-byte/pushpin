# this handler responds to every request with "hello world"

import os
import time
import tnetstring
import zmq

instance_id = f'basichandler.{os.getpid()}'.encode()

ctx = zmq.Context()
in_sock = ctx.socket(zmq.PULL)
in_sock.connect('ipc://client-out')
out_sock = ctx.socket(zmq.PUB)
out_sock.connect('ipc://client-in')

# await subscription
time.sleep(0.01)

while True:
    m_raw = in_sock.recv()
    req = tnetstring.loads(m_raw[1:])
    print(f'IN {req}')

    resp = {
        b'from': instance_id,
        b'id': req[b'id'],
        b'code': 200,
        b'reason': b'OK',
        b'headers': [[b'Content-Type', b'text/plain']],
        b'body': b'hello world\n',
    }
    print(f'OUT {resp}')
    out_sock.send(req[b'from'] + b' T' + tnetstring.dumps(resp))
