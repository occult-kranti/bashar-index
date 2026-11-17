<#
.SYNOPSIS
Plan, run, or inspect the bounded YouTube-to-Drive audio collector.
.DESCRIPTION
Uses tools and private state outside this repository. Run uploads each native
audio/metadata pair, verifies both remote checksums, then deletes its local copies. No
transcription, audio encoding, hidden jobs, or credential-file reads are started.
See WINDOWS_DRIVE.md for the one-time rclone connection.
#>
[CmdletBinding()]
param(
    [ValidateSet('Plan', 'Run', 'RunAll', 'Index', 'RunFinal', 'Status')]
    [string]$Mode = 'Plan',

    [string]$PrivateRoot = (Join-Path $env:USERPROFILE 'et-channelers-private'),
    [string]$ToolRoot = (Join-Path $env:USERPROFILE 'et-channelers-tools'),
    [string]$Queue = '',
    [string]$FullQueue = '',
    [string]$FiftyQueue = '',
    [string]$FinalQueue = '',
    [string]$Remote = 'etdrive:04 Audio',
    [string]$RcloneConfig = '',
    [switch]$SkipCatalogCheckpoint,

    [Alias('Workers')]
    [ValidateRange(1, 8)]
    [int]$DlWorkers = 4,
    [ValidateRange(1, 4)]
    [int]$UploadTransfers = 2,
    [ValidateRange(1, 17)]
    [double]$MaxLocalGb = 17,
    [ValidateRange(1, 16)]
    [int]$UploadBatchItems = 8,
    [ValidateRange(0, 300)]
    [double]$UploadBatchSeconds = 10,
    [ValidateRange(1, 64)]
    [int]$ReadyItems = 16,
    [ValidateRange(0.01, 100)]
    [double]$RateMiB = 2,
    [ValidateRange(0, 3600)]
    [double]$MinInterval = 5,
    [ValidateSet('default', 'mweb')]
    [string]$YoutubeClient = 'default',
    [switch]$BrowserAudio,

    [ValidateRange(0, 2147483647)]
    [int]$Limit = 0
)

$ErrorActionPreference = 'Stop'
if ($UploadBatchItems -gt $ReadyItems) {
    throw 'UploadBatchItems cannot exceed ReadyItems.'
}
$EtScripts = Join-Path $ToolRoot 'venv\Scripts'
$EtPython = Join-Path $EtScripts 'python.exe'
$EtYtdlp = Join-Path $EtScripts 'yt-dlp.exe'
$EtRclone = Join-Path $ToolRoot 'rclone.exe'
$EtRunner = Join-Path $PSScriptRoot 'drive_ingest.py'
$EtStageBuilder = Join-Path $PSScriptRoot 'prepare_collection_stages.py'
$EtCatalog = Join-Path $PSScriptRoot 'archive_catalog.py'
$EtJobs = Join-Path $PrivateRoot 'jobs'
$EtFiftyEnriched = Join-Path $EtJobs 'queue_newest50_enriched.csv'
$EtBuiltFinalQueue = Join-Path $EtJobs 'queue_final_round.csv'
if ($Mode -in @('RunAll', 'Index') -and $FinalQueue -and -not [string]::Equals(
        [IO.Path]::GetFullPath($FinalQueue), [IO.Path]::GetFullPath($EtBuiltFinalQueue),
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'RunAll and Index build jobs/queue_final_round.csv under PrivateRoot. A custom -FinalQueue is supported only by -Mode RunFinal.'
}

if (-not (Test-Path -LiteralPath $EtPython -PathType Leaf)) {
    throw "Python environment missing: $EtPython. See WINDOWS_DRIVE.md or pass -ToolRoot."
}
if (-not (Test-Path -LiteralPath $EtRunner -PathType Leaf)) {
    throw "Collector missing: $EtRunner. Update this checkout before running."
}
if (-not $Queue) {
    $EtEnrichedQueue = Join-Path $PrivateRoot 'jobs\queue_newest20_enriched.csv'
    $Queue = if (Test-Path -LiteralPath $EtEnrichedQueue -PathType Leaf) {
        $EtEnrichedQueue
    } else {
        Join-Path $PrivateRoot 'jobs\queue_newest20.csv'
    }
}
if (-not $FullQueue) {
    $FullQueue = Join-Path $PrivateRoot 'jobs\queue_youtube_all_merged.csv'
}
if (-not $FiftyQueue) { $FiftyQueue = Join-Path $EtJobs 'queue_newest50.csv' }
if (-not $FinalQueue) { $FinalQueue = $EtBuiltFinalQueue }
if ($Mode -eq 'RunAll') {
    if ($Limit -gt 0) {
        throw 'RunAll requires complete phases; use -Mode Run -Limit N for a pilot.'
    }
}
if ($Mode -in @('RunAll', 'Index')) {
    foreach ($EtInput in @($FullQueue, $FiftyQueue, $EtStageBuilder)) {
        if (-not (Test-Path -LiteralPath $EtInput -PathType Leaf)) { throw "Stage input missing: $EtInput" }
    }
}
if ($Mode -eq 'RunFinal' -and -not (Test-Path -LiteralPath $EtFiftyEnriched -PathType Leaf)) {
    throw 'Enriched newest-50 queue missing. Run -Mode Index to prepare the local stages first.'
}
if ($Mode -eq 'RunFinal' -and -not (Test-Path -LiteralPath $FinalQueue -PathType Leaf)) {
    throw 'Final-round index missing. Run -Mode Index to prepare it.'
}
if ($Mode -ne 'Status' -and -not (Test-Path -LiteralPath $Queue -PathType Leaf)) {
    throw "Queue missing: $Queue. Restore the newest-20 queue or pass -Queue."
}
if ($Mode -in @('Run', 'RunAll', 'RunFinal')) {
    foreach ($EtTool in @($EtYtdlp, $EtRclone)) {
        if (-not (Test-Path -LiteralPath $EtTool -PathType Leaf)) {
            throw "Required tool missing: $EtTool. See WINDOWS_DRIVE.md or pass -ToolRoot."
        }
    }
}
if ($RcloneConfig -and -not (Test-Path -LiteralPath $RcloneConfig -PathType Leaf)) {
    throw "Named rclone configuration does not exist: $RcloneConfig"
}

$EtCommand = if ($Mode -in @('RunAll', 'RunFinal')) { 'run' } else { $Mode.ToLowerInvariant() }
$EtArguments = @(
    '-I', $EtRunner, $EtCommand,
    '--root', $PrivateRoot,
    '--queue', $Queue,
    '--remote', $Remote,
    '--newest', '20',
    '--workers', [string]$DlWorkers,
    '--upload-transfers', [string]$UploadTransfers,
    '--upload-batch-items', [string]$UploadBatchItems,
    '--upload-batch-seconds', $UploadBatchSeconds.ToString([Globalization.CultureInfo]::InvariantCulture),
    '--ready-items', [string]$ReadyItems,
    '--max-local-gb', $MaxLocalGb.ToString([Globalization.CultureInfo]::InvariantCulture),
    '--max-item-mb', '0',
    '--min-free-gb', '3',
    '--rate-mib', $RateMiB.ToString([Globalization.CultureInfo]::InvariantCulture),
    '--http-chunk-mib', '1',
    '--min-interval', $MinInterval.ToString([Globalization.CultureInfo]::InvariantCulture),
    '--ytdlp', $EtYtdlp,
    '--youtube-client', $YoutubeClient,
    '--rclone', $EtRclone
)
if ($BrowserAudio) { $EtArguments += '--browser-audio' }
if ($RcloneConfig) {
    $EtArguments += @('--rclone-config', $RcloneConfig)
}
if ($Mode -in @('Run', 'RunAll', 'RunFinal')) {
    if ($Limit -gt 0) {
        $EtArguments += @('--limit', [string]$Limit)
    } else {
        $EtArguments += '--all'
    }
}

$EtCompletionCheck = @'
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent))
from drive_ingest import load_state, receipt_complete, select_queue, terminal_unavailable
root, queue, remote, newest = Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], int(sys.argv[5])
entire = len(sys.argv) > 6 and sys.argv[6] == 'entire'
rows = select_queue(queue, newest, entire)
state = load_state(root / 'sync' / 'drive_ingest_manifest.jsonl')
verified = [r['video_id'] for r in rows if receipt_complete(state.get(r['video_id'], {}), r, remote)]
unavailable = [r['video_id'] for r in rows if terminal_unavailable(state.get(r['video_id'], {}))]
resolved = set(verified) | set(unavailable)
pending = [r['video_id'] for r in rows if r['video_id'] not in resolved]
print(json.dumps({'phase': 'final_completion_gate' if entire else f'newest{newest}_completion_gate', 'required': len(rows),
                  'verified': len(verified), 'unavailable': len(unavailable), 'pending': len(pending),
                  'sample_pending_ids': pending[:5]}))
raise SystemExit(3 if pending or (not rows and not entire) else 0)
'@
$EtIndexArguments = @('-I', $EtStageBuilder, '--newest20', $Queue, '--newest50', $FiftyQueue,
                     '--full', $FullQueue, '--out-dir', $EtJobs)

function Invoke-EtPython([string[]]$Arguments) {
    # Windows PowerShell 5 can turn benign native stderr into a terminating error
    # when an outer caller redirects *> to a log. The native exit code is authoritative.
    $EtNativePreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $global:LASTEXITCODE = $null
        & $EtPython @Arguments 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.ToString() } else { $_ }
        }
        $script:EtExitCode = if ($null -eq $global:LASTEXITCODE) { 3 } else { [int]$global:LASTEXITCODE }
    } finally { $ErrorActionPreference = $EtNativePreference }
}

function Invoke-EtCatalogCheckpoint {
    if ($SkipCatalogCheckpoint -or -not (Test-Path -LiteralPath $EtCatalog -PathType Leaf)) { return }
    $EtStopMarker = Join-Path $PrivateRoot 'sync\STOP_DRIVE_INGEST'
    if (Test-Path -LiteralPath $EtStopMarker) { $script:EtExitCode = 130; return }
    Invoke-EtPython -Arguments @('-I', $EtCatalog, 'prepare', '--root', $PrivateRoot, '--queue', $FullQueue, '--remote', $Remote)
    if ($script:EtExitCode -ne 0) { return }
    if (Test-Path -LiteralPath $EtStopMarker) { $script:EtExitCode = 130; return }
    $EtCatalogArguments = @('-I', $EtCatalog, 'upload', '--root', $PrivateRoot,
                            '--remote', $Remote, '--rclone', $EtRclone)
    if ($RcloneConfig) { $EtCatalogArguments += @('--rclone-config', $RcloneConfig) }
    Invoke-EtPython -Arguments $EtCatalogArguments
}

$EtPreviousPath = $env:PATH
$EtPreviousOverride = [Environment]::GetEnvironmentVariable('ET_YOUTUBE_ROBOTS_OVERRIDE', 'Process')
$EtExitCode = 1
try {
    # The installed Deno runtime lives beside yt-dlp and must be discoverable.
    $env:PATH = "$EtScripts;$EtPreviousPath"
    if ($Mode -in @('Run', 'RunAll', 'RunFinal')) {
        $env:ET_YOUTUBE_ROBOTS_OVERRIDE = '1'
    }
    if ($Mode -eq 'Index') {
        Invoke-EtPython -Arguments $EtIndexArguments
    } elseif ($Mode -eq 'RunFinal') {
        # This mode resumes only the final stage after the same newest-50 gate.
        Invoke-EtPython -Arguments @('-I', '-c', $EtCompletionCheck, $EtRunner, $PrivateRoot, $EtFiftyEnriched, $Remote, '50')
        if ($EtExitCode -eq 0) { Invoke-EtCatalogCheckpoint }
        if ($EtExitCode -eq 0) {
            $EtFinalArguments = @($EtArguments)
            $EtFinalArguments[[Array]::IndexOf($EtFinalArguments, '--queue') + 1] = $FinalQueue
            $EtFinalArguments += '--entire-queue'
            Invoke-EtPython -Arguments $EtFinalArguments
            if ($EtExitCode -eq 0 -and $Limit -eq 0) {
                Invoke-EtPython -Arguments @('-I', '-c', $EtCompletionCheck, $EtRunner, $PrivateRoot, $FinalQueue, $Remote, '50', 'entire')
                if ($EtExitCode -eq 0) { Invoke-EtCatalogCheckpoint }
            }
        }
    } else {
        # Validate and refresh all local stage inputs before starting network work.
        $EtExitCode = 0
        if ($Mode -eq 'RunAll') {
            Invoke-EtPython -Arguments $EtIndexArguments
        }
        if ($EtExitCode -eq 0) {
            Invoke-EtPython -Arguments $EtArguments
        }
        if ($Mode -eq 'RunAll' -and $EtExitCode -eq 0) {
            Invoke-EtPython -Arguments @('-I', '-c', $EtCompletionCheck, $EtRunner, $PrivateRoot, $Queue, $Remote, '20')
            if ($EtExitCode -eq 0) { Invoke-EtCatalogCheckpoint }
            if ($EtExitCode -eq 0) {
                $EtFiftyArguments = @($EtArguments)
                $EtFiftyArguments[[Array]::IndexOf($EtFiftyArguments, '--queue') + 1] = $EtFiftyEnriched
                $EtFiftyArguments[[Array]::IndexOf($EtFiftyArguments, '--newest') + 1] = '50'
                Invoke-EtPython -Arguments $EtFiftyArguments
            }
            if ($EtExitCode -eq 0) {
                Invoke-EtPython -Arguments @('-I', '-c', $EtCompletionCheck, $EtRunner, $PrivateRoot, $EtFiftyEnriched, $Remote, '50')
                if ($EtExitCode -eq 0) { Invoke-EtCatalogCheckpoint }
            }
            if ($EtExitCode -eq 0) {
                $EtFinalArguments = @($EtArguments)
                $EtFinalArguments[[Array]::IndexOf($EtFinalArguments, '--queue') + 1] = $FinalQueue
                $EtFinalArguments += '--entire-queue'
                Invoke-EtPython -Arguments $EtFinalArguments
                if ($EtExitCode -eq 0) {
                    Invoke-EtPython -Arguments @('-I', '-c', $EtCompletionCheck, $EtRunner, $PrivateRoot, $FinalQueue, $Remote, '50', 'entire')
                    if ($EtExitCode -eq 0) { Invoke-EtCatalogCheckpoint }
                }
                if ($EtExitCode -eq 0) {
                    Write-Output 'Newest 20, newest 50, and the remaining archive have finished their receipt checks.'
                }
            } else {
                Write-Warning 'A collection tier is incomplete or temporarily blocked. Later stages have not started; resume the same command when its recorded cooldown ends.'
            }
        }
    }
} finally {
    $env:PATH = $EtPreviousPath
    [Environment]::SetEnvironmentVariable('ET_YOUTUBE_ROBOTS_OVERRIDE', $EtPreviousOverride, 'Process')
}
exit $EtExitCode
