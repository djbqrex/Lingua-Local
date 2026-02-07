# Verify certificate is accessible for IIS
Write-Host "Checking certificate for IIS use..."
Write-Host ""

$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object {$_.Thumbprint -eq '33079FDE1B9FF972B92588992A470A98458C5195'}

if ($cert) {
    Write-Host "Certificate found:"
    Write-Host "  Subject: $($cert.Subject)"
    Write-Host "  Has Private Key: $($cert.HasPrivateKey)"
    Write-Host "  Store: LocalMachine\My"
    Write-Host ""
    
    if ($cert.HasPrivateKey) {
        Write-Host "Certificate should be visible in IIS."
        Write-Host ""
        Write-Host "If not visible, try:"
        Write-Host "1. Close and reopen IIS Manager"
        Write-Host "2. Or restart IIS: iisreset"
        Write-Host "3. Or try binding to 'All Unassigned' instead of specific IP"
    } else {
        Write-Host "WARNING: Certificate does not have private key!"
    }
} else {
    Write-Host "Certificate not found!"
}

