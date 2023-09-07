import sys
import zmq

if len(sys.argv) < 2:
    print(f'usage: {sys.argv[0]} [pub_spec]')
    sys.exit(1)

spec = sys.argv[1]

zmq_context = zmq.Context.instance()
sock = zmq_context.socket(zmq.XPUB)
sock.rcvhwm = 0
if hasattr(sock, 'immediate'):
    sock.immediate = 1
sock.connect(spec)

while True:
    m = sock.recv()
    mtype = int(m[0])
    topic = m[1:].decode('utf-8')
    if mtype == 0:
        print(f'UNSUB {topic}')
    elif mtype == 1:
        print(f'SUB {topic}')
