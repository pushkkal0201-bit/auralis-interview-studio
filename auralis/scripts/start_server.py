"""Local-only Windows-friendly launcher with honest port fallback."""
import os
import socket
import uvicorn


def choose_port(preferred=8000, width=10):
    for port in range(preferred, min(65536,preferred+width)):
        sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1',port))
        except OSError:
            continue
        finally:
            sock.close()
        return port
    raise SystemExit('All Auralis local ports are in use. Close an old instance or set AURALIS_PORT.')


def main():
    preferred=int(os.getenv('AURALIS_PORT','8000'))
    if preferred<1024 or preferred>65525:
        raise SystemExit('AURALIS_PORT must be between 1024 and 65525.')
    port=choose_port(preferred)
    if port!=preferred:
        print(f'Port {preferred} is already occupied, probably by an older Auralis instance.',flush=True)
        print(f'Opening the new version on port {port} instead. Do not open the old URL.',flush=True)
    print(f'\nAURALIS 5.7.2: http://127.0.0.1:{port}\n',flush=True)
    uvicorn.run('app.main:app',host='127.0.0.1',port=port,log_level='info')


if __name__=='__main__':main()
