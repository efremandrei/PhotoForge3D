$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
& .\.venv\Scripts\python.exe -m pip install pyinstaller==6.22.3
& .\.venv\Scripts\python.exe scripts\make_icon.py
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --onedir --name PhotoForge3D-PC --icon assets\icon.ico --collect-data trimesh --hidden-import scipy.spatial._ckdtree launch_pc.py
if ($LASTEXITCODE -ne 0) { throw 'Windows packaging failed.' }
$package=Join-Path (Get-Location) 'dist\PhotoForge3D-PC'
New-Item -ItemType Directory -Force (Join-Path $package 'tools') | Out-Null
Copy-Item -LiteralPath 'tools\colmap' -Destination (Join-Path $package 'tools\colmap') -Recurse -Force
Copy-Item -LiteralPath 'tools\openmvs' -Destination (Join-Path $package 'tools\openmvs') -Recurse -Force
Copy-Item -LiteralPath README.md,THIRD_PARTY.md,LICENSE,Start-PC.cmd -Destination $package -Force
Copy-Item -LiteralPath licenses -Destination (Join-Path $package 'licenses') -Recurse -Force
Copy-Item -LiteralPath assets -Destination (Join-Path $package 'assets') -Recurse -Force
Write-Output ('Package ready for verification: '+$package)
