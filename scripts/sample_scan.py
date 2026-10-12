"""Real-engine integration scan using the official OpenMVG example dataset."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
from photoforge.engine import Jobs, ROOT
from photoforge.mesh import prepare

folder = ROOT / 'samples/sceaux'
folder.mkdir(parents=True, exist_ok=True)
source_file=ROOT / 'samples/sources.json'
if not source_file.exists():
    r=requests.get('https://api.github.com/repos/openMVG/ImageDataset_SceauxCastle/contents/images',timeout=60)
    r.raise_for_status()
    source_file.write_text(json.dumps([s for s in r.json() if s['name'].endswith('JPG')]))
for source in json.loads(source_file.read_text('utf-8-sig')):
    target = folder / source['name']
    if not target.exists():
        r = requests.get(source['download_url'], timeout=90)
        r.raise_for_status()
        target.write_bytes(r.content)
jobs = Jobs()
job = jobs.create(sorted(folder.glob('*.JPG')), 'OpenMVG integration sample')
(ROOT / 'artifacts/sample-job.txt').write_text(job['id'])
print(job['id'], flush=True)
previous = ''
while job['status'] in ('queued', 'running'):
    time.sleep(3)
    job = jobs.get(job['id'])
    if previous != job['message']:
        print(job['status'], job['progress'], job['message'], flush=True)
        previous = job['message']
if job['status'] != 'complete':
    print(json.dumps(job), flush=True)
    sys.exit(1)
report = prepare(jobs.path(job['id']) / 'surface.ply', ROOT / 'artifacts/PhotoForge3D-sample-100mm.stl', solidify=True)
(ROOT / 'artifacts/sample-report.json').write_text(json.dumps(dict(job=job, export=report), indent=2))
print(json.dumps(report), flush=True)
