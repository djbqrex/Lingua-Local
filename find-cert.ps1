# Find certificates with private keys that can be used for IIS SSL
Write-Host "Searching for certificates with private keys..."
Write-Host ""

$certs = Get-ChildItem Cert:\LocalMachine\My
$found = $false

foreach ($cert in $certs) {
    if ($cert.HasPrivateKey) {
        Write-Host "Found certificate with private key:"
        Write-Host "  Subject: $($cert.Subject)"
        Write-Host "  Issuer: $($cert.Issuer)"
        Write-Host "  Thumbprint: $($cert.Thumbprint)"
        Write-Host "  Friendly Name: $($cert.FriendlyName)"
        Write-Host ""
        $found = $true
    }
}

if (-not $found) {
    Write-Host "No certificates with private keys found."
    Write-Host ""
    Write-Host "You may need to:"
    Write-Host "1. Re-run mkcert to create the certificate (it installs with private key automatically)"
    Write-Host "2. Or combine the PEM files into a PFX using OpenSSL"
}

