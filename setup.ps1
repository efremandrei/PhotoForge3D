$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.10 or newer first.' }
}
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
New-Item -ItemType Directory -Force tools | Out-Null
$engines = @(
    @{Name='colmap'; Url='https://github.com/colmap/colmap/releases/download/4.2.1/colmap-x64-windows-nocuda.zip'},
    @{Name='openmvs'; Url='https://github.com/cdcseacave/openMVS/releases/download/v2.4.0/OpenMVS_Windows_x64.zip'}
)
foreach ($engine in $engines) {
    $destination = Join-Path $PSScriptRoot ('tools\'+$engine.Name)
    if (-not (Test-Path -LiteralPath $destination)) {
        $archive = Join-Path $PSScriptRoot ('tools\'+$engine.Name+'.zip')
        Invoke-WebRequest -Uri $engine.Url -OutFile $archive
        Expand-Archive -LiteralPath $archive -DestinationPath $destination
    }
}
Write-Output 'Setup complete. Run Start-PC.cmd.'
