"""Opt-in local SQLite backup (contains CVs and transcripts: keep private)."""
from datetime import datetime
from pathlib import Path
import os
import sqlite3

root=Path(__file__).resolve().parent.parent
source=Path(os.getenv('AURALIS_DATA_DIR',os.getenv('ROLEREADY_DATA_DIR',root/'.data')))/'auralis.sqlite3'
if not source.exists():
    raise SystemExit('No interview database found yet. Run one interview first.')
folder=root/'backups'
folder.mkdir(exist_ok=True)
output=folder/('auralis-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.sqlite3')
with sqlite3.connect(str(source)) as src,sqlite3.connect(str(output)) as dest:
    src.backup(dest)
print('Local-only interview database backup:',output)
print('PRIVATE: Contains CVs, job descriptions and answer transcripts. Do not upload to public repositories.')
