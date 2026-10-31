"""Read-only proof that a specific pre-backup staging session exists in a RESTORED DB.

Does not create a backup or trigger recovery; do that separately in Render's
Recovery UI. It neither changes either database nor prints stored payloads.
"""
import hashlib
import os
import sys
from urllib.parse import urlsplit


def run():
    if os.getenv('AURALIS_RESTORE_VALIDATION') != 'I_CONFIRM_READ_ONLY':
        raise ValueError('Set AURALIS_RESTORE_VALIDATION=I_CONFIRM_READ_ONLY')
    src=os.getenv('DATABASE_URL','')
    dst=os.getenv('AURALIS_RESTORED_DATABASE_URL','')
    sid=os.getenv('AURALIS_RESTORE_EXPECTED_SESSION_ID','')
    if not src.startswith(('postgresql://','postgres://')) or not dst.startswith(('postgresql://','postgres://')):
        raise ValueError('Configure PostgreSQL DATABASE_URL and distinct AURALIS_RESTORED_DATABASE_URL.')
    if src==dst or not sid or len(sid)>128:
        raise ValueError('Specify two different connection URLs and a known pre-backup staging session ID.')
    import psycopg
    rows=[]
    for url in (src,dst):
        with psycopg.connect(url.replace('postgres://','postgresql://',1),connect_timeout=8) as conn:
            conn.read_only=True
            with conn.cursor() as cursor:
                cursor.execute('SELECT current_database(),inet_server_addr()::text,inet_server_port()')
                ident=cursor.fetchone()
                cursor.execute('SELECT owner,payload FROM sessions WHERE id=%s',(sid,))
                row=cursor.fetchone()
                if row is None:raise AssertionError('The designated session was absent in one database.')
                rows.append((ident,hashlib.sha256((row[0]+'\x00'+row[1]).encode()).hexdigest()))
    if rows[0][0]==rows[1][0]:
        raise AssertionError('Source and restore appear to be the SAME database server/database.')
    if rows[0][1]!=rows[1][1]:
        raise AssertionError('Session payload/ownership differed after restoration.')
    print('PASS: independent restored database contains the expected staging session with identical owner and payload.')
    print('This verifies one record, NOT a complete full-database recovery, retention guarantee or RPO/RTO.')
    return 0

if __name__=='__main__':
    try:sys.exit(run())
    except (ValueError, AssertionError) as e:
        print('FAIL:',str(e));sys.exit(1)
    except Exception:
        print('FAIL: database connection, schema or permission error (details suppressed).');sys.exit(1)
