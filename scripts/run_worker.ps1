param(
    [string]$WorkerName = "worker-a",
    [string]$ServiceName = $WorkerName
)

$workspace = "c:\Users\Asus\Desktop\customs-brain"
Set-Location $workspace
$env:PYTHONPATH = "$workspace;$workspace\backend"
$env:WORKER_NAME = $WorkerName
$env:SERVICE_NAME = $ServiceName
& "$workspace\.venv\Scripts\python.exe" -m workers.worker
