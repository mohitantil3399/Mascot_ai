# run_host.ps1 - Explicitly invokes the .NET 9 SDK in D:\SyncDevice\dotnet_sdk
$DotnetExe = "D:\SyncDevice\dotnet_sdk\dotnet.exe"
if (-not (Test-Path $DotnetExe)) {
    Write-Host "Warning: $DotnetExe not found. Falling back to system dotnet..." -ForegroundColor Yellow
    $DotnetExe = "dotnet"
}

Write-Host "Building Desktop Companion Native Host using $DotnetExe..." -ForegroundColor Cyan
& $DotnetExe build "$PSScriptRoot\DesktopCompanion.csproj" --nologo

$DllPath = "$PSScriptRoot\bin\Debug\net9.0-windows10.0.19041.0\DesktopCompanion.dll"
Write-Host "Running DesktopCompanion.dll via trusted dotnet host process..." -ForegroundColor Green
& $DotnetExe "$DllPath"
