<# Bounded foreground supervisor: never clears STOP or bypasses a refusal. #>
[CmdletBinding()]
param(
    [string]$PrivateRoot = (Join-Path $env:USERPROFILE 'et-channelers-private'),
    [string]$LauncherPath = '',
    [string]$ToolRoot = (Join-Path $env:USERPROFILE 'et-channelers-tools'),
    [ValidateSet('Run','RunAll','RunFinal')][string]$Mode = 'RunAll',
    [string]$Remote = 'etdrive:04 Audio',
    [string]$RcloneConfig = '',
    [switch]$SkipCatalogCheckpoint,
    [ValidateRange(1,8)][int]$DlWorkers = 4,
    [ValidateRange(1,2)][int]$UploadTransfers = 2,
    [ValidateRange(1,16)][int]$UploadBatchItems = 8,
    [ValidateRange(0,300)][double]$UploadBatchSeconds = 10,
    [ValidateRange(1,64)][int]$ReadyItems = 16,
    [ValidateRange(0.01,100)][double]$RateMiB = 2,
    [ValidateRange(0,3600)][double]$MinInterval = 5,
    [ValidateRange(1,4)][int]$MaxAttempts = 3,
    [switch]$ResetRetryBudget
)
$ErrorActionPreference = 'Stop'
if (-not $LauncherPath) { $LauncherPath = Join-Path $PSScriptRoot 'start_drive_ingest.ps1' }
$EtSync = Join-Path $PrivateRoot 'sync'
$EtStopPath = Join-Path $EtSync 'STOP_DRIVE_INGEST'
$EtCooldownPath = Join-Path $EtSync 'drive_ingest_cooldown.json'
$EtStatePath = Join-Path $EtSync 'drive_ingest_resume_state.json'
$EtRunner = $LauncherPath
$EtLockPath = Join-Path $EtSync 'drive_ingest_supervisor.lock'
if (-not (Test-Path -LiteralPath $EtRunner -PathType Leaf)) { throw 'Reviewed launcher not found.' }
if ($UploadBatchItems -gt $ReadyItems) { throw 'UploadBatchItems cannot exceed ReadyItems.' }
New-Item -ItemType Directory -Force -Path $EtSync | Out-Null
$EtLock = $null
$EtAttempts = 0
$EtNext = 0.0
$EtPreviousCode = 0

function Read-DriveUntil {
    if (-not (Test-Path -LiteralPath $EtCooldownPath -PathType Leaf)) { return 0.0 }
    try {
        $EtCooldown = Get-Content -LiteralPath $EtCooldownPath -Raw | ConvertFrom-Json
        $EtUntil = [double]$EtCooldown.until_epoch
        if ([double]::IsNaN($EtUntil) -or [double]::IsInfinity($EtUntil) -or $EtUntil -le 0 -or $EtUntil -ge 253402300799) { throw 'invalid' }
        return $EtUntil
    } catch { throw 'Drive cooldown is unreadable; no retry or network request was started.' }
}
function Write-ResumeState([string]$State, [double]$Until = 0, [int]$Code = 0) {
    $EtRecord = [ordered]@{schema_version=2;state=$State;updated_at=[DateTime]::UtcNow.ToString('o');
        mode=$Mode;supervisor_pid=$PID;attempts=$EtAttempts;max_attempts=$MaxAttempts;
        until_epoch=$Until;exit_code=$Code;download_workers=$DlWorkers;upload_transfers=$UploadTransfers}
    $EtBytes = [Text.UTF8Encoding]::new($false).GetBytes(($EtRecord | ConvertTo-Json) + [Environment]::NewLine)
    $EtTemporary = $EtStatePath + '.tmp'
    $EtStream = [IO.File]::Open($EtTemporary, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $EtStream.Write($EtBytes, 0, $EtBytes.Length); $EtStream.Flush($true) } finally { $EtStream.Dispose() }
    if (Test-Path -LiteralPath $EtStatePath -PathType Leaf) { [IO.File]::Replace($EtTemporary, $EtStatePath, [NullString]::Value) }
    else { [IO.File]::Move($EtTemporary, $EtStatePath) }
}
try {
    try { $EtLock = [IO.File]::Open($EtLockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None) }
    catch { Write-Error 'Another supervisor owns this private root; no second collector was started.'; exit 3 }
    if (Test-Path -LiteralPath $EtStatePath -PathType Leaf) {
        $EtPrior = Get-Content -LiteralPath $EtStatePath -Raw | ConvertFrom-Json
        if ($EtPrior.schema_version -eq 2) {
            foreach ($EtField in @('attempts','until_epoch','exit_code')) {
                if ($EtPrior.PSObject.Properties.Name -notcontains $EtField -or $null -eq $EtPrior.$EtField) { throw 'Supervisor state is incomplete; no network request was started.' }
            }
            $EtAttempts = [int]$EtPrior.attempts
            $EtNext = [double]$EtPrior.until_epoch
            $EtPreviousCode = [int]$EtPrior.exit_code
            if ($EtAttempts -lt 0 -or $EtAttempts -gt 100 -or [double]::IsNaN($EtNext) -or [double]::IsInfinity($EtNext) -or $EtNext -lt 0 -or $EtNext -ge 253402300799) { throw 'Supervisor state is invalid; no network request was started.' }
        } elseif ($EtPrior.one_attempt -and $EtPrior.state -eq 'paused_after_one_attempt') {
            $EtAttempts = 1
            $EtPreviousCode = [int]$EtPrior.exit_code
        } else { throw 'Unknown supervisor state; preserve it and review before resuming.' }
    }
    if ($ResetRetryBudget) { $EtAttempts = 0 } # Explicit operator action; never clears a cooldown.
    while ($true) {
        if (Test-Path -LiteralPath $EtStopPath) { Write-ResumeState 'stopped' 0 130; exit 130 }
        if ($EtAttempts -ge $MaxAttempts) { Write-ResumeState 'retry_budget_exhausted' $EtNext 75; exit 75 }
        $EtNext = [math]::Max($EtNext, (Read-DriveUntil))
        $EtRemaining = $EtNext - [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        if ($EtRemaining -gt 0) {
            Write-ResumeState 'waiting_for_drive_cooldown' $EtNext $EtPreviousCode
            while ($EtRemaining -gt 0) {
                if (Test-Path -LiteralPath $EtStopPath) { Write-ResumeState 'stopped' $EtNext 130; exit 130 }
                Start-Sleep -Milliseconds ([int][math]::Min(2000, [math]::Max(1, $EtRemaining * 1000)))
                $EtNext = [math]::Max($EtNext, (Read-DriveUntil))
                $EtRemaining = $EtNext - [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
            }
        }
        if (Test-Path -LiteralPath $EtStopPath) { Write-ResumeState 'stopped' $EtNext 130; exit 130 }
        $EtAttempts++
        Write-ResumeState 'running_stages' 0 0 # Persist the spent attempt before starting the child.
        $EtArguments = @('-NoProfile','-ExecutionPolicy','Bypass','-File',$EtRunner,'-Mode',$Mode,
            '-PrivateRoot',$PrivateRoot,'-ToolRoot',$ToolRoot,'-Remote',$Remote,'-DlWorkers',[string]$DlWorkers,
            '-UploadTransfers',[string]$UploadTransfers,'-UploadBatchItems',[string]$UploadBatchItems,
            '-UploadBatchSeconds',$UploadBatchSeconds.ToString([Globalization.CultureInfo]::InvariantCulture),
            '-ReadyItems',[string]$ReadyItems,'-RateMiB',$RateMiB.ToString([Globalization.CultureInfo]::InvariantCulture),
            '-MinInterval',$MinInterval.ToString([Globalization.CultureInfo]::InvariantCulture))
        if ($RcloneConfig) { $EtArguments += @('-RcloneConfig',$RcloneConfig) }
        if ($SkipCatalogCheckpoint) { $EtArguments += '-SkipCatalogCheckpoint' }
        $EtNativePreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            $global:LASTEXITCODE = $null
            & powershell.exe @EtArguments 2>&1 | ForEach-Object {
                if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.ToString() } else { $_ }
            }
            $EtPreviousCode = if ($null -eq $global:LASTEXITCODE) { 3 } else { [int]$global:LASTEXITCODE }
        } finally { $ErrorActionPreference = $EtNativePreference }
        if ($EtPreviousCode -eq 0) { Write-ResumeState 'stages_complete' 0 0; exit 0 }
        if ($EtPreviousCode -ne 75) { Write-ResumeState 'stopped_after_nonquota_result' 0 $EtPreviousCode; exit $EtPreviousCode }
        # Quotas alone are retryable. Keep the later provider/core deadline, with a 10/20/40/60 minute backoff.
        $EtBackoff = [math]::Min(3600, 600 * [math]::Pow(2, $EtAttempts - 1))
        $EtNext = [math]::Max((Read-DriveUntil), [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + $EtBackoff)
        Write-ResumeState 'waiting_for_drive_cooldown' $EtNext 75
    }
} finally {
    if ($EtLock) { $EtLock.Dispose() }
}
