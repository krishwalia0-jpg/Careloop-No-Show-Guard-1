"""Check the already generated CareLoop deliverables without Colab or API keys."""
from pathlib import Path
import csv, json, sqlite3
root=Path(__file__).resolve().parent
with (root/'appointments_clean.csv').open(newline='') as f:
    reader=csv.DictReader(f); rows=list(reader)
assert len(rows)==990 and len(rows[0])==16
assert len({r['appointment_id'] for r in rows})==990
assert sum(int(r['no_show']) for r in rows)==218
assert len(json.loads((root/'rejected_rows.json').read_text()))==32
with (root/'test_risk_scores.csv').open(newline='') as f:
    test=list(csv.DictReader(f))
assert len(test)==198
print('PASS: 990 clean rows, 218 no-shows, 32 rejected CSV-module rows, 198 test risk scores')
con=sqlite3.connect(':memory:')
script=(root/'02_queries.sql').read_text().split('-- Next execute')[0]
script=script.replace('CREATE DATABASE IF NOT EXISTS noshowguard;','').replace('USE noshowguard;','')
con.executescript(script)
con.executescript((root/'load_data.sql').read_text())
print('PASS: SQL load',con.execute('SELECT COUNT(*), SUM(no_show) FROM appointments').fetchone())
try:
    con.execute("INSERT INTO appointments SELECT * FROM appointments WHERE appointment_id='A0001'")
except sqlite3.IntegrityError as exc:
    print('PASS: duplicate key rejected:',exc)
else:
    raise AssertionError('Duplicate primary key unexpectedly accepted')
print('NOTE: Weather and Gemini API results require live external calls.')
