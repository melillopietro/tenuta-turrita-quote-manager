# Tenuta Turrita - Setup Automatico Windows (Windows 10 / Windows 11)
# Configura runtime Python, ambiente virtuale e dipendenze al primo avvio.

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "======================================================================" -ForegroundColor DarkGreen
Write-Host " TENUTA TURRITA - CONFIGURAZIONE AUTOMATICA PRIMO AVVIO (WINDOWS)" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor DarkGreen
Write-Host ""

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    Write-Host "[OK] Ambiente virtuale già presente e configurato." -ForegroundColor Cyan
    exit 0
}

function Find-SystemPython {
    foreach ($cmd in @("py -3", "python", "py")) {
        try {
            $parts = $cmd.Split(" ")
            $exe = $parts[0]
            $args = if ($parts.Length -gt 1) { $parts[1] } else { "--version" }
            $res = Start-Process -FilePath $exe -ArgumentList $args -NoNewWindow -PassThru -Wait -RedirectStandardOutput nul -RedirectStandardError nul
            if ($res.ExitCode -eq 0) {
                return $exe
            }
        } catch {}
    }
    return $null
}

$SysPython = Find-SystemPython

if (-not $SysPython) {
    Write-Host "[INFO] Python non rilevato nel sistema. Avvio installazione automatica..." -ForegroundColor Yellow

    $installedViaWinget = $false
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "[INFO] Tentativo di installazione tramite Windows Package Manager (winget)..." -ForegroundColor Yellow
        try {
            Start-Process -FilePath "winget" -ArgumentList "install --id Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements" -NoNewWindow -Wait
            Start-Sleep -Seconds 3
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            $SysPython = Find-SystemPython
            if ($SysPython) { $installedViaWinget = $true }
        } catch {}
    }

    if (-not $installedViaWinget) {
        Write-Host "[INFO] Download dell'installer ufficiale Python da python.org in corso..." -ForegroundColor Yellow
        $tempDir = [System.IO.Path]::GetTempPath()
        $installerPath = Join-Path $tempDir "python-3.12.5-amd64.exe"
        $downloadUrl = "https://www.python.org/ftp/python/3.12.5/python-3.12.5-amd64.exe"

        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
        Write-Host "[INFO] Installazione automatica non presidiata di Python..." -ForegroundColor Yellow

        $proc = Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 SimpleInstall=1 Include_test=0" -Wait -PassThru
        if ($proc.ExitCode -ne 0 -and $proc.ExitCode -ne 3010) {
            Write-Host "[AVVISO] Codice uscita installer: $($proc.ExitCode)" -ForegroundColor DarkYellow
        }

        Start-Sleep -Seconds 4
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $localAppPython = Join-Path $env:LocalAppData "Programs\Python\Python312\python.exe"
        if (Test-Path $localAppPython) {
            $SysPython = $localAppPython
        } else {
            $SysPython = Find-SystemPython
        }
    }
}

if (-not $SysPython) {
    Write-Host "[ERRORE] Impossibile configurare automaticamente Python." -ForegroundColor Red
    Write-Host "Installa Python manualmente da https://www.python.org/downloads/ ricordando di selezionare 'Add Python to PATH'." -ForegroundColor Yellow
    exit 1
}

Write-Host "[INFO] Utilizzo interprete Python: $SysPython" -ForegroundColor Green
Write-Host "[INFO] Creazione ambiente virtuale locale (.venv)..." -ForegroundColor Yellow

Start-Process -FilePath $SysPython -ArgumentList "-m venv .venv" -NoNewWindow -Wait

if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERRORE] Creazione dell'ambiente virtuale fallita." -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Aggiornamento gestore pacchetti (pip)..." -ForegroundColor Yellow
Start-Process -FilePath $VenvPython -ArgumentList "-m pip install --upgrade pip" -NoNewWindow -Wait

Write-Host "[INFO] Installazione dipendenze gestionali (requirements.txt)..." -ForegroundColor Yellow
$reqPath = Join-Path $ProjectRoot "requirements.txt"
Start-Process -FilePath $VenvPython -ArgumentList "-m pip install -r `"$reqPath`"" -NoNewWindow -Wait

Write-Host ""
Write-Host "======================================================================" -ForegroundColor DarkGreen
Write-Host " [OK] Configurazione completata con successo!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor DarkGreen
Write-Host ""
