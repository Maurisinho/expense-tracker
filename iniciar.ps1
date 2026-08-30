# Inicia el servidor web del gestor de gastos y un túnel de Cloudflare
# para acceder desde el iPhone, desde cualquier lugar.
#
# Uso:
#   .\iniciar.ps1            (usa el puerto 5000)
#   .\iniciar.ps1 -Port 8080

param(
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"
$directorio = Split-Path -Parent $MyInvocation.MyCommand.Path
$temp = Join-Path $env:TEMP "expense-tracker"
New-Item -ItemType Directory -Force -Path $temp | Out-Null
$logTunel = Join-Path $temp "cloudflared.log"
$logTunelErr = Join-Path $temp "cloudflared.err.log"
$serverLog = Join-Path $temp "server.log"
$serverErr = Join-Path $temp "server.err.log"
Remove-Item $logTunel, $logTunelErr, $serverLog, $serverErr -ErrorAction SilentlyContinue

$escuchando = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $escuchando) {
    Write-Host "Arrancando el servidor web en el puerto $Port..."
    $python = (Get-Command python -ErrorAction Stop).Source
    $proc = Start-Process -FilePath $python `
        -ArgumentList @("-m", "expense_tracker.webapp", "--host", "0.0.0.0", "--port", "$Port") `
        -WorkingDirectory $directorio -WindowStyle Hidden `
        -RedirectStandardOutput $serverLog -RedirectStandardError $serverErr -PassThru
    Start-Sleep -Seconds 3
    if ($proc.HasExited) {
        Write-Host "El servidor no arrancó. Revisa: $serverErr"
        Get-Content $serverErr -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    Write-Host "Ya hay un servidor escuchando en el puerto $Port."
}

$xulpn = (Get-Command cloudflared -ErrorAction Stop).Source
Write-Host "Publicando el túnel de Cloudflare (acceso desde cualquier lugar)..."
$cf = Start-Process -FilePath $xulpn `
    -ArgumentList @("tunnel", "--url", "http://127.0.0.1:$Port", "--no-autoupdate") `
    -WindowStyle Hidden -RedirectStandardOutput $logTunel -RedirectStandardError $logTunelErr -PassThru
if ($cf.HasExited) {
    Write-Host "cloudflared no arrancó."
    exit 1
}

$url = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    $contenido = ""
    if (Test-Path $logTunel) { $contenido += Get-Content $logTunel -Raw -ErrorAction SilentlyContinue }
    if (Test-Path $logTunelErr) { $contenido += Get-Content $logTunelErr -Raw -ErrorAction SilentlyContinue }
    if ($contenido -match "https://[a-z0-9-]+\.trycloudflare\.com") {
        $url = $matches[0].ToString()
        break
    }
}

$excel = & python -c "from expense_tracker.storage import default_data_file; print(default_data_file())"

Write-Host ""
if ($url) {
    Write-Host "======================================================"
    Write-Host "  Abre en tu iPhone (desde cualquier sitio):"
    Write-Host "  $url"
    Write-Host "======================================================"
    try { Start-Process $url } catch {}
} else {
    Write-Host "No se pudo obtener la URL del túnel. Revisa $logTunelErr"
    if (Test-Path $logTunelErr) { Get-Content $logTunelErr }
}
Write-Host ""
Write-Host "Los datos se guardan en tu Excel en la nube:"
Write-Host "  $excel"
Write-Host ""
Write-Host "El túnel y el servidor siguen en segundo plano."
Write-Host "Para detenerlos:"
Write-Host "  Get-Process | Where-Object { $_.ProcessName -match 'python|cloudflared' } | Stop-Process"