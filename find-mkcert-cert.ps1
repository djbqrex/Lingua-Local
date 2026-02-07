# Check both CurrentUser and LocalMachine stores for mkcert certificate
Write-Host "Checking CurrentUser store..."
$certs = Get-ChildItem Cert:\CurrentUser\My
foreach ($cert in $certs) {
    if ($cert.HasPrivateKey) {
        $subject = $cert.Subject
        $issuer = $cert.Issuer
        if ($issuer -like '*mkcert*' -or $subject -like '*192.168.1.174*' -or $subject -like '*localhost*') {
            Write-Host "FOUND in CurrentUser store:"
            Write-Host "  Subject: $subject"
            Write-Host "  Issuer: $issuer"
            Write-Host "  Thumbprint: $($cert.Thumbprint)"
            Write-Host ""
            Write-Host "NOTE: IIS needs certificates in LocalMachine store!"
            Write-Host "We need to export and re-import to LocalMachine."
        }
    }
}

Write-Host "Checking LocalMachine store..."
$certs = Get-ChildItem Cert:\LocalMachine\My
$found = $false
foreach ($cert in $certs) {
    if ($cert.HasPrivateKey) {
        $subject = $cert.Subject
        $issuer = $cert.Issuer
        if ($issuer -like '*mkcert*' -or $subject -like '*192.168.1.174*' -or $subject -like '*localhost*') {
            Write-Host "FOUND in LocalMachine store:"
            Write-Host "  Subject: $subject"
            Write-Host "  Issuer: $issuer"
            Write-Host "  Thumbprint: $($cert.Thumbprint)"
            $found = $true
        }
    }
}

if (-not $found) {
    Write-Host "Not found in LocalMachine store."
}

