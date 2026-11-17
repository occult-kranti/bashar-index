param(
    [string]$PrivateRoot = (Join-Path $env:USERPROFILE 'et-channelers-private'),
    [string]$ToolsRoot = (Join-Path $env:USERPROFILE 'et-channelers-tools'),
    [int]$Port = 8768
)
$ErrorActionPreference = 'Stop'
$EtRepository = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$EtPython = Join-Path $ToolsRoot 'venv\Scripts\python.exe'
$EtService = Join-Path $PSScriptRoot 'chromium_capture_service.py'
$EtFFmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
$EtFFprobe = (Get-Command ffprobe -ErrorAction Stop).Source
$EtJobs = Join-Path $PrivateRoot 'jobs'
$EtArgs = @('-I', $EtService, '--root', $PrivateRoot,
    '--queue', (Join-Path $EtJobs 'queue_newest20_enriched.csv'),
    '--requested', (Join-Path $EtJobs 'queue_requested_videos.csv'),
    '--managed-root', $ToolsRoot, '--managed-root', $EtRepository,
    '--ffmpeg', $EtFFmpeg, '--ffprobe', $EtFFprobe,
    '--rclone', (Join-Path $ToolsRoot 'rclone.exe'), '--port', [string]$Port)
$EtOtherWorktree = Join-Path (Split-Path $EtRepository -Parent) 'bashar-dashboard-redesign'
if (Test-Path -LiteralPath $EtOtherWorktree) {
    $EtArgs += @('--managed-root', $EtOtherWorktree)
}
foreach ($EtPath in @($EtPython, $EtService, $PrivateRoot, $ToolsRoot, $EtJobs)) {
    if (-not (Test-Path -LiteralPath $EtPath)) { throw 'A required capture path is missing.' }
}
# Start-Process joins argument arrays on Windows: quote each known path/value.
$EtQuotedArgs = $EtArgs | ForEach-Object {
    if ($_ -match '["\r\n]') { throw 'Unsupported character in a capture argument.' }
    '"' + $_ + '"'
}
$EtProcess = Start-Process -FilePath $EtPython -ArgumentList $EtQuotedArgs -WindowStyle Hidden -PassThru `
    -WorkingDirectory $EtRepository `
    -RedirectStandardOutput (Join-Path $EtJobs 'browser-capture-stdout.log') `
    -RedirectStandardError (Join-Path $EtJobs 'browser-capture-stderr.log')
[ordered]@{pid=$EtProcess.Id; port=$Port; started_at=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $EtJobs 'browser-capture-process.json') -Encoding UTF8
Write-Output "Capture service started; check http://127.0.0.1:$Port/capture/v1/health . Chrome activation is separate."
