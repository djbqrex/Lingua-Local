# PowerShell script to import PEM certificate into Windows Certificate Store for IIS
# Run this as Administrator

$certPath = Join-Path $PSScriptRoot "certs\192.168.1.174+4.pem"
$keyPath = Join-Path $PSScriptRoot "certs\192.168.1.174+4-key.pem"
$pfxPath = Join-Path $PSScriptRoot "certs\192.168.1.174+4.pfx"

Write-Host "Converting PEM certificate to PFX format..."

# Check if OpenSSL is available
$openssl = Get-Command openssl -ErrorAction SilentlyContinue
if (-not $openssl) {
    Write-Host "OpenSSL not found. Trying alternative method..."
    Write-Host ""
    Write-Host "Please install OpenSSL or use the manual import method:"
    Write-Host "1. Open PowerShell as Administrator"
    Write-Host "2. Run: Import-Certificate -FilePath '$certPath' -CertStoreLocation Cert:\LocalMachine\My"
    Write-Host ""
    Write-Host "Or convert manually using OpenSSL:"
    Write-Host "openssl pkcs12 -export -out $pfxPath -inkey $keyPath -in $certPath -name `"192.168.1.174`""
    exit 1
}

# Convert PEM to PFX
& openssl pkcs12 -export -out $pfxPath -inkey $keyPath -in $certPath -name "192.168.1.174" -passout pass:

if (Test-Path $pfxPath) {
    Write-Host "Certificate converted successfully!"
    Write-Host ""
    Write-Host "Importing into Windows Certificate Store..."
    
    # Import PFX into LocalMachine\My store
    Import-PfxCertificate -FilePath $pfxPath -CertStoreLocation Cert:\LocalMachine\My -Password (ConvertTo-SecureString -String "" -Force -AsPlainText)
    
    Write-Host ""
    Write-Host "Certificate imported successfully!"
    Write-Host "You can now select it in IIS Manager under SSL certificate dropdown."
} else {
    Write-Host "Failed to convert certificate. Please check OpenSSL installation."
}

