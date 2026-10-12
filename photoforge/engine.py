import json
import os
import subprocess
import threading
import time
import uuid
import sys
from pathlib import Path
from PIL import Image, ImageOps
from .mesh import summary, load_mesh

ROOT = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
COLMAP = ROOT / 'tools/colmap/bin/colmap.exe'
MVS = ROOT / 'tools/openmvs/vc17/x64/Release'
NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


class Jobs:
    def __init__(self, base=ROOT / 'jobs'):
        self.base = Path(base)
        self.base.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.worker_lock = threading.Lock()
        self.processes = {}
        self.canceled = set()
        # Interrupted jobs must not appear to keep processing forever after restart.
        for p in self.base.glob('*/job.json'):
            d = json.loads(p.read_text('utf-8'))
            if d['status'] in ('queued', 'running'):
                d.update(status='failed', message='PC processing was interrupted. Create a new scan to retry.')
                p.write_text(json.dumps(d), encoding='utf-8')

    def path(self, job_id):
        try:
            if str(uuid.UUID(job_id)) != job_id:
                raise ValueError()
        except ValueError:
            raise ValueError('Invalid scan identifier.')
        p = self.base / job_id
        if not (p / 'job.json').exists():
            raise ValueError('Scan not found on this PC.')
        return p

    def get(self, job_id):
        with self.lock:
            return json.loads((self.path(job_id) / 'job.json').read_text('utf-8'))

    def update(self, job_id, **fields):
        with self.lock:
            p = self.path(job_id) / 'job.json'
            d = json.loads(p.read_text('utf-8'))
            d.update(fields, updated=time.time())
            tmp = p.with_suffix('.tmp')
            tmp.write_text(json.dumps(d, indent=2), encoding='utf-8')
            tmp.replace(p)

    def create(self, paths, name='My object'):
        if not 8 <= len(paths) <= 240:
            raise ValueError('Choose 8–240 photos. For an object, aim for 30–80 photos around all sides.')
        if not COLMAP.exists() or not (MVS / 'DensifyPointCloud.exe').exists():
            raise ValueError('Reconstruction tools are missing. Run setup.ps1 first.')
        job_id = str(uuid.uuid4())
        p = self.base / job_id
        images = p / 'images'
        images.mkdir(parents=True)
        import hashlib
        seen = set()
        try:
            for index, path in enumerate(paths):
                with Image.open(path) as im:
                    if im.width * im.height > 60_000_000:
                        raise ValueError('Photo exceeds 60 megapixels. Resize it before importing.')
                    im = ImageOps.exif_transpose(im).convert('RGB')
                    if min(im.size) < 320:
                        raise ValueError('Photos must be at least 320 pixels on their shorter side.')
                    im.thumbnail((1600, 1600))
                    digest = hashlib.sha256(im.tobytes()).hexdigest()
                    if digest in seen:
                        raise ValueError('Duplicate photos found. Select distinct angles.')
                    seen.add(digest)
                    im.save(images / f'{index:04d}.jpg', quality=95)
        except Exception:
            import shutil
            shutil.rmtree(p)
            raise
        d = dict(id=job_id, name=name[:80], count=len(paths), status='queued', progress=0,
                 message='Waiting for PC processor', created=time.time(), updated=time.time())
        (p / 'job.json').write_text(json.dumps(d), encoding='utf-8')
        threading.Thread(target=self.run, args=(job_id,), daemon=True).start()
        return d

    def cancel(self, job_id):
        if self.get(job_id)['status'] not in ('queued', 'running'):
            raise ValueError('Only queued or running scans can be canceled.')
        self.canceled.add(job_id)
        proc = self.processes.get(job_id)
        if proc and proc.poll() is None:
            proc.terminate()
        self.update(job_id, status='canceled', message='Canceled')

    def command(self, job_id, args, message, progress):
        if job_id in self.canceled:
            raise InterruptedError('Canceled')
        self.update(job_id, status='running', message=message, progress=progress)
        p = self.path(job_id)
        with (p / 'processing.log').open('ab') as log:
            log.write(('\n' + subprocess.list2cmdline([str(a) for a in args]) + '\n').encode())
            log.flush()
            proc = subprocess.Popen([str(a) for a in args], cwd=p, stdout=log, stderr=log, creationflags=NO_WINDOW)
            self.processes[job_id] = proc
            rc = proc.wait()
        self.processes.pop(job_id, None)
        if job_id in self.canceled:
            raise InterruptedError('Canceled')
        if rc:
            raise RuntimeError(f'{message} failed (code {rc}). See processing.log. Try more overlapping, sharp photos with a textured, stationary object.')

    def run(self, job_id):
        # CPU jobs are serialized to prevent several scans exhausting memory.
        with self.worker_lock:
            try:
                self.reconstruct(job_id)
            except InterruptedError:
                self.update(job_id, status='canceled', message='Canceled')
            except Exception as ex:
                self.update(job_id, status='failed', message=str(ex))

    def reconstruct(self, job_id):
        p = self.path(job_id)
        images, db = p / 'images', p / 'database.db'
        sparse, dense = p / 'sparse', p / 'dense'
        sparse.mkdir()
        threads = '8'
        self.command(job_id, [COLMAP, 'feature_extractor', '--database_path', db, '--image_path', images,
                     '--FeatureExtraction.use_gpu', '0', '--FeatureExtraction.num_threads', threads,
                     '--FeatureExtraction.max_image_size', '1200'], 'Finding photo features', 8)
        self.command(job_id, [COLMAP, 'exhaustive_matcher', '--database_path', db,
                     '--FeatureMatching.use_gpu', '0', '--FeatureMatching.num_threads', threads], 'Matching overlapping angles', 23)
        self.command(job_id, [COLMAP, 'mapper', '--database_path', db, '--image_path', images,
                     '--output_path', sparse, '--Mapper.num_threads', threads, '--Mapper.min_model_size', '5'], 'Solving camera positions', 38)
        models = list(sparse.glob('*/images.bin'))
        if not models:
            raise ValueError('Photos could not be aligned. Keep the object still and move the camera, with strong overlap between angles.')
        model = max(models, key=lambda f: f.stat().st_size).parent
        self.command(job_id, [COLMAP, 'image_undistorter', '--image_path', images, '--input_path', model,
                     '--output_path', dense, '--output_type', 'COLMAP', '--max_image_size', '1200'], 'Correcting lens distortion', 50)
        self.command(job_id, [COLMAP, 'model_converter', '--input_path', dense / 'sparse',
                     '--output_path', dense / 'sparse', '--output_type', 'TXT'], 'Preparing reconstruction', 55)
        registered = sum(1 for line in (dense / 'sparse/images.txt').read_text().splitlines()
                         if line.strip() and not line.startswith('#') and line.rstrip().endswith('.jpg'))
        if registered < max(5, int(self.get(job_id)['count'] * .6)):
            raise ValueError(f'Only {registered} photos aligned. Retake with more overlap and consistent lighting.')
        self.update(job_id, registered=registered)
        scene = p / 'scene.mvs'
        self.command(job_id, [MVS / 'InterfaceCOLMAP.exe', '-i', dense, '-o', scene, '--binary', '0'], 'Importing camera geometry', 58)
        self.command(job_id, [MVS / 'DensifyPointCloud.exe', scene, '-o', p / 'scene_dense.mvs',
                     '--resolution-level', '1', '--min-resolution', '320', '--max-threads', threads,
                     '--tower-mode', '0'], 'Reconstructing dense surface points', 65)
        self.command(job_id, [MVS / 'ReconstructMesh.exe', p / 'scene_dense.mvs',
                     '-o', p / 'surface.mvs', '--max-threads', threads], 'Building the 3D surface', 88)
        mesh = load_mesh(p / 'surface.ply')
        if job_id in self.canceled:
            raise InterruptedError('Canceled')
        self.update(job_id, status='complete', message='Surface ready. Inspect, crop background, set size, then export.', progress=100, mesh=summary(mesh))
