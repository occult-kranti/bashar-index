<#
.SYNOPSIS
Plan, run, or inspect the bounded YouTube-to-Drive audio collector.
.DESCRIPTION
Uses tools and private state outside this repository. Run uploads each native
audio file, verifies its remote checksum, then deletes its local copy. No
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

    [ValidateRange(0, 2147483647)]
    [int]$Limit = 0
)

$ErrorActionPreference = 'Stop'
$EtScripts = Join-Path $ToolRoot 'venv\Scripts'
$EtPython = Join-Path $EtScripts 'python.exe'
$EtYtdlp = Join-Path $EtScripts 'yt-dlp.exe'
$EtRclone = Join-Path $ToolRoot 'rclone.exe'
$EtRunner = Join-Path $PSScriptRoot 'drive_ingest.py'
$EtStageBuilder = Join-Path $PSScriptRoot 'prepare_collection_stages.py'
$EtJobs = Join-Path $PrivateRoot 'jobs'
$EtFiftyEnriched = Join-Path $EtJobs 'queue_newest50_enriched.csv'

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
if (-not $FinalQueue) { $FinalQueue = Join-Path $EtJobs 'queue_final_round.csv' }
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
if ($Mode -in @('RunAll', 'RunFinal') -and -not (Test-Path -LiteralPath $EtFiftyEnriched -PathType Leaf)) {
    throw 'Enriched newest-50 queue missing. Run -Mode Index to prepare the local stages first.'
}
if ($Mode -eq 'RunFinal' -and -not (Test-Path -LiteralPath $FinalQueue -PathType Leaf)) {
    throw 'Final-round index missing. Run -Mode Index to prepare it; no final downloads start automatically.'
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
    '--workers', '4',
    '--max-local-gb', '19',
    '--max-item-mb', '0',
    '--min-free-gb', '3',
    '--rate-mib', '2',
    '--http-chunk-mib', '1',
    '--min-interval', '5',
    '--ytdlp', $EtYtdlp,
    '--rclone', $EtRclone
)
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
from drive_ingest import load_state, receipt_complete, select_queue
root, queue, remote, newest = Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], int(sys.argv[5])
rows = select_queue(queue, newest)
state = load_state(root / 'sync' / 'drive_ingest_manifest.jsonl')
pending = [r['video_id'] for r in rows if not receipt_complete(state.get(r['video_id'], {}), r, remote)]
print(json.dumps({'phase': f'newest{newest}_completion_gate', 'required': len(rows),
                  'verified': len(rows) - len(pending), 'pending': len(pending),
                  'sample_pending_ids': pending[:5]}))
raise SystemExit(3 if pending or not rows else 0)
'@
$EtIndexArguments = @('-I', $EtStageBuilder, '--newest20', $Queue, '--newest50', $FiftyQueue,
                     '--full', $FullQueue, '--out-dir', $EtJobs)

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
        & $EtPython @EtIndexArguments
        $EtExitCode = $LASTEXITCODE
    } elseif ($Mode -eq 'RunFinal') {
        # This mode requires a separate explicit invocation; RunAll never reaches it.
        & $EtPython '-I' '-c' $EtCompletionCheck $EtRunner $PrivateRoot $EtFiftyEnriched $Remote '50'
        $EtExitCode = $LASTEXITCODE
        if ($EtExitCode -eq 0) {
            $EtFinalArguments = @($EtArguments)
            $EtFinalArguments[[Array]::IndexOf($EtFinalArguments, '--queue') + 1] = $FinalQueue
            $EtFinalArguments += '--entire-queue'
            & $EtPython @EtFinalArguments
            $EtExitCode = $LASTEXITCODE
        }
    } else {
        & $EtPython @EtArguments
        $EtExitCode = $LASTEXITCODE
        if ($Mode -eq 'RunAll' -and $EtExitCode -eq 0) {
            & $EtPython '-I' '-c' $EtCompletionCheck $EtRunner $PrivateRoot $Queue $Remote '20'
            $EtExitCode = $LASTEXITCODE
            if ($EtExitCode -eq 0) {
                $EtFiftyArguments = @($EtArguments)
                $EtFiftyArguments[[Array]::IndexOf($EtFiftyArguments, '--queue') + 1] = $EtFiftyEnriched
                $EtFiftyArguments[[Array]::IndexOf($EtFiftyArguments, '--newest') + 1] = '50'
                & $EtPython @EtFiftyArguments
                $EtExitCode = $LASTEXITCODE
            }
            if ($EtExitCode -eq 0) {
                & $EtPython '-I' '-c' $EtCompletionCheck $EtRunner $PrivateRoot $EtFiftyEnriched $Remote '50'
                $EtExitCode = $LASTEXITCODE
            }
            if ($EtExitCode -eq 0) {
                & $EtPython @EtIndexArguments
                $EtExitCode = $LASTEXITCODE
                if ($EtExitCode -eq 0) {
                    Write-Output 'Newest 20 and 50 complete. Remaining uploads indexed for a later final round; no final-round download started.'
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
