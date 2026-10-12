import numpy as np
import pytest
import trimesh
from photoforge.mesh import prepare, load_mesh, preview


def test_closed_mesh_roundtrip_preserves_proportions_and_mm(tmp_path):
    box = trimesh.creation.box(extents=[2, 4, 6])
    raw, out = tmp_path/'box.ply', tmp_path/'box.stl'
    box.export(raw)
    report = prepare(raw, out, 120)
    mesh = load_mesh(out)
    assert mesh.is_watertight and mesh.is_volume
    assert np.allclose(mesh.extents, [40, 80, 120], atol=.001)
    assert np.allclose(mesh.bounds[0], 0)
    assert report['units']=='mm' and not report['inferred_repair']


def test_open_surface_requires_explicit_repair(tmp_path):
    sphere = trimesh.creation.icosphere(subdivisions=2)
    sphere.update_faces(sphere.triangles_center[:, 2]<.4)
    raw = tmp_path/'open.ply'; sphere.export(raw)
    with pytest.raises(ValueError, match='open holes'):
        prepare(raw, tmp_path/'blocked.stl')
    assert not (tmp_path/'blocked.stl').exists()
    report = prepare(raw, tmp_path/'sealed.stl', solidify=True, resolution=64)
    assert report['watertight'] and report['inferred_repair']
    assert 'inferred' in report['warning']


@pytest.mark.parametrize('size',[0,-10,float('nan'),float('inf'),2001])
def test_invalid_sizes_rejected(tmp_path,size):
    with pytest.raises(ValueError,match='dimension'):
        prepare(tmp_path/'none',tmp_path/'none.stl',size)


def test_crop_rejects_empty_or_out_of_bounds_ranges(tmp_path):
    raw=tmp_path/'box.ply';trimesh.creation.box().export(raw)
    with pytest.raises(ValueError,match='crop range'):
        prepare(raw,tmp_path/'out.stl',crop=[[.9,.1],[0,1],[0,1]])
    with pytest.raises(ValueError,match='Crop removed'):
        prepare(raw,tmp_path/'out.stl',crop=[[.49,.51],[.49,.51],[.49,.51]])


def test_preview_preserves_surface_instead_of_skipping_triangles(tmp_path):
    sphere=trimesh.creation.icosphere(subdivisions=4)
    raw=tmp_path/'sphere.ply';sphere.export(raw)
    data=preview(raw)
    triangles=np.array(data['triangles'])
    display=trimesh.Trimesh(vertices=triangles.reshape(-1,3),faces=np.arange(triangles.size//3).reshape(-1,3),process=True)
    assert display.is_watertight
    assert len(display.faces)<=1300
    assert data['stats']['triangles']==len(sphere.faces)
