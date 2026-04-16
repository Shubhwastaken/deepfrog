$workspace = "c:\Users\Asus\Desktop\customs-brain"
$workerScript = Join-Path $workspace "scripts\run_worker.ps1"

Start-Process powershell.exe -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $workerScript,
    "-WorkerName",
    "worker-a",
    "-ServiceName",
    "worker-a"
) -WorkingDirectory $workspace

Start-Process powershell.exe -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $workerScript,
    "-WorkerName",
    "worker-b",
    "-ServiceName",
    "worker-b"
) -WorkingDirectory $workspace
