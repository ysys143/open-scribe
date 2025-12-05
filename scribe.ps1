# Open-Scribe PowerShell Module
# Windows PowerShell support for open-scribe

param()

# Set installation directory with fallback to default location
$INSTALL_DIR = if ($env:OPEN_SCRIBE_HOME) {
    $env:OPEN_SCRIBE_HOME
} else {
    Join-Path $env:USERPROFILE ".local\share\open-scribe"
}

# Virtual environment and Python paths
$VENV_DIR = Join-Path $INSTALL_DIR ".venv"
$PYTHON_EXE = Join-Path $VENV_DIR "Scripts\python.exe"
$MAIN_PY = Join-Path $INSTALL_DIR "main.py"
$VERSION_CHECK_FILE = Join-Path $INSTALL_DIR ".ytdlp_version_check"

function scribe {
    <#
    .SYNOPSIS
    Open-Scribe - YouTube transcription tool

    .DESCRIPTION
    Transcribe YouTube videos or local audio files with various engines

    .PARAMETER URL
    YouTube URL or local audio file path

    .PARAMETER Arguments
    Additional arguments to pass to the transcriber

    .EXAMPLE
    scribe "https://www.youtube.com/watch?v=VIDEO_ID"
    scribe "C:\audio\file.mp3" --engine whisper-api
    #>

    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true, Position=0)]
        [string]$URL,

        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Arguments
    )

    # Check if installation directory exists
    if (-not (Test-Path $INSTALL_DIR)) {
        Write-Host "❌ Error: open-scribe not found at $INSTALL_DIR" -ForegroundColor Red
        Write-Host "Please run: make install" -ForegroundColor Yellow
        return 1
    }

    # Check if Python executable exists
    if (-not (Test-Path $PYTHON_EXE)) {
        Write-Host "❌ Error: Python environment not found at $VENV_DIR" -ForegroundColor Red
        Write-Host "Please run: make install" -ForegroundColor Yellow
        return 1
    }

    # Check and update yt-dlp for YouTube URLs
    if ($URL -match "^https?://") {
        Check-And-Update-YtDlp
    }

    # Expand environment variables and handle paths
    $EXPANDED_URL = if ($URL -match "^https?://") {
        $URL
    } else {
        # Expand environment variables and home directory for local paths
        $URL -replace '^\$\{?env:(\w+)\}?', { $env:$($_.Groups[1].Value) } `
             -replace '^~', $env:USERPROFILE
    }

    # Run transcription
    & $PYTHON_EXE $MAIN_PY $EXPANDED_URL @Arguments
}

function Check-And-Update-YtDlp {
    <#
    .SYNOPSIS
    Check and update yt-dlp if needed
    #>

    $CURRENT_DATE = Get-Date -Format "yyyyMMdd"

    # Check if we already checked today
    if (Test-Path $VERSION_CHECK_FILE) {
        $LAST_CHECK = Get-Content $VERSION_CHECK_FILE -Raw -ErrorAction SilentlyContinue
        if ($LAST_CHECK -eq $CURRENT_DATE) {
            return  # Already checked today
        }
    }

    Write-Host "🔍 Checking yt-dlp version..." -ForegroundColor Cyan

    # Get current yt-dlp version
    $CURRENT_VERSION = & $PYTHON_EXE -m pip list 2>$null | Select-String "yt-dlp" | ForEach-Object { $_.ToString().Split()[1] }

    if (-not $CURRENT_VERSION) {
        Write-Host "⚠️  yt-dlp not installed. Installing..." -ForegroundColor Yellow
        Push-Location $INSTALL_DIR
        & $PYTHON_EXE -m pip install yt-dlp 2>&1 | Out-Null
        Pop-Location
        Set-Content $VERSION_CHECK_FILE $CURRENT_DATE
        return
    }

    # Check for updates
    Write-Host "📦 Checking for yt-dlp updates..." -ForegroundColor Cyan
    Push-Location $INSTALL_DIR

    $UPDATE_OUTPUT = & $PYTHON_EXE -m pip install --upgrade yt-dlp 2>&1 | Out-String

    Pop-Location

    if ($UPDATE_OUTPUT -match "Successfully installed") {
        $NEW_VERSION = [regex]::Match($UPDATE_OUTPUT, "yt-dlp==([0-9.]+)").Groups[1].Value
        Write-Host "✅ yt-dlp updated: $CURRENT_VERSION → $NEW_VERSION" -ForegroundColor Green
    } else {
        Write-Host "✅ yt-dlp is up to date: $CURRENT_VERSION" -ForegroundColor Green
    }

    # Mark that we checked today
    Set-Content $VERSION_CHECK_FILE $CURRENT_DATE
}

# Export function for module loading
Export-ModuleMember -Function scribe
