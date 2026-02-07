# HTTPS Setup for Mobile Access

## Problem
Mobile browsers (Chrome/Firefox on Android) require HTTPS to access the microphone when connecting via IP address. Accessing via `http://192.168.1.174:8080` blocks microphone access.

## Quick Solutions

### Option 1: Enable Microphone in Browser Settings (May Work)

**For Chrome on Android:**
1. Open Chrome and navigate to `http://192.168.1.174:8080`
2. Tap the lock/info icon (🔒 or ℹ️) in the address bar
3. Select "Site settings"
4. Enable "Microphone"
5. Refresh the page

**For Firefox on Android:**
1. Open Firefox and navigate to `http://192.168.1.174:8080`
2. Tap the menu (☰) → Settings
3. Go to "Privacy & Security"
4. Under "Permissions", tap "Microphone"
5. Add your IP address and allow access

**Note:** This may not work on all Android versions due to security restrictions.

### Option 2: Set Up HTTPS with Self-Signed Certificate (Recommended)

#### Step 1: Install mkcert (Easiest)

**On Windows:**
```powershell
# Install via Chocolatey
choco install mkcert

# Or download from: https://github.com/FiloSottile/mkcert/releases
```

**On Linux/Mac:**
```bash
# Install mkcert
brew install mkcert  # Mac
# or
sudo apt install mkcert  # Ubuntu/Debian
```

#### Step 2: Create Local CA and Certificates

```bash
# Create local CA
mkcert -install

# Create certificate for your IP addresses
mkcert 192.168.1.174 172.23.128.1 100.82.168.57 localhost 127.0.0.1

# This creates two files:
# - 192.168.1.174+4.pem (certificate)
# - 192.168.1.174+4-key.pem (private key)
```

#### Step 3: Configure uvicorn with SSL

Update your docker-compose.yml to mount certificates and use SSL:

```yaml
services:
  language-assistant:
    # ... existing config ...
    volumes:
      - ./models:/app/models
      - ./backend:/app/backend
      - ./frontend:/app/frontend
      - ./tmp:/app/tmp
      - ./certs:/app/certs  # Add this line
    environment:
      # ... existing env vars ...
      - SSL_CERT_PATH=/app/certs/192.168.1.174+4.pem
      - SSL_KEY_PATH=/app/certs/192.168.1.174+4-key.pem
```

#### Step 4: Update Backend to Support SSL

We'll need to modify the uvicorn command to use SSL certificates.

### Option 3: Use IIS as Reverse Proxy (Windows - No Extra Downloads)

IIS is built into Windows and can act as a reverse proxy with HTTPS.

#### Step 1: Enable IIS Features

Open PowerShell as Administrator and run:

```powershell
# Enable IIS and required features
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServer
Enable-WindowsOptionalFeature -Online -FeatureName IIS-CommonHttpFeatures
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpErrors
Enable-WindowsOptionalFeature -Online -FeatureName IIS-ApplicationInit
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HealthAndDiagnostics
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpLogging
Enable-WindowsOptionalFeature -Online -FeatureName IIS-Security
Enable-WindowsOptionalFeature -Online -FeatureName IIS-RequestFiltering
Enable-WindowsOptionalFeature -Online -FeatureName IIS-Performance
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpCompressionStatic
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerManagementTools
Enable-WindowsOptionalFeature -Online -FeatureName IIS-ManagementConsole
```

Or use Windows Features GUI:
1. Press `Win + R`, type `optionalfeatures`, press Enter
2. Enable "Internet Information Services" and all sub-features

#### Step 2: Install Application Request Routing (ARR) and URL Rewrite

1. Download ARR 3.0: https://www.iis.net/downloads/microsoft/application-request-routing
2. Download URL Rewrite 2.1: https://www.iis.net/downloads/microsoft/url-rewrite
3. Install both (restart may be required)

#### Step 3: Create Self-Signed Certificate

Open PowerShell as Administrator:

```powershell
# Create self-signed certificate for your IP
$cert = New-SelfSignedCertificate -DnsName "192.168.1.174", "localhost" -CertStoreLocation "cert:\LocalMachine\My"

# Note the thumbprint from the output - you'll need it
$cert.Thumbprint
```

#### Step 4: Configure IIS Site

1. Open IIS Manager (`Win + R` → `inetmgr`)
2. Right-click "Sites" → "Add Website"
3. Configure:
   - **Site name:** `Lingua-Local`
   - **Application pool:** Create new or use DefaultAppPool
   - **Physical path:** Any folder (e.g., `C:\inetpub\wwwroot\lingua-local`)
   - **Binding:** 
     - Type: `https`
     - IP address: `192.168.1.174` (or "All Unassigned")
     - Port: `8443`
     - SSL certificate: Select the certificate you created (thumbprint matches)
   - Click OK

#### Step 5: Configure URL Rewrite and Reverse Proxy

1. Select your site in IIS Manager
2. Double-click "URL Rewrite"
3. Click "Add Rule" → "Reverse Proxy"
4. Configure:
   - **Inbound rules:**
     - Pattern: `(.*)`
     - Rewrite URL: `http://localhost:8080/{R:1}`
     - Check "Enable reverse proxy"
   - Click OK

#### Step 6: Enable Proxy in ARR

1. Select your server (top level) in IIS Manager
2. Double-click "Application Request Routing Cache"
3. Click "Server Proxy Settings" (right panel)
4. Check "Enable proxy"
5. Click "Apply"

#### Step 7: Access via HTTPS

On your phone, use: `https://192.168.1.174:8443`

**Note:** You'll need to accept the self-signed certificate warning on your phone the first time.

### Option 4: Use ngrok (Quick Testing)

For quick testing, you can use ngrok to create an HTTPS tunnel:

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8080
```

This gives you an HTTPS URL like `https://abc123.ngrok.io` that you can access from your phone.

**Note:** Free ngrok URLs change each time and have limitations.

## Recommended Approach

For Windows users, **Option 3 (IIS)** is recommended as it uses built-in Windows features. For cross-platform or simpler setup, use **Option 2 (mkcert)**.

## After Setting Up HTTPS

1. Update CORS settings to include HTTPS origins:
   ```yaml
   - CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,https://192.168.1.174:8443,https://172.23.128.1:8443
   ```

2. Restart your Docker container:
   ```bash
   docker-compose restart
   ```

3. Access from phone using HTTPS URL

4. Accept the self-signed certificate warning on your phone (first time only)

## Troubleshooting

- **Certificate warnings:** This is normal for self-signed certificates. Accept the warning on your phone.
- **Still blocked:** Make sure you're using HTTPS (not HTTP) and that the certificate is accepted.
- **Browser still blocks:** Try clearing browser cache and site data, then revisit.

