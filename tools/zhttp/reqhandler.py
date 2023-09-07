# this handler responds to every request with "hello world"

import tnetstring
import zmq

ctx = zmq.Context()
sock = ctx.socket(zmq.REP)
sock.connect('ipc://client')

while True:
    m_raw = sock.recv()
    req = tnetstring.loads(m_raw[1:])
    print(f'IN {req}')

    resp = {
        b'id': req[b'id'],
        b'code': 200,
        b'reason': b'OK',
        b'headers': [[b'Content-Type', b'text/plain']],
        b'body': b'hello world\n',
    }
    print(f'OUT {resp}')
    sock.send(b'T' + tnetstring.dumps(resp))
