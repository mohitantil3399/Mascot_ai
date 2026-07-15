$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Select-Object -First 1
if (-not $cert) {
    $cert = New-SelfSignedCertificate -DnsName "AntigravityLocalDev" -Type CodeSigningCert -CertStoreLocation "Cert:\CurrentUser\My"
}

$targetDir = "$PSScriptRoot\bin\Debug\net9.0-windows10.0.19041.0"
if (Test-Path $targetDir) {
    Get-ChildItem -Path $targetDir -Include "*.dll", "*.exe" -Recurse | ForEach-Object {
        Unblock-File $_.FullName -ErrorAction SilentlyContinue
        Set-AuthenticodeSignature -FilePath $_.FullName -Certificate $cert -ErrorAction SilentlyContinue | Out-Null
    }
}
Write-Host "Signed all binaries in $targetDir with cert: $($cert.Subject)" -ForegroundColor Green
