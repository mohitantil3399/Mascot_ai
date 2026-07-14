# run_host.ps1 - Explicitly invokes the .NET 9 SDK in D:\SyncDevice\dotnet_sdk
$DotnetExe = "D:\SyncDevice\dotnet_sdk\dotnet.exe"
if (-not (Test-Path $DotnetExe)) {
    Write-Host "Warning: $DotnetExe not found. Falling back to system dotnet..." -ForegroundColor Yellow
    $DotnetExe = "dotnet"
}

Write-Host "Running Desktop Companion Native Host using $DotnetExe..." -ForegroundColor Cyan
& $DotnetExe run --project "$PSScriptRoot\DesktopCompanion.csproj"
