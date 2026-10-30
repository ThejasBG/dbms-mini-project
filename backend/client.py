import json,socket,struct
from backend.config import TCP_HOST,TCP_PORT
def request(payload,timeout=20):
    b=json.dumps(payload).encode()
    with socket.create_connection((TCP_HOST,TCP_PORT),timeout=timeout) as s:
        s.settimeout(timeout); s.sendall(struct.pack("!I",len(b))+b)
        header=_exact(s,4); n=struct.unpack("!I",header)[0]
        if n>1_000_000: raise ValueError("Response too large")
        return json.loads(_exact(s,n).decode())
def _exact(s,n):
    parts=[]
    while n:
        b=s.recv(n)
        if not b: raise ConnectionError("Backend disconnected")
        parts.append(b); n-=len(b)
    return b"".join(parts)
