import asyncio,json,struct
from backend.config import TCP_HOST,TCP_PORT
from backend.service import handle
MAX=1_000_000
async def read_frame(r):
    n=struct.unpack("!I",await r.readexactly(4))[0]
    if n>MAX: raise ValueError("Frame too large")
    return json.loads((await r.readexactly(n)).decode())
async def write_frame(w,obj):
    b=json.dumps(obj,default=str).encode(); w.write(struct.pack("!I",len(b))+b); await w.drain()
async def connected(r,w):
    try:
        while True:
            req=await read_frame(r); result=await asyncio.to_thread(handle,req); await write_frame(w,result)
    except (asyncio.IncompleteReadError,ConnectionResetError): pass
    except Exception as e:
        print("TCP client error:",type(e).__name__)
        try: await write_frame(w,{"error":"Malformed request"})
        except Exception: pass
    finally:
        w.close()
        try: await w.wait_closed()
        except Exception: pass
async def main():
    server=await asyncio.start_server(connected,TCP_HOST,TCP_PORT)
    print(f"TCP backend listening on {TCP_HOST}:{TCP_PORT}")
    async with server: await server.serve_forever()
if __name__=="__main__": asyncio.run(main())
