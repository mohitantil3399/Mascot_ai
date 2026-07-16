# scripts/publish.ps1
# ─────────────────────────────────────────────────────────────────────────────
# One-command release pipeline for mascot-ai
#
# Usage:
#   .\scripts\publish.ps1 -Version "1.1.0" -Token "pypi-xxxx..."
#
# What it does:
#   1. Builds the React UI (npm run build) in apps/ui-frontend
#   2. Copies the dist/ into mascot_ai/ui_dist/  (package data)
#   3. Copies orchestrator source into mascot_ai/orchestrator/
#   4. Builds the .NET native host (Release)
#   5. Bumps version in pyproject.toml
#   6. Runs `uv build` to create .whl and .tar.gz
#   7. Runs `uv publish` to upload to PyPI
#   8. Reminds you to upload DesktopCompanion.exe to GitHub Releases
# ─────────────────────────────────────────────────────────────────────────────

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,

    [Parameter(Mandatory=$true)]
    [string]$Token
)

$Root       = $PSScriptRoot | Split-Path -Parent
$UiFrontend = "$Root\apps\ui-frontend"
$Orchestrator = "$Root\apps\ai-orchestrator"
$NativeHost = "$Root\apps\native-host"

# Resolve dotnet.exe — tries standard install paths, then falls back to PATH
$DotnetExe = "dotnet"   # default: relies on PATH (works if .NET SDK is installed normally)
$StandardPaths = @(
    "C:\Program Files\dotnet\dotnet.exe",        # standard Windows installer
    "C:\Program Files (x86)\dotnet\dotnet.exe",  # 32-bit install
    "D:\SyncDevice\dotnet_sdk\dotnet.exe"         # custom / portable install
)
foreach ($p in $StandardPaths) {
    if (Test-Path $p) { $DotnetExe = $p; break }
}

function Step($msg) { Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "   OK: $msg" -ForegroundColor Green }
function Fail($msg) { Write-Host "   FAIL: $msg" -ForegroundColor Red; exit 1 }

# ── Step 1: Build React UI ───────────────────────────────────────────────────
Step "Building React UI (npm run build)..."
Push-Location $UiFrontend
npm run build
if ($LASTEXITCODE -ne 0) { Fail "npm run build failed" }
Pop-Location
Ok "UI built -> apps/ui-frontend/dist/"

# ── Step 2: Copy UI dist into mascot_ai/ui_dist ─────────────────────────────
Step "Copying UI dist into mascot_ai/ui_dist/..."
$uiDst = "$Root\mascot_ai\ui_dist"
if (Test-Path $uiDst) { Remove-Item -Recurse -Force $uiDst }
Copy-Item -Recurse "$UiFrontend\dist" $uiDst
Ok "Copied to mascot_ai/ui_dist/"

# ── Step 3: Copy orchestrator source into mascot_ai/orchestrator ─────────────
Step "Copying orchestrator source into mascot_ai/orchestrator/..."
$orchDst = "$Root\mascot_ai\orchestrator"
if (Test-Path $orchDst) { Remove-Item -Recurse -Force $orchDst }
New-Item -ItemType Directory -Force $orchDst | Out-Null
New-Item -ItemType Directory -Force "$orchDst\api" | Out-Null
New-Item -ItemType Directory -Force "$orchDst\inference" | Out-Null
Copy-Item "$Orchestrator\main.py"                      "$orchDst\"
Copy-Item "$Orchestrator\api\ws_endpoint.py"           "$orchDst\api\"
Copy-Item "$Orchestrator\inference\engine.py"          "$orchDst\inference\"
Copy-Item "$Orchestrator\inference\prompts.py"         "$orchDst\inference\"
Copy-Item "$Orchestrator\inference\vision_parser.py"   "$orchDst\inference\"
"" | Set-Content "$orchDst\__init__.py"
"" | Set-Content "$orchDst\api\__init__.py"
"" | Set-Content "$orchDst\inference\__init__.py"
Ok "Copied to mascot_ai/orchestrator/"

# ── Step 4: Build .NET Native Host (Release) ─────────────────────────────────
Step "Building .NET Native Host (Release)..."
& $DotnetExe publish "$NativeHost\DesktopCompanion.csproj" -c Release --self-contained false -o "$NativeHost\publish\Release" --nologo
if ($LASTEXITCODE -ne 0) { Fail "dotnet publish failed" }
Ok "Built -> apps/native-host/publish/Release/DesktopCompanion.exe"

# ── Step 5: Bump version in pyproject.toml ───────────────────────────────────
Step "Bumping version to $Version in pyproject.toml..."
$toml = Get-Content "$Root\pyproject.toml" -Raw
$toml = $toml -replace 'version = "\d+\.\d+\.\d+"', "version = `"$Version`""
Set-Content "$Root\pyproject.toml" $toml -NoNewline
Ok "Version set to $Version"

# ── Step 6: uv build ─────────────────────────────────────────────────────────
Step "Running uv build..."
Push-Location $Root
if (Test-Path ".\dist") { Remove-Item -Recurse -Force ".\dist" }
uv build
if ($LASTEXITCODE -ne 0) { Fail "uv build failed" }
Pop-Location
Ok "Built dist/mascot_ai-$Version-py3-none-any.whl"

# ── Step 7: uv publish ────────────────────────────────────────────────────────
Step "Publishing to PyPI..."
$env:UV_PUBLISH_TOKEN = $Token
Push-Location $Root
uv publish
Pop-Location
$env:UV_PUBLISH_TOKEN = ""
Ok "Published mascot-ai $Version to PyPI!"

# ── Step 8: Remind about GitHub Release ──────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host " NEXT: Create a GitHub Release for v$Version" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host " Upload this file as a release asset:" -ForegroundColor White
Write-Host "   $NativeHost\publish\Release\DesktopCompanion.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host " URL: https://github.com/mohitantil3399/Mascot_ai/releases/new" -ForegroundColor White
Write-Host " Tag: v$Version" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Then REVOKE your PyPI token at: https://pypi.org/manage/account/token/" -ForegroundColor Red
