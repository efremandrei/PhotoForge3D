import json
import uuid
import pytest
import trimesh
from fastapi.testclient import TestClient
from photoforge.engine import Jobs
from photoforge.server import create_app


@pytest.fixture
def client(tmp_path):
    jobs=Jobs(tmp_path)
    job_id=str(uuid.uuid4());p=tmp_path/job_id;p.mkdir()
    (p/'job.json').write_text(json.dumps(dict(id=job_id,status='complete',created=1)))
    trimesh.creation.box(extents=[1,2,3]).export(p/'surface.ply')
    return TestClient(create_app(jobs,'test-pairing')),job_id


def test_pairing_required_for_photos_and_models(client):
    c,j=client
    assert c.get('/health').json()['app']=='PhotoForge3D'
    assert c.get('/jobs').status_code==401
    assert c.get(f'/jobs/{j}/preview').status_code==401
    assert c.get('/jobs',headers={'X-Pairing-Token':'wrong'}).status_code==401


def test_real_export_download_and_invalid_input(client):
    c,j=client;c.headers['X-Pairing-Token']='test-pairing'
    assert c.get(f'/jobs/{j}/model.stl').status_code==409
    r=c.post(f'/jobs/{j}/export',json={'longest_mm':60})
    assert r.status_code==200 and r.json()['dimensions']==[20,40,60]
    data=c.get(f'/jobs/{j}/model.stl')
    assert data.status_code==200 and len(data.content)>84
    assert c.post(f'/jobs/{j}/export',json={'longest_mm':-1}).status_code==422
    assert c.get('/jobs/not-an-id').status_code==400


def test_upload_rejects_too_few_photos(client):
    c,j=client;c.headers['X-Pairing-Token']='test-pairing'
    r=c.post('/jobs',files=[('images',('one.jpg',b'bad','image/jpeg'))])
    assert r.status_code==400
