$ErrorActionPreference='Stop'
$meter=Join-Path $PSScriptRoot 'Measure-AgentTask.ps1'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$testDir=Join-Path $root ('Saved/Agent/MetricsTests/'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($testDir)
$log=Join-Path $testDir 'fixture.jsonl'
$thread='00000000-0000-0000-0000-000000000001'
$utf8=New-Object Text.UTF8Encoding($false)
$header=@{type='session_meta';payload=@{id=$thread}}|ConvertTo-Json -Compress
[IO.File]::WriteAllText($log,$header+"`n",$utf8)
function Usage([long]$n) {
    $row=@{type='event_msg';timestamp=[DateTimeOffset]::UtcNow.ToString('o');payload=@{type='token_count';info=@{total_token_usage=@{total_tokens=$n;input_tokens=$n-10;cached_input_tokens=$n-20;output_tokens=10;reasoning_output_tokens=2}}}}|ConvertTo-Json -Depth 8 -Compress
    [IO.File]::AppendAllText($log,$row+"`n",$utf8)
}
function Run($action,$id,$extra=@{}) {
    & $meter -Action $action -TaskId $id -StorageDir $testDir -ThreadId $thread -TelemetryPath $log @extra | Out-Null
}
function State($id){Get-Content -LiteralPath (Join-Path $testDir ($id+'.json')) -Raw|ConvertFrom-Json}
function Assert($ok,$message){if(!$ok){throw $message}}
Usage 100
Run Start sample @{UsedPercent=30;WindowMinutes=300;ResetsAt='same-window'}
Run Start sample -WarningAction SilentlyContinue
Usage 130
Run Checkpoint sample
Usage 150
Run Pause sample
Usage 500
Run Resume sample
Usage 550
Run Finish sample @{Outcome='passed';ReworkCount=1;UsedPercent=32;WindowMinutes=300;ResetsAt='same-window'}
$s=(State sample).summary
Assert ($s.tokens.total_tokens -eq 100) 'Pause/resume token exclusion failed'
Assert ($s.tokens.input_tokens -eq 100 -and $s.tokens.output_tokens -eq 0) 'Counter accounting failed'
Assert ($s.token_status -eq 'observed' -and $s.account_percentage_points -eq 2) 'Snapshot status failed'
Assert ($s.wall_seconds -ge $s.active_elapsed_seconds -and $s.paused_seconds -ge 0) 'Timing failed'
Run Finish sample
Assert (@(Get-Content (Join-Path $testDir 'tasks.jsonl')).Count -eq 1) 'Finish duplicated a record'
Run Start rollback
Usage 20
Run Finish rollback
Assert ((State rollback).summary.token_status -eq 'unknown') 'Counter rollback was not rejected'
& $meter -Action Start -TaskId missing -StorageDir $testDir -ThreadId $thread -TelemetryPath (Join-Path $testDir 'absent') | Out-Null
Run Finish missing
Assert ($null -eq (State missing).summary.tokens) 'Missing usage was fabricated'
Run Start reset @{UsedPercent=80;WindowMinutes=300;ResetsAt='old-window'}
Usage 40
Run Finish reset @{UsedPercent=2;WindowMinutes=300;ResetsAt='new-window'}
Assert ($null -eq (State reset).summary.account_percentage_points) 'Reset window was compared'
Run Start concurrent @{UsedPercent=20;WindowMinutes=300;ResetsAt='window'}
Run Finish concurrent @{UsedPercent=30;WindowMinutes=300;ResetsAt='window';ConcurrentUsage=$true}
Assert ($null -eq (State concurrent).summary.account_percentage_points) 'Concurrent quota attributed'
Run Start guard
& $meter -Action Finish -TaskId guard -StorageDir $testDir -ThreadId wrong -WarningAction SilentlyContinue | Out-Null
Assert ((State guard).status -eq 'active') 'Thread mismatch mutated task'
Run Finish guard
# A partially written final line must not hide the previous valid usage event.
[IO.File]::AppendAllText($log,'{"type":"event_msg","payload":{"type":"token_count"',$utf8)
Run Start truncated
Assert ($null -ne (State truncated).segment_usage) 'Truncated tail handling failed'
Run Finish truncated
& $meter -Action Start -TaskId partial -StorageDir $testDir -ThreadId $thread -TelemetryPath (Join-Path $testDir 'late.jsonl') | Out-Null
Run Pause partial
[IO.File]::WriteAllText((Join-Path $testDir 'late.jsonl'),[IO.File]::ReadAllText($log),$utf8)
Run Resume partial
Run Finish partial
Assert ((State partial).summary.token_status -eq 'partial') 'Partial coverage not disclosed'
# Old events outside the bounded tail must produce unknown, not an expensive full scan.
[IO.File]::AppendAllText($log,"`n"+('x' * (4MB+1024))+"`n",$utf8)
Run Start bounded
Assert ($null -eq (State bounded).segment_usage) 'Reader exceeded the tail limit'
Usage 70
Run Finish bounded
Assert ((State bounded).summary.token_status -eq 'unknown') 'Unknown start became an invented baseline'
[IO.File]::WriteAllText($log,([IO.File]::ReadAllText($log).Replace($thread,'00000000-0000-0000-0000-000000000002')),$utf8)
Run Start identity
Assert ($null -eq (State identity).segment_usage) 'Mismatched log header was accepted'
Run Finish identity
Write-Host 'Agent task metrics tests passed: pause, deltas, missing/reset counters, quota reset/concurrency, thread guard, partial writes, idempotency, partial coverage, bounded reads, log identity.'
