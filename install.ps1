$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 -m venv (Join-Path $Root ".venv") }
elseif (Get-Command python -ErrorAction SilentlyContinue) { & python -m venv (Join-Path $Root ".venv") }
else { throw "Python >=3.11 required" }
if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment" }
$Python = Join-Path $Root ".venv\Scripts\python.exe"
& $Python -c "import sys; assert sys.version_info >= (3,11), 'Python >=3.11 required'"
if ($LASTEXITCODE -ne 0) { throw "Unsupported Python version" }
if ($env:LUCIDA_API_SOURCE) {
    & $Python -m pip install -e $env:LUCIDA_API_SOURCE
} else {
    & $Python -m pip install 'git+https://github.com/jerrecode/lucida-api.git@main'
}
if ($LASTEXITCODE -ne 0) { throw "API installation failed" }
& $Python -m pip install 'PySide6>=6.6,<7'
if ($LASTEXITCODE -ne 0) { throw "Qt installation failed" }
& $Python -m pip install --no-deps -e $Root
if ($LASTEXITCODE -ne 0) { throw "GUI installation failed" }
& $Python -c "import lucida_gui.app; print('GUI import OK')"
