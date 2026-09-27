[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('Start','Checkpoint','Pause','Resume','Finish','Report')][string]$Action,
    [ValidatePattern('^[a-z0-9][a-z0-9-]{0,79}$')][string]$TaskId,
    [string]$Title, [string]$TaskType='implementation',
    [ValidateSet('lazy','guided')][string]$Mode='lazy', [string]$Model='unknown',
    [string]$ThreadId=$env:CODEX_THREAD_ID, [string]$TelemetryPath,
    [string]$RepoRoot, [string]$StorageDir,
    [ValidateSet('unknown','passed','partial','failed','cancelled')][string]$Outcome='unknown',
    [ValidateRange(0,10000)][int]$ReworkCount=0, [string]$Note='',
    [ValidateRange(-1,100)][double]$UsedPercent=-1,
    [int]$WindowMinutes=0, [string]$ResetsAt='', [switch]$ConcurrentUsage
)
# Local, best-effort telemetry. Never reads or emits conversation text.
$ErrorActionPreference='Stop'
$watch=[Diagnostics.Stopwatch]::StartNew()
$utf8=New-Object System.Text.UTF8Encoding($false)
$lock=$null
function Read-Usage($path,$thread) {
    $stream=$null; $reader=$null
    try {
        if (!$path -or !$thread -or !(Test-Path -LiteralPath $path)) { return $null }
        $stream=[IO.File]::Open($path,'Open','Read','ReadWrite')
        $reader=New-Object IO.StreamReader($stream)
        $header=$reader.ReadLine() | ConvertFrom-Json
        if ($header.type -ne 'session_meta' -or $header.payload.id -ne $thread) { return $null }
        # Seek a bounded tail, not Get-Content -Tail over a large rollout.
        $reader.DiscardBufferedData()
        $start=[Math]::Max(0,$stream.Length-4MB)
        [void]$stream.Seek($start,[IO.SeekOrigin]::Begin)
        $tail=$reader.ReadToEnd(); $lines=$tail -split "`n"
        for($i=$lines.Count-1;$i -ge 0;$i--) {
            if($lines[$i] -notmatch '"type"\s*:\s*"token_count"') { continue }
            try {
                $event=$lines[$i] | ConvertFrom-Json
                $u=$event.payload.info.total_token_usage
                if($event.type -ne 'event_msg' -or !$u -or $null -eq $u.total_tokens) { continue }
                $counts=[ordered]@{}
                foreach($key in @('total_tokens','input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')) {
                    if($null -ne $u.$key) { $counts[$key]=[long]$u.$key }
                }
                return [pscustomobject]@{observed_at=$event.timestamp;counts=[pscustomobject]$counts}
            } catch { continue }
        }
    } catch { return $null }
    finally { if($reader){$reader.Dispose()} elseif($stream){$stream.Dispose()} }
    return $null
}
function Save-State($s,$path) {
    $tmp=$path+'.tmp'
    [IO.File]::WriteAllText($tmp,($s|ConvertTo-Json -Depth 12),$utf8)
    Move-Item -LiteralPath $tmp -Destination $path -Force
}
function Close-Segment($s,$usage,$now) {
    $delta=$null
    if($s.segment_usage -and $usage) {
        $values=[ordered]@{}; $valid=$true
        foreach($key in $s.segment_usage.counts.psobject.Properties.Name) {
            if($null -eq $usage.counts.$key -or $usage.counts.$key -lt $s.segment_usage.counts.$key) {$valid=$false;break}
            $values[$key]=[long]$usage.counts.$key-[long]$s.segment_usage.counts.$key
        }
        if($valid){$delta=[pscustomobject]$values}
    }
    $s.segments+=@([pscustomobject]@{start=$s.segment_start;end=$now;usage_start=$s.segment_usage;usage_end=$usage;token_delta=$delta})
}
try {
    if(!$RepoRoot){$RepoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))}
    if(!$StorageDir){$StorageDir=Join-Path $RepoRoot 'Saved/Agent/Metrics'}
    [void][IO.Directory]::CreateDirectory($StorageDir)
    # Exclusive short-lived file lock prevents duplicate Finish records and lost updates.
    $lock=[IO.File]::Open((Join-Path $StorageDir '.lock'),'OpenOrCreate','ReadWrite','None')
    if($Action -eq 'Report') {
        $log=Join-Path $StorageDir 'tasks.jsonl'
        if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log -Tail 10} else {'No completed task records.'}
        return
    }
    if(!$TaskId){throw 'TaskId is required.'}
    $statePath=Join-Path $StorageDir ($TaskId+'.json')
    $now=[DateTimeOffset]::UtcNow.ToString('o')
    $quota=$null
    if($UsedPercent -ge 0){$quota=[pscustomobject]@{used_percent=$UsedPercent;window_minutes=$WindowMinutes;resets_at=$ResetsAt;concurrent=[bool]$ConcurrentUsage}}
    if($Action -eq 'Start') {
        if(Test-Path -LiteralPath $statePath){throw 'Task already exists; use Resume or a new TaskId.'}
        foreach($p in Get-ChildItem -LiteralPath $StorageDir -Filter '*.json' -File){
            $other=Get-Content -LiteralPath $p.FullName -Raw|ConvertFrom-Json
            if($ThreadId -and $other.thread_id -eq $ThreadId -and $other.status -ne 'finished'){throw 'This thread already has an unfinished task; resume/finish it first.'}
        }
        if(!$TelemetryPath -and $ThreadId) {
            $codexRoot=if($env:CODEX_HOME){$env:CODEX_HOME}else{Join-Path $env:USERPROFILE '.codex'}
            $sessions=Join-Path $codexRoot 'sessions'
            $matches=@(Get-ChildItem -LiteralPath $sessions -Filter "*$ThreadId*.jsonl" -File -Recurse -ErrorAction SilentlyContinue)
            if($matches.Count -eq 1){$TelemetryPath=$matches[0].FullName}
        }
        $usage=Read-Usage $TelemetryPath $ThreadId
        $state=[pscustomobject]@{schema=1;task_id=$TaskId;title=$Title;task_type=$TaskType;mode=$Mode;model=$Model;thread_id=$ThreadId;telemetry_path=$TelemetryPath;status='active';started_at=$now;segment_start=$now;segment_usage=$usage;segments=@();events=@();quota_start=$quota;quota_end=$null;summary=$null}
    } else {
        $state=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        if($state.status -eq 'finished') {
            if($Action -eq 'Finish'){$state.summary|ConvertTo-Json -Depth 8 -Compress;return}
            throw 'Task is already finished.'
        }
        if($state.thread_id -and $ThreadId -ne $state.thread_id){throw 'Thread mismatch; do not attribute another conversation to this task.'}
        $usage=Read-Usage $state.telemetry_path $state.thread_id
        switch($Action) {
            'Pause' {
                if($state.status -ne 'active'){throw 'Task is not active.'}
                Close-Segment $state $usage $now; $state.status='paused'
            }
            'Resume' {
                if($state.status -ne 'paused'){throw 'Task is not paused.'}
                $state.segment_start=$now; $state.segment_usage=$usage; $state.status='active'
            }
            'Finish' {
                if($state.status -eq 'active'){Close-Segment $state $usage $now}
                $state.status='finished'; $state.quota_end=$quota
                $seconds=0.0; $known=0; $totals=[ordered]@{}
                foreach($seg in $state.segments) {
                    $seconds+=([DateTimeOffset]::Parse($seg.end)-[DateTimeOffset]::Parse($seg.start)).TotalSeconds
                    if($seg.token_delta){
                        $known++
                        foreach($key in $seg.token_delta.psobject.Properties.Name){
                            if(!$totals.Contains($key)){$totals[$key]=[long]0};$totals[$key]+=[long]$seg.token_delta.$key
                        }
                    }
                }
                $wall=([DateTimeOffset]::Parse($now)-[DateTimeOffset]::Parse($state.started_at)).TotalSeconds
                $tokenStatus=if(!$known){'unknown'}elseif($known -lt $state.segments.Count){'partial'}else{'observed'}
                $quotaDelta=$null
                if($quota -and $state.quota_start -and $quota.resets_at -and $quota.window_minutes -gt 0 -and $quota.resets_at -eq $state.quota_start.resets_at -and $quota.window_minutes -eq $state.quota_start.window_minutes -and !$quota.concurrent -and !$state.quota_start.concurrent -and $quota.used_percent -ge $state.quota_start.used_percent){$quotaDelta=$quota.used_percent-$state.quota_start.used_percent}
                $state.summary=[pscustomobject]@{schema=1;task_id=$TaskId;task_type=$state.task_type;mode=$state.mode;model=$state.model;started_at=$state.started_at;finished_at=$now;wall_seconds=[Math]::Round($wall,2);active_elapsed_seconds=[Math]::Round($seconds,2);paused_seconds=[Math]::Round($wall-$seconds,2);token_status=$tokenStatus;tokens=if($known){[pscustomobject]$totals}else{$null};token_cutoff=if($usage){$usage.observed_at}else{$null};account_percentage_points=$quotaDelta;outcome=$Outcome;rework_count=$ReworkCount;note=$Note;collector_ms=$watch.ElapsedMilliseconds}
            }
        }
    }
    $state.events+=@([pscustomobject]@{action=$Action;at=$now;note=$Note;usage=$usage;collector_ms=$watch.ElapsedMilliseconds})
    if($Action -eq 'Finish') {
        $log=Join-Path $StorageDir 'tasks.jsonl'
        # Recover safely if a previous append succeeded but state persistence failed.
        $exists=$false
        if(Test-Path -LiteralPath $log){foreach($line in [IO.File]::ReadLines($log)){if(($line|ConvertFrom-Json).task_id -eq $TaskId){$exists=$true;break}}}
        if(!$exists){[IO.File]::AppendAllText($log,($state.summary|ConvertTo-Json -Depth 8 -Compress)+[Environment]::NewLine,$utf8)}
    }
    Save-State $state $statePath
    if($Action -eq 'Finish'){$state.summary|ConvertTo-Json -Depth 8 -Compress}
    else {[pscustomobject]@{task_id=$TaskId;status=$state.status;tokens_available=[bool]$usage;collector_ms=$watch.ElapsedMilliseconds}|ConvertTo-Json -Compress}
} catch {
    Write-Warning ('Metrics unavailable: '+$_.Exception.Message+' Continue the development task; do not invent missing data.')
} finally {if($lock){$lock.Dispose()}}
