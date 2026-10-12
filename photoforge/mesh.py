"""Measured mesh preparation; inferred repairs always require explicit opt-in."""
from pathlib import Path
import numpy as np
import trimesh
import fast_simplification
from scipy import ndimage
from skimage.measure import marching_cubes


def load_mesh(path):
    mesh = trimesh.load_mesh(path, process=True)
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) < 4:
        raise ValueError('No usable surface was reconstructed. Add sharper, overlapping photos.')
    if not np.isfinite(mesh.vertices).all():
        raise ValueError('Mesh contains invalid coordinates.')
    return mesh


def summary(mesh):
    return dict(vertices=len(mesh.vertices), triangles=len(mesh.faces),
                watertight=bool(mesh.is_watertight), dimensions=mesh.extents.tolist(),
                volume=float(abs(mesh.volume)) if mesh.is_watertight else None)


def prepare(source, output, longest_mm=100, crop=None, solidify=False, resolution=160):
    if not np.isfinite(longest_mm) or not 1 <= longest_mm <= 2000:
        raise ValueError('Longest dimension must be between 1 and 2000 mm.')
    mesh = load_mesh(source).copy()
    before = summary(mesh)
    # Crop in the measured model axes, with fractions relative to original bounds.
    if crop is not None:
        c = np.array(crop, dtype=float)
        if c.shape != (3, 2) or not np.isfinite(c).all() or np.any(c < 0) or np.any(c > 1) or np.any(c[:, 0] >= c[:, 1]):
            raise ValueError('Each crop range must satisfy 0 <= minimum < maximum <= 1.')
        lo = mesh.bounds[0] + mesh.extents * c[:, 0]
        hi = mesh.bounds[0] + mesh.extents * c[:, 1]
        keep = np.all((mesh.vertices >= lo) & (mesh.vertices <= hi), axis=1)
        mesh.update_faces(np.all(keep[mesh.faces], axis=1))
        mesh.remove_unreferenced_vertices()
    parts = mesh.split(only_watertight=False)
    if not len(parts):
        raise ValueError('Crop removed the surface. Widen the crop ranges.')
    mesh = max(parts, key=lambda p: p.area).copy()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(mesh)
    trimesh.repair.fill_holes(mesh)
    inferred = False
    if not mesh.is_watertight:
        if not solidify:
            raise ValueError('Surface has open holes. Capture the missing sides, or enable Seal gaps; this infers geometry and can thicken the surface.')
        inferred = True
        pitch = float(mesh.extents.max()) / resolution
        vox = mesh.voxelized(pitch)
        grid = np.pad(vox.matrix, 3)
        grid = ndimage.binary_closing(grid, iterations=2)
        grid = ndimage.binary_fill_holes(grid)
        v, f, _, _ = marching_cubes(grid.astype(np.float32), level=0.5)
        mesh = trimesh.Trimesh(vertices=(v - 3) * pitch + vox.transform[:3, 3], faces=f, process=True)
        mesh = max(mesh.split(only_watertight=False), key=lambda p: p.area)
        trimesh.repair.fix_normals(mesh)
    if not mesh.is_watertight or not mesh.is_volume:
        raise ValueError('Unable to produce a closed solid. Retake missing angles or adjust the crop.')
    mesh.apply_scale(longest_mm / mesh.extents.max())
    mesh.apply_translation(-mesh.bounds[0])
    output = Path(output)
    mesh.export(output, file_type='stl')
    # Verify the actual STL after serialization, not just the in-memory mesh.
    exported = load_mesh(output)
    if not exported.is_watertight or not exported.is_volume:
        output.unlink(missing_ok=True)
        raise ValueError('STL verification failed.')
    return dict(**summary(exported), units='mm', inferred_repair=inferred,
                reconstruction=before, warning='Sealed/thickened geometry is inferred; inspect it in your slicer.' if inferred else 'Inspect orientation and supports in your slicer before printing.')


def preview(path, limit=1300):
    mesh = load_mesh(path)
    original = summary(mesh)
    display = mesh.simplify_quadric_decimation(face_count=limit) if len(mesh.faces)>limit else mesh
    faces = display.faces
    vertices = display.vertices.copy()
    vertices -= mesh.bounds.mean(axis=0)
    vertices /= max(float(mesh.extents.max()), 1e-9)
    return dict(triangles=vertices[faces].round(5).tolist(), stats=original)
