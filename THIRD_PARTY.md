# Third-party components

- **COLMAP 4.2.1**, BSD 3-Clause: [source and tag](https://github.com/colmap/colmap/tree/4.2.1), [official Windows CPU release](https://github.com/colmap/colmap/releases/tag/4.2.1). Distributed unmodified in `tools/colmap`. Original release DLLs and plugins accompany the executable.
- **OpenMVS v2.4.0**, AGPL-3.0: [corresponding source and tag](https://github.com/cdcseacave/openMVS/tree/v2.4.0), [official release](https://github.com/cdcseacave/openMVS/releases/tag/v2.4.0). Distributed unmodified in `tools/openmvs`. Original runtime DLLs accompany the executables.
- Python runtime and dependencies: PyInstaller collects package license metadata and the Python license in `_internal`. Dependency versions are pinned in `requirements.txt`.
- Integration fixture: [OpenMVG ImageDataset_SceauxCastle](https://github.com/openMVG/ImageDataset_SceauxCastle). Used for testing only; photographs are not included in the public app package.

The Android client and PC application source are in this repository under AGPL-3.0-or-later. Upstream engine copyright notices are preserved in `licenses/` in the Windows distribution. Engine sources are unchanged from the linked tags.
