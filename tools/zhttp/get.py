import sys
import uuid
import tnetstring
import zmq

if len(sys.argv) < 2:
    print(f'usage: {sys.argv[0]} [url]')
    sys.exit(1)

ctx = zmq.Context()
sock = ctx.socket(zmq.REQ)
sock.connect('ipc://server')

req = {
    b'method': b'GET',
    b'uri': sys.argv[1].encode('utf-8'),
    #b'follow-redirects': True,
    #b'ignore-tls-errors': True,
}

sock.send(b'T' + tnetstring.dumps(req))

resp = tnetstring.loads(sock.recv()[1:])
if b'type' in resp and resp[b'type'] == b'error':
    print(f"error: {resp[b'condition']}")
    sys.exit(1)

print(f"code={resp[b'code']} reason=[{resp[b'reason']}]")
for h in resp[b'headers']:
    print(f'{h[0]}: {h[1]}')

if b'body' in resp:
    print(f"\n{resp[b'body']}")
else:
    print('\n')
